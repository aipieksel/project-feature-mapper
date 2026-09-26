---
name: project-feature-mapper
description: "Supply input then output to map an application's features and export reusable source, skills, tools and dependencies. Automatically create or update the inventory and code package at that output. Use for source-backed feature inventories and reuse handoffs; excludes replacement implementation and visual design specifications."
---

# Project Feature Mapper

## Invocation: two paths

```text
$project-feature-mapper <input> <output>
```

The first path is the source application; the second is the output directory.
Treat this invocation alone as a request to complete the whole mapping and reuse
export workflow. No extra wording, mode flag, update instruction, selection plan
or confirmation is needed from the user. Quote paths containing spaces; resolve
relative paths against the current working directory and treat path text as
data, not shell code.

Automatically inspect the input, discover its features and dependencies, prepare
the export selection, write the reusable source package, reconcile the Markdown
inventory and verify the resulting handoff. Create the output directory if it
does not exist. If it already contains this source's inventory, update that same
inventory and package, including newly added features; preserve decisions, notes
and earlier snapshots. Adopt a matching legacy map without requiring a new output.

Do not stop after a plan, dry run or file copy: complete the documentation and
export steps and report changes plus any unresolved evidence. Only seek missing
information when the two paths cannot be resolved unambiguously or the requested
output has a conflicting owner; normal first runs and repeat runs need no further
instructions. Source-access and evidence limitations still apply as defined below.

## Purpose

Produce a source-backed account of what the application exposes and actually
does, detailed enough for another builder to reproduce its functionality without
access to this conversation. Write `FEATURE_SCOPE.md` as the global map and a
separate `pages/<route-id>/page.md` for every page route. Connect routes, rendered
components, conditions, features and supporting code with direct links. With
local source, also export the implementation and resources needed to reuse
those features. Do not build the replacement or choose its architecture.

Read [the output contract](references/feature-scope-contract.md) before drafting.
It defines the file structure, route identity, graph, evidence boundaries and
level of detail. Scale the documentation to the application; completeness comes
from resolved coverage, not length or the number of links.

## Modes and repeat runs

- **Local source: map and export by default.** Follow the connected traversal
  below and [the reuse and update contract](references/reuse-and-updates.md).
  Capture complete source files, skill bundles, tools, tests and runtime
  dependencies, with explicit adaptation boundaries and unresolved needs.
- **Inventory only:** honor an explicit documentation-only/no-code request.
  Produce or update the Markdown map without replacing an existing code export;
  label that export's older snapshot if the inventory has advanced.
- **Browser/documents only:** map the accessible behavior and mark source
  unavailable. Do not fabricate an implementation package.
- **Same source and output means update.** Read the existing global/page map,
  reuse manifest and notes first. Preserve stable route/feature IDs, owner
  decisions and unaffected detail. Reconcile new, changed, retired and unresolved
  features against fresh source discovery; do not append a duplicate inventory
  or regenerate documents from an empty template. Adopt a legacy Markdown-only
  inventory in place after verifying that it describes the supplied source.

An update is semantic work as well as copying files: recheck changed defaults,
handlers, dependencies and all consuming routes, including newly registered
entrypoints. A cached file list is a starting point, never the scope authority.

## Establish the target

Use the project, repository, running application, source archive or supplied
artifacts identified by the user. Resolve the real root, applicable `AGENTS.md`,
documentation entrypoint, version/revision and relevant local changes before
inspection. Read the project documentation before interpreting its code.

Use a clear target from conversation context; ask only when the target or scope
cannot be established. Default to the whole maintained application unless the
user selects pages, modules or workflows. Record included roles, editions,
platforms and feature-flag configurations. Do not silently narrow a whole-app
request to the first page, default role or easiest module.

Use the explicit output path when supplied. Otherwise follow the project's
documentation convention; without one, place `FEATURE_SCOPE.md` at the project
root and its route files under sibling `pages/`. With only remote/browser
artifacts, use the current workspace's permitted deliverable location. Read the
contract's collision and naming rules before creating route files. For updates,
reconcile the existing index and pages, preserving owner-authored decisions and
unaffected scope. When splitting a prior single-file inventory, carry its detail
and decisions into the appropriate pages/shared sections and repair links. Do
not discard content merely because it is absent from the current source. If a
destination serves unrelated work, use a distinct inventory directory and
record the mapping instead of overwriting it.

The task authorizes inspection, the documentation set and selected source/resource
copies into the requested output. Preserve the original application source,
configuration, records and credentials. Code packaging does not authorize data
migration or copying private settings, credentials or browser profiles. Use a disposable sample or
existing tests for state-changing checks. Live submissions, deletions, provider
calls, deployments or changes to the user's active session require the authority
applicable to that action; document unverified behavior when that authority or
access is absent. Do not expose secret values or customer records in evidence.

