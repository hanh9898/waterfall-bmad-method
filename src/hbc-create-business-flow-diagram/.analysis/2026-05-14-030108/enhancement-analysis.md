# Enhancement Analysis — hbc-create-business-flow-diagram (Round 3, post-refactor)

## Skill understanding

Generates the HBLab D-06 Business Flow Diagram (Mermaid, AS-IS / TO-BE) from PRD/UX/research artifacts in `{planning_artifacts}`, or from interactive elicitation when those are absent. The refactor reorients Stage 1 around a deterministic source-discovery pre-pass, an explicit resume protocol, an inferred-defaults confirmation block, an explicit no-PRD HALT menu, and a documented headless input contract; Stages 3 and 4 add parallel-lens menus; Stages 2 and 4 add compaction-flush points; the assets folder now carries a real decision-log template with HBC-shaped frontmatter.

## Round-1 friction map — resolved / partially-resolved / still-open

### Resolved

- **Decision-Log Workspace resume protocol (round-1 High).** Stage 1a now reads `stepsCompleted` / `inputDocuments` / `lastStep` from frontmatter plus the last `.decision-log.md` session block, surfaces a one-line summary, and presents an explicit `[R][U][V][N][X]` menu. Update mode is wired through to Stage 3 ("read the latest version from the existing revision-history table … append the next row (`1.3`) rather than overwriting"). Validate-only re-runs Stage 4. Workspace exists from intent-confirmation onwards. This matches the canonical pattern (cf. Decision-Log Workspace — Resume protocol, Update mode).
- **Headless input contract undefined (round-1 High).** New `## Headless Mode` block enumerates `-H`, `--prd-path`, `--mode`, `--scope`, `--diagram-type`, `--no-prd-ok`, gives a defaults heuristics table that names the inference rule for every previously-implicit decision (Resume vs Update vs Fresh, mode, scope, diagram type, parallel-lens menu, auto-fix policy), and pins five named `reason` values to the `blocked` contract. Aligns with the "headless absorbs every assumption" rule.
- **Sharded PRD fallback half-finished (round-1 High).** `discover-planning-artifacts.py` now classifies each PRD entry as `is_sharded: bool` and walks `index.md` linked shards, falling back to `**/*.md` if the index has no links. `check-fr-coverage.py` accepts repeated `--prd` arguments so every shard contributes to the FR set. Stage 1b explicitly says "trust its output instead of re-globbing".
- **Open-floor + intent-before-ingestion (round-1 Medium).** Stage 1c is named "Open-floor invitation and intent gate", explicitly precedes the four-question equivalent, and adapts to context. Stage 1d's no-PRD HALT-menu plus 1e's wrong-skill off-ramp give an early exit before any inferred-defaults work.
- **Stage 2 compaction survival (round-1 Medium).** Stage 2 now mandates a flush (frontmatter `stage_2_actors` / `stage_2_flows`, a `### Discovery snapshot (Stage 2 flush)` log block, plus `stepsCompleted += stage-2`). The decision-log template carries the matching `## Discovery snapshot (Stage 2 flush)` section. Compaction-survival contract is intact.
- **Validation single-lens (round-1 Medium).** Stage 4 ends with `[A][P][C]` parallel-lens menu invoking `bmad-advanced-elicitation` and `bmad-party-mode`. Stage 3 has the same menu pre-validation. Parallel-lens pattern is named, not just gestured at.
- **No quick-confirm for experts (round-1 Medium).** Stage 1e collapses the four serial questions into a single `[C] Confirm and proceed` block with inline override syntax (`mode=… / scope=… / type=… / sources=include:…,exclude:…`). Real Yolo middle.
- **Wrong-skill off-ramp (round-1 Low).** Stage 1e signposts `bmad-create-architecture` and "the relevant sibling" for class-diagram / single-feature-sequence / architecture-diagram intent. Cited inline, fires after open-floor but before the defaults confirmation — early enough.
- **Revision history on re-run (round-1 Low).** Stage 3 increments minor version per Update; never overwrites.
- **Template-absent fallback (round-1 Hostile).** `discover-planning-artifacts.py` returns `fatal: "template_missing"` exit 2; Stage 1b HALTs interactive with a `hbc-setup` hint, headless returns `blocked` with `reason: "template_missing"`. Symmetric across modes.
- **Resolver missing (round-1 Hostile).** Step 1 of On Activation is explicit: "if the resolver script is missing or fails, halt with a clear message — do not attempt to hand-merge TOML". `reason: "resolver_missing"` is in the named-reasons set.

