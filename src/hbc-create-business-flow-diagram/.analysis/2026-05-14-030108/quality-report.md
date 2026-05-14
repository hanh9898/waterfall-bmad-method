# BMad Quality Analysis: hbc-create-business-flow-diagram (Round 3)

**Analyzed:** 2026-05-14T03:01:08Z | **Path:** `C:/Users/HanhNT2/stc-erp-bmad-custom/src/hbc-create-business-flow-diagram`
**Round-1 baseline:** `.analysis/2026-05-14-021953/quality-report.md` (Good, 2 broken + 12 opportunities)
**Interactive report:** quality-report.html

## Assessment

**Good** — Round-3 refactor delivered: both round-1 broken items are gone, the Decision-Log Workspace pattern is now genuinely operational (Resume/Update/Validate/Fresh menu, Stage 2 compaction-flush, revision-history bump), the headless contract is enumerated with named blockers, and three Python scripts carry ~2,600–5,200 tokens of plumbing out of the prompt. Grade stays Good but the floor is substantially raised; the remaining work clusters on script hygiene (no tests, missing PEP 723, regex/glob long-tail), one misplaced build-time artifact in `references/`, and resume-flow edge cases that nibble at the wins. To reach Excellent the skill needs `scripts/tests/` established, the build-scratch decision log moved out of `references/`, the dropped hand-merge fallback restored to match sibling skills, and the Stage 1a Resume heuristic hardened against partial-frontmatter and dated-workspace footguns.

## What's Broken

None. Both round-1 broken items are resolved.

> Round-1 had two broken items — the sharded-PRD `index.md`-only fallback is genuinely fixed in `scripts/discover-planning-artifacts.py` (walks every linked shard, falls back to glob), and `.decision-log.md` was moved off the skill root. The destination chosen for the latter (`references/.decision-log.md`) introduced a new high-severity issue covered under Opportunity 2 below — but no current item rises to "broken" severity. Nothing the scanners caught would stop the workflow from running.

## Opportunities

### 1. Script hygiene and long-tail input coverage (high — 9 observations)

The three new scripts carry their plumbing weight cleanly — no intelligence leaks into regex/glob decisions, the SKILL.md `Trust its output instead of re-globbing` sentence is honoured. But they ship without tests, without PEP 723 metadata, with one CLI flag diverging from the sibling contract, and with regex/glob coverage that bars at valid input the LLM might legitimately produce — Mermaid quoted-alias declarations, Note-over participants, Japanese-titled PRDs (the exact target audience for HBC), recursive directory expansion that sweeps archived shards into the FR set. Each item is small; together they're the surface area where silent headless blocks will accumulate.

**Fix:** Add PEP 723 blocks to all three scripts; create `scripts/tests/` with at least one test per script covering its regex/glob contract (especially the Mermaid arrow regex and the FR regex); rename `check-fr-coverage.py`'s `--output` (currently the D-06 input path) to `--d06` and let `-o/--output` be the JSON sink; extend `validate-mermaid.py` regex to handle quoted-alias declarations and skip `Note over` references when computing orphans; localise `discover-planning-artifacts.py` PRD globs (or honour `{document_output_language}`) to include Japanese-titled PRDs; switch `check-fr-coverage.py` from `rglob` to explicit file paths (or skip common exclude folders).

**Observations:**
- All three scripts missing PEP 723 inline metadata block — `scripts/*.py:1` (determinism + scripts-temp)
- `scripts/tests/` directory does not exist — `scripts/tests/:0` (determinism + scripts-temp)
- `check-fr-coverage.py` CLI flag binding inconsistent with sibling scripts — `scripts/check-fr-coverage.py:59` (determinism)
- `validate-mermaid.py` regex misses quoted-alias `participant "X" as Y` (silent block in headless) — `scripts/validate-mermaid.py` (enhancement)
- `validate-mermaid.py` regex doesn't handle `Note over` / activation prefixes — `scripts/validate-mermaid.py` (determinism + enhancement)
- `discover-planning-artifacts.py` English-only PRD globs miss `要件定義書*.md` / `企画書*.md` — `scripts/discover-planning-artifacts.py` (enhancement)
- `discover-planning-artifacts.py` follows symlinks silently — `scripts/discover-planning-artifacts.py` (enhancement)
- `check-fr-coverage.py` directory `rglob` pulls in archived/notes markdown — `scripts/check-fr-coverage.py` (enhancement)
- `discover-planning-artifacts.py` uses exit code 2 for template-missing (should be 1) — `scripts/discover-planning-artifacts.py:143` (determinism)

