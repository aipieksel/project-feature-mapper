# Project Feature Mapper

Maintained by [aipieksel](https://github.com/aipieksel).

A source-backed feature inventory and reusable-code export skill. It maps routes, UI controls, conditional behavior, supporting source and dependencies, and writes a handoff for another builder. It excludes replacement implementation and visual design specifications.

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
