# Architecture Analysis — hbc-create-business-flow-diagram (Round 5, post round-4 polish)

Scanner: L1 (architecture) · Date: 2026-05-14 · Round-4 delta of round 3 (~260 → ~237 SKILL.md lines)

## Assessment

The round-4 pass cleanly resolves all 9 round-3 themes and the skill now reads as a mature, deliberately-built Decision-Log Workspace workflow with first-class headless and a sound script-prompt split. It crosses from "Good with rough edges" to "Excellent" on intent and structural cohesion — every load-bearing principle from the principles file has a deliberate, traceable home — though it is *not* defect-free at the surface: round 4 introduced a small handful of low-cost regressions (a meta-explanatory preamble in the carved-out reference, a contract-vs-prose drift between the carved file and SKILL.md, and an Overview line that now over-promises versus the actual surface). None of them break execution; they're polish-the-polish items.

## Round-3 findings: resolution audit

| Round-3 finding | Status | Evidence |
|---|---|---|
| H-1: `references/.decision-log.md` is build-time scratch in a runtime-only directory | **Resolved** | Directory listing of `references/` shows only `headless-contract.md`; the build log is gone. |
| H-2: Hand-merge fallback dropped from activation | **Resolved** | `SKILL.md:37` restores the three-file base → team → user merge with explicit structural-merge rules, matching `bmad-create-architecture` sibling pattern. |
| H-3: SKILL.md size over the multi-branch ceiling | **Resolved** | `prompt-metrics-prepass.json:9` reports 237 lines / 3,998 tokens (was 260). Inside multi-branch guidance now, with room. |
| M-4: Resume protocol synthesizes state at runtime | **Resolved** | `scripts/discover-planning-artifacts.py:118-182` emits `resume_state` (with `recommended_intent` derived from `stepsCompleted`); `SKILL.md:83-109` consumes it directly rather than re-parsing. |
| M-5: `[A][P][C]` parallel-lens menu duplicated at Stages 3 + 4 | **Resolved** | `SKILL.md:61-73` defines the menu once at top level; Stage 3 (`SKILL.md:192`) and Stage 4 (`SKILL.md:218`) refer back. Headless surfaced via `--review-lenses=skip\|advanced\|party`; fires logged to `review_lenses_run`. |
| M-6: `## Headless Mode` carve-out candidate | **Resolved** | Carved to `references/headless-contract.md` (70 lines / 957 tokens per `prompt-metrics-prepass.json:30`). SKILL.md keeps a 1-paragraph pointer (`SKILL.md:57-59`). See N-3 below for a small surface issue this introduced. |
| M-7: "unambiguous auto-fix" prose-gated determinism leak | **Resolved** | `validate-mermaid.py:140-147` emits `auto_fixable: bool` + `fix_hint` per issue; `SKILL.md:214` says "apply only validator issues marked `auto_fixable: true`", citing `fix_hint`. Judgment lives in the script, prompt applies. |
| M-8: Workflow-type prepass mismatch (Simple vs Complex) | **Effectively resolved** | The runtime now reads unambiguously as Complex Workflow (headless contract, three scripts, resume state machine, decision-log workspace) and the prepass agrees (`workflow-integrity-prepass.json:105`). The conflicting build-log claim is also gone with the build log itself (round-3 H-1 fix). |
| L-9: Trigger-phrase coverage, JSON substitution reminder, decision-log interpolation | **Resolved** | `SKILL.md:3` adds `'vẽ sơ đồ luồng nghiệp vụ'` and `'vẽ D-06'` triggers. `references/headless-contract.md:33` carries the explicit "Substitute every `{placeholder}` with its resolved value before emitting" line. `SKILL.md:111` says "interpolate placeholders … the same way Stage 1e interpolates the primary template." `customize.toml:22` unified the `updated` field naming. |

Carryover from earlier rounds:

- The prepass critical issue "Referenced stage file does not exist: 06-business-flow-diagram.md" (`workflow-integrity-prepass.json:120-125`) is the same false positive from rounds 2 + 3 — the prepass extracts `D-06-business-flow-diagram.md` (the output document filename, appearing in five places in SKILL.md and the headless contract) as a stage reference. The skill has no carved stage files — the workflow is inline. No skill-side action.

## New issues introduced by the round-4 polish

### Medium