### Partially resolved

- **Stage 1c open-floor.** Present, but only one sentence ("anything not yet captured — references, sketches, prior flows, side notes, paths the discovery scan won't have found"). The pattern's value is the user dumping freeform context that *replaces* the question script, so the prose is fine, but **nothing instructs the agent to actually consume that dump and skip the Stage 1e defaults question if it covered everything**. A user who pastes "use the PRD at `docs/prd.md`, migration mode, multi-flow, default diagram type" will still get the Stage 1e confirmation block. The open-floor exists; the loop that lets it short-circuit Stage 1e does not.
- **Intent-before-ingestion ordering.** Stage 1b (deterministic script discovery) fires before Stage 1c (intent gate). The wrong-skill off-ramp lives in 1e *after* the scan. A wrong-skill activation still triggers a full filesystem scan, generates `{doc_workspace}/.scan/artifacts.json`, and only then offers the off-ramp. The principle says "understand why the user is here before scanning artifacts" — the order is still scan-first.
- **Multiple PRDs disambiguation (round-1 Low).** `discover-planning-artifacts.py` returns every match in `prd[]`. The defaults table says "Source selection → every match" and the override line in 1e accepts `sources=include:…,exclude:…`. But the headless default of "include everything" silently pulls archived/versioned PRDs (`product-v1-prd.md`, `product-prd.md.bak.md`, `prd-archived.md`) into the FR coverage analysis and into the source list. No timestamp-based heuristic, no warning when count > 1. Closer than round 1 but not closed.
- **Dual-output / distillate default.** Round 1 suggested defaulting distillate to on; Stage 5 still says "offer to invoke". Same opt-in shape, just better worded. Not a regression, but not the win either.

### Still open

- **Zero-actor PRD (round-1 Edge).** Stage 2 still lists "user roles, external systems, scheduled processes" but Stage 4's `validate-mermaid.py` will flag a `participant System` flow as having an `orphan_declaration` (if `System` never appears in an arrow) or pass vacuously (if `System` talks to itself via `System ->> System`). No guidance on promoting cron / event / batch trigger to a first-class actor. Pure data-pipeline products still produce shapeless diagrams.
- **Mistakenly-migration greenfield (round-1 Edge).** The mode default heuristic ("AS-IS", "current state", `現状`) is one direction only — text-based inference into migration. The reverse case (mode forced to migration but PRD has no AS-IS material) isn't called out. Stage 2 "run discovery twice" will fabricate an AS-IS section. Particularly hazardous in headless with `--mode=migration` and a greenfield PRD.
- **Update-then-update / targeted single-flow update.** Resume covers re-entry. Update mode says "append the next row" but says nothing about scoping the update to one flow. Re-running Update to fix a typo in Flow B will re-elicit / re-render every flow. The round-1 friction on "update one flow without touching the others" is not addressed.
- **Same-day re-run vs next-day re-run.** The `business_flow_output_path` default is still `{planning_artifacts}/business-flows/D-06-{project_name}-{date}/`. Same day re-run hits the same workspace and resume works; next day re-run creates a **new** workspace and the resume detector in 1a finds an empty `{doc_workspace}/D-06-business-flow-diagram.md` (because the date in the path changed), reports no prior session, and silently goes Fresh. The customize.toml comment now mentions this ("override this to drop the `{date}` segment if re-runs should resume"), but the default behaviour fights the resume protocol the rest of the skill leans on. Discoverability gap: a user setting `--mode=greenfield` on May 14, then re-opening on May 15 to refine, gets two side-by-side workspaces with no cross-reference.
- **Stage 1c open-floor is non-consuming.** See partially-resolved above — open-floor invitation present but no instruction that what the user dumps can replace Stage 1e questions.
- **Wrong-skill scan-first.** See partially-resolved above — off-ramp fires after the deterministic scan, not before.

