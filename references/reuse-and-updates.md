# Reusable source and repeat-run contract

Read this for local-source mapping and for updates to an existing map/export.
The mapper owns semantic discovery, dependency tracing and document reconciliation.
`scripts/reuse_bundle.py` owns deterministic copying, change reporting and source
snapshot integrity. It does not discover imports, rewrite the inventory, prove
feature coverage or validate the replacement application.

The user-facing invocation is simply `$project-feature-mapper <input> <output>`.
Determine create, legacy-map adoption or update from the output's existing state.
The mapper prepares/revises the selection plan and runs the helper commands below
internally; never require the user to supply JSON, helper flags or the word
"update". A helper dry run is an internal scope check, not the final deliverable.

## Output and ownership

Use the user's output directory for both the map and its reusable source:

```text
FEATURE_SCOPE.md
pages/<stable-route-id>/page.md
reuse/
  REUSE.md
  owner.json
  manifest.json
  snapshots/<snapshot-id>/
    manifest.json
    source/project/<original-relative-path>
    source/<external-root-id>/<original-relative-path>
```

The helper manages `owner.json`, `manifest.json` and the snapshot directories.
The mapper maintains `REUSE.md` and the page/global Markdown through focused,
semantic edits. Preserve any owner notes or decisions already present, including
additional files. The helper never replaces those documents. Snapshots contain
complete original files, preserving binary contents and executable permissions;
do not refactor, redact or truncate copies and then claim they match the source.
Exclude sensitive files instead, explaining the missing configuration contract.

The current manifest identifies one snapshot. Identical inputs reuse it without
timestamp churn. Changed inputs create another snapshot; retired files disappear
from the current selection but remain in earlier snapshots. Earlier snapshots
are historical evidence, not additional active features. No automatic cleanup
or migration of the source application's live data is part of this workflow.

## Discover enough implementation to reuse

Start from the feature graph and inspect the full maintained implementation
surface, including non-UI entrypoints. Aim to preserve the reusable implementation,
not a collection of illustrative snippets. For each feature follow:

- Source imports, aliases, barrels, lazy loaders, registries and shared types.
- Server/domain services, persistence, queue/workflow state machines, error and
  cancellation propagation, validators, serializers and compatibility code.
- Runtime file reads, subprocess commands, working directories, configuration
  defaults, relative/absolute roots and environment-variable names.
- App-executed skills and their full linked resource bundles: instructions,
  references, scripts, templates, schemas, assets, helper modules and manifests.
- Tests, deliberately reusable fixtures, sample resources, dependency manifests,
  lockfiles, necessary compiler/bundler configuration and attribution files.
- Existing routes/components as behavioral reference, and reusable browser state
  or event logic hidden inside them. Label presentation-specific source clearly.

An `app/lib` import may depend on `data/tools`, a launcher in `data/scripts`, a
repository-root convention or an external CLI. A `SKILL.md` may invoke code through
prose rather than imports. These are ordinary dependency edges, not optional
extras. Revisit shared consumers when changing a dependency's classification.
Preserve maintained inactive code when useful for reuse, but label its inactive
status; do not equate all copied code with an exposed feature. Evaluate embedded
donor applications by actual runtime involvement rather than copying their whole
historical tree automatically.

Use complete relevant directories where that is safer than selecting individual
helpers, then inspect and explain exclusions. A dependency/import scanner can
assist discovery, but cannot decide whether a runtime branch, resource or skill
reference is required. Keep unresolved targets on the map and in the export.

Separate source from operational data by purpose. For example, `data/tools` can
be implementation while an adjacent `data/app_files` contains private product
records. Explicitly exclude the actual application's runtime stores, logs,
backups, generated output and private configuration. Built-in exporter filters
cover common credential/cache paths, not every possible application's data or
every secret format. Review the selected scope before copying; no generic filter
is a complete secret/data detector. Keep reusable fixtures and runtime-required
generated resources only after verifying their role and contents.

External roots may be exported only when they are identified dependencies within
the authorized task. Declare the exact resolved directory and relevant files;
do not scan a user's general skill collection or follow directory symlinks
implicitly. Unavailable executables, installed providers or restricted/private
resources belong in prerequisites/unresolved boundaries, not copied binaries or
invented substitutes. Project development skills are distinct from app-executed
skills; preserve relevant development guidance as reference when useful.

## Same source + same output: reconcile in place

1. Read the existing `FEATURE_SCOPE.md`, page files, `reuse/REUSE.md`, current
   manifest and any existing decision records. Resolve the supplied source/output
   to real paths. The helper rejects a managed output belonging to another source.
   For a legacy Markdown-only map, verify its recorded source and evidence before
   adopting it. A missing manifest does not mean the prior inventory is empty.
2. Compare current source with the prior selection and snapshot. Rediscover all
   route/registry/background roots, including new paths outside earlier include
   directories. Follow changed producers to every consuming feature/page. A
   renamed route keeps its feature identity when the semantics are continuous;
   record the old/new route mapping. Treat a genuinely removed feature as retired
   with evidence, rather than deleting its history or reintroducing it as active.
3. Update the selection plan to cover the resulting dependency graph. Reuse prior
   plan entries as leads; recheck old unresolved items and decisions. An unchanged
   file can need new documentation because its caller or effective defaults changed.
4. Export the reviewed selection, then reconcile against the immutable snapshot.
   If source changes between inspection and export, revisit the affected claims.
   The helper rejects selected-file changes during copying, but cannot detect
   whether prose written earlier describes different bytes. Use snapshot files
   as the final source authority and explicitly record later source drift.