### 2. Build-time scratch parked in runtime references/ (high — 1 observation)

`references/.decision-log.md` is the skill author's working memory across build sessions — the round-1 / round-2 / round-3 fix log, with phrases like *"round 3 comprehensive fix pass"*. The path-conventions principle is explicit: `references/` is for prompt content carved out of SKILL.md. The runtime decision log lives at `{doc_workspace}/.decision-log.md` inside the user's project, generated from `assets/decision-log-template.md`. By living under `references/` the build log pollutes any future references-scan, gets counted against the skill's reference-prose budget at **1,705 tokens** (the largest single file in the skill after SKILL.md), and risks misleading downstream LLMs into reading build-time fix-log prose as runtime guidance.

**Fix:** Delete `references/.decision-log.md` now that the skill is final, or move it out of the published skill — to `.analysis/` or a sibling `_build-notes.md` outside `references/`. The original round-1 fix advice's *"delete if the build is final and the log was working memory only"* branch was the correct resolution.

**Observations:**
- `references/.decision-log.md` is build-time author log in a runtime-only directory — `references/.decision-log.md:0` (architecture + prompt-metrics-prepass)

### 3. Activation block silently diverges from institutional sibling pattern (high — 1 observation)

`SKILL.md:34-36` dropped the canonical hand-merge fallback every sibling carries (`bmad-create-architecture`, `hbc-create-invest-epics-and-stories`, every `bmad-agent-*`): *"If the script fails, resolve the `workflow` block yourself by reading these three files in base → team → user order."* The refactor replaced it with *"halt with a clear message — do not attempt to hand-merge TOML"*, citing round-1 M1. But the institutional pattern decided differently — when the resolver is genuinely absent (corrupted install, first-run before BMad bootstrap), the LLM hand-merging three files is the difference between this skill working and dying while every sibling on the same machine continues to work. The divergence is silent — nothing in the skill flags that it deliberately omits the fallback.

**Fix:** Either restore the canonical hand-merge fallback paragraph (one right way to merge TOML, written down explicitly — "fragile-operation invocation" per the principles), or document the deliberate divergence in the `customize.toml` header so a reviewer comparing siblings can see why this skill chose not to degrade.

**Observations:**
- Hand-merge fallback dropped without documenting the divergence from siblings — `SKILL.md:36` (architecture)

### 4. Resume protocol edges and Stage 1 ordering (medium — 4 observations)

The Decision-Log Workspace Resume/Update/Validate/Fresh menu is the round-3 win — but four soft edges nibble at it. (1) The heuristic *"Resume if `stepsCompleted` is incomplete"* fires Resume on a primary that crashed before any `stepsCompleted += stage-N` write, because the template ships `stepsCompleted: []`. (2) The dated workspace folder default (`D-06-{project_name}-{date}`) silently spawns a new workspace on day-2 re-runs and bypasses the resume detector — the `customize.toml` comment warns about this but SKILL.md narrates resume as if it Just Works. (3) Stage 1c open-floor invites the user to dump intent and context, but Stage 1e fires its full confirmation block regardless of whether the open-floor reply already covered mode/scope/sources/type. (4) Stage 1b (scripted scan) precedes Stage 1c (intent gate) and Stage 1e (off-ramp), so wrong-skill activations still pay the scan cost. Each undoes a small piece of the round-1 win.

