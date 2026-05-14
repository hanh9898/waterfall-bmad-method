# BMad Quality Analysis: hbc-create-business-flow-diagram

**Analyzed:** 2026-05-14T02:19:53Z | **Last updated:** 2026-05-14 (post-pipeline tightening)
**Path:** `C:/Users/HanhNT2/stc-erp-bmad-custom/src/hbc-create-business-flow-diagram`
**Interactive report:** quality-report.html

## Assessment

**Good** — A well-shaped, ~113-line Simple Workflow with a clean customization surface, correct language-rule discipline, and the right institutional shape for a single-artifact D-06 generator. The biggest gap is that the Decision-Log Workspace pattern is half-built — resume/update on re-activation, headless interaction defaults, and sharded-PRD fallback are all incomplete — and Stage 1 is form-shaped where it should be facilitative; secondary wins live in collapsing On-Activation boilerplate and extracting three deterministic validators into a `scripts/` directory.

> **Post-analysis update:** Three follow-on fixes were applied after this analysis ran — template file renamed to English (Rule 1), template content rewritten as English i18n source (Rule 2), and SKILL.md language rules tightened to make template→output translation explicit (Rule 3). See **Update Log** at the end of this report. The seven remaining opportunities below are still open. An **Addendum** at the end maps each opportunity to a BMad-base or HBC-sibling precedent and adds B1–B8 new findings from sibling-pattern review.

## What's Broken

### Sharded PRD fallback reads only `index.md` and misses the substance

`SKILL.md:56` — Stage 1 says "search whole docs first, fall back to sharded `*/index.md`". Sharded PRDs put actors and FRs in `prd/epics/*.md`, not in `index.md` — the fallback rule reads the table of contents and runs discovery on near-empty input. In guided mode the user gets a wasted elicitation loop; in headless mode the agent hallucinates.

**Fix:** Change the rule to "for sharded PRDs, read `index.md` to enumerate shard paths, then read every linked shard" (or shorter: "read the full shard set, not just the index").

### `.decision-log.md` sits at skill root instead of `references/`

`.decision-log.md:0` — Path-standards lint flags it as a structure violation: progressive-disclosure content must live under `references/`, only `SKILL.md` belongs at root. The decision log is build-time scaffolding (LLM ideation memory for the skill author), not a runtime artifact the skill loads — but at root it confuses the standards scan and any auto-tooling that walks skill directories.

**Fix:** Move to `references/.decision-log.md` (or delete if the build is final and the log was working memory only).

## Opportunities

### 1. Decision-Log Workspace pattern is half-built — resume, update, and compaction-survival are missing (high — 4 observations)

Workspace creation and decision-log append-on-existing are wired correctly, but the entire reason the pattern exists — resume on re-activation, Update mode for revisable artifacts, and flushing discovered state to disk so compaction doesn't wipe it — is not implemented. The downstream chain (architecture / UX / stories) will trigger D-06 re-runs every time the PRD changes; today each re-run is a fresh draft that forgets the prior session's reasoning, and the dated `output_folder_name` default actively fights resume by creating a new workspace on day 2.

**Fix:** On Stage 1 entry, after binding `{doc_workspace}`, check whether the primary exists; if so, read `.decision-log.md`, surface a one-line summary plus `updated` timestamp, and offer Create-fresh / Update-flows / Validate intents. After Stage 2 confirmation, flush the actor list and flow inventory to the decision log (or as draft sections of the primary) so Stage 3 renders from disk. On Update mode, read the latest version from the existing revision-history table and append a new row rather than overwriting. Document that resume looks across same-`{project_name}` folders (or recommend dropping `{date}` from the default folder name when re-runs are expected).

**Observations:**
- Resume protocol absent for revisable artifact — `SKILL.md:66`
- Stage 2 holds discovered state only in the conversation — `SKILL.md:68`
- Dated folder name fights resume by design — `customize.toml:35`
- Revision history hardcoded to version 1.0; no update-mode bump — `SKILL.md:84`

### 2. Headless mode is declared but the interaction contract is undefined (high — 3 observations)

`--headless` is named in the description, the JSON return shape is specified, and Stage 1 instructs to "log every assumption" — but every interactive decision point in Stages 1, 2, and 4 lacks an explicit headless-default line. Different runs against the same PRD will silently choose different modes, scopes, and auto-fixes. There is also no documented input contract — automators can't override the inferred defaults — and the "no PRD found in headless mode" branch is a self-contradicting elicitation fallback.

