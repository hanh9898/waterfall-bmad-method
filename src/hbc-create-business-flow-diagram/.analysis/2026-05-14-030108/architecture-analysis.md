# Architecture Analysis — hbc-create-business-flow-diagram (Round 3, post-refactor)

Scanner: L1 (architecture) · Date: 2026-05-14 · Refactor delta of round 1 (~113 → ~260 lines)

## Assessment

The refactor lands most of round 1's structural asks cleanly — `## Overview` exists, the Decision-Log Workspace pattern is now genuinely operational (resume menu, Stage 2 flush, revision-bump on Update), customization collapsed to a single output scalar, and three Python scripts move parse / coverage work out of the prompt. The skill now reads as a deliberately-built Decision-Log-Workspace workflow with first-class headless support and a working PRD-shard story. Cost of the rewrite: SKILL.md jumped to ~260 lines / ~3,770 tokens with 9 fenced blocks and 2 tables, which is in the "multi-branch up to ~250" zone of the principles size guidance but now over it. The two genuine new structural problems are (1) `references/.decision-log.md` is the build-time author log placed in a runtime-only directory, mis-using the `references/` slot, and (2) the activation block silently dropped the canonical hand-merge fallback that every sibling skill still carries.

## Round-1 findings: what's resolved, what isn't

| Round-1 finding | Status | Evidence |
|---|---|---|
| H1: `## Overview` heading absent | **Resolved** | `SKILL.md:8` |
| H2: 5-step activation is boilerplate that should be ~5 lines | **Not applicable / withdrawn** | The 5-step block is the institutional canonical pattern (every sibling — `hbc-create-invest-epics-and-stories`, `bmad-create-architecture`, `bmad-agent-*` — uses it identically). Round 1 was wrong to flag it. Current form is correct. |
| H3: `### Stage N:` headings claim Complex but skill is Simple | **Resolved differently** | Headings dropped the "Stage" word (`### 1. Prerequisites and Scope`, `### 2. Discovery`, …). Whether the prepass still infers "complex" depends on its regex; the lived classification ("Simple Workflow" in the build-time `.decision-log.md:16`) and the on-disk shape (everything inline, no `references/` workflow carve-outs) agree. |
| M1: Hand-merge TOML fallback in activation | **Resolved by deletion, but see N1 below** | `SKILL.md:36` explicitly halts on resolver failure. |
| M2: Stage 1 dense workspace paragraph | **Resolved** | Stage 1 now split into 1a–1e with discrete responsibilities. |
| M3: Mermaid syntax checks done by LLM | **Resolved** | `scripts/validate-mermaid.py` parses blocks, declared-vs-used participants, expected-actor coverage. |
| M4: JSON contract uses non-standard `primary` field | **Resolved** | Renamed to `artifact` (`SKILL.md:85`), `reason` values enumerated (`SKILL.md:93`). |
| M5: `## On Complete` re-resolves the customize block | **Resolved** | `SKILL.md:36` "do not re-resolve in `## On Complete`"; `SKILL.md:259` reads from memory. |
| L1: `{date}` format unspecified | **Resolved** | `customize.toml:34` "{date} resolves to YYYY-MM-DD." |
| L2: Language rules buried inside Step 5 | **Resolved** | Lifted to top-level `## Language Rules` (`SKILL.md:23`). |
| L3: Description misses Vietnamese "vẽ" trigger | **Not addressed** | `SKILL.md:3` still only `'tạo sơ đồ luồng nghiệp vụ'`. Same low severity. |
| N1: Prepass false positive on `06-business-flow-diagram.md` | **Still present** | `workflow-integrity-prepass.json:134` still flags critical "missing stage" because the prepass is extracting `D-06-business-flow-diagram.md` as a stage reference. No change in prepass logic; same false positive. |

## Findings (new state)

### High