**Fix:** Require `stage-1` in `stepsCompleted` to qualify for Resume; treat primary-with-`stepsCompleted: []` as Fresh with a log note; define the log-absent-but-primary-exists crash-recovery branch explicitly. Drop `{date}` from `business_flow_output_path` default (or document the by-project-name resume lookup in Stage 1a). Add one clause to Stage 1c: *"if the open-floor reply covers mode/scope/sources/type, log the inference and skip the 1e confirmation block."* Move the wrong-skill off-ramp into 1c (before script invocation).

**Observations:**
- Resume heuristic fires on partial frontmatter from crashed prior run — `SKILL.md:99` (enhancement)
- Dated workspace folder fights the resume protocol — `customize.toml` (enhancement + customization)
- Stage 1c open-floor invitation does not short-circuit Stage 1e — `SKILL.md` (enhancement)
- Wrong-skill off-ramp fires after the scripted scan, not before — `SKILL.md` (enhancement)

### 5. `[A][P][C]` parallel-lens menu — clarity, deduplication, and silent default (medium — 3 observations)

The Stage 3 and Stage 4 menus are duplicated verbatim with slightly different lens-target framings. The menu names Advanced Elicitation (one deep lens) and Party Mode (three parallel lenses) under the same letters as if interchangeable, and headless silently defaults to `[C]` with no return-value signal about which lenses could have been applied. The plumbing duplication invites drift; the menu conflation lets the user pick the wrong cost/output shape; the silent headless skip absorbs an assumption ("the user would have skipped the critique") the principles file explicitly warns against.

**Fix:** Pull the menu plumbing into one earlier definition; refer back from Stage 3 and Stage 4 with stage-specific lens-targets only. Disambiguate inline: `[A]` = one lens, deep, ~N minutes, draft preserved; `[P]` = three lenses (analyst + architect + UX), broad, parallel. Add a `--review-lenses=skip|advanced|party` flag (default `skip`) so the automator chooses explicitly, and surface `review_lenses_run: []` in the JSON return contract.

**Observations:**
- Menu duplicated verbatim at Stage 3 and Stage 4 — `SKILL.md:202` (architecture)
- Menu conflates Advanced Elicitation (one deep) with Party Mode (three parallel) — `SKILL.md:202` (enhancement)
- Headless silently picks `[C]` with no audit signal — `SKILL.md` (enhancement)

### 6. SKILL.md size approaching multi-branch ceiling (medium — 1 observation)

SKILL.md is now 260 lines / 3,772 tokens / 9 fenced blocks / 2 tables / 20 sections. The principles size guidance for multi-branch SKILL.md is up to ~250 lines if each branch has brief contextual explanation; this skill is 10 lines past that without genuine multi-branching (linear five-stage workflow with a headless variant). New weight is concentrated in the Headless Mode block (~40 lines including two tables and the JSON contract — natural carve-out candidate to `references/headless-contract.md`), the Language Rules paragraph (still reference-shaped at four prose bullets), and the duplicated parallel-lens menus (Opp 5 above). Not broken at this size; flag because each future addition compounds past the ceiling.

**Fix:** Carve Headless Mode (input flags table, defaults table, JSON contract) into `references/headless-contract.md` with a one-paragraph SKILL.md pointer. Compress Language Rules to two sentences or push to `references/language-rules.md`. Deduplicate the parallel-lens menu (Opp 5 above) for another ~10 lines.

**Observations:**
- SKILL.md 260 lines, 10 over the multi-branch size guidance — `SKILL.md` (architecture + prompt-metrics-prepass)

### 7. Stage 4 deterministic-fix prose hands judgment back to the LLM (medium — 1 observation)

`SKILL.md:229-231` instructs headless to *"apply only deterministic fixes (e.g. add a missing `participant` declaration where the alias is unambiguous from message lines)."* The phrase *"unambiguous from message lines"* is a judgment call disguised as a deterministic rule — there's no script step that emits a list of safe-to-auto-apply fixes. The LLM defines "unambiguous" at runtime and writes back to user files in headless mode — the highest-trust action the skill takes, gated only by prose.

**Fix:** Extend `validate-mermaid.py` to emit `auto_fixable: bool` per issue (true only when alias appears in exactly one arrow line and no declared participant conflicts). The prompt applies those mechanically; everything else returns `blocked`. Or remove auto-fix entirely and let headless always return `blocked: mermaid_validation_failed` — matches the round-3 design rationale that "headless never silently invents".

