# Feature scope documentation contract

For local-source runs, also follow [reuse and updates](reuse-and-updates.md).
The Markdown map remains the behavior authority; the reuse package supplies
versioned implementation evidence and adaptation context. On repeat runs update
this same set, preserving decisions and stable identities. Link the current
snapshot and label any sections not yet reconciled with it; a new code export
does not automatically refresh the prose or establish feature completeness.

Write a detailed product behavior reference organized around the application's
real functional areas. Use prose for sequences and exceptions, compact tables
for parallel controls/settings, and internal links for shared contracts. Keep
separate conditions explicit; do not compress a complex feature into a slogan.

`FEATURE_SCOPE.md` is the global index and connected map. Detailed route scope
lives in `pages/<route-id>/page.md`. Adapt headings to the project and omit
irrelevant categories. Do not impose an arbitrary word limit or number of
features. If work pauses, save the index, completed/partial pages and explicit
remaining routes/edges; resume that set rather than starting over.

## File structure and route identity

For example, given three page routes `/`, `/projects/:projectId` and
`/projects/:projectId/settings`, an inventory can contain:

```text
FEATURE_SCOPE.md
pages/
  home/page.md
  projects--param-project-id/page.md
  projects--param-project-id--settings/page.md
```

Use the project's existing inventory convention when present. Choose stable,
filesystem-safe IDs derived from the complete route identity, including app or
router namespace when needed. Preserve exact route patterns in the index; never
infer URLs back from slugs. Distinguish literal, parameter, optional, catch-all,
index and route-group identities. Detect collisions (including case-folding and
sanitized names); add a stable disambiguator and record the mapping. Treat route
strings as data, never unchecked filesystem paths. Protect existing unrelated
`pages/`, `page.md` and owner-authored content by choosing a distinct inventory
directory before writing.

Give **every page-route definition its own `page.md`**, including parameterized
templates and nested pages. Document one parameter template rather than one file
per real ID. An alias/redirect gets a short page describing its exact source,
destination, conditions and any state/query/parameter transfer, with links to
the target page for shared content. Different route definitions that use one
component remain separate page files. Variants of one route caused by query,
hash, tab, role or flags belong in that route's page with their predicates; use a
separate page only when the router defines a separate page route.

Inherited shells/layouts are enumerated on each consuming page, with common
behavior linked to a shared global contract. Dialogs, drawers and other surfaces
without their own route belong to their owning page(s); identify shared mounts
and conditional ownership. Keep API/background/CLI-only behavior in the global
document and connect it to consuming pages rather than inventing page URLs. For
an application without routes, apply the same per-page structure to its actual
windows/screens/modes and record that identity scheme.

## Global map in FEATURE_SCOPE.md

Keep the global document useful as a starting point, not a second copy of all
pages. It contains:

- The opening scope/evidence statement below and a complete route-to-file index:
  exact pattern, route identity, source registration, guards, rendered page,
  parent/alias/redirect relationships and link to its `page.md`.
- A connected map of routes, component instances, feature/action nodes,
  conditions and supporting data/service/API/background nodes. A linked table
  is sufficient; a Mermaid diagram may clarify relationships but cannot replace
  the detailed evidence. Preserve mount/callsite identity and effective context
  so multiple uses of the same component do not collapse into one behavior.
- A reverse index from shared components, features/actions and supporting source
  to every consuming route/page, with usage conditions and links back to local
  detail. A standalone file list or import tree does not satisfy this map.
- Shared functional contracts and cross-page journeys, non-UI features, inactive
  and partial capabilities, global evidence gaps and cross-page rebuild checks.
- Coverage reconciliation: routes and edges inspected; exclusions and unresolved
  edges with reasons and missing evidence; remaining role/flag/data variants.

A practical relationship table is:

| From node / route context | Relation and effective condition | To node / feature | Source callsite → implementation | Page scope / status |
|---|---|---|---|---|

Use readable node identities and links, not a disconnected bag of identifiers.
Every link chain must explain actual functional involvement. Index source by
relevant symbols/callsites where a file serves multiple unrelated features.

## Required content in every page.md

Start with page identity, exact route/entry, purpose/actors and a backlink to the
global map. Describe parameters, aliases, direct-entry/refresh constraints,
inherited guards/layouts and related/nested routes. Then provide:

1. **What renders:** the complete component-instance composition, including
   inherited shell content, wrappers with behavioral effects, nested children,
   lazy/registered components and secondary/portal surfaces. For each instance,
   identify parent mount/callsite, props/context affecting behavior, conditions,
   features and direct links to the implementing source. Express semantic
   containment rather than visual positioning.
2. **Every element and feature:** apply the surface/element and behavior sections
   below to everything rendered on this route, including shared controls. Name
   the owning instance and list its actual actions, passive content and states;
   link detailed shared contracts without omitting the local inventory.