## Traverse the application as a connected graph

Build a worklist seeded from **every maintained page-route registration and
active application entrypoint**, not just navigation links. Resolve the actual
router: file-based routes/groups, nested/index routes and inherited layouts,
parameters/catch-alls, aliases/redirects, guards, loaders, route errors and
not-found handling where present. Preserve URL templates and route identity;
do not create a file for every live record ID. Distinguish page routes from
API endpoints and background/CLI entrypoints while retaining their connections.

For each route, recursively trace the render tree and behavior dependencies:

- Resolve imports, path aliases, barrels/reexports, wrappers and lazy imports
  to actual implementations. Follow child mounts, slots/children, portals,
  providers, hooks, callbacks and component registries/configuration. An import
  is a discovery lead, not proof that the component renders there.
- Record each **rendered instance and effective context**: parent callsite,
  passed props, inherited guard/provider state, route parameters and effective
  role/flag/data conditions. Reusing a component on another route or with other
  props adds a distinct usage edge and may add features. Read common code once,
  but revisit its behavior when the context changes.
- Follow both sides of conditional rendering, switch/registry alternatives,
  early returns and loading/error/empty/denied fallbacks. Preserve combined
  predicates across ancestors; a child flag is not sufficient if its parent
  also requires permission. Include effects that reveal dialogs, secondary
  controls, responsive functional variants or deferred content. Enumerate the
  defined branches without inventing impossible combinations; label proven
  unreachable branches with the evidence that makes them unreachable.
- Follow each control/event to its callback, validation, service/API handler,
  permission check, data write, cache/state refresh and visible outcome. Follow
  supporting code across maintained frontend/backend packages when available;
  an HTTP call alone does not prove the server behavior. Trace data/flags back
  to their producers and settings forward to real consumers.
- Reverse-search callers, registrations and consumers of discovered components,
  actions and services. Reconcile against a fresh inventory of maintained route,
  component/feature registry and non-UI entrypoint definitions so a missed root
  or unexposed helper is not concealed by a perfect traversal of known roots.

Track nodes and edges with stable identities and direct source links. Each edge
records its relation (renders, passes, gates, invokes, reads, writes, navigates),
effective condition, source callsite and destination, consuming route/page and
inspection status. New edges enter the worklist until no discovered in-scope
edge remains unaccounted for. Deduplicate by node **and relevant context**, not
filename alone. Record cycle/back-reference edges without recursively expanding
them forever; summarize repeated/data-driven instances by their template and
behavior variants, not every row value.

Keep unresolved dynamic imports, remote schemas, inaccessible modules and
runtime-selected components on the map with the exact missing evidence. They
prevent a completeness claim for that branch, but not useful work elsewhere.
Do not guess an edge or classify unknown runtime behavior as dead code. A text
search, AST result or empty worklist alone is not semantic proof of completeness.

## Scope every page and its behavior

1. **Map the application before detailing it.** Follow router and navigation
   definitions, entrypoints, menus, registries and feature flags. Include direct
   links, query/hash states, nested tabs, dialogs, drawers, context menus,
   settings, onboarding, permission/error surfaces and alternate entrypoints.
   Include active non-UI jobs, commands, imports/exports and integrations. A
   sidebar or screenshot alone is not the surface map.
2. **Inventory every element on each in-scope surface.** Inspect templates,
   configuration-driven schemas and render conditions as well as handlers.
   Include actions, links, inputs and all options; headings, labels and help;
   tables with actual columns/row actions; lists, totals, charts, status
   indicators, progress, notifications and empty/error content. Expand secondary
   and conditional controls. Record semantic purpose and behavior, not styling
   or physical placement. Enumerate fixed options exactly; describe dynamic
   option sources and rules instead of copying every live record.
3. **Trace each interaction to its outcome.** Follow event handler to state,
   validation, service/API, authorization, persistence and returned UI state.
   Cover eligibility, defaults, limits, dependencies, loading/disabled states,
   success, cancellation, failure, retry and side effects. Inspect downstream
   consumers before claiming a saved preference has an effect. Trace computed
   indicators and charts to their data, formula, units and refresh conditions.
4. **Trace active behavior back to an entrypoint.** Inspect domain services,
   background registrations, schemas, serializers, migrations and integration
   adapters for behavior the UI map missed. Distinguish active background work,
   API/CLI-only capability, gated functionality, unused helpers, stored-only
   fields and historical code. An exported function or schema field alone does
   not establish a supported feature. Consult history only for a specific gap or
   an explicitly historical request; old features do not become current scope.
5. **Follow complete user journeys across boundaries.** Check how navigation,
   selection, edits and results behave across pages, dialog dismissal, refresh,
   restart, import/export and roles where applicable. Distinguish draft versus
   saved data, preference storage versus enforcement, client hints versus
   enforced permission, and a displayed success message versus a durable effect.