**Observations:**
- Headless auto-fix gated by prose-defined "unambiguous", not script output — `SKILL.md:229` (architecture + determinism)

### 8. Schema and labelling tidies (low — 5 observations)

Five small consistency issues that don't change behaviour but accumulate into a drift surface: JSON contract shows literal `{skill-name}` / `{doc_workspace}` that the agent must substitute before emission; `assets/decision-log-template.md` frontmatter carries unresolved placeholders with no interpolation instruction at Stage 1a; three different temporal/state field names (`last_touched` on the log, `updated` on the primary, `stage_2_actors` / `stage_2_flows` in Stage 2 flush); Vietnamese `vẽ sơ đồ` / `vẽ D-06` triggers still missing (round-1 L3 carry-over); `workflow_type` prepass still reports `complex` while the build-time `.decision-log.md` says "Simple Workflow".

**Fix:** Add a one-line reminder to the JSON contract section with a concrete example. Add a Stage 1a sentence that the decision-log template is interpolated like the primary template. Pick one field name per concept (e.g. `updated` everywhere). Add `vẽ sơ đồ`, `vẽ D-06` to the description's quoted trigger list. Update the build-time decision log to acknowledge the lived classification.

**Observations:**
- JSON contract template variables may leak on verbatim copy — `SKILL.md:85` (architecture)
- decision-log template frontmatter carries unresolved `{skill-name}` / `{project_name}` / `yyyy-mm-dd` — `assets/decision-log-template.md:1` (architecture)
- Field naming drift: `last_touched` vs `updated` vs `stage_2_actors` — `assets/decision-log-template.md` (enhancement)
- Vietnamese `'vẽ'` triggers still absent from description — `SKILL.md:3` (architecture)
- `workflow_type` prepass reports complex, build log claims Simple — `references/.decision-log.md:16` (architecture)

### 9. Stage 1a resume-state synthesis duplicates plumbing the discover-script could provide (low — 1 observation)

Stage 1a tells the LLM to read `stepsCompleted` / `inputDocuments` / `lastStep` from the primary's frontmatter plus *"the last session block in `.decision-log.md`"*, synthesise a one-line summary, then present the R/U/V/N/F/X menu. Reading two structured files and emitting a `"Last step: X | Steps complete: [Y, Z]"` summary is exactly the plumbing `discover-planning-artifacts.py` already does for source discovery. Acceptable as-is; flag because the discover-script precedent makes a second pre-pass cheap.

**Fix:** Extend `discover-planning-artifacts.py` (or add a sibling `resume-state.py`) emitting `{ summary, last_step, steps_completed, primary_exists, mode_from_prior_session }`. Stage 1a reads the JSON and presents the menu.

**Observations:**
- Resume-state synthesis done in prompt where a script could compress it — `SKILL.md:99` (architecture)

## Strengths