5. Apply focused edits to the existing Markdown. Preserve owner decisions and
   detail; replace superseded factual claims with current evidence and explain
   conflicts. Preserve retired page files with a retirement note and index link
   rather than deleting them automatically. Update affected forward/reverse links
   and scenarios, including the newly exported implementation references.
6. Reconcile source → features → pages → copied implementations in both directions.
   Report added/changed/retired features, unresolved dependencies and remaining
   runtime checks. Explicitly label any pages not reconciled to the latest snapshot
   if work is incomplete. An export alone is never a completed inventory update.

Do not generate the Markdown from an empty template or blindly rerun a previous
generator that overwrites owner edits. Re-read a document before writing when it
may have changed concurrently, and merge the actual content. Automatic update
does not require another permission question for the same authorized scope.

## Selection plan and executable helper

Create the agent-reviewed plan in task scratch space; its contents are preserved
in the export manifest. The JSON schema uses only these top-level fields:

```json
{
  "roots": {"project": "/absolute/source"},
  "features": {
    "EXTRACT": {
      "summary": "Capture a page and persist its artifacts",
      "disposition": "adapt",
      "entrypoints": ["project:app/server/extract.ts"],
      "verification": "Source-inspected; execution unverified"
    }
  },
  "include": [
    {"path": "app/server", "features": ["EXTRACT"], "role": "runtime"},
    {"path": "data/tools/capture", "features": ["EXTRACT"], "role": "tool"},
    {"path": "package.json", "features": ["EXTRACT"], "role": "configuration"}
  ],
  "exclude": [
    {"pattern": "data/app_files/**", "reason": "Live application records"}
  ],
  "dependencies": [
    {
      "from": "project:app/server/extract.ts",
      "to": "project:data/tools/capture/SKILL.md",
      "kind": "runtime-file",
      "evidence": "The inspected extraction handler reads this skill before invoking its runner"
    }
  ],
  "requirements": [
    {"kind": "runtime", "name": "Node", "details": "Record the inspected required version"}
  ],
  "unresolved": [
    {"feature": "EXTRACT", "reason": "Installed capture executable is unavailable for inspection"}
  ]
}
```

Use actual paths, versions and evidence for the target. Root `project` defaults to
`--source`; additional named roots require explicit absolute directory paths.
Include entries default to root `project`, expand complete directories and merge
shared feature ownership without duplicating files. Roles are `runtime`, `tool`,
`test`, `configuration` and `reference`. Feature dispositions are `reuse`, `adapt`
and `reference`; they express an inspected migration judgment, not tested portability.
Use the feature's details to distinguish active, gated and inactive availability.

Dependency endpoints and entrypoints use exact file references
`root-id:relative/path`. Missing endpoints become explicit unresolved entries.
Executable/environment dependencies go in `requirements`; missing evidence goes
in `unresolved`. Exclusion rules take an optional root, a case-sensitive Python
`fnmatch` pattern and a reason; `directory/**` excludes that directory's contents.
Avoid broad roots where individual maintained source areas can establish the scope.

Invoke the helper through this skill's resolved installation directory:

```sh
python3 /path/to/project-feature-mapper/scripts/reuse_bundle.py \
  --source /absolute/source --output /absolute/feature-map \
  --plan /absolute/task-work/reuse-selection.json --dry-run

python3 /path/to/project-feature-mapper/scripts/reuse_bundle.py \
  --source /absolute/source --output /absolute/feature-map \
  --plan /absolute/task-work/reuse-selection.json

python3 /path/to/project-feature-mapper/scripts/reuse_bundle.py \
  --source /absolute/source --output /absolute/feature-map --verify
```

Inspect dry-run scope and exclusions; this is a read-only review, not an additional
user approval gate. Later helper runs may omit `--plan` to reuse the last selection,
but a complete skill rerun still rediscovers source and revises that selection when
needed. A missing explicitly selected file requires reconciling the selection;
files removed within a retained directory are reported as retired automatically.

The helper rejects path traversal, symlink entries/managed destinations, portable
case collisions and modified managed manifests/snapshots. Directory scans report
excluded symlinks; an explicitly selected symlink is an error. Declare a required
resolved external source instead. It preserves prior output on detected copy or
publication failures; a verified, unpublished snapshot may remain for the next
retry. A concurrent export is rejected by its output lock. After an interrupted
process, establish that the recorded export is inactive before removing only its
stale lock. Never delete a live lock or clean unrelated output to force a retry.

If generated snapshot bytes were manually edited, retain those edits and reconcile
their meaning; do not overwrite them or recompute checksums to hide the conflict.
Keep owner-authored prose in `REUSE.md` or the existing map rather than editing
machine manifests. No hash check establishes that the original implementation
is correct, that every dependency was discovered, or that a new build works.

## Human-readable reuse handoff

Write/update `reuse/REUSE.md` and link it from the global map. Include:

- The current source snapshot identity, scope, provenance and inspection date.
- Feature → entrypoint → shared dependency/resource → consuming-page mappings.
- What can be reused, what needs adapting and what is presentation reference;
  explain concrete framework, storage, lifecycle or path coupling.
- Runtime/package/tool requirements and relevant tests/fixtures, with honest
  copied/inspected/executed evidence distinctions.
- Exclusions, unavailable external dependencies, current defects and unresolved
  decisions. Identify data compatibility work separately from copying source.
- What changed since the preceding map/export and whether each affected page
  has been reconciled to the current snapshot.

Use verified links into the exported snapshot as portable evidence alongside
original-source pointers. Retain source-relative paths and symbols so links can
be remapped on another machine. Do not claim the original commit contains dirty
working files; the manifest's hashes identify the actual copied bytes.

The desired result is a builder who can find both the behavior and its existing
implementation, see the missing prerequisites and adaptations, and reuse the code
without guessing. It is not a guarantee of an independently working replacement.