Persist the route/component/feature relationships in the global map, with each
route linked to its own `page.md`. Each page lists everything it renders,
including inherited/shared components, their elements and context-specific
features. Shared contracts may be defined once in the global document, but every
page still enumerates its instances, conditions and controls and links to those
contracts. Do not replace individual controls with phrases
such as “standard CRUD,” “usual settings” or “all common actions.”

Repository search and scripts help find candidates; they cannot decide feature
coverage. Exclude dependencies, build output and archives from the initial scan,
then inspect them only when they are the actual runtime authority or explain a
specific gap. Never silently exclude a maintained subapplication.

## Use evidence honestly

Prefer current source and configuration for implementation truth, and the
running application for what is exposed and observable. Use tests and existing
documentation as corroboration or discrepancy leads. Identify when the checkout
and running version differ; do not combine them into an imaginary single build.
When evidence conflicts, show the discrepancy and its effect on the inventory.

Use the available authorized browser/computer surface when the user or project
requires it, or when runtime inspection is needed to resolve important UI
uncertainty. Honor explicit surface choices and applicable browser instructions.
Source-only inspection is valid: mark behavior as source-verified and state what
was not exercised. Do not launch a live system or install dependencies merely
to turn a documentation task into a test campaign.

With screenshots, browser access or documents only, describe supported visible
and observed behavior, explicitly bound the scope, and mark hidden conditions,
persistence and backend enforcement unknown. Do not infer that a control works
from its label, or that a feature is absent because one screenshot lacks it.
Continue with accessible evidence and report specific unresolved surfaces;
never present a partial inventory as complete.

Keep availability separate from evidence strength. For example:

- “Visible retention setting; preference is saved, but no active deletion
  consumer exists in the inspected source” describes a partial implementation.
- “Retention setting observed; enforcement not inspected” describes a knowledge
  gap, not an unimplemented feature.
- “Rename service implemented; no exposed action or active caller found in the
  inspected application” does not imply a Rename button exists.

## Preserve functionality without documenting design

Keep control types and labels, page identity, navigation destinations, tab
meaning, dialog open/close behavior, focus/keyboard behavior, gestures and
functional accessibility. Keep responsive differences only when they change
available controls or behavior. Preserve exact values, formats, timing and
thresholds when they affect results or interoperability.

Exclude palettes, typography, spacing, sizes, radii, shadows, CSS classes,
design tokens, visual composition, grid geometry, asset-placement recipes and
pixel-reproduction instructions. A table's columns and sorting are functional;
its column widths and appearance are not. A waveform's inputs and timing are
functional; its color and dimensions are not. Describe a color-coded status by
its meaning, not its paint value.

This exclusion applies to the behavior documentation, not to the bytes of
exported source. Preserve complete selected files, including embedded styles
and required assets; label old presentation as reference/adaptation material.
Do not strip code or skill content to make its snapshot visually neutral.

Write behavior in plain language that survives a stack change. Preserve external
protocols, file formats, URLs, shortcuts and platform-specific capabilities when
they affect compatibility. Put internal symbols/paths in evidence pointers;
do not prescribe the current framework, component library or internal database
structure as the new architecture. Do not erase genuine platform behavior just
to make the prose sound generic.

## Reconcile, then finish

Before finalizing, reconcile the graph in both directions: every discovered
page route has a page file; each render/condition/action/dependency edge has
page/global coverage or an explicit evidence-backed exclusion or unresolved
boundary; every described capability has supporting code or accurately bounded
runtime/document evidence. Verify reverse links from shared code/features to
all consuming pages. Check inherited predicates, alternate branches and
defaults, not just route/file counts. Cross-check repeated facts across pages,
shared contracts and workflows for contradictions.

Verify documentation links, source files and actual symbols/line locations at
the inspected revision. Links must lead to the code that establishes the claim,
not just an existing file. Report open edges and unchecked configurations; do
not promise that direct links make omissions impossible.

Use the output contract's behavior-based rebuild checks to test whether a builder
could infer the same observable outcome, including failure and persistence.
Document defects faithfully under current behavior. Distinguish confirmed parity
requirements from unresolved rebuild decisions; do not silently fix defects or
instruct the builder to reproduce them as intended behavior.

Deliver the global index and linked page files, and briefly report their scope,
evidence basis and specific gaps. Keep shared and non-UI scope reachable from
the index. For local-source export, also link `reuse/REUSE.md`, the current
manifest and the selected immutable source snapshot. Report added/changed/retired
scope, unresolved dependencies and verification separately. The export helper
checks copying/integrity, not semantic completeness or runtime functionality.
For inventory-only work, no reuse manifest is required. Do not add a screenshot
archive, architecture plan or separate report per component by default. The
handoff must remain understandable without this conversation.