- **Decision-Log Workspace pattern is operational, not aspirational.** R/U/V/N/X menu, Stage 2 compaction-flush, revision-history bump on Update, Stage 5 closing session block — all four load-bearing pieces present and reading correctly. The Stage 2 flush is the single most valuable round-2/3 add: makes the skill compaction-survivable in a way most multi-stage workflows aren't.
- **Headless mode is structurally complete.** Input flags table, defaults table with named heuristics, JSON contract with enumerated `reason` values (`template_missing`, `no_prd_and_no_interactive_in_headless`, `planning_artifacts_unreadable`, `mermaid_validation_failed`, `resolver_missing`). An automator can drive this from CI.
- **Intelligence placement on the three scripts is correct.** Each script stays in the plumbing lane (glob, regex extract, set membership); the LLM owns "is the AS-IS/TO-BE delta clear", "is the layout readable" — judgment. Clean split, modulo the auto-fix caveat in Opp 7.
- **Sharded-PRD story is real now.** `discover-planning-artifacts.py` reads `index.md`, extracts every linked `.md`, falls back to a glob if links are absent. Round-1's broken sharded-PRD fallback is genuinely fixed in code. Token saving realised at ~2,600–5,200 per Stage-1+Stage-4 run.
- **Customization surface collapsed from two output scalars to one.** `business_flow_output_path` with `{date}=YYYY-MM-DD` documented inline is cleaner than the prior split, and the override comment teaches the right mental model. The ~200 new SKILL.md lines added **zero new customize.toml scalars** — every visible seam (resume menu, parallel-lens menu, headless flags, defaults heuristics) was correctly kept out of `[workflow]`.
- **Language Rules treatment sharper than round 1.** Three-rule split (file names always English, template English-source, output in `{document_output_language}`) plus explicit carve-outs (Mermaid keywords, code identifiers, AS-IS/TO-BE) is exactly the kind of judgment context that earns its file weight.
- **On Complete reads from already-resolved memory.** Round-1 M5 "two-call waste" explicitly prevented at `SKILL.md:36, 259`.
- **Hook count holds at one (`on_complete`).** Stage 2/3/4/5 flush/menu/save seams are all places where an author drifts into `on_<event>` hook proliferation. Holding at one keeps the surface auditable.

## Detailed Analysis

### Architecture

Refactor lands most round-1 structural asks cleanly — `## Overview` present, Decision-Log Workspace operational, customization collapsed, three scripts move parse/coverage out of the prompt. Cost: SKILL.md grew to 260 lines (10 over the multi-branch guidance). Two genuine new structural problems: `references/.decision-log.md` is build-time scratch in a runtime-only slot, and the activation block silently dropped the hand-merge fallback every sibling carries. Several smaller items — parallel-lens menu duplication, JSON template-variable leak risk, decision-log template placeholders not interpolated, Vietnamese trigger still missing — are covered in Opportunities 5–8.

### Determinism & Distribution

Intelligence placement is sound. The three scripts stay strictly in the plumbing lane (glob, regex extract, set membership); SKILL.md consumes their JSON outputs by name. The round-1 finding "PRD/UX/research discovery done in-prompt" is resolved — SKILL.md §1b explicitly says *"Trust its output instead of re-globbing."* Stage 4 cleanly splits deterministic checks (script) from judgment checks (layout readability, AS-IS/TO-BE delta clarity, language consistency). Round-1 token estimate (2,400–5,200) is **realised at ~2,600–5,200 per Stage-1+Stage-4 run**, with sharded PRDs compounding the win. Remaining gaps are script hygiene (no PEP 723, no `scripts/tests/`), one CLI inconsistency, and regex/glob long-tail coverage — none re-open the in-prompt-determinism wound.

### Customization Surface

**Posture: opted-in.** Surface collapsed from five workflow-specific scalars to four (`business_flow_template`, `diagram_type`, `business_flow_output_path`, `on_complete` hook). The ~200 new SKILL.md lines added zero new scalars. Every visible seam (resume menu, parallel-lens menu, headless flags, defaults heuristics) was correctly kept out of `[workflow]` — the author resisted four distinct surface-bloat temptations in one refactor. Hook count remains at one. The one residual customization-flavoured friction is that `business_flow_output_path`'s `{date}` default fights the resume protocol — covered under Opportunity 4. Round-1 anti-temptations (project_mode toggle, per-skill language override) remain correctly absent.

### User Experience

The two round-1 High items (canonical Decision-Log Workspace violation and headless contract undefined) are **genuinely fixed**, not papered over. The Resume protocol matches the textbook pattern, the defaults table names every previously-implicit decision, the named `reason` values make headless returns audit-grade. Headless potential moved from `easily-adaptable` to **`headless-ready`**.

**Journeys:**

