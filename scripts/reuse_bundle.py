#!/usr/bin/env python3
"""Copy an agent-reviewed source selection into verified, repeatable snapshots.

This tool deliberately does not infer feature semantics or discover imports.
The mapper supplies that analysis through a selection plan.
"""

import argparse
import contextlib
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


class BundleError(Exception):
    pass


VERSION = 1
ROLES = {"runtime", "tool", "test", "configuration", "reference"}
DISPOSITIONS = {"reuse", "adapt", "reference"}
BLOCKED_PARTS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".next",
    ".nuxt", ".output", ".local", ".cache", ".pytest_cache",
}
SECRET_NAMES = {"credentials.json", "secrets.json", "id_rsa", "id_ed25519",
                ".npmrc", ".pypirc", ".netrc", ".dev.vars"}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise BundleError(message)


def relpath(value, allow_dot=False):
    require(isinstance(value, str) and value, "Expected a nonempty relative path.")
    require(not any(ord(c) < 32 for c in value) and "\\" not in value,
            f"Unsupported path: {value!r}")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts,
            f"Path must stay inside its declared root: {value}")
    require(allow_dot or str(path) != ".", "A file path cannot be '.'.")
    return str(path)


def safe_path(root, relative):
    result = root
    for part in PurePosixPath(relpath(relative, allow_dot=True)).parts:
        result = result / part
        require(not result.is_symlink(), f"Symlink requires an explicit resolved source root: {result}")
    return result


def blocked(relative):
    path = PurePosixPath(relative)
    if any(part in BLOCKED_PARTS for part in path.parts):
        return "installed dependencies, cache, VCS or private service state"
    name = path.name.lower()
    template = name.endswith((".example", ".sample", ".template"))
    if ((name == ".env" or name.startswith(".env.") or name.startswith(".dev.vars"))
            and not template):
        return "private environment configuration"
    if name in SECRET_NAMES or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        return "credential or private-key file"
    if name == ".ds_store" or name.endswith((".pyc", ".pyo")):
        return "generated metadata"
    return None


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise BundleError(f"Cannot read JSON at {path}: {exc}") from exc


def fingerprint(path):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f"Not a regular source file: {path}")
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    after = path.lstat()
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode)
    require(signature(before) == signature(after), f"Source changed while reading: {path}")
    return {"sha256": hasher.hexdigest(), "bytes": before.st_size,
            "mode": stat.S_IMODE(before.st_mode)}


