# Project Feature Mapper

Maintained by [aipieksel](https://github.com/aipieksel).

Project Feature Mapper is a Codex skill for understanding what an existing app actually does and preparing a reusable handoff for another builder. It follows routes, UI controls, conditions, source files, and dependencies, then writes a feature inventory and source export at the output path you choose.

Give it an input project and an output folder. It examines the current source, maps each page and global behavior, and records what can be reused and what needs adaptation. The output is a source-backed map and code package; it does not build a replacement app or promise visual parity without separate verification.

## What you receive

- `FEATURE_SCOPE.md` for the whole application.
- `pages/<route-id>/page.md` for every route and its behavior.
- A reuse bundle with dependencies, adaptation notes, and preserved snapshots.

## Install and invoke

Copy the entire folder into your assistant's supported skill directory; keep `references/` and `scripts/` beside [SKILL.md](SKILL.md). Python 3.10+ runs the included helpers.

```text
$project-feature-mapper /path/to/source-project /path/to/output
$project-feature-mapper "/path/to/My App" "/path/to/My App Map"
```

The first path is input; the second is output. The skill creates or updates the same source's map and export while preserving prior decisions and notes. An explicit documentation-only request limits the work accordingly. Conflicting ownership or unavailable source remains an explicit boundary.

## Output and verification

`FEATURE_SCOPE.md` is the global inventory; `pages/<route-id>/page.md` records each route. The reuse contract governs implementation copies, dependency closure, adaptation notes and preserved snapshots. Read [the output contract](references/feature-scope-contract.md) and [reuse/update rules](references/reuse-and-updates.md).

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/reuse_bundle.py --help
```

Helper checks establish file/package behavior; they do not prove that an agent mapped every feature or that a browser, service or live provider was verified. Never copy credentials, private configuration or runtime records into a reusable export. This package is licensed under [MIT](LICENSE).