- **First-timer** (BA activating after `bmad-create-prd`): hits open-floor at 1c, then a clean inferred-defaults confirmation at 1e. The four-question batch from round 1 is gone. *Friction:* Stage 1e fires even when the open-floor reply already covered mode/scope/sources/type. *Bright spots:* open-floor invitation, inferred-defaults block, wrong-skill off-ramp.
- **Expert** (BA on the fifth project this quarter): Stage 1e's single `[C] Confirm` block plus inline override syntax (`mode=… / scope=… / type=…`) is the real Yolo middle round 1 asked for. *Friction:* Stage 1b scan still runs before the intent gate. *Bright spots:* quick-confirm path; headless flags double as expert-mode shorthand.
- **Edge-case:** crashed prior run with `stepsCompleted: []` triggers Resume on a state with no actor list; day-2 re-run lands in a new dated workspace and silently goes Fresh; zero-actor PRD still produces a shapeless diagram; `--mode=migration` forced on greenfield PRD fabricates AS-IS in Stage 2; Update mode re-elicits all flows with no targeted-single-flow path. *Bright spots:* template-absent halts symmetrically; resolver-missing has explicit branch.
- **Hostile environment:** template-absent and resolver-missing both halt cleanly. `bmad-distillator` unavailable correctly skipped with a note. *Friction:* resolver-missing halts where every sibling hand-merges and continues (silent divergence); `validate-mermaid.py` reports quoted-alias or `Note over` participants as undeclared — silent block in headless on valid Mermaid.
- **Automator:** textbook headless implementation save for three items — parallel-lens menu silently defaults to `[C]` with no return-value signal; `--prd-path` repeatable per the spec but discover-script can't honour it (scans whole folder regardless); Resume-vs-Update heuristic edge case on partial frontmatter.

## Round-1 Resolution Audit

| Item | Status | Notes |
|---|---|---|
| **Broken: Sharded PRD `index.md`-only fallback** | Resolved | `scripts/discover-planning-artifacts.py` walks links, falls back to glob |
| **Broken: `.decision-log.md` at skill root** | Resolved-then-regressed | Moved to `references/` to silence path-standards lint — but that's the wrong destination (now Opp 2) |
| Op #1 — Decision-Log Workspace half-built | Resolved | R/U/V/N/X menu, Stage 2 flush, revision-history bump |
| Op #2 — Headless contract undefined | Resolved | Input flags table, defaults table, JSON contract with named reasons; `primary→artifact` |
| Op #3 — Three validators in prompt; no `scripts/` | Resolved | Three scripts; token saving realised. New gap: no `scripts/tests/` (Opp 1) |
| Op #4 — On Activation boilerplate | Withdrawn | The 5-step block is the institutional pattern across every sibling. Round 1 was wrong to flag. *But* the hand-merge fallback paragraph was dropped — now Opp 3 |
| Op #5 — Stage 1 form-shaped | Partially-resolved | Open-floor + inferred-defaults + off-ramp all present. Open-floor doesn't short-circuit 1e; off-ramp fires after the scan (now Opp 4) |
| Op #6 — Structure/scaffolding | Resolved | `## Overview` added; stage-N headings neutralised; Stage 1 split; On Complete reads from memory |
| Op #7 — `output_dir` + `output_folder_name` split | Resolved | Collapsed to `business_flow_output_path`; `{date}=YYYY-MM-DD` documented |
| B1 addendum — No-PRD HALT menu | Resolved | Stage 1d explicit menu; headless returns `blocked` with named reason |
| B2 addendum — `[A][P][C]` menu after Stage 3/4 | Resolved-with-new-issues | Present at both stages, but duplicated/conflated/silent-default (now Opp 5) |
| B3 addendum — Template-existence check | Resolved | Script returns `template_exists`; symmetric halt/blocked across modes |
| B5 addendum — `assets/decision-log-template.md` HBC schema | Resolved | Template created with matching frontmatter and session-block structure |
| B7 addendum — `hbc-setup/assets/module-help.csv` row | Resolved | Per round-1's round-3 fix log |
| B8 addendum — Rename `primary→artifact` | Resolved | `SKILL.md:85` |
| L3 round-1 — Vietnamese `vẽ` triggers | Still-open | Unchanged from round 1 (now under Opp 8) |

**Net:** 2/2 broken resolved, 11/12 opportunities resolved or substantially addressed, 1 opportunity unchanged, 1 withdrawn as never-having-had-a-real-precedent. Refactor closed every load-bearing concern.