def normalize_plan(raw, source):
    require(isinstance(raw, dict), "Selection plan must be an object.")
    plan = json.loads(json.dumps(raw))
    allowed = {"roots", "features", "include", "exclude", "dependencies", "requirements", "unresolved"}
    require(not set(plan) - allowed, f"Unknown plan fields: {sorted(set(plan) - allowed)}")
    roots = plan.setdefault("roots", {})
    require(isinstance(roots, dict), "roots must map root IDs to directory paths.")
    roots.setdefault("project", str(source))
    for name, value in roots.items():
        require(re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name) is not None,
                f"Invalid source root ID: {name}")
        require(isinstance(value, str) and Path(value).is_absolute(),
                f"Source root must be an absolute directory: {name}")
        roots[name] = str(Path(value).resolve())
        require(Path(roots[name]).is_dir(), f"Source root unavailable: {name}: {roots[name]}")
    require(roots["project"] == str(source), "Plan project root does not match --source.")
    features = plan.get("features")
    require(isinstance(features, dict) and features, "Define at least one mapped feature.")
    for name, feature in features.items():
        require(isinstance(name, str) and name and isinstance(feature, dict),
                "Feature IDs must map to feature objects.")
        require(feature.get("disposition") in DISPOSITIONS, f"Invalid disposition for {name}.")
        require(isinstance(feature.get("summary"), str) and feature["summary"].strip(),
                f"Feature {name} needs a summary.")
        require(isinstance(feature.get("entrypoints"), list) and feature["entrypoints"],
                f"Feature {name} needs explicit entrypoints.")
        for ref in feature["entrypoints"]:
            parse_ref(ref, roots)
    require(isinstance(plan.get("include"), list) and plan["include"],
            "Select files/directories in include.")
    for item in plan["include"]:
        require(isinstance(item, dict), "Each include must be an object.")
        item.setdefault("root", "project")
        require(item["root"] in roots, f"Unknown include root: {item['root']}")
        item["path"] = relpath(item.get("path"), allow_dot=True)
        require(item.get("role") in ROLES, f"Invalid include role: {item.get('role')}")
        require(isinstance(item.get("features"), list) and item["features"],
                "Every include needs consuming feature IDs.")
        require(all(name in features for name in item["features"]), "Unknown consuming feature ID.")
    for name in ("exclude", "dependencies", "requirements", "unresolved"):
        plan.setdefault(name, [])
        require(isinstance(plan[name], list), f"{name} must be a list.")
    for rule in plan["exclude"]:
        require(isinstance(rule, dict) and rule.get("root", "project") in roots,
                "Invalid exclusion root.")
        rule.setdefault("root", "project")
        rule["pattern"] = relpath(rule.get("pattern"), allow_dot=True)
        require(isinstance(rule.get("reason"), str) and rule["reason"].strip(),
                "Each exclusion needs a reason.")
    for edge in plan["dependencies"]:
        require(isinstance(edge, dict) and edge.get("kind") and edge.get("evidence"),
                "Dependencies need from/to file references, kind and inspection evidence.")
        parse_ref(edge.get("from"), roots)
        parse_ref(edge.get("to"), roots)
    for gap in plan["unresolved"]:
        require(isinstance(gap, dict) and gap.get("reason"),
                "Each unresolved dependency needs a reason.")
    return plan


def parse_ref(value, roots):
    require(isinstance(value, str) and ":" in value, "File references use root-id:relative/path.")
    root, path = value.split(":", 1)
    require(root in roots, f"Unknown reference root: {root}")
    return root + ":" + relpath(path)


def exclusion(plan, root_id, relative):
    reason = blocked(relative)
    if reason:
        return reason
    for rule in plan["exclude"]:
        if rule["root"] == root_id and (
                fnmatch.fnmatchcase(relative, rule["pattern"])
                or fnmatch.fnmatchcase(relative + "/", rule["pattern"])):
            return rule["reason"]
    return None


def collect_files(plan, output):
    """Expand allowlisted directories, preserving ownership and all exclusions."""
    selected, skipped, folded = {}, {}, {}
    # Record output exclusions even before the first export creates that path.
    for root_id, directory in plan["roots"].items():
        root = Path(directory)
        if output == root:
            skipped[root_id + ":reuse"] = "feature-map output"
            skipped[root_id + ":FEATURE_SCOPE.md"] = "generated feature inventory"
        elif root in output.parents:
            skipped[root_id + ":" + output.relative_to(root).as_posix()] = "feature-map output"

    def consider(root_id, relative, item, explicit=False):
        root = Path(plan["roots"][root_id])
        path = root / relative
        key = root_id + ":" + relative
        reason = exclusion(plan, root_id, relative)
        if path.is_symlink():
            reason = "symlink; resolve its required target as an explicit source root"
        # Do not recursively consume our own artifacts when output is in source.
        if path == output or output in path.parents:
            if output != root or relative == "reuse" or relative.startswith("reuse/"):
                reason = "feature-map output"
            elif relative == "FEATURE_SCOPE.md":
                reason = "generated feature inventory"
        if reason:
            require(not explicit, f"Explicit selection excluded: {key}: {reason}")
            skipped[key] = reason
            return
        path = safe_path(root, relative)
        require(path.exists(), f"Selected source is missing: {key}")
        if path.is_dir():
            for child in sorted(path.iterdir()):
                child_relative = child.relative_to(root).as_posix()
                consider(root_id, child_relative, item)
            return
        require(path.is_file(), f"Unsupported source entry: {key}")
        portable = key.casefold()
        require(portable not in folded or folded[portable] == key,
                f"Case-insensitive path collision: {key} and {folded.get(portable)}")
        folded[portable] = key
        if key not in selected:
            selected[key] = {
                "root": root_id, "path": relative,
                "bundle_path": "source/" + root_id + "/" + relative,
                **fingerprint(path), "features": [], "roles": [],
            }
        record = selected[key]
        record["features"] = sorted(set(record["features"]) | set(item["features"]))
        record["roles"] = sorted(set(record["roles"]) | {item["role"]})

    for item in plan["include"]:
        root = Path(plan["roots"][item["root"]])
        path = safe_path(root, item["path"])
        require(path.exists(), f"Selected source is missing: {item['root']}:{item['path']}")
        consider(item["root"], item["path"], item, explicit=not path.is_dir())
    require(selected, "The selection contains no exportable files.")
    return [selected[key] for key in sorted(selected)], [
        {"file": key, "reason": skipped[key]} for key in sorted(skipped)
    ]