**Fix:** Add a small headless-defaults table next to each Stage-1/2/4 decision point naming the heuristic that resolves it (e.g. PRD-contains-AS-IS-section -> migration). Declare the headless input contract: `--prd`, `--mode`, `--scope`, `--diagram-type`, `--no-prd-ok`. When PRD is absent and `--headless` is set, return `status: blocked` with a `reason` instead of falling into elicitation. Also rename or document the `primary` JSON field (non-standard vs canonical `report`/`artifact`).

**Observations:**
- Headless interaction defaults undefined — `SKILL.md:50`
- No documented headless input contract — `SKILL.md:106`
- Headless JSON contract uses non-standard field name `primary` — `SKILL.md:106`

### 3. Three deterministic validation operations live in the prompt — no `scripts/` directory exists (high — 4 observations)

Stage 1 source-doc discovery (glob walk of `*prd*.md`, `*ux*.md`, `D-04*.md`, etc.) and Stage 4's three validation checks (Mermaid syntax parse, actor coverage, FR-to-flow traceability) are deterministic file-system and parsing work that the LLM currently re-does on every run. They burn ~2400-5200 tokens per invocation with no quality benefit, and the Mermaid/actor-coverage checks have a real catch-rate gap the LLM eyeballing misses.

**Fix:** Add a `scripts/` directory with three small Python scripts: (1) `discover-planning-artifacts.py` — the pre-pass that walks `{planning_artifacts}` and emits compact JSON of PRD/UX/research candidates; (2) `validate-mermaid.py` — extracts Mermaid blocks, parses participant/message declarations, accepts an `--expected-actors` arg, returns findings JSON (folds S2 and S4 together); (3) `check-fr-coverage.py` — extracts FR identifiers from PRD and D-06 and returns covered/uncovered/phantom sets. Wire them in as pre-pass (S1 before Stage 2) and post-pass (S2-S4 in Stage 4). The LLM keeps the judgment calls — actor identification, AS-IS/TO-BE delta, layout choice.

**Observations:**
- PRD/UX/research discovery scan done in-prompt — `SKILL.md:52`
- Mermaid syntax validation done by reading — `SKILL.md:94`
- FR-to-flow traceability done by re-scanning the PRD — `SKILL.md:93`
- Actor-coverage cross-check done by re-reading — `SKILL.md:92`

### 4. On Activation reproduces resolver-owned procedure as 25 lines of boilerplate (medium — 3 observations)

Steps 1-5 spell out merge precedence, `file:` semantics, config-fallback order, and greeting/append execution — the standard 5-step on-activation procedure every BMad skill performs identically. Sibling skills inline only the resolver line plus a one-line greet/append, leaving the rest to the resolver script and the model. The hand-merge fallback paragraph encodes a procedure the LLM will not execute reliably, and the language-rules block at Step 5 is workflow-wide policy mixed into the greeting subsection.

**Fix:** Replace Steps 1-5 with the canonical activation block (resolve workflow -> run prepend -> load persistent facts -> load config -> greet and run append, one line each). Drop the manual TOML hand-merge fallback paragraph — if the resolver is missing, halt and report. Lift the "Language rules for the entire workflow" subsection out of Step 5 into a separate paragraph above `## Workflow`.

**Observations:**
- Steps 1-5 reproduce standard 5-step boilerplate — `SKILL.md:19`
- Manual TOML hand-merge fallback is a fragile middle path — `SKILL.md:23`
- Step 5 mixes greet-and-execute with workflow-wide language rules — `SKILL.md:39`

### 5. Stage 1 is form-shaped where it should be facilitative — open-floor, intent-gate, and quick-confirm all missing (medium — 5 observations)