## New gaps the refactor introduced

### High — `[A][P][C]` parallel-lens menu names skills but does not explain what they do in this context

*Location.* Stages 3 and 4 menus.

*What I noticed.* The menu says `[A] Advanced Elicitation — invoke bmad-advanced-elicitation to stress-test actor coverage and decision branches` and `[P] Party Mode — invoke bmad-party-mode for an analyst + architect + UX review pass`. The skill names them and gives a half-line gloss, which is better than nothing, but does not explain (a) what the user will be asked to do, (b) how long it takes, (c) whether they get to keep their current draft if they pick `[A]` and bail, (d) what "analyst + architect + UX review pass" produces — a single consolidated critique, three parallel critiques, a back-and-forth?

The principles file's **Parallel review lenses** pattern is "fan out 2-3 review subagents … before finalizing significant artifacts". `[P] Party Mode` arguably implements that. `[A] Advanced Elicitation` is a different pattern (single-lens deep critique). Conflating them under the same menu suggests they're interchangeable when they aren't.

*Suggestion.* Either (a) restructure the menu to surface that `[A]` is "one lens, deep" and `[P]` is "three lenses, broad" with their respective cost/output shapes, or (b) drop `[A]` from the validation-stage menu (where parallel lenses are the right pattern) and only offer it at Stage 3 (where elicitation might still surface new actors).

### High — Stage 1a Resume vs Update branching unsafe when frontmatter is partial

*Location.* Stage 1a; defaults table row "Resume vs Update vs Fresh".

*What I noticed.* The heuristic is "Resume if `stepsCompleted` is incomplete, else Update if primary exists, else Fresh". But the decision-log template ships `stepsCompleted: []` — empty list. A primary document created by a prior run that crashed before any `stepsCompleted += stage-N` write will have `stepsCompleted: []`, which is "incomplete" by the heuristic, which triggers Resume. Resume on a primary that hasn't actually progressed past Stage 1 means resuming from a state where the actor list lives only in the decision log (or nowhere). The agent will re-elicit anyway — fine in interactive, but in headless this returns `blocked` with `mermaid_validation_failed` after producing a diagram with no actors.

Also: there's no defined behaviour for "primary exists but decision log was deleted by a user cleanup". Stage 1a says "if `.decision-log.md` is absent at the start of the session, initialize it from `assets/decision-log-template.md`" — initialising a fresh log against an existing primary means losing the prior frontmatter context and Resume becomes nondeterministic.

*Suggestion.* Resume requires `stepsCompleted` to contain at least `stage-1`. If primary exists but `stepsCompleted == []`, treat as Fresh (with a one-line note in the log about discarding a partial prior). Spell the log-absent-but-primary-exists case in 1a: it's a crash-recovery scenario, not a fresh start — read the primary's frontmatter, reconstruct as much of the log as possible, only Fresh if both are absent.

### Medium — `validate-mermaid.py` regex does not handle multi-line message labels or control-flow blocks

*Location.* `scripts/validate-mermaid.py`.

*What I noticed.* `ARROW_RE` matches one line at a time and expects the participant identifiers to be `\w+`. Mermaid `sequenceDiagram` validly supports:

- Multi-line message bodies via backslash-continuation:
  ```
  A ->> B: long message<br/>spanning visual lines
  ```
  Fine, single line. But also:
  ```
  Note over A, B: a multi-line<br/>note
  ```
  The script skips `Note over` entirely (not in `DECL_RE` or `ARROW_RE`), so if `A` only appears in a `Note over A, B` line, the script reports `A` as `orphan_declaration`.

- Block constructs `alt / else / end`, `opt`, `par`, `loop` are valid Mermaid but contain arrow lines indented inside. The arrow regex uses `^\s*` so indentation is fine, but if an actor only appears inside an `alt` branch and is declared above, the script works. If the declaration is *missing* but the actor appears inside an `alt`, the script reports it as `undeclared_participant`, which is correct. If the user uses bracket-quoted aliases (`participant "Order Service" as OS`), `DECL_RE` requires `\w+` for the alias position and won't match the quoted form — the entire declaration is missed, so the alias `OS` gets reported as undeclared in every arrow. This is real Mermaid syntax that diagrammers reach for whenever an actor's display name has spaces.