def unresolved_references(plan, files):
    included = {item["root"] + ":" + item["path"] for item in files}
    gaps = list(plan["unresolved"])
    for name, feature in plan["features"].items():
        for ref in feature["entrypoints"]:
            ref = parse_ref(ref, plan["roots"])
            if ref not in included:
                gaps.append({"feature": name, "file": ref, "reason": "Feature entrypoint not exported."})
    for edge in plan["dependencies"]:
        for side in ("from", "to"):
            ref = parse_ref(edge[side], plan["roots"])
            if ref not in included:
                gaps.append({"file": ref, "dependency": edge,
                             "reason": "Declared dependency endpoint not exported."})
    return gaps


def provenance(roots):
    result = {}
    for name, directory in sorted(roots.items()):
        item = {"path": directory, "basis": "selected working-tree bytes"}
        for key, flag in (("git_root", "--show-toplevel"), ("git_head", "HEAD")):
            try:
                proc = subprocess.run(["git", "-C", directory, "rev-parse", flag],
                                      capture_output=True, text=True, timeout=5, check=False)
                if proc.returncode == 0:
                    item[key] = proc.stdout.strip()
            except (OSError, subprocess.TimeoutExpired):
                pass
        result[name] = item
    return result


def seal(manifest):
    return {**manifest, "integrity_sha256": digest(manifest)}


def checked_manifest(path):
    manifest = read_json(path)
    require(isinstance(manifest, dict) and manifest.get("schema_version") == VERSION,
            f"Unrecognized reuse manifest; preserve and reconcile it: {path}")
    content = {key: value for key, value in manifest.items() if key != "integrity_sha256"}
    require(manifest.get("integrity_sha256") == digest(content),
            f"Reuse manifest has been edited or damaged; preserve and reconcile it: {path}")
    require(isinstance(manifest.get("snapshot_id"), str)
            and re.fullmatch("[0-9a-f]{64}", manifest["snapshot_id"]),
            "Invalid snapshot ID.")
    require(manifest.get("snapshot") == "reuse/snapshots/" + manifest["snapshot_id"],
            "Invalid snapshot path.")
    require(digest(manifest["selection"]) == manifest["snapshot_id"],
            "Manifest selection does not match its snapshot ID.")
    return manifest