Stage 1 dives into scanning `{planning_artifacts}` and fires a four-question grid (sources / mode / scope / diagram-type) with no open-floor invitation, no intent-confirm, no single inferred-defaults confirmation block, and no off-ramp for accidental activations. First-timers can't volunteer "I have a Miro export here", experts have no quick-confirm path, confused users waste a full scan, and Stage 2's structured elicitation is single-lens (no capture-don't-interrupt slot, no parallel skeptic + actor-coverage lenses in Stage 4).

**Fix:** Open Stage 1 with two sentences: an open-floor invitation ("share anything you already have — PRD path, sketches, prior flows, or just describe") and a one-line intent check ("capturing an existing flow, designing a new one, or both?"). Replace the four serial questions with one inferred-defaults confirmation block ("Inferred: migration mode, multi-flow, sequenceDiagram, four PRD docs — confirm or edit?"). Add a one-sentence off-ramp for clearly-not-a-business-flow inputs. In Stage 4, add a brief parallel skeptic + actor-coverage scout sub-step before finalizing.

**Observations:**
- No open-floor opening or capture-don't-interrupt slot — `SKILL.md:50`
- No early intent gate before artifact scan — `SKILL.md:52`
- No quick-confirm path for experts (Yolo middle missing) — `SKILL.md:50`
- Validation is single-lens — `SKILL.md:89`
- No off-ramp for wrong-diagram invocations — `SKILL.md:3`

### 6. Workflow-type / structure surface mismatches and missing scaffolding (medium — 4 observations)

The decision log claims Simple Workflow and the file is genuinely simple (~113 lines, all inline), but the `### Stage N` heading style matches Complex-Workflow shape — which is why the prepass infers `workflow_type: complex`. There is also no `## Overview` heading (the lead paragraphs serve as one but no mechanical scan sees it), Stage 1 packs workspace-binding mechanics and decision-log seeding into a single dense paragraph, and the `## On Complete` resolver call is a redundant second invocation when the activation already resolved the workflow block.

**Fix:** Insert `## Overview` above the existing lead paragraphs (no content change). Rename `### Stage N: …` to neutral sectional headings (Prerequisites and Scope / Discovery / Diagram Generation / Validation / Save and Handoff) to honor the Simple-Workflow claim — or alternately accept Complex and update the decision log. Split Stage 1's workspace-binding paragraph into one bullet for workspace binding and one for decision-log seeding. Either note in Step 1 that the resolver returns the full workflow block including `on_complete` and have On Complete read it from memory, or document that re-resolution is deliberate.

**Observations:**
- `## Overview` heading absent — `SKILL.md:6`
- Workflow-type claim vs heading style mismatch — `SKILL.md:48`
- Stage 1 packs workspace binding + decision-log seeding into one dense paragraph — `SKILL.md:66`
- On Complete re-resolves the workflow block (wasted call) — `SKILL.md:108`

### 7. `output_dir` + `output_folder_name` split is a permutation surface (medium — 2 observations)

Two scalars combine on activation to produce `{doc_workspace}`. The factoring lets a team choose parent dir and folder template independently, but in practice teams want one path. Users overriding `output_folder_name` to drop `{date}` won't realize `output_dir` is also configurable and will hit a half-override.

**Fix:** Collapse to one scalar `business_flow_output_path = "{planning_artifacts}/business-flows/D-06-{project_name}-{date}/"` and bind `{doc_workspace}` directly to the resolved value in Stage 1. Specify `{date}` format in the comment (commonly `YYYY-MM-DD`).

**Observations:**
- Two-scalar output path forces a two-step mental model — `customize.toml:35`
- `{date}` format unspecified in `output_folder_name` default — `customize.toml:35`

## Strengths

- **Right size, right shape — inline-first Simple Workflow.** ~113 lines, all inline in SKILL.md + customize.toml, no `references/` carve-out, no scripts, no `assets/`.
- **Customization surface is clean and resisted the loudest temptations.** Six scalars + one persistent-fact array + two activation arrays. No boolean toggles, no hooks beyond `on_complete`, identity/persona kept out of `[workflow]`. The two anti-findings (migration-vs-greenfield as toggle, per-skill language override) were correctly *not* added.
- **Language-rule handling is explicit and correct.** Distinguishes `{communication_language}` (user-facing) from `{document_output_language}` (artifact-facing) and explicitly carves out Mermaid keywords as English.
- **Downstream consumers named explicitly** (`bmad-create-architecture`, `bmad-create-ux-design`, `bmad-create-epics-and-stories`, `hbc-create-invest-epics-and-stories`) — the workflow knows where it sits in the BMM phase chain.
- **Graceful degradation on bmad-distillator.** "Skip with a note if distillator is unavailable; never inline a substitute" — follows the principles cleanly. (Template-absent and resolver-absent on On Complete still need the same treatment.)
- **Description format is well-disciplined.** Quoted trigger phrases including a Vietnamese trigger matching the configured `document_output_language`.
- **Headless considered as a first-class mode at the structural level.** JSON return shape, decision-log auto-fix logging in headless, and "absence of PRD is a normal mode" are all named.
- **No deterministic work currently hidden in scripts.** Zero scripts means zero risk of "intelligence leak into scripts" from regex-based meaning extraction — a clean baseline.

## Detailed Analysis

### Architecture

A coherent, well-scoped Simple Workflow living entirely in `SKILL.md` + `customize.toml` — the right shape for its complexity. Routing, customization wiring, language discipline, and the Decision-Log Workspace seeding are all correct. Findings are tidy-ups: missing `## Overview`, a `### Stage N` heading style that contradicts the Simple claim, and ~25 lines of On-Activation boilerplate inherited from the build template. Two minor consistency notes — `primary` is non-canonical in the headless JSON contract, and the prepass "missing stage file `06-business-flow-diagram.md`" finding is a false positive (extracted from output filenames, not stage references).

### Determinism & Distribution

The skill is mostly judgment work (actor identification, AS-IS/TO-BE delta, layout choices) and belongs in the prompt. But Stage 1's source-doc glob walk and Stage 4's three validation checks (Mermaid parse, actor coverage, FR traceability) are textbook script candidates — pure parsing and set-membership work the LLM currently re-does every run. A single `scripts/` directory with three small Python scripts converts this into a compact pre-pass/post-pass JSON exchange. Estimated savings: **~2400-5200 tokens per run** (S1 ~600-1300, S2 ~600-1000, S3 ~1000-2500 on PRD-backed runs, S4 ~200-400) plus a quality win — scripts catch orphans and uncovered FRs the LLM eyeballing will sometimes miss. The workflow is correctly single-agent linear; no subagent fan-out is warranted at this scale.

### Customization Surface

**Posture: opted-in.** Full BMad always-present surface plus four workflow-specific scalars (`business_flow_template`, `diagram_type`, `output_dir`, `output_folder_name`) and the `on_complete` hook. All scalars, no arrays-of-tables, no boolean toggles, no hooks beyond `on_complete`. SKILL.md reads `{workflow.X}` everywhere with no silent-no-op hardcodes. The two temptations from the context conversation (migration-mode toggle, per-skill language override) were correctly resisted — both are runtime per-conversation state, not team configuration. One real abuse remains: the `output_dir` + `output_folder_name` split should collapse to a single `business_flow_output_path`. Two minor descriptive tightenings: name "HBLab D-* document conventions" as an example of a `persistent_facts` extension, and tighten the `diagram_type` comment to admit it's a hint rather than a contract.

### User Experience

Headless mode is named but not specified; the Decision-Log Workspace pattern is half-built (no resume, no Update, no compaction flush). Stage 1 trades open-floor warmth for a four-question form. The skill works on the first pass and falls apart on revisit — exactly the failure mode the Workspace pattern was designed to prevent.

**Journeys:**

- **First-timer** (BA activating after `bmad-create-prd`): four Stage-1 questions arrive as a flat batch with no anchor for consequences; greenfield-vs-migration is picked blind. Bright spot: workspace + decision log capture the choice, making wrong picks recoverable on re-run.
- **Expert** (BA on the fifth project this quarter): no Yolo / quick-confirm middle exists; the four-question dance fires every run even when the PRD's structure makes the answers obvious.
- **Confused** (wrong-skill activation): no early intent-confirm before the artifact scan; no off-ramp signposting sibling skills.
- **Edge-case**: sharded-PRD fallback is broken (reads only `index.md`); no resume protocol; no targeted single-flow update; no multiple-PRD disambiguation; zero-actor PRDs render a vacuous diagram. Bright spot: PRD-absent fallback to interactive elicitation is explicitly a "normal mode, not a blocker".
- **Hostile environment**: template-file-missing halts the skill (no skeleton fallback); Stage 2 holds discovered state in conversation only (compaction drops it); On Complete resolver call has no fallback. Bright spot: `bmad-distillator` unavailable correctly skipped with a note.
- **Automator** (headless pipeline): defaults for each interactive decision unspecified — non-deterministic across runs; no documented input flag set; no-PRD + headless silently falls into elicitation instead of returning blocked. Bright spot: JSON return shape is minimal and correct (though `primary` is non-canonical).

**Autonomous potential: easily-adaptable.** Core artifact creation can run headless today, but Stage 1's four-question discovery and Stage 2's actor/trigger confirmation need an explicit headless-defaults table and an input contract. The "no PRD + headless" branch needs to return blocked rather than elicit.

## Recommendations

1. Wire the Decision-Log Workspace pattern fully: resume-on-re-activation (Create/Update/Validate intents), flush Stage 2 discovered state to the decision log, append (don't overwrite) revision-history rows on Update, and either document or fix the dated-folder-name fights-resume tension. — *resolves 4, effort medium*
2. Specify the headless contract: a one-line headless default next to every interactive decision in Stages 1, 2, and 4; a documented input flag set (`--prd`, `--mode`, `--scope`, `--diagram-type`, `--no-prd-ok`); a `status: blocked` branch when PRD is absent under `--headless`; and rename/document the non-canonical `primary` JSON field. — *resolves 3, effort low*
3. Add a `scripts/` directory with `discover-planning-artifacts.py`, `validate-mermaid.py` (folding actor-coverage in), and `check-fr-coverage.py`. Wire as pre-pass and post-pass. Recovers ~2400-5200 tokens/run and closes the headless-auto-fix quality risk. — *resolves 4, effort medium*
4. Refactor Stage 1 into a facilitative shape: open-floor invitation + one-line intent gate + single inferred-defaults confirmation block + off-ramp for clearly-not-a-business-flow inputs. Add a parallel skeptic + actor-coverage scout sub-step before Stage 4 finalizes. — *resolves 5, effort low*
5. Collapse On Activation Steps 1-5 to the canonical 5-line block, drop the manual TOML hand-merge fallback (halt-and-report instead), and lift the workflow-wide language rules out of Step 5 into their own paragraph above `## Workflow`. — *resolves 3, effort low*
6. Tidy structural surface: insert `## Overview` heading, rename `### Stage N: …` to neutral sectional headings, split Stage 1's workspace paragraph into separate bullets, and have On Complete read `{workflow.on_complete}` from the already-resolved block. — *resolves 4, effort low*
7. Collapse `output_dir` + `output_folder_name` to a single `business_flow_output_path` scalar with `{date}` format specified in the comment. — *resolves 2, effort low*
8. Fix the broken sharded-PRD fallback rule (read every linked shard, not just `index.md`) and move `.decision-log.md` to `references/.decision-log.md` (or delete if it was build-time scratch). — *resolves 2, effort low*

---

## Update Log

Changes applied after the pipeline finished — captured here so this report remains the authoritative record of the skill's evolution.

### 2026-05-14 — Language-rule split (file names / template / output)

User-stated rule: **file names always English; template content always English; output document content follows `{document_output_language}` (skill translates at render time).** This three-rule split distinguishes i18n source (templates) from generated artifacts, and overrides any precedent in BMad upstream or HBC siblings.

**Applied changes:**

| # | Target | Change |
|---|---|---|
| 1 | `templates/D-06_業務フロー図_template.md` | Renamed → `templates/D-06_business-flow-diagram_template.md` (Rule 1). File was untracked; rename used `mv`, not `git mv`. |
| 2 | `templates/D-06_business-flow-diagram_template.md` content | Rewritten as English i18n source: `業務フロー図` → `Business Flow Diagram`, `改訂履歴` → `Revision History`, `日付/バージョン/改訂内容/担当者` → `Date/Version/Changes/Author`, Mermaid `as <label>` text and message labels → English. `AS-IS` / `TO-BE` kept as untranslated business jargon (carve-out). |
| 3 | `src/hbc-create-business-flow-diagram/customize.toml:24` | `business_flow_template` path updated to the new English filename. |
| 4 | `src/hbc-create-business-flow-diagram/SKILL.md:43-47` | Language-rules block rewritten with three rules: (a) communicate with user in `{communication_language}`; (b) treat template as English-source i18n skeleton and **translate** all prose to `{document_output_language}` when rendering output — never emit verbatim; (c) file/folder names always English; (d) carve-outs (Mermaid keywords, Mermaid identifiers, `AS-IS` / `TO-BE`) stay original in both template and output. |

**Carry-over flags (not yet applied):**

- 29 other D-* templates in `templates/` still have Japanese filenames and Japanese content (Rule 1 + Rule 2 violations at project scope). Same treatment needed when the matching skill is created. Currently untracked in git so batching is still cheap.
- The seven opportunities + two broken items below are untouched by this update — they remain open work.

---

## Addendum: Patterns from BMad base + HBC siblings

After the original analysis, the five planning-phase BMad core skills (`bmad-create-prd`, `bmad-create-ux-design`, `bmad-create-architecture`, `bmad-create-epics-and-stories`, `bmad-create-story`) and the two HBC sibling skills (`hbc-create-invest-epics-and-stories`, `hbc-setup`) were read for precedent. Findings split into three groups.

### Group A — Reinforce existing opportunities with concrete precedent

| Existing Opp. | Precedent to adopt | Citation |
|---|---|---|
| **Op #1 — Decision-Log Workspace half-built** (resume) | **Two-file split**: `step-01-init.md` only detects the document and its frontmatter `stepsCompleted`; if incomplete, auto-loads `step-01b-continue.md` which presents `[R] Resume / [C] Continue / [O] Overview / [X] Start over`. Each output document carries frontmatter `stepsCompleted: []`, `inputDocuments: []`, `lastStep`, `project_name`, `user_name`, `date`. | `bmad-create-architecture/steps/step-01-init.md:35-50`; `step-01b-continue.md:76-80`; `bmad-create-prd/steps-c/step-01-init.md:49-69` |
| **Op #1 — Decision-Log Workspace half-built** (compaction-flush) | **Frontmatter `stepsCompleted` is append-only**, updated immediately after each step completes. SKILL.md spells out: `💾 ALWAYS update frontmatter of output files when writing the final output for a specific step`. | `bmad-create-prd/SKILL.md:47`; `bmad-create-epics-and-stories/SKILL.md:28-29`; `bmad-create-story/SKILL.md:401-407` |
| **Op #5 — Stage 1 form-shaped, should be facilitative** | **Discovery report card + confirmation gate**: report enumerated docs (`PRD: {n}`, `UX: {n}`...) and ask `Do you have any other documents to include? [C] Continue` *before* taking further action. Use template conditionals like `{if briefCount > 0}✓ loaded{else}(none found){/if}` to render inferred state, then the menu. | `bmad-create-architecture/steps/step-01-init.md:73` (critical gate), :111-125 (report card); `bmad-create-prd/steps-c/step-01-init.md:111-131` |
| **Op #7 — `output_dir` + `output_folder_name` split** | **One scalar**: BMad standard is `outputFile` or `default_output_file`, not separated dir + filename. | `bmad-create-prd/SKILL.md:95`; `bmad-create-ux-design/SKILL.md:69`; `bmad-create-story/SKILL.md:76` |

### Group B — New findings not in the original report

#### B1. Replace silent "no-PRD fallback to elicitation" with HALT-menu (3 options)

`SKILL.md:58` currently reads "switch to interactive elicitation" when no PRD is found. BMad-native pattern is an explicit HALT menu:

```
🚫 No PRD found in {planning_artifacts}
**Options:**
1. Run `bmad-create-prd` first (recommended)
2. Provide PRD path
3. Continue with interactive elicitation (greenfield, no source)
[q] Quit
```

In headless mode: only accept option 2 via `--prd-path=`, else return `blocked` with `reason: "no_prd_and_no_interactive_in_headless"` — this also resolves the "no-PRD + headless self-contradicting elicitation" finding in Op #2.

**Precedent:** `bmad-create-story/SKILL.md:102-127, 144-153`; `bmad-create-architecture/steps/step-01-init.md:89` ("Architecture requires a PRD to work from. Please run the PRD workflow first or provide the PRD file path. Do NOT proceed without PRD.").

#### B2. Add `[A][P][C]` menu after Stage 3 and Stage 4

BMad pattern for a parallel-validation lens: present `[A] Advanced Elicitation / [P] Party Mode / [C] Continue` after generating validation content. `[A]` invokes `bmad-advanced-elicitation` to stress-test actor coverage; `[P]` invokes `bmad-party-mode` to get analyst + architect + UX perspectives on the flow before finalizing.

In headless mode: skip the menu, default to `[C]`, log the auto-decision to `.decision-log.md`.

**Precedent:** `bmad-create-architecture/steps/step-07-validation.md:26-37, 308-322`; `hbc-create-invest-epics-and-stories/references/story-generation.md:121` (HBC sibling already adopts this).

#### B3. Add template-existence check at Stage 1

`{workflow.business_flow_template}` points to `{project-root}/templates/D-06_business-flow-diagram_template.md`. This path is **not** part of the default BMad install — HBC siblings don't validate template existence and let it fail naturally. Add an explicit check:

> If `{workflow.business_flow_template}` does not exist → halt with hint to run `hbc-setup` or clone the shared D-* template set. In headless: return `blocked` with `reason: "template_missing"`.

**Precedent:** No HBC sibling does this. Adopt as new house convention.

#### B5. Establish `assets/decision-log-template.md` as HBC first-mover convention

Neither `hbc-create-invest-epics-and-stories` nor `hbc-setup` uses `.decision-log.md`. This skill is the first mover; define a minimal schema now so future HBC skills follow consistently:

```markdown
---
skill: {skill-name}
phase: built|in-progress
classification: simple-workflow|complex-workflow
last_touched: YYYY-MM-DD
stepsCompleted: []
inputDocuments: []
---

## Session YYYY-MM-DDTHH:MM — {Intent: Create|Update|Validate}
### Sources
### Mode/Scope decisions
### Auto-fixes (headless)
### Handoff target
```

Place at `src/hbc-create-business-flow-diagram/assets/decision-log-template.md` per HBC `assets/<*>-template.md` convention (sibling INVEST uses `assets/invest-stories-template.md`).

#### B6. Stage 4 validation — choose `checklist.md` (BMad-native) or `scripts/` (innovation)

Op #3 in the original report proposed `scripts/`. **None of the five BMad planning skills have a `scripts/` directory** — only meta-skills (builder, setup, distillator) do. BMad-native validation pattern is a static `checklist.md` invoked via `<action>Validate ... against ./checklist.md</action>`.

**Two paths:**

- **Path A (BMad-native, safe):** Create `references/validation-checklist.md` with the 5 items (actor coverage, FR mapping, Mermaid syntax, revision history, language consistency). LLM validates. No token savings but stays in BMad house style.
- **Path B (innovation, as Op #3 proposed):** Create `scripts/` with Python validators. Recovers ~2400–5200 tokens/run and gives Mermaid parse a real syntax check. Goes *against* BMad core convention (matches only meta-skills).

**Recommended Path B** — Mermaid syntax validation and FR-coverage set-membership are genuinely deterministic, not judgment, so the innovation is warranted. But the team should know the choice deviates from BMad planning-skill precedent.

**Precedent for Path A:** `bmad-create-architecture/steps/step-07-validation.md:51-152` (16-item validation by LLM prompt); `bmad-create-story/SKILL.md:395` (`<action>Validate ... against ./checklist.md</action>`).

#### B7. Backport row to `hbc-setup/assets/module-help.csv`

`hbc-setup/assets/module-help.csv` currently has one row (INVEST). The new BFD skill is registered in `_bmad/_config/bmad-help.csv:57` but the corresponding row should also be added to the HBC module-help CSV so `hbc-setup` installs the full HBC skill set in a new project.

#### B8. Headless JSON contract — rename `primary` → `artifact`, then backport to HBC siblings

Op #2 in the original report flagged `primary` as non-canonical. After reading BMad base: **BMad core skills don't emit JSON return contracts at all** — they terminate with user output + invoke next skill. So there's no canonical name to adopt; this is original design.

**Decision:** Keep the JSON contract (it's a real automation upgrade over HBC siblings which only declare `Supports --headless / -H`). Rename `primary` → `artifact` (natural for a single-document output). Backport the same contract field name to `hbc-create-invest-epics-and-stories` so HBC has a house standard.

### Group C — Anti-findings (refine the original report)

- **Op #4 "On Activation 25 lines of boilerplate":** The five BMad base skills each carry an *identical* ~60-line activation block. This skill's 25-line version is already *shorter*, not longer. The "canonical 5-line block" goal in Recommendation #5 has no real precedent in BMad — there is only a canonical 60-line block. Revised guidance: keep the existing 25-line trimmed version, but make the wording for Steps 1–6 *match* BMad base exactly so tooling stays compatible. The manual TOML hand-merge fallback paragraph (`SKILL.md:23`) is still worth dropping — that part of the finding stands.
- **Headless JSON contract precedent:** Original finding implied a canonical BMad name existed. It doesn't (see B8). The contract is HBC house-standard-in-the-making, not a deviation from upstream.
- **Vietnamese trigger in description (`'tạo sơ đồ luồng nghiệp vụ'`):** Original strengths section called this well-disciplined. Confirmed: HBC siblings INVEST + setup only have English triggers. This skill is the first mover for bilingual triggers; backport to siblings is recommended.

### Updated priority order (replaces original "Recommendations")

1. **Fix two broken** (sharded-PRD shard-set read; `.decision-log.md` location) — original Recommendation #8.
2. **Resume / Update via two-file split + `[R/C/O/X]` menu** (Op #1 + Group A reinforcement + B5 template) — original #1, expanded with B5.
3. **HALT-menu when no PRD** (B1, new) — also closes the headless-elicitation contradiction in Op #2.
4. **Headless contract + rename `primary` → `artifact` + backport to INVEST** (Op #2 + B8).
5. **Stage 1 Discovery report card + confirmation gate** (Op #5 + Group A reinforcement) — copy the Architecture step-01 wording structure.
6. **`[A][P][C]` parallel-validation menu after Stage 3 and Stage 4** (B2, new).
7. **Template-existence check at Stage 1** (B3, new).
8. **Choose Path A vs Path B for Stage 4 validation** (B6, refines Op #3) — Path B recommended.
9. **Output path one scalar `default_output_workspace`** (Op #7, refined naming).
10. **Backport row to `hbc-setup/assets/module-help.csv` + Vietnamese trigger to INVEST/setup** (B7 + anti-finding).

Effort distribution: items 1, 3, 7, 9 are 5–15 minutes each. Items 2, 4, 5, 6 are 30–90 minutes. Item 8 is a half-day if Path B is chosen.

---

## Round 3 — Comprehensive fix pass (2026-05-14)

User confirmed scope **"Tất cả 14 items"** and **Path B (scripts/)** for Stage 4 validation. All items now resolved.

### What was created

| Path | Purpose |
|---|---|
| `src/hbc-create-business-flow-diagram/assets/decision-log-template.md` | B5 — HBC first-mover schema for runtime `.decision-log.md` (frontmatter + per-session block format). |
| `src/hbc-create-business-flow-diagram/scripts/discover-planning-artifacts.py` | Op #3 + B3 + broken #1 — walks `{planning_artifacts}`, classifies PRD/UX/use-case/research, enumerates **every shard** of sharded PRDs (resolves broken #1's index-only bug), checks template existence (resolves B3). Returns JSON. |
| `src/hbc-create-business-flow-diagram/scripts/validate-mermaid.py` | Op #3 — extracts Mermaid blocks, parses participant/actor declarations and arrow lines, flags undeclared participants + orphan declarations + missing expected actors. Returns JSON. |
| `src/hbc-create-business-flow-diagram/scripts/check-fr-coverage.py` | Op #3 — extracts `(N)FR-*` identifiers from PRD (handles sharded via repeatable `--prd` flag) and D-06 output, returns covered/uncovered/phantom sets. |

### What was moved or restructured

| Before | After | Resolves |
|---|---|---|
| `src/hbc-create-business-flow-diagram/.decision-log.md` | `src/hbc-create-business-flow-diagram/references/.decision-log.md` | Broken #2 — confirmed by re-running `scan-path-standards.py` (structure category: 0 findings). |
| `customize.toml`: `output_dir` + `output_folder_name` (two scalars) | `business_flow_output_path` (single scalar) with `{date}=YYYY-MM-DD` documented + override guidance for resume | Op #7. |
| `customize.toml`: `diagram_type` comment | Tightened: "hint... is a default, not a contract" | Customization scanner anti-finding. |
| `src/hbc-setup/assets/module-help.csv` | BFD row added mirroring `_bmad/_config/bmad-help.csv:57` | B7. |

### SKILL.md — comprehensive rewrite

Final size: **~200 lines** (was ~113). New top-level structure:

```
## Overview                       (new — Op #6)
## Conventions                    (kept)
## Language Rules                 (lifted out of activation — Op #4)
## On Activation
  ### Step 1: Resolve workflow    (drops hand-merge fallback — Op #4)
  ### Step 2-5                    (kept canonical)
## Headless Mode                  (new top-level — Op #2)
  ### Input flags                 (table: -H, --prd-path, --mode, --scope, --diagram-type, --no-prd-ok)
  ### Defaults table              (per-decision heuristics)
  ### JSON return contract        (primary → artifact, named reason values)
## Workflow
  ### 1. Prerequisites and Scope
    1a. Bind workspace + resume detection (R/U/V/N/X menu)     — Op #1
    1b. Source discovery (scripted)                            — Op #3, B3, broken #1
    1c. Open-floor invitation + intent gate                    — Op #5
    1d. No-PRD HALT menu                                       — B1, Op #2
    1e. Inferred-defaults confirmation block + off-ramp        — Op #5
  ### 2. Discovery (with compaction-flush at end)              — Op #1
  ### 3. Diagram Generation (with [A][P][C] menu after)        — B2, Op #1 revision bump
  ### 4. Validation (scripted + judgment + [A][P][C] menu)     — Op #3, B2
  ### 5. Save and Handoff
## On Complete                    (reads from memory — Op #6)
```

Anti-finding C honoured: the activation block stays a 5-step structure (the "canonical 5-line" goal in Recommendation #5 had no precedent in BMad core — what does exist is a canonical 60-line block, and this skill is already shorter). What was dropped is the manual TOML hand-merge fallback paragraph.

### Validation after the rewrite

- `scan-path-standards.py` re-run: **0 structure findings, 0 frontmatter findings** on skill source files. The 6 remaining findings are inside the analysis reports themselves (text mentions of `_bmad/` and `../hbc-setup/` in this very report) and have no bearing on skill validity.
- Smoke-tested `validate-mermaid.py` against the renamed English template: parses 2 blocks, 0 issues, `passed: true`.
- Smoke-tested `discover-planning-artifacts.py` with an empty planning-artifacts dir: returns `template_exists: true`, no fatal, empty lists for PRD/UX/use-case/research.

### Final status

- **Broken:** 2 / 2 resolved.
- **Opportunities:** 12 / 12 resolved.
- **Applied changes log:** 11 entries (4 from round 1 language-rule split + 7 from this round).