3. **Conditional coverage:** record each predicate's source, inherited conditions,
   evaluated state/role/flag/parameter/data, true/false/fallback result, resulting
   elements/actions and whether source-inspected, runtime-observed, unresolved
   or proven unreachable. Include compound guards, early returns, loading,
   errors, empty data and deferred interactions, not just visible defaults.
4. **Connected behavior:** trace entry/control → callback/handler → validation
   and authorization → service/API/data → persistent/transient effect → UI
   outcome. Link the actual callsites and implementations, dependencies,
   navigation destinations, consumed shared contracts and affected other pages.
5. **Rebuild scope and limits:** concrete behavior-based scenarios, page-specific
   evidence boundaries, defects/owner decisions and coverage gaps. Distinguish
   current behavior from proposed fixes and unseen runtime behavior.

Each page must explain its own functional scope while using explicit links for
shared detail. A route title and link to a component file alone is insufficient.

## Opening and scope

Start with `# <Project> — Feature Scope` and a short statement of:

- Product purpose, intended actors and the jobs they perform.
- Inspected project/version/revision and date; relevant local changes or a
  different observed runtime version. Use “unknown” where unavailable.
- Included application boundaries, roles, variants and evidence channels.
- Explicit exclusions and known inaccessible surfaces. State that visual design
  is excluded and whether coverage is complete **within the inspected boundary**.

Report implemented current behavior. Put planned, legacy, unexposed, ineffective
and uncertain capabilities in clearly named boundaries, not the active feature
list. Avoid claims such as “100% complete” when role/flag/runtime coverage is
unknown. A reader must be able to tell source verification from runtime proof.

## Surface and element inventory

Give each page or meaningful surface a stable descriptive identity, its route or
entry condition, purpose, available actors, nested surfaces and related workflows.
Routes include functional query/hash parameters and direct-entry constraints.
Non-web systems may use windows, menus, commands or modes instead of URLs.

For each surface in its owning page file, document all of its elements. A useful table is:

| Element / visible label | Type and meaning | Availability / states | Action, data or outcome | Detail / evidence |
|---|---|---|---|---|

The table is a compact index, not a substitute for a complex behavior section.
Record exact labels/options/error wording when known and useful for matching the
interface. Include these only where present:

- Headings, explanatory/help text, tooltips and validation messages, with their
  purpose and display conditions. Do not transcribe every live data value.
- Inputs: label, type, allowed values, default, requiredness, validation,
  dependencies and how/when edits apply.
- Buttons, links and menus: every item, destination or effect, enabled/disabled
  conditions, confirmation, cancellation, keyboard/focus and dismissal rules.
- Tables/lists: every column and row/bulk action, data meaning, search matching,
  filters, sort defaults/direction/ties, pagination, selection and empty states.
- Charts, counts and indicators: data source, computation/aggregation, units,
  time range, refresh, selection and drill-down. Flag decorative or placeholder
  data honestly rather than assigning an invented analytical meaning.
- Tabs/dialogs/drawers/overlays: how entered, controls revealed, state retained
  or discarded, escape/outside-close behavior and return destination.
- Notifications/sounds/progress: event, content/meaning, timing, repetition,
  dismissal and suppression controls, if observable or source-established.

Functional grouping and parent/child relationships are included. Physical
position, composition, sizing and aesthetic choices are excluded.

## Feature behavior and end-to-end journeys

Give substantial features their own sections. Describe, when applicable:

1. Purpose, actor, entrypoints and prerequisites.
2. Exact inputs/options/defaults, constraints and validation order.
3. Trigger and ordered steps through intermediate states to the outcome.
4. Data read/written; transient versus saved state; effects on other features.
5. User-visible success, empty, denied, partial, failure and cancellation paths.
6. Retry/resume/undo, duplicate submissions, cleanup and recovery behavior.
7. Permission/ownership checks and meaningful dependencies.
8. Confirmed limitations, unexposed branches, discrepancies and evidence.

Preserve actual boundaries: editing a completion preview may affect Copy without
updating history; closing a modal may discard edits; cancelling a job may stop
future work while keeping existing output. Do not fill those blanks with familiar
application conventions. Record precise timings/limits only when established.

Describe journeys across surfaces separately when their ordering or shared state
would be lost in isolated feature entries. Include alternate triggers, handoffs,
saved results and downstream consumers. A compact state-transition table helps
when several actions are available only in specific states.

## Cross-cutting functional contracts

Consolidate repeated contracts in the global document and link to them from the
affected pages/features; maintain reverse links to all consumers.
Cover the following where they exist; they are discovery prompts, not features
to add or empty chapters to create:

- **Settings:** each option/range and step, effective default, scope (user,
  workspace, project, device or global), save timing, dependencies and actual
  effect. Distinguish displayed defaults, runtime defaults and migrated values
  when they differ. Identify stored-but-unused settings.
- **Commands and triggers:** shortcuts, gestures, voice phrases, API/CLI calls,
  timers, webhooks, startup jobs and menu actions; eligibility and conflicts.
- **Data and persistence:** entities, identities/relationships, uniqueness,
  defaults, lifecycle, retention/deletion and recovery. State what survives
  navigation, refresh, restart or reauthentication. Describe storage semantics
  without prescribing implementation internals for the rebuild.
- **Import/export:** every exposed path, format/version, fields and omissions,
  selection/scope, file naming, encoding, validation, duplicate handling,
  overwrite/merge rules, failure atomicity and round-trip losses. A Download
  button alone is not proof of a complete portable export.
- **Permissions:** actors/roles, ownership, feature flags, visible availability
  versus enforced authorization, denied/expired/revoked behavior and recovery.
- **Integrations:** supported providers and operations, inputs/outputs,
  configuration, authentication method (never credentials), external effects,
  timeouts/retries/limits, degraded behavior and what was actually verified.
- **Background work:** registration/trigger, lifetime, progress, cancellation,
  failure, retries and durable results; note implementation without an active
  consumer or scheduler.
- **Signals and diagnostics:** real status transitions, event messages/sounds,
  progress semantics and logging controls/output. Distinguish a real metric or
  durable log from a simulated indicator or merely displayed destination.

## Evidence and unresolved boundaries

Attach **clickable source links** to material route/render/condition/action/data
claims, including exact defaults and exceptions. Link the actual registration or
mount/callsite as well as its implementation; a component definition alone cannot
prove which page renders it. Link predicates and downstream consumers, not just
an API import. Shared evidence may support a coherent feature section; avoid
repeating a citation after every sentence.

Resolve each file and symbol in the inspected source. Use verified repository
permalinks at the inspected commit when available; for local-only sources use
Markdown file links with absolute targets and supported line locators (for
example `[loadNote — src/notes.ts](/absolute/project/src/notes.ts:42)`). Follow the
current renderer's link conventions; never invent a remote URL, commit or line
anchor. Keep project-relative path and symbol in the label/text and record the
source root/revision in the index so links can be remapped when moving stacks or
machines. For dirty/uncommitted code, identify that snapshot explicitly instead
of citing a commit that contains different code. Use relative Markdown links
between generated documents and validate their anchors.

With only runtime or document evidence, record the route, action, actor/state,
observed result or real external document locator. Mark source unavailable;
never fabricate direct code links to satisfy the format. Existing test files
count as source evidence; claim a passed test only if execution is verified.

Make two distinctions clear in ordinary prose or compact columns:

- **Availability:** exposed and implemented, conditionally available, active
  non-UI capability, partly wired/stored only, unexposed/inactive, or unknown.
- **Evidence:** source-verified, runtime-observed, test-verified, documented only,
  inference, or unknown. Multiple evidence types may apply; none is automatically
  equivalent to another.

When source and UI or documentation disagree, cite both and state what is known.
To claim “not implemented,” inspect the relevant consumers and registration
paths; otherwise say “not found in the inspected scope.” Disambiguate absent
control, inaccessible role and inaccessible backend. Do not fabricate UI actions
from model fields, exports or an unused service.

End the global map with a compact coverage summary linking each route to its page
and each active non-UI area to its contract. Reconcile route roots, contextual
component usages, predicates and action/data edges against the source and the
reverse consumer index. Each page also records its local open edges. Account for
cycles, excluded/unreachable paths and runtime-only unknowns explicitly; no
unchecked branch disappears merely because a file was already read. Verify
source link targets semantically as well as mechanically. Counts are optional
and must come from the actual map. Document current defects without burying
working features in recommendations.

## Behavioral rebuild checks

Include concrete acceptance scenarios in each page for its substantial features
and non-obvious boundaries; put shared/cross-page scenarios in the global
document with links from affected pages. Derive them from inspected behavior:

> Given <actor, state and persisted data>, when <action and input>, then
> <observable outcome, data effect and what survives the relevant boundary>.

Cover the main outcome plus applicable conditional, validation, authorization,
failure/recovery and persistence cases. Share scenarios across tightly related
controls rather than creating a test per label. Include exact options and
limits when they distinguish correct behavior. These are handoff criteria, not
a claim the replacement exists or tests ran.

Separate established behavior to preserve from defects and ambiguous behavior
requiring an owner decision. Keep suggested enhancements out of the current
inventory and parity checks unless the user explicitly adopts them. A builder
should not have to guess what exists, what is intended, or what remains unknown.