def verify_snapshot(manifest, output):
    snapshot = safe_path(output, manifest["snapshot"])
    saved = checked_manifest(safe_path(snapshot, "manifest.json"))
    require(saved == manifest, "Current manifest differs from its immutable snapshot.")
    expected = {"manifest.json"}
    for item in manifest["selection"]["files"]:
        relative = relpath(item["bundle_path"])
        expected.add(relative)
        file = safe_path(snapshot, relative)
        require(file.is_file(), f"Snapshot file missing: {file}")
        actual = fingerprint(file)
        require(all(actual[key] == item[key] for key in actual),
                f"Snapshot file was modified; preserve and reconcile it: {file}")
    actual_files = set()
    for base, dirs, files in os.walk(snapshot, followlinks=False):
        for name in dirs + files:
            require(not (Path(base) / name).is_symlink(), "Unexpected symlink in source snapshot.")
        for name in files:
            actual_files.add((Path(base) / name).relative_to(snapshot).as_posix())
    require(actual_files == expected, "Snapshot has unexpected files; preserve and reconcile it.")


def current_manifest(output, source):
    path = safe_path(output, "reuse/manifest.json")
    if path.exists():
        previous = checked_manifest(path)
        require(previous["selection"]["plan"]["roots"]["project"] == str(source),
                "This output belongs to a different source root. Use a separate output.")
        return previous
    return None


def check_owner(output, source):
    path = safe_path(output, "reuse/owner.json")
    if not path.exists():
        return None
    owner = read_json(path)
    require(isinstance(owner, dict), "Unrecognized reuse owner record.")
    content = {key: value for key, value in owner.items() if key != "integrity_sha256"}
    require(owner.get("schema_version") == VERSION and owner.get("integrity_sha256") == digest(content),
            "Reuse owner record was edited or damaged; preserve and reconcile it.")
    require(owner.get("source_root") == str(source), "This output belongs to a different source root.")
    return owner


def delta(previous, files):
    old = {} if previous is None else {
        item["root"] + ":" + item["path"]: item for item in previous["selection"]["files"]
    }
    new = {item["root"] + ":" + item["path"]: item for item in files}
    common = old.keys() & new.keys()
    return {
        "added": sorted(new.keys() - old.keys()),
        "changed": sorted(key for key in common if any(
            old[key][field] != new[key][field] for field in ("sha256", "mode"))),
        "retired": sorted(old.keys() - new.keys()),
        "reclassified": sorted(key for key in common if any(
            old[key][field] != new[key][field] for field in ("features", "roles"))),
    }


@contextlib.contextmanager
def export_lock(reuse):
    lock = reuse / ".export-lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise BundleError(f"Another export or an interrupted export owns {lock}. "
                          "Establish that it is inactive before removing its lock.") from exc
    try:
        (lock / "owner.json").write_bytes(encoded({"pid": os.getpid()}))
        yield
    finally:
        (lock / "owner.json").unlink(missing_ok=True)
        lock.rmdir()


def write_atomic(reuse, filename, value):
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=reuse)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, safe_path(reuse, filename))
    finally:
        Path(name).unlink(missing_ok=True)


def publish_current(reuse, manifest):
    write_atomic(reuse, "manifest.json", manifest)