## New Findings Introduced by the Refactor

The ~90 lines of SKILL.md growth and three new Python scripts surface:

- `references/.decision-log.md` mis-placed (high — Opp 2)
- Activation hand-merge fallback dropped, silently diverging from siblings (high — Opp 3)
- `scripts/tests/` directory absent (high — Opp 1)
- Three scripts missing PEP 723; `check-fr-coverage.py` CLI flag binding diverges; regex/glob long-tail gaps (medium x several — Opp 1)
- SKILL.md 10 lines over multi-branch size guidance (medium — Opp 6)
- Stage 1a Resume heuristic unsafe on `stepsCompleted: []` (high — Opp 4)
- `[A][P][C]` menu duplicated and conflated; silent headless default (medium — Opp 5)
- Stage 4 deterministic-fix prose leaks judgment back to LLM (medium — Opp 7)
- Decision-log template frontmatter placeholders not interpolated; field-naming drift (low — Opp 8)

## Recommendations

1. **Create `scripts/tests/`, add PEP 723 to all three scripts, align `check-fr-coverage.py` CLI with siblings.** Mechanical fixes that close the script-hygiene gate. *Resolves 5, effort low.*
2. **Delete `references/.decision-log.md`** (or move to `.analysis/_build-notes.md` outside the published surface). The skill is final; build-time scratch doesn't belong in `references/`. *Resolves 1, effort low.*
3. **Restore the canonical hand-merge fallback paragraph**, OR document the deliberate divergence in the `customize.toml` header. Choose explicitly so reviewers comparing siblings understand why. *Resolves 1, effort low.*
4. **Harden Stage 1a Resume.** Require `stage-1` in `stepsCompleted` for Resume; treat `stepsCompleted: []` primary as Fresh; spell the log-absent-but-primary-exists branch; drop `{date}` from `business_flow_output_path` default. *Resolves 2, effort medium.*
5. **Extend `validate-mermaid.py` for quoted-alias and `Note over`; localise discover-script PRD globs for Japanese; switch `check-fr-coverage.py` from `rglob` to explicit file paths.** Closes the silent-block-in-headless cases on valid input. *Resolves 3, effort medium.*
6. **Deduplicate the `[A][P][C]` menu; disambiguate `[A]` vs `[P]` inline; add `--review-lenses` flag and `review_lenses_run` JSON field.** *Resolves 3, effort low.*
7. **Make Stage 1c open-floor consuming; move the wrong-skill off-ramp ahead of the scripted scan.** *Resolves 2, effort low.*
8. **Carve Headless Mode into `references/headless-contract.md`** with a one-paragraph SKILL.md pointer. Brings SKILL.md back under the multi-branch size guidance. *Resolves 1, effort low.*
9. **Replace "apply only deterministic fixes where unambiguous" with either script-emitted `auto_fixable: bool` per issue, or explicit "headless always blocks on validation failure".** Removes the prose-gated judgment leak on the highest-trust action. *Resolves 1, effort medium.*
10. **Schema tidies:** JSON contract substitution reminder; Stage 1a decision-log template interpolation; one term per concept; Vietnamese `vẽ` triggers. *Resolves 5, effort low.*

---

## Round 4 — All 9 round-3 themes resolved (2026-05-14)

User confirmed scope **"fix hết"** after seeing round-3's 3 high + 5 medium + 1 low themes. All resolved in one comprehensive pass. The deterministic side of the pipeline (lint + tests) now reports `pass` across the board; a fresh LLM-scanner pass would be needed to formally re-grade.

### Lint pipeline at end of round 4

| Scanner | Status | Notes |
|---|---|---|
| `scan-path-standards.py` on skill source | **pass** | 0 findings on skill files (.analysis/ noise only) |
| `scan-scripts.py` | **pass** | 0 findings; was 3 medium "no unit test found" |
| `python scripts/tests/run-tests.py` | **22 pass / 1 skip** | symlink test skipped on Windows |
| `validate-mermaid.py` smoke vs renamed template | **passed** | 2 blocks, 0 issues |

### Resolution table (9 themes → 9 resolved)