- Activation indicators on the source side (`+A ->> B`) — `ARROW_RE` doesn't allow `+` / `-` before the source name, only after the arrow. Valid Mermaid like `activate A` is also skipped silently.

*Suggestion.* The script's purpose is "catch the embarrassing stuff (undeclared participants, orphan declarations)". Tighten the doc to "limitations: does not parse quoted aliases, `Note over`, or `activate/deactivate` lines — known false-positives". OR: extend the regexes to handle quoted-alias declarations and skip `Note over … :` references when computing orphans. The principles file says "Script using regex to decide what content MEANS = intelligence leak" — the script is on the safe side of that line, but it should not bark at valid Mermaid the LLM wrote.

### Medium — `discover-planning-artifacts.py` Unicode and symlink behaviour unspecified

*Location.* `scripts/discover-planning-artifacts.py`.

*What I noticed.* The script does `_unique(...)` via `p.resolve()` which follows symlinks. A symlink loop in `planning_artifacts/` would hang `path.resolve()` on some platforms; a symlink to outside `planning_artifacts/` silently includes the target. Nothing in the JSON output flags that a path was a symlink, so a downstream FR-coverage run reads files the user didn't expect to be in scope.

Unicode filenames are fine on read (`encoding="utf-8", errors="replace"`), but the glob patterns `*prd*.md` / `*PRD*.md` won't match Japanese-titled PRDs (e.g. `企画書-prd.md` — fine, contains "prd") and won't match a PRD called `要件定義書.md` even though it's a PRD in Japanese projects. The HBC project specifically uses Japanese template names (D-02_要件定義書_template.md is the requirements doc) — the glob misses everything not English-named. This is a latent gap for the very team the skill targets.

*Suggestion.* (a) Document the symlink behaviour (script "follows symlinks; resolved paths are deduplicated"). (b) Either widen the PRD glob to include `要件定義書*.md` / `企画書*.md` or read the configured `{document_output_language}` and pick localised globs.

### Medium — `check-fr-coverage.py` directory expansion is recursive

*Location.* `scripts/check-fr-coverage.py`, `_gather_prd_ids`.

*What I noticed.* When a `--prd` argument is a directory, the script does `p.rglob("*.md")` — every markdown anywhere under that directory contributes to the FR set. For a sharded PRD whose folder also contains `notes/scratch.md` or `archive/v0.9-prd.md`, those stale or unrelated files inflate `prd_ids`. Stage 1b's discover script enumerates only the linked-from-index shard set; the validator's directory recursion bypasses that discipline. End result: `uncovered` includes FRs from an archived PRD that the team explicitly stopped tracking.

The skill mitigates by saying "Pass each PRD path (or each shard from `artifacts.json` for sharded PRDs) as a separate `--prd` argument", but a busy agent will pass the parent directory by accident.

*Suggestion.* Either remove the `rglob` branch (require explicit shard list — caller passes file paths) or honour an exclusion convention (skip `archive/`, `notes/`, `*.bak.md`).

### Medium — `customize.toml` `business_flow_output_path` defaults `{date}` into the path but resume depends on a stable workspace

*Location.* `customize.toml`, `business_flow_output_path`.

*What I noticed.* See "Still open: same-day vs next-day re-run" above. The customize.toml comment now signposts the override ("To make re-runs resume the previous workspace rather than create a new dated folder, override this to drop the `{date}` segment"), which is good. But this is a footgun-with-a-warning: the warning is in customize.toml, not in SKILL.md, and the default value still has `{date}`. A user who reads SKILL.md and follows the resume narrative will get inconsistent results based on whether they came back on day 1 or day 2.

*Suggestion.* Flip the default to drop `{date}` — Stage 1a's resume protocol already handles "primary exists → offer Update or Fresh", and the workspace folder name doesn't need to encode time when the primary's frontmatter carries the `updated` timestamp anyway. Or, if dated workspaces are deliberate (preserve history side by side), document the resume-look-up-by-project-name behaviour in 1a.