def copy_source(origin, target, mode):
    fd = os.open(origin, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as source:
        require(stat.S_ISREG(os.fstat(source.fileno()).st_mode),
                f"Source is no longer a regular file: {origin}")
        with target.open("xb") as destination:
            shutil.copyfileobj(source, destination)
    os.chmod(target, mode)


def build_selection(plan, output):
    initial_provenance = provenance(plan["roots"])
    files, skipped = collect_files(plan, output)
    return {
        "plan": plan, "files": files, "excluded": skipped,
        "unresolved": unresolved_references(plan, files),
        "provenance": initial_provenance,
    }


def export_bundle(source, output, raw_plan=None, dry_run=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    require(source.is_dir(), f"Source directory unavailable: {source}")
    owner = check_owner(output, source)
    previous = current_manifest(output, source)
    if raw_plan is None:
        require(previous is not None, "First export requires --plan with a reviewed selection.")
        raw_plan = previous["selection"]["plan"]
    reused_plan = raw_plan == (previous or {}).get("selection", {}).get("plan")
    plan = normalize_plan(raw_plan, source)
    # Existing map-only outputs are adopted without rewriting their Markdown.
    if previous is None and owner is None and output.exists() and any(output.iterdir()) and output != source:
        require((output / "FEATURE_SCOPE.md").is_file(),
                "Nonempty output has no feature inventory or reuse manifest; preserve unrelated files.")
    selection = build_selection(plan, output)
    snapshot_id = digest(selection)
    result = {
        "mode": "update" if previous else ("upgrade" if (output / "FEATURE_SCOPE.md").exists() else "create"),
        "status": "dry-run" if dry_run else "published",
        "snapshot_id": snapshot_id, "files": len(selection["files"]),
        "bytes": sum(item["bytes"] for item in selection["files"]),
        "changes": delta(previous, selection["files"]),
        "excluded": selection["excluded"], "unresolved": selection["unresolved"],
        "selection_reused": reused_plan,
        "verification": "File integrity only; feature completeness and runtime behavior require review.",
    }
    if previous:
        verify_snapshot(previous, output)
    if dry_run:
        return result
    output.mkdir(parents=True, exist_ok=True)
    reuse = safe_path(output, "reuse")
    reuse.mkdir(exist_ok=True)
    with export_lock(reuse):
        require(current_manifest(output, source) == previous, "Output advanced during this export; retry.")
        check_owner(output, source)
        if owner is None:
            write_atomic(reuse, "owner.json", seal({"schema_version": VERSION, "source_root": str(source)}))
        if previous and previous["snapshot_id"] == snapshot_id:
            require(build_selection(plan, output) == selection, "Source changed during the unchanged check; retry.")
            result["status"] = "unchanged"
            return result
        snapshots = safe_path(reuse, "snapshots")
        snapshots.mkdir(exist_ok=True)
        destination = safe_path(snapshots, snapshot_id)
        stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=reuse))
        try:
            for item in selection["files"]:
                origin = safe_path(Path(plan["roots"][item["root"]]), item["path"])
                target = safe_path(stage, item["bundle_path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                copy_source(origin, target, item["mode"])
                require(fingerprint(target) == {key: item[key] for key in ("sha256", "bytes", "mode")},
                        f"Source changed during copy: {origin}")
            # Re-expand directories to catch additions/removals as well as changed bytes.
            require(build_selection(plan, output) == selection,
                    "Selected source changed during export; previous snapshot remains current. Retry after it stabilizes.")
            manifest = seal({
                "schema_version": VERSION, "snapshot_id": snapshot_id,
                "snapshot": "reuse/snapshots/" + snapshot_id,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "bundle_status": "partial" if selection["unresolved"] else "selected-files-copied",
                "selection": selection,
            })
            if destination.exists():
                manifest = checked_manifest(safe_path(destination, "manifest.json"))
                require(manifest["selection"] == selection, "Existing snapshot identity conflict.")
                verify_snapshot(manifest, output)
            else:
                (stage / "manifest.json").write_bytes(encoded(manifest))
                os.rename(stage, destination)
            publish_current(reuse, manifest)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plan", type=Path, help="Reviewed JSON selection; defaults to the previous selection on reruns.")
    parser.add_argument("--dry-run", action="store_true", help="Report selected files and changes without writing.")
    parser.add_argument("--verify", action="store_true", help="Verify the current export without modifying it.")
    args = parser.parse_args()
    try:
        if args.verify:
            require(not args.plan and not args.dry_run, "--verify is separate from export/dry-run.")
            manifest = current_manifest(args.output.resolve(), args.source.resolve())
            require(manifest is not None, "No current reuse manifest.")
            verify_snapshot(manifest, args.output.resolve())
            result = {"status": "verified", "snapshot_id": manifest["snapshot_id"],
                      "verification": "Stored snapshot integrity only; not current-source or runtime parity."}
        else:
            result = export_bundle(args.source, args.output,
                                   read_json(args.plan) if args.plan else None, args.dry_run)
        print(encoded(result).decode(), end="")
        return 0
    except (BundleError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