**H1 — `references/.decision-log.md` is build-time scratch parked in a runtime-only directory**
`references/.decision-log.md`, ~76 lines / 1,705 tokens (per `prompt-metrics-prepass.json:30-33`). The principles file path-conventions section is explicit: "`references/` is for prompt content carved out of SKILL.md. `assets/` is for templates and other static content the workflow loads. … Never put workflow content directly at skill root." This file is *neither*: it is the skill author's working memory across build sessions (the round-1, round-2, round-3 fix-log), and the runtime workflow never reads it — the runtime decision log lives at `{doc_workspace}/.decision-log.md` inside the user's project, generated from `assets/decision-log-template.md`. By living under `references/` it:
- Pollutes any future references-scan that walks `references/*.md` looking for carved-out workflow prompts (the file contains build-time language like "round 3 comprehensive fix pass", which would mislead a downstream LLM into thinking it's runtime guidance).
- Gets counted toward the skill's reference-prose budget by the prepass (`prompt-metrics-prepass.json:30-33` shows it at 1,705 tokens — the largest single file in the skill after SKILL.md, larger than any of the three scripts).
- The path-standards scan it was moved to silence (per `.decision-log.md:69`) only ever cared about *root-level* prompt files; nothing in the principles authorised parking build memory in `references/`. The original round-1 finding's "delete if the build is final and the log was working memory only" branch was the correct resolution.

The correct location for a build-time decision log is outside the published skill surface — either delete it now that the skill is final, or move it to the build workspace (`.analysis/` or a sibling `_build-notes.md` outside `references/`).

**H2 — Activation block silently dropped the hand-merge fallback that every sibling skill carries**
`SKILL.md:34-36`. Compare with `bmad-create-architecture/SKILL.md:33-35`: "Run: `python3 .../resolve_customization.py …` / **If the script fails**, resolve the `workflow` block yourself by reading these three files in base → team → user order and applying the same structural merge rules as the resolver". The same template is in every `bmad-agent-*` and the `hbc-create-invest-epics-and-stories` sibling. The refactor replaced this with: "If the resolver script is missing or fails, halt with a clear message — do not attempt to hand-merge TOML."

The rationale (per the round-3 entry in `references/.decision-log.md:71`, "dropped hand-merge fallback") cites the round-1 M1 finding. But round 1 framed the fallback as encoding a fragile LLM procedure; the institutional pattern decided differently — when the resolver is genuinely absent (corrupted install, first-run before BMad bootstrap completes), the LLM hand-merging three files is the difference between the skill working and dying. The fallback is "fragile-operation invocation" territory (principles file: "When Procedure IS Value") — one right way to merge TOML, written down explicitly. Failure mode now: any user whose `_bmad/scripts/resolve_customization.py` is missing or fails will see this skill halt where every other BMad skill on the same machine continues to work. The divergence is silent — nothing in the skill flags that it deliberately omits the fallback. Either restore the fallback to match the institutional pattern, or document the deliberate divergence in the customize.toml header so reviewers understand why this skill alone refuses to degrade gracefully.

### Medium

**M1 — SKILL.md is now over the multi-branch size guidance**
`SKILL.md`, 260 lines / 3,772 tokens / 9 fenced blocks / 2 tables / 20 sections (per `prompt-metrics-prepass.json:8-17`). Principles size guidance: "Multi-branch SKILL.md: up to ~250 lines if each branch has brief contextual explanation. Past those: lift to `references/` or `assets/`." The skill is 10 lines past that threshold without genuine multi-branching — it's a linear five-stage workflow with a headless variant. The new weight is concentrated in three places:
1. `## Headless Mode` (lines 54-93, ~40 lines including two tables + JSON contract). This is the natural carve-out candidate — headless input flags + defaults table + JSON contract is reference material the *runtime* prompt only needs when `-H` is in play. Lifting to `references/headless-contract.md` (or merging into `customize.toml` comments + a one-paragraph SKILL.md pointer) would drop ~35 lines.
2. `## Language Rules` (lines 23-28). Round 1 was right to want them out of activation; the lift to top-level was correct, but four prose bullets is still a reference-material shape, not a SKILL.md-spine shape. Either compress to two sentences or push to `references/language-rules.md`.
3. Stage 4 validator invocation lines (215-218) carry two full shell commands inline; only one of them runs without a per-flow loop (the script's `--prd` is `action="append"`, so the comment about "Pass each PRD path … as a separate `--prd` argument" implies the LLM constructs the command, which is fine but verbose).

The skill is not broken at this size; it's "earned its keep but no further" territory. Worth flagging because each future addition will compound past the hard ceiling.

**M2 — The Resume / Update / Validate / Fresh menu hard-codes a state machine the script could provide**
`SKILL.md:99-117`. Stage 1a tells the LLM to read `stepsCompleted`, `inputDocuments`, `lastStep` from the primary's frontmatter plus "the last session block in `.decision-log.md`", synthesise a one-line summary, then present an R/U/V/N/X menu. This is determinism-leaks-into-the-LLM territory (principles file: "Intelligence placement / Scripts handle plumbing"): reading two structured files and emitting a one-line "Last step: X | Steps complete: [Y, Z]" is exactly the kind of work `discover-planning-artifacts.py` already does for source discovery. The decision (which menu option to take) is judgment and belongs in the prompt; the *summary* is plumbing. A small extension to the discover script (or a sibling `resume-state.py`) emitting `{summary, last_step, steps_completed, primary_exists, mode_from_prior_session}` would let the prompt focus on the choice, not on the parse.

This is a "would the LLM do this correctly without being told" call: yes for one file, no when compaction is the threat. The prompt is currently betting on compaction NOT happening between resume-detection and menu rendering. Acceptable as-is; flag because the discover-script precedent makes a second pre-pass cheap.

**M3 — Stage 4 headless block contradicts its own "intelligence placement" line**
`SKILL.md:229-231`. The block says "apply only deterministic fixes (e.g. add a missing `participant` declaration where the alias is unambiguous from message lines)." The phrase "where the alias is unambiguous from message lines" is a judgment call disguised as a deterministic rule — the LLM has to decide what counts as "unambiguous," and there's no script step that emits a list of safe-to-apply auto-fixes. This is the pattern the principles file flags as "determinism leak into the LLM" (the inverse of M2). Two cleaner shapes:
- The validator script emits a `auto_fixable` boolean per issue (true only for participants where the alias appears in exactly one arrow line and no declared participant conflicts). The prompt applies those; everything else returns `blocked`.
- Or the prompt is explicit that headless never auto-fixes — every issue triggers `blocked: mermaid_validation_failed` with the list. Forces the human into the loop on validation, which matches the round-3 design rationale that "headless never silently invents."

The current middle path lets the LLM define "unambiguous" at runtime and write back to user files in headless mode. That's the highest-trust action the skill takes and it's gated by prose.

**M4 — The `[A][P][C]` parallel-lens menu is duplicated verbatim at Stage 3 and Stage 4**
`SKILL.md:202-209` and `SKILL.md:234-241`. Identical structure (Advanced Elicitation / Party Mode / Continue), identical headless-default-to-`[C]` rule, slightly different option text. Principles file: "Multiple files that could be a single instruction" — applies inside-file too. The two menus differ in *what they lens against* (Stage 3 is generated diagrams, Stage 4 is validation findings), but the menu plumbing is the same. Pulling the menu definition into one earlier section and referring back at each invocation would save ~10 lines and prevent the two menus from drifting (Stage 3 says "stress-test actor coverage and decision branches", Stage 4 says "challenge edge cases (failure paths, race conditions, hostile inputs)" — slightly different framings of the same lens, which is fine, but the *plumbing* duplication isn't).

**M5 — Workflow-type prepass mismatch (still)**
`workflow-integrity-prepass.json:115` reports `workflow_type: complex`; build-time `references/.decision-log.md:16` still asserts "Simple Workflow". Round 1's H3 flagged this; the refactor renamed `### Stage N:` to `### N. …` but the prepass either still infers from numbered subheadings or from the 5-stage count alone. The lived classification is still ambiguous: 260 lines, three scripts, 2 tables, headless mode, parallel-lens menus, Decision-Log Workspace — this is genuinely closer to Complex Workflow now. The build log claim should be updated to match.

### Low

**L1 — JSON contract `skill` field will template-leak**
`SKILL.md:85,90`. The contract shows `"skill": "{skill-name}"` — at runtime the agent must substitute the literal `hbc-create-business-flow-diagram` before emitting. The template artifact `{skill-name}` is documented at the Conventions block, so an LLM reading the contract carefully will resolve it; an LLM that just copies the JSON verbatim will emit `{skill-name}` as a literal string to the caller. Low risk in practice but worth a concrete example in the contract or an inline reminder ("substitute `{skill-name}`, `{doc_workspace}` before emission").

**L2 — `assets/decision-log-template.md` carries unresolved template variables in frontmatter**
`assets/decision-log-template.md:1-11`. The template uses `{skill-name}`, `{project_name}`, `yyyy-mm-dd` as placeholder values inside the *frontmatter* of the file the workflow writes. Stage 1e says "Initialize the primary document from `{workflow.business_flow_template}`, translating template prose to `{document_output_language}`" — but there's no equivalent line saying "and resolve the placeholders in `assets/decision-log-template.md` before writing it to `{doc_workspace}/.decision-log.md`." A literal copy would produce a decision log whose `skill: {skill-name}` is uninterpolated. Stage 1a says "initialize it from `assets/decision-log-template.md`" without specifying the interpolation step.

**L3 — Vietnamese trigger phrase coverage (unchanged from round-1 L3)**
`SKILL.md:3` — still no `'vẽ sơ đồ'` / `'vẽ D-06'` variant. Carried forward as unchanged.

**L4 — `## Conventions` block is stamped twice in spirit**
`SKILL.md:16-21` carries the canonical Conventions block; `SKILL.md:23-28` ("Language Rules") immediately re-introduces template-variable behaviour for `{document_output_language}`. Not a real violation — the Language Rules add genuine information about translation policy — but a reader skimming the top of the file sees back-to-back template-variable lectures. Cohesion smell, not a fix.

## Strengths (preserve)

- **Decision-Log Workspace pattern is now genuinely operational, not aspirational.** The Resume / Update / Validate / Fresh menu, the revision-history bump on Update (Stage 3, `SKILL.md:197-199`), the Stage 2 compaction-flush (`SKILL.md:181-186`), and the closing session block at Stage 5 are the four load-bearing pieces of the pattern — all present, all reading correctly. The Stage 2 flush in particular is the single most valuable round-2/3 add: it makes the skill compaction-survivable in a way most multi-stage workflows aren't.
- **Headless mode is structurally complete.** Input flags table, defaults table with named heuristics, JSON contract with enumerated `reason` values, named blockers (`template_missing`, `no_prd_and_no_interactive_in_headless`, `planning_artifacts_unreadable`, `mermaid_validation_failed`, `resolver_missing`). An automator can drive this skill from CI.
- **Intelligence placement on the three scripts is largely correct.** `discover-planning-artifacts.py` does shard enumeration (plumbing); `validate-mermaid.py` does declared-vs-used participant set algebra (plumbing); `check-fr-coverage.py` does set intersection on FR ids (plumbing). The LLM owns "is this AS-IS/TO-BE delta clear", "is layout readable" — all judgment. The split is clean, with the M3 caveat about "unambiguous auto-fix" leaking judgment back into the prompt.
- **Sharded-PRD story is real now.** The discover script reads `index.md`, extracts every linked `.md`, falls back to a glob if links are absent. Round 1's broken-fallback finding is genuinely fixed in code, not just in prose.
- **Customization collapsed from two scalars to one.** `business_flow_output_path` with `{date}` documented inline is cleaner than the prior `output_dir` + `output_folder_name` split, and the override comment ("drop the `{date}` segment to resume the same workspace") teaches the right mental model.
- **Language-rules treatment is sharper than round 1.** Three-rule split (file names always English, template English-source, output in `{document_output_language}`) plus an explicit list of carve-outs (Mermaid keywords, code identifiers, AS-IS/TO-BE) is exactly the kind of judgment context that earns its file weight.
- **`## On Complete` reads from already-resolved memory** (`SKILL.md:36, 259`). The round-1 M5 finding's "two-call waste" is now explicitly prevented.
- **Description still has quoted trigger phrases in both languages.** The conservative-triggering discipline survives the rewrite.
