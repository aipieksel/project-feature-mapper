"""Behavioral checks for source preservation and repeat exports; no live app access."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("reuse_bundle", Path(__file__).with_name("reuse_bundle.py"))
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


class ReuseBundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.source = self.base / "project"
        self.source.mkdir()
        self.output = self.base / "feature-map"
        self.write("app/run.ts", 'export const run = () => "hello";\n')
        self.write("tools/capture/SKILL.md", "Read references/rules.md and execute scripts/run.py.\n")
        self.write("tools/capture/references/rules.md", "Preserve the full result.\n")
        self.write("tools/capture/scripts/run.py", 'print("fixture")\n')
        self.write("tools/capture/assets/template.html", "<main>Fixture</main>\n")
        self.write("tools/capture/assets/icon.bin", b"\x00\xff\x05")
        self.write("package.json", '{"dependencies":{"example":"1.0.0"}}\n')
        self.plan = {
            "features": {
                "EXTRACT": {
                    "summary": "Capture a page", "disposition": "adapt",
                    "entrypoints": ["project:app/run.ts"],
                    "verification": "source-inspected; not executed",
                }
            },
            "include": [
                {"path": "app", "features": ["EXTRACT"], "role": "runtime"},
                {"path": "tools/capture", "features": ["EXTRACT"], "role": "tool"},
                {"path": "package.json", "features": ["EXTRACT"], "role": "configuration"},
            ],
            "dependencies": [{
                "from": "project:app/run.ts", "to": "project:tools/capture/SKILL.md",
                "kind": "runtime-file", "evidence": "The capture runner reads the selected skill.",
            }],
        }

    def write(self, path, content):
        target = self.source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content if isinstance(content, bytes) else content.encode())
        return target

    def export(self, plan=None, **kwargs):
        return bundle.export_bundle(self.source, self.output,
                                    self.plan if plan is None else plan, **kwargs)

    def manifest(self):
        return bundle.current_manifest(self.output, self.source)

    def snapshot_file(self, relative, root="project", manifest=None):
        manifest = manifest or self.manifest()
        return self.output / manifest["snapshot"] / "source" / root / relative

    def test_export_copies_whole_skill_binary_and_executable_bytes(self):
        script = self.source / "tools/capture/scripts/run.py"
        script.chmod(0o755)
        original = {p.relative_to(self.source): p.read_bytes()
                    for p in self.source.rglob("*") if p.is_file()}
        result = self.export()
        self.assertEqual(result["mode"], "create")
        self.assertEqual(result["unresolved"], [])
        for name, data in original.items():
            self.assertEqual(self.snapshot_file(name).read_bytes(), data)
            self.assertEqual((self.source / name).read_bytes(), data)
        self.assertEqual(self.snapshot_file("tools/capture/scripts/run.py").stat().st_mode & 0o777, 0o755)
        bundle.verify_snapshot(self.manifest(), self.output)

    def test_legacy_inventory_and_owner_notes_are_preserved(self):
        self.output.mkdir()
        contents = {
            "FEATURE_SCOPE.md": "# Owner map\nKeep IDs and these decisions.\n",
            "pages/home/page.md": "Owner's detailed page contract\n",
            "reuse/REUSE.md": "Owner notes on portability\n",
            "other.txt": "Unrelated file\n",
        }
        for name, value in contents.items():
            target = self.output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(value)
        self.assertEqual(self.export()["mode"], "upgrade")
        self.write("app/run.ts", "changed\n")
        self.export()
        for name, value in contents.items():
            self.assertEqual((self.output / name).read_text(), value)

    def test_identical_rerun_reuses_selection_without_churn(self):
        first = self.export()
        path = self.output / "reuse/manifest.json"
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        second = bundle.export_bundle(self.source, self.output)
        self.assertEqual(second["status"], "unchanged")
        self.assertTrue(second["selection_reused"])
        self.assertEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)
        self.assertEqual(len(list((self.output / "reuse/snapshots").iterdir())), 1)

    def test_update_discovers_additions_and_retires_removed_files_without_deleting_history(self):
        self.export()
        old = self.manifest()
        self.write("app/run.ts", "new implementation\n")
        self.write("app/new-route.ts", "new route\n")
        (self.source / "tools/capture/assets/icon.bin").unlink()
        result = bundle.export_bundle(self.source, self.output)
        self.assertEqual(result["changes"]["changed"], ["project:app/run.ts"])
        self.assertEqual(result["changes"]["added"], ["project:app/new-route.ts"])
        self.assertEqual(result["changes"]["retired"], ["project:tools/capture/assets/icon.bin"])
        self.assertEqual(self.snapshot_file("app/run.ts", manifest=old).read_text(),
                         'export const run = () => "hello";\n')
        self.assertFalse(self.snapshot_file("tools/capture/assets/icon.bin").exists())
        bundle.verify_snapshot(old, self.output)

    def test_reverting_source_reuses_earlier_verified_snapshot(self):
        first = self.export()
        original = (self.source / "app/run.ts").read_bytes()
        self.write("app/run.ts", "changed\n")
        self.export()
        self.write("app/run.ts", original)
        restored = self.export()
        self.assertEqual(restored["snapshot_id"], first["snapshot_id"])
        self.assertEqual(len(list((self.output / "reuse/snapshots").iterdir())), 2)

    def test_changed_source_root_cannot_replace_another_inventory(self):
        self.export()
        other = self.base / "other"
        other.mkdir()
        before = (self.output / "reuse/manifest.json").read_bytes()
        with self.assertRaisesRegex(bundle.BundleError, "different source root"):
            bundle.export_bundle(other, self.output)
        self.assertEqual((self.output / "reuse/manifest.json").read_bytes(), before)

    def test_explicit_external_root_is_copied_without_following_symlinks(self):
        external = self.base / "external-skill"
        external.mkdir()
        (external / "SKILL.md").write_text("External fixture skill\n")
        plan = copy.deepcopy(self.plan)
        plan["roots"] = {"external": str(external)}
        plan["include"].append({"root": "external", "path": "SKILL.md",
                                "features": ["EXTRACT"], "role": "tool"})
        self.export(plan)
        self.assertEqual(self.snapshot_file("SKILL.md", "external").read_text(), "External fixture skill\n")

    def test_symlink_dependency_is_excluded_and_reported_unresolved(self):
        outside = self.base / "outside"
        outside.write_text("Keep external data private\n")
        (self.source / "app/link.ts").symlink_to(outside)
        plan = copy.deepcopy(self.plan)
        plan["dependencies"].append({
            "from": "project:app/run.ts", "to": "project:app/link.ts",
            "kind": "import", "evidence": "Fixture import",
        })
        result = self.export(plan)
        self.assertTrue(any(x["file"] == "project:app/link.ts" for x in result["excluded"]))
        self.assertTrue(any(x.get("file") == "project:app/link.ts" for x in result["unresolved"]))
        self.assertEqual(self.manifest()["bundle_status"], "partial")
        self.assertFalse(self.snapshot_file("app/link.ts").exists())

    def test_missing_declared_dependency_does_not_claim_complete_export(self):
        plan = copy.deepcopy(self.plan)
        plan["dependencies"][0]["to"] = "project:app/missing.ts"
        result = self.export(plan)
        self.assertTrue(result["unresolved"])
        self.assertEqual(self.manifest()["bundle_status"], "partial")

    def test_credential_and_runtime_exclusions_keep_source_tools(self):
        self.write("app/.env", "SECRET=fixture\n")
        self.write("app/.env.example", "SECRET=\n")
        self.write("app/node_modules/pkg/index.js", "installed dependency\n")
        self.write("data/app_files/private.json", '{"record":"fixture"}')
        self.write("data/tools/helper.py", "print('source')\n")
        plan = copy.deepcopy(self.plan)
        plan["include"].append({"path": "data", "features": ["EXTRACT"], "role": "tool"})
        plan["exclude"] = [{"pattern": "data/app_files/**", "reason": "Live application records"}]
        result = self.export(plan)
        self.assertFalse(self.snapshot_file("app/.env").exists())
        self.assertFalse(self.snapshot_file("data/app_files/private.json").exists())
        self.assertTrue(self.snapshot_file("app/.env.example").exists())
        self.assertTrue(self.snapshot_file("data/tools/helper.py").exists())
        self.assertEqual(len(result["excluded"]), 3)

    def test_explicit_credentials_or_traversal_selection_is_rejected(self):
        self.write("app/.env", "SECRET=fixture\n")
        for name in ("app/.env", "../outside", "/etc/passwd"):
            with self.subTest(path=name):
                plan = copy.deepcopy(self.plan)
                plan["include"].append({"path": name, "features": ["EXTRACT"], "role": "configuration"})
                with self.assertRaises(bundle.BundleError):
                    self.export(plan)
        self.assertFalse(self.output.exists())

    def test_output_nested_under_selected_source_is_not_recopied(self):
        self.output = self.source / "app/feature-map"
        first = self.export()
        second = self.export()
        third = self.export()
        self.assertEqual(first["files"], second["files"])
        self.assertEqual(second["status"], "unchanged")
        self.assertEqual(third["status"], "unchanged")
        self.assertFalse(any("feature-map" in x["path"] for x in self.manifest()["selection"]["files"]))

    def test_source_root_can_also_host_inventory(self):
        self.output = self.source
        self.write("FEATURE_SCOPE.md", "Existing local map\n")
        self.export()
        self.assertEqual(self.export()["status"], "unchanged")
        self.assertEqual((self.output / "FEATURE_SCOPE.md").read_text(), "Existing local map\n")

    def test_owner_modified_export_is_not_overwritten(self):
        self.export()
        file = self.snapshot_file("app/run.ts")
        file.write_text("Owner modification\n")
        self.write("app/run.ts", "new source\n")
        with self.assertRaisesRegex(bundle.BundleError, "modified"):
            self.export()
        self.assertEqual(file.read_text(), "Owner modification\n")

    def test_owner_modified_manifest_is_not_overwritten(self):
        self.export()
        path = self.output / "reuse/manifest.json"
        value = json.loads(path.read_text())
        value["bundle_status"] = "owner edit"
        path.write_text(json.dumps(value))
        before = path.read_bytes()
        with self.assertRaisesRegex(bundle.BundleError, "edited or damaged"):
            self.export()
        self.assertEqual(path.read_bytes(), before)

    def test_unrelated_nonempty_output_is_preserved(self):
        self.output.mkdir()
        (self.output / "notes.md").write_text("Unrelated notes\n")
        with self.assertRaisesRegex(bundle.BundleError, "Nonempty output"):
            self.export()
        self.assertEqual(list(self.output.iterdir()), [self.output / "notes.md"])

    def test_dry_run_does_not_create_output(self):
        result = self.export(dry_run=True)
        self.assertEqual(result["status"], "dry-run")
        self.assertGreater(result["files"], 0)
        self.assertFalse(self.output.exists())

    def test_source_change_during_copy_keeps_previous_snapshot_current(self):
        self.export()
        before = (self.output / "reuse/manifest.json").read_bytes()
        self.write("app/run.ts", "next version\n")
        original_copy = bundle.copy_source
        changed = False

        def mutate(origin, target, mode):
            nonlocal changed
            original_copy(origin, target, mode)
            if not changed:
                changed = True
                self.write("app/new-during-copy.ts", "concurrent change\n")

        with patch.object(bundle, "copy_source", side_effect=mutate):
            with self.assertRaisesRegex(bundle.BundleError, "changed during export"):
                self.export()
        self.assertEqual((self.output / "reuse/manifest.json").read_bytes(), before)
        self.assertFalse(list((self.output / "reuse").glob(".stage-*")))
        self.assertFalse((self.output / "reuse/.export-lock").exists())

    def test_failed_publication_keeps_previous_snapshot_current(self):
        self.export()
        before = (self.output / "reuse/manifest.json").read_bytes()
        self.write("app/run.ts", "next version\n")
        with patch.object(bundle, "publish_current", side_effect=OSError("simulated disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                self.export()
        self.assertEqual((self.output / "reuse/manifest.json").read_bytes(), before)
        bundle.verify_snapshot(self.manifest(), self.output)
        self.assertEqual(self.export()["status"], "published")

    def test_interrupted_first_export_can_retry_in_the_same_output(self):
        with patch.object(bundle, "publish_current", side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError):
                self.export()
        self.assertFalse((self.output / "reuse/manifest.json").exists())
        self.assertTrue((self.output / "reuse/owner.json").exists())
        self.assertEqual(self.export()["status"], "published")
        bundle.verify_snapshot(self.manifest(), self.output)

    def test_overlapping_includes_merge_shared_feature_ownership(self):
        plan = copy.deepcopy(self.plan)
        plan["features"]["BUILD"] = {
            "summary": "Build a page", "disposition": "reuse",
            "entrypoints": ["project:app/run.ts"],
        }
        plan["include"].append({"path": "app/run.ts", "features": ["BUILD"], "role": "runtime"})
        self.export(plan)
        files = self.manifest()["selection"]["files"]
        entry = next(x for x in files if x["path"] == "app/run.ts")
        self.assertEqual(entry["features"], ["BUILD", "EXTRACT"])
        self.assertEqual(sum(x["path"] == "app/run.ts" for x in files), 1)

    def test_existing_lock_prevents_parallel_publication(self):
        self.export()
        lock = self.output / "reuse/.export-lock"
        lock.mkdir()
        self.write("app/run.ts", "new version\n")
        with self.assertRaisesRegex(bundle.BundleError, "owns"):
            self.export()
        self.assertTrue(lock.exists())

    def test_symlink_output_children_are_not_written(self):
        self.output.mkdir()
        (self.output / "FEATURE_SCOPE.md").write_text("Existing inventory\n")
        outside = self.base / "outside-dir"
        outside.mkdir()
        (self.output / "reuse").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(bundle.BundleError, "Symlink"):
            self.export()
        self.assertEqual(list(outside.iterdir()), [])

    def test_cli_dry_run_export_update_and_offline_verification(self):
        plan_path = self.base / "selection.json"
        plan_path.write_text(json.dumps(self.plan))
        command = [sys.executable, "-B", str(Path(__file__).with_name("reuse_bundle.py")),
                   "--source", str(self.source), "--output", str(self.output)]

        def run(*args):
            result = subprocess.run(command + list(args), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        self.assertEqual(run("--plan", str(plan_path), "--dry-run")["status"], "dry-run")
        self.assertFalse(self.output.exists())
        first = run("--plan", str(plan_path))
        self.assertEqual(first["status"], "published")
        self.assertEqual(run("--verify")["status"], "verified")
        self.write("app/run.ts", "changed through CLI fixture\n")
        updated = run()
        self.assertEqual(updated["changes"]["changed"], ["project:app/run.ts"])
        self.assertNotEqual(first["snapshot_id"], updated["snapshot_id"])
        self.assertEqual(run()["status"], "unchanged")
        # Stored snapshot verification intentionally works without the original source.
        self.source.rename(self.base / "source-offline")
        self.assertEqual(run("--verify")["status"], "verified")


if __name__ == "__main__":
    unittest.main()