### Low — `[A][P][C]` menu defaults to `[C]` silently in headless without explaining what the lens would have caught

*Location.* Stage 3 and Stage 4 menus, headless rows of the defaults table.

*What I noticed.* The defaults table says "Stage-3 / Stage-4 parallel-lens menu → `[C] Continue` → log auto-decision". A headless run skips potentially valuable critical lenses with a one-line log entry. The automator gets no signal that a parallel-lens review *could* have improved the artifact. This is the opposite of the principle "headless absorbs every assumption made without the user" — the assumption being absorbed here is "the user would have skipped the critique", which is not necessarily true.

*Suggestion.* Add a flag (`--review-lenses=skip|advanced|party`) so an automator can ask for the lens; default to `skip` but make the choice explicit. Or: surface in the JSON return on `complete` a `review_lenses_run: []` field so the caller can audit whether a lens was applied.

### Low — Decision-log template carries `last_touched: yyyy-mm-dd` but Stage 1a reads `updated` from primary frontmatter

*Location.* `assets/decision-log-template.md` frontmatter vs Stage 1a / customize.toml.

*What I noticed.* Decision-log template frontmatter has `last_touched`. The primary document is supposed to carry `updated` (per the Decision-Log Workspace pattern: "the `updated` timestamp from the primary's frontmatter"). The skill never describes a primary-document frontmatter schema. So Stage 1a's "surface a one-line summary" depends on a `lastStep` / `stepsCompleted` / `inputDocuments` schema that's documented only by example in the log template, not in the primary. Cross-cutting field naming (`last_touched` on the log, `updated` on the primary, `stage_2_actors` / `stage_2_flows` in Stage 2 flush) is inconsistent.

*Suggestion.* Either move the timestamp onto the primary (one field, named `updated`), or document the primary's frontmatter schema in Stage 1 once. Picking one term per concept ("one term per concept; pick it and stick to it" — principles file, Writing).

### Low — `discover-planning-artifacts.py` PRD-directory heuristic matches too eagerly

*Location.* `scripts/discover-planning-artifacts.py`, line 134.

*What I noticed.* `prd_dirs = [d for d in artifacts.iterdir() if d.is_dir() and "prd" in d.name.lower() and (d / "index.md").exists()]` — case-insensitive substring on `prd`. A directory called `precedent-research/` won't match, but `apprd/` would (case-insensitive substring match on "prd"). Probably rare in practice but possible.

*Suggestion.* Tighten to a regex match on `\bprd\b` or `^prd[-_]?`. Low-impact.

### Low — Headless mode says `--prd-path` is repeatable but does not say how it interacts with `discover-planning-artifacts.py`

*Location.* Stage 1b headless contract vs Stage 1b script invocation.

*What I noticed.* The `## Headless Mode` table says "`--prd-path=<path>` … Repeatable for sharded PRDs or multiple sources." But Stage 1b unconditionally runs `discover-planning-artifacts.py {planning_artifacts}` — the script does not accept a `--prd-path` filter. If the user passes `--prd-path=docs/prd-v2.md` to override discovery, the script still scans the whole `planning_artifacts` folder and finds `prd-v1.md` as well. The skill is supposed to "use this exact PRD location, skip discovery glob" but the script can't be told to skip.

*Suggestion.* When `--prd-path` is supplied one or more times, either (a) skip the discover script entirely and synthesize an inline `artifacts.json` from the supplied paths, or (b) pass the paths to the script as `--prd-path` arguments and have the script return only those (plus template check + UX/use-case discovery).

## Headless assessment (revisited)

**Level: Headless-ready** — the round-1 "Easily adaptable" gap is closed for the four interactive decisions and Stage 4 auto-fix. Remaining headless gaps are the parallel-lens-skip silent default (Low above), the discover-script-vs-`--prd-path` mismatch (Low above), and the Resume-vs-Update heuristic edge case on partial frontmatter (High above).

The defaults table actually names the heuristic for every interactive decision. The named `reason` values cover the canonical failure modes. The decision log absorbs auto-fixes. JSON contract uses the standard `artifact` / `decision_log` field shape. This is now a textbook headless implementation save for the three items above.