**M-1 — Overview's "Sits between PRD and Architecture" framing now over-promises versus the surface**
`SKILL.md:12`. The sentence "Sits between PRD and Architecture in the BMM planning phase. Downstream Architecture / UX / Story workflows consume the produced flows." was carried forward from round 3, but round 4 added the explicit downstream-consumers list at `SKILL.md:228` (`bmad-create-architecture`, `bmad-create-ux-design`, `bmad-create-epics-and-stories`, `hbc-create-invest-epics-and-stories`) which is the authoritative statement. The Overview line is now redundant scaffolding ("This workflow is designed to…" pattern per the principles file's "Meta-explanation" anti-pattern). Either drop the line from the Overview and let the Stage-5 list speak, or trim the Stage-5 paragraph to "Hand off to the downstream workflows named in the Overview." One source of truth, not two. Severity is medium not low because both surfaces are subject to drift — adding a new downstream consumer (say, `bmad-create-test-design`) updates one and not the other.

**M-2 — `## Headless Mode` SKILL.md anchor is now thinner than its forward-references demand**
`SKILL.md:57-59`. The carved-out `references/headless-contract.md` is the right size and shape, but the SKILL.md section that remains is a single-paragraph pointer that says "Stages below cite that contract where each interactive decision has a headless default." In practice, three later stages (`1a:89`, `1d:146`, `4:214`, `5:232`) reference specific `reason` values *by name* (`template_missing`, `no_prd_and_no_interactive_in_headless`, `mermaid_validation_failed`, `fr_coverage_gap`) but those values are only defined inside the carved file. An LLM hitting a `blocked` path on a session where context has been compacted and `references/headless-contract.md` hasn't been re-read will see the name with no anchor to its meaning. Two cleaner shapes:

- Keep the closed-set table of `reason` values inline at `## Headless Mode` (it's 6 short rows; even at full width it's smaller than the parallel-lens menu block above it). The carve-out keeps the flags table and JSON shape.
- Or have each stage that uses a `reason` value cite the carved file by name at the point of use (e.g. `SKILL.md:214` could say "return `blocked` with one of the defined reasons in `references/headless-contract.md` — here, `mermaid_validation_failed`"). The pointer is cheap and survives compaction.

Currently the prepass / metrics say "fine" because the file is small (957 tokens), but the principle "Carved-out files survive context compaction — critical instructions in the file itself" cuts both ways. The blocker semantics are critical instructions that ought not to live exclusively in the carve-out *or* exclusively in SKILL.md.

### Low

**N-1 — `references/headless-contract.md:3` opens with a meta-explanation of *why it was carved out***
`references/headless-contract.md:3`: "Carved out of `SKILL.md` per principle 'carve to references/ when the section is a contract or reference table, not a procedure.' This file is the authoritative reference for `--headless` / `-H` invocation of `hbc-create-business-flow-diagram`." The second sentence is genuine content; the first is meta-explanation about the build decision that produced the file ("This workflow is designed to…" anti-pattern, principles-file: "What Doesn't Earn Its Keep"). Cut the first sentence; the second sentence already self-identifies the file's role to anyone who reads it standalone.

**N-2 — Stale `__pycache__` from the previous test naming**
`scripts/tests/__pycache__/` carries both old-name (`test_check_fr.cpython-314.pyc`, `test_discover.cpython-314.pyc`, `test_validate_mermaid.cpython-314.pyc`) and new-name (`test_check-fr-coverage.cpython-314.pyc`, `test_discover-planning-artifacts.cpython-314.pyc`, `test_validate-mermaid.cpython-314.pyc`) compiled files. This is a build-environment artifact from the rename, not a skill defect — and `__pycache__/` should be `.gitignore`d at repo level anyway — but the doubled set suggests neither this skill nor the repo carries the standard Python `.gitignore` pattern. Worth a `.gitignore` of `__pycache__/` and `*.pyc` at the skill or repo root so the rename is fully clean.

**N-3 — `## Parallel-lens menu` section heading is over-long for a level-2 heading**
`SKILL.md:61`: `## Parallel-lens menu (used at end of Stage 3 and Stage 4)`. The parenthetical is information the in-section pointers (`SKILL.md:192`, `SKILL.md:218`) carry anyway. As a top-level heading it makes the table of contents read oddly compared to the sibling stage sections (`## Workflow`, `## On Complete`). Trim to `## Parallel-lens menu` and let Stage 3 and Stage 4 say "Present the parallel-lens menu defined above" (which they already do). Pure aesthetics, but the top-level section list reads cleaner.

**N-4 — `SKILL.md:204` "If FR coverage was not requested…" sentence is stale**
`SKILL.md:204`: "If FR coverage was not requested or the PRD has no FR identifiers, the script's `uncovered` and `phantom` will both be empty." `check-fr-coverage.py` has `--prd` as `required=True, action="append"`, so the script is always run when Stage 4 fires; "not requested" is no longer a runtime mode. The sentence is a leftover from an earlier shape where coverage was optional. Tighten to "If the PRD declares no FR identifiers, `uncovered` and `phantom` are both empty (valid pass)." Or remove — the script behaviour is documented in its own docstring.

## Strengths to preserve

These are the round-4 additions that made the round-3 → round-4 jump worth doing:

- **`recommended_intent` synthesised in the script, consumed by the prompt.** `discover-planning-artifacts.py:169-180` encodes the Fresh / Resume / Update state machine deterministically (Fresh when no primary or no `stage-1`; Update when `stage-5`; Resume otherwise). SKILL.md`:89` consumes it. This is the principles-file "Intelligence placement" split done correctly — script computes state, prompt makes the call. The 1a / 1b ordering (workspace scan before open-floor, with `recommended_intent` surfaced as the menu default) reads naturally and survives compaction because the state lives in two files.
- **Auto-fix gating moved into the script.** `validate-mermaid.py:140-147` decides per-issue whether something is `auto_fixable` (true only when the alias appears in arrow lines with no display-label conflict). `SKILL.md:214` says "apply only validator issues marked `auto_fixable: true` … citing the validator's `fix_hint`." The round-3 M3 "unambiguous in prose" leak is fully closed: the judgment lives in tested code, the prompt is mechanical.
- **Wrong-skill off-ramp positioned before scripted ingestion.** `SKILL.md:119` fires the off-ramp inside 1b, after the open-floor reply but before any heavier work. This matches the principles-file "Intent-before-ingestion" pattern named on line 150. The off-ramp explicitly names the alternative skills (`bmad-create-architecture` for system architecture) rather than just declining.
- **Short-circuit on a complete open-floor reply.** `SKILL.md:121` lets 1b skip 1e when the user volunteered everything 1e would otherwise confirm. This is the "Capture-don't-interrupt" / "Soft-gate elicitation" pair on line 148-149 of the principles applied to flow control, not just elicitation. Drops one confirmation round-trip on the common "user knows exactly what they want" case.
- **Compaction-flush at Stage 2 (`SKILL.md:171-176`).** Round-3 design carried into round 4 unchanged, and remains the most valuable single piece of the workflow — actor list + flow inventory get written to both primary frontmatter AND `.decision-log.md` before the workflow continues. Compaction here can't drop work.
- **Headless contract carved to `references/headless-contract.md` with a closed-set `reason` enum.** `references/headless-contract.md:58-69` defines six and only six `reason` values; the carve-out preamble names them as a "closed set — automators rely on the closed-set guarantee." That's a real downstream contract, not handwaving.
- **22-test scripts/tests/ suite with PEP-723 inline metadata.** `scripts/tests/run-tests.py` uses importlib path-based loading to handle the hyphenated `test_<script>.py` naming the path-standards check requires. `--d06` / `-o` / `--output` flag shapes are stable across the three scripts. The script-prompt boundary is tested at the script side; the prompt side trusts the script.
- **Description quoted-trigger discipline survived the rewrite.** `SKILL.md:3` carries both English and Vietnamese triggers with the round-4 additions (`'vẽ sơ đồ luồng nghiệp vụ'`, `'vẽ D-06'`); none of the triggers are vague enough to hijack unrelated conversations. The description-overbroadens failure mode from the principles file is closed.
- **Conventions block stamped verbatim** at `SKILL.md:16-22`, including the round-4 placeholder-substitution-before-output line. Carved file uses `{communication_language}` and `{document_output_language}` (`SKILL.md:26-27`) — and the carved `references/headless-contract.md` correctly stays prose-only because it's a contract file, not a stage prompt that needs language framing.

## Verdict

Excellent. Round 4 absorbed the round-3 deltas without over-correcting, the principles-file checklist comes back clean on every load-bearing item (intelligence placement, decision-log workspace, headless contract surface, compaction survival, conventions stamp, description discipline, trigger-phrase coverage). The four medium / low findings above are polish-the-polish: M-1 and M-2 are real architectural calls (single-source-of-truth for downstream consumers and for blocker semantics); N-1 / N-3 / N-4 are 1-line edits; N-2 is a `.gitignore` line. No finding in this round threatens execution or violates a stated promise.