| Theme | What was done |
|---|---|
| **H-1 Script hygiene** (9 sub-findings) | PEP 723 in all scripts + tests; scripts/tests/ created with 22 tests; check-fr-coverage.py CLI renamed (--d06 + -o/--output); DECL_RE supports quoted aliases; NOTE_RE and ACTIVATION_RE added so Note over / activate participants count as used; JP PRD globs (要件定義書/企画書/ユースケース/画面); symlink flagged via is_symlink field; EXCLUDE_DIRS skips archive/notes/drafts/etc.; template_missing now exits 1 (was 2). |
| **H-2 build-scratch in references/** | `references/.decision-log.md` deleted. Round-1's "delete if build is final" branch taken. |
| **H-3 Hand-merge fallback dropped** | Canonical sibling paragraph restored at SKILL.md Step 1: "If the script fails or is missing, resolve the workflow block yourself by reading these three files in base → team → user order…". |
| **M-4 Resume protocol edges** (4) | Stage 1a now driven by `recommended_intent` from discover script; empty `stepsCompleted` treated as crash-recovered Fresh; `business_flow_output_path` default drops `{date}`; Stage 1b open-floor short-circuits Stage 1e if reply already specifies mode/scope/sources/type; off-ramp moved to Stage 1b (before scripted scan in 1c). |
| **M-5 [A][P][C] menu** (3) | Defined once at top-level "Parallel-lens menu" section; Stage 3 and Stage 4 invoke with stage-specific lens-targets only; cost and shape disambiguated (`[A]` ~5 min single lens, `[P]` ~15 min three parallel); `--review-lenses=skip\|advanced\|party` flag added; `review_lenses_run: []` field added to JSON contract. |
| **M-6 SKILL.md size** | `## Headless Mode` (input flags table + defaults table + JSON contract + reason values) carved out to `references/headless-contract.md`. SKILL.md now **236 lines**, within multi-branch guidance. |
| **M-7 Auto-fix prose-gated** | `validate-mermaid.py` now emits `auto_fixable: bool`, `arrow_count`, and `fix_hint` per issue. Stage 4 in SKILL.md: "apply only validator issues marked `auto_fixable: true`… for non-auto-fixable issues, return `blocked` with `reason: mermaid_validation_failed` or `fr_coverage_gap`". |
| **M-8 Resume-state synthesis** | `--workspace=<path>` flag added to discover script; emits `resume_state` with primary metadata + `recommended_intent`. Stage 1a consumes JSON directly. Three tests cover Fresh/Resume/Update recommendations. |
| **L-9 Schema tidies** (5) | JSON contract substitution reminder in `references/headless-contract.md`; Stage 1a explicitly interpolates decision-log template placeholders; `updated` field unified across primary + decision log + template; Vietnamese `'vẽ sơ đồ luồng nghiệp vụ'` + `'vẽ D-06'` added to description; build log deleted (was the source of the Simple-vs-complex contradiction). |

### File layout at end of round 4

```
src/hbc-create-business-flow-diagram/
├── SKILL.md                                  (236 lines)
├── customize.toml                            (single business_flow_output_path)
├── assets/
│   └── decision-log-template.md              ('updated' field)
├── references/
│   └── headless-contract.md                  (carved from SKILL.md)
└── scripts/
    ├── discover-planning-artifacts.py        (PEP 723, JP globs, symlinks, resume_state)
    ├── validate-mermaid.py                   (PEP 723, quoted aliases, Note over, auto_fixable)
    ├── check-fr-coverage.py                  (PEP 723, --d06, EXCLUDE_DIRS)
    └── tests/
        ├── __init__.py
        ├── run-tests.py                      (importlib runner — hyphen-safe)
        ├── test_discover-planning-artifacts.py    (8 tests)
        ├── test_validate-mermaid.py               (7 tests)
        └── test_check-fr-coverage.py              (7 tests)
```

The skill is production-ready. To formally re-grade Good → potentially Excellent, the four LLM scanners would need to re-run against this state — the deterministic pipeline (lint + tests) is now entirely clean.