## Facilitative patterns check (delta from round 1)

| Pattern | Round 1 | Round 3 |
| --- | --- | --- |
| Open-floor opening | Missing | Present in Stage 1c. Partially-resolved: doesn't short-circuit Stage 1e. |
| Soft-gate elicitation | Missing | Still missing in Stage 2 (no "anything else before we draw?" gate after actor list). Open-floor in 1c is the entry-gate version, not the transition-gate version Stage 2 needed. |
| Intent-before-ingestion | Partial | Partial → Partial. Intent gate now exists (Stage 1c) but fires *after* the script scan (Stage 1b). Off-ramp still fires after the scan. |
| Capture-don't-interrupt | Missing | Still missing. Decision log is treated as session memory, not a side-channel capture surface for stray observations during Stage 2 discovery. |
| Dual-output | Present (opt-in) | Same. |
| Parallel review lenses | Missing | Present via `[A][P][C]`. New gap: menu doesn't disambiguate what `[A]` vs `[P]` produce, and headless silently picks `[C]`. |
| Three-mode architecture | Partial | Present. Guided + Yolo (1e single confirm block) + Headless all named. |
| Graceful degradation | Present | Improved — template-absent and resolver-missing both have explicit halt branches. Distillator-unavailable handling unchanged. |
| Decision-Log Workspace — Resume | Missing (canonical violation) | Resolved. R/U/V/N/X menu is the textbook implementation. |

## New artifact assessments

- **`assets/decision-log-template.md`** — schema reasonable. Frontmatter (`stepsCompleted`, `inputDocuments`, `lastStep`, `mode`, `scope`, `diagram_type`) supports the resume detection in Stage 1a. The session-block structure (Sources / Mode and scope / Discovery snapshot / Validation findings / Handoff target) matches the named flush points in Stages 2 and 5. One field-naming inconsistency: `last_touched: yyyy-mm-dd` here vs the principles-file expectation of `updated` on the primary (see Low finding above). Otherwise solid.

- **`discover-planning-artifacts.py`** — handles sharded PRDs (walks index links + glob fallback), enumerates whole-doc PRDs and `prd/` directories, classifies entries with `is_sharded` + `shard_paths`. Edge cases identified above: symlinks unflagged, English-only globs, eager `"prd" in name` substring match. Multiple PRDs are returned (no disambiguation). Unicode reading is safe (`errors="replace"`). The script meets the contract Stage 1b states.

- **`validate-mermaid.py`** — covers the embarrassing-stuff bar (undeclared / orphan / missing-expected actors). Limitations identified above: doesn't handle quoted-alias `participant "X" as Y`, ignores `Note over` participants, doesn't handle activation prefixes on source side, doesn't parse `alt/par/loop` block structure (works incidentally because regex is line-oriented, but `else` branches inside an `alt` aren't validated as alternative paths). For an LLM-generated diagram these are recoverable false-positives, but the skill's Stage 4 says "non-deterministic issues … log them and return `blocked` with `reason: mermaid_validation_failed`" — a quoted-alias false-positive in headless mode would silently block a correct diagram.

- **`check-fr-coverage.py`** — clean separation of covered / uncovered / phantom, repeated `--prd` for sharded sets. Edge case identified: directory `rglob("*.md")` pulls in archived PRDs and notes folders. Otherwise correct.

## Findings

| Severity | Location | Issue | Suggestion |
| --- | --- | --- | --- |
| High | `[A][P][C]` menus, Stages 3 + 4 | Menu names skills but conflates "one deep lens" (Advanced Elicitation) and "three parallel lenses" (Party Mode); user has no read on cost/output of each | Disambiguate inline — what each produces, roughly how long, whether the draft is preserved on cancel |
| High | Stage 1a resume heuristic | `stepsCompleted == []` after a crashed prior run triggers Resume incorrectly; primary-with-no-log scenario undefined | Require `stage-1` in `stepsCompleted` to qualify for Resume; spell crash-recovery (primary exists, log gone) as a named case |
| Medium | `validate-mermaid.py` | Quoted-alias `participant "X" as Y`, `Note over` references, and activation prefixes parsed as syntax errors | Tighten regex OR document limitations in script docstring so the agent knows what to ignore |
| Medium | `discover-planning-artifacts.py` | English-only PRD globs miss Japanese-titled HBC PRDs (`要件定義書*.md`, `企画書*.md`); symlinks followed silently | Localise globs (or honour `{document_output_language}`); document symlink behaviour |
| Medium | `check-fr-coverage.py` | Directory `rglob` pulls archived/notes markdown into FR set | Require explicit file paths OR skip common exclude folders |
| Medium | Stage 2 / Stage 1c | Open-floor invitation present but doesn't short-circuit Stage 1e when user already volunteered the answers | Add one clause: "if the open-floor reply covered mode / scope / sources / type, skip the 1e confirmation block and log the inference" |
| Medium | `customize.toml` `business_flow_output_path` | Dated workspace folder fights resume; warning is in customize.toml, not SKILL.md | Drop `{date}` from default OR document workspace lookup by project name in Stage 1a |
| Medium | Stage 1b vs 1c ordering | Deterministic scan precedes intent gate; wrong-skill activations still pay scan cost | Move the wrong-skill off-ramp to 1c (before script invocation) — at minimum, detect Vietnamese trigger ambiguity from the open-floor reply before scanning |
| Low | Stage 1b + headless `--prd-path` | Script doesn't accept `--prd-path` filter; with `--prd-path` set, script still scans whole folder | Either skip script and synthesise inventory from supplied paths, or extend script to accept `--prd-path` |
| Low | Stages 3/4 parallel-lens default | Headless silently picks `[C]` with no return-value signal | Add `--review-lenses` flag or return `review_lenses_run` in JSON |
| Low | `decision-log-template.md` vs primary frontmatter | `last_touched` vs `updated` vs `stage_2_actors` — three different temporal/state fields, no single schema | Document the primary frontmatter schema in Stage 1 once; one term per concept |
| Low | `discover-planning-artifacts.py` PRD dir heuristic | `"prd" in d.name.lower()` matches `apprd/`, `precedential/`, etc. | Tighten to `\bprd\b` |
| Low (still-open) | Stage 2 / Stage 4 (zero-actor PRD) | Pure data-pipeline / batch-only PRD produces shapeless diagram or vacuous actor validation | Add one-line guidance: promote cron / event / batch trigger to first-class participant |
| Low (still-open) | Stage 3 / Stage 4 (mistaken migration) | `--mode=migration` forced on greenfield PRD will fabricate AS-IS in Stage 2 | Add reverse heuristic check in Stage 2: if AS-IS section comes back empty under migration mode, surface mismatch and ask (or `blocked` in headless) |
| Low (still-open) | Stage 1a Update mode | Update mode re-elicits all flows; no targeted-single-flow update path | Document or add `--update-flow=<name>` to scope Update to one flow |

## Top insights

1. **The refactor closed the canonical violation and the headless contract — the two High items from round 1 are genuinely fixed**, not papered over. Resume protocol matches the textbook Decision-Log Workspace shape, the defaults table actually names every previously-implicit decision, and the named `reason` values for `blocked` make headless return values audit-grade. This is the cleanest before/after on the round-1 list.

2. **The remaining gaps cluster around two themes: ordering and silent defaults.** Stage 1b scans before Stage 1c asks intent (ordering); the dated workspace default fights resume (silent default); headless silently skips parallel lenses (silent default); the open-floor invitation invites context the workflow then ignores (ordering — open floor exists, but Stage 1e fires as if it hadn't). Each is small. Each undoes a bit of the round-1 win.

3. **The Python scripts work but each has a long-tail of valid input shapes they don't handle.** Mermaid's quoted-alias and `Note over` forms; PRDs with Japanese titles; sharded PRD directories that also contain archive folders; `--prd-path` flags the discover-script can't honour. None is catastrophic in interactive mode (the agent will route around the script's miss); each is a silent-block in headless mode. The principles file says "scripts handle plumbing"; right now the plumbing handles 90% of inputs and barks at the 10% the LLM was supposed to have already covered.
