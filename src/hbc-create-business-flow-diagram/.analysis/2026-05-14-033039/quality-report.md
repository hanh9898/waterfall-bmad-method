# BMad Quality Analysis: hbc-create-business-flow-diagram (Round 5)

**Analyzed:** 2026-05-14T03:30:39Z | **Path:** `C:/Users/HanhNT2/stc-erp-bmad-custom/src/hbc-create-business-flow-diagram`
**Round-1 baseline:** `.analysis/2026-05-14-021953/quality-report.md` (Good, 2 broken + 12 opportunities)
**Round-3 baseline:** `.analysis/2026-05-14-030108/quality-report.md` (Good, 0 broken + 3 high + 5 medium + 1 low)
**Interactive report:** quality-report.html

## Assessment

**Good (at the ceiling)** — Round 4 closed all nine round-3 themes with high confidence (architecture and customization scanners independently rate the skill Excellent), but the enhancement scanner withholds the promotion on the strength of one new High and four still-open round-3 edge cases. The new High (N1: undefined version-bump semantics on back-to-back Update sessions) is the only finding gating the Good -> Excellent transition; everything else in this round is polish-grade. Closing N1 plus the Stage 1b partial-reply tightening (N2) tips the skill to Excellent without further structural work.

The skill has crossed from "Good with rough edges" to the canonical Decision-Log Workspace + headless contract + parallel-lens menu + open-floor short-circuit shape that the principles file describes. The first-invocation experience is now textbook; the unfinished work is concentrated on second-and-later invocations (Update-then-Update version bumps, partial-open-floor reads, crash-recovery vs clean-Fresh audit signal). Two scanners argue for Excellent on architectural grounds; one scanner argues Good-very-close-to-Excellent on UX grounds. We side with the latter because the enhancement scanner's N1 is a real production audit-trail risk that has not been written down.

## Round-4 success rate: 9/9 round-3 themes resolved

All nine themes the round-3 report opened are explicitly confirmed absent from this round's scanner output. High confidence.

| Round-3 finding | Status | Scanner confirmation |
|---|---|---|
| H-1 (a-i): Script hygiene and long-tail input coverage (9 sub-findings) | **Resolved** | `scripts-temp.json` status=pass, 0 findings; determinism scanner Round-3 / round-4 resolutions table confirms each sub-finding closed with file:line evidence. |
| H-2: Build-time decision log parked in references/ | **Resolved** | `references/` now contains only `headless-contract.md`; architecture scanner verifies. |
| H-3: Activation block diverges from sibling hand-merge pattern | **Resolved** | `SKILL.md:37` restores the three-file base -> team -> user merge with explicit structural-merge rules. |
| M-4 (a-d): Resume protocol edges and Stage 1 ordering (4 sub-findings) | **Resolved** | `discover-planning-artifacts.py:170-181` computes recommended_intent server-side; `customize.toml:36` dropped `{date}`; SKILL.md:121-122 added short-circuit clause; wrong-skill off-ramp moved to 1b before consume step. |
| M-5 (a-c): Parallel-lens menu clarity, dedup, headless signal (3 sub-findings) | **Resolved** | `SKILL.md:61-73` defines the menu once at top level with cost/shape disambiguation; `--review-lenses=skip\|advanced\|party` flag added; `review_lenses_run` in JSON return contract. |
| M-6: SKILL.md size over multi-branch ceiling | **Resolved** | `prompt-metrics-prepass.json:9` reports 237 lines / 3,998 tokens (was 260 / 3,772 with two tables). |
| M-7: Stage 4 deterministic-fix prose hands judgment back to LLM | **Resolved** | `validate-mermaid.py:140-147` emits per-issue `auto_fixable: bool` + `fix_hint`; `SKILL.md:214` consumes mechanically. |
| M-8: Workflow-type prepass mismatch (Simple vs Complex) | **Resolved** | The conflicting build-log claim is gone with the build log itself; prepass agrees (Complex). |
| L-9 (a-e): Schema and labelling tidies (5 sub-findings) | **Resolved** | `SKILL.md:3` carries Vietnamese triggers; `assets/decision-log-template.md:1-11` unified field names on `updated`; `references/headless-contract.md:33` carries placeholder-substitution line; Stage 1a explicitly interpolates the decision-log template. |

The one prepass critical issue ("Referenced stage file does not exist: 06-business-flow-diagram.md", `workflow-integrity-prepass.json:120-125`) is the same false positive from rounds 2 + 3 — the prepass extracts the output document filename as a stage reference. The skill has no carved stage files; the workflow is inline. No skill-side action.

The path-standards scanner shows 31 high-severity findings, all of them inside `.analysis/<timestamp>/` quality-report files from rounds 1 and 3 — prior-round output, not skill source. The scanner has no `.analysis/` exclusion, so it self-reports against its own historical artifacts. Skill source is clean (the architecture scanner re-ran `scan-path-standards.py` against `SKILL.md` / `references/` / `assets/` / `customize.toml` alone in round 3 and confirmed zero structure findings; nothing in round 4 changed the skill-source surface). Not a real finding.

## What's Broken

None. Zero critical, zero high in the skill source itself. The one new High in this round is an architectural omission, not a defect — see Opportunity 1.

## Opportunities

### 1. Update-then-Update version-bump semantics undefined (high — 1 observation)

`recommended_intent = "Update"` fires whenever `stage-5 in stepsCompleted`, and Stage 3 mechanically bumps the minor version every time. Back-to-back same-day fix-typo sessions therefore produce `1.0 -> 1.1 -> 1.2 -> 1.3` revision-history rows for cosmetic edits the audit reader can't distinguish from semantic changes. The version-bump rule has become load-bearing on a model judgement ("is this polish or semantic?") the skill never asks the model to make and the headless contract gives no flag for. **Fix:** Insert a scope-of-change gate at Stage 3 Update entry — prompt the user (interactive) or check `--scope-of-change=polish|semantic` (headless) before bumping. Polish appends a note to the prior version row; semantic bumps minor. Alternative: auto-detect by diffing the Stage 2 flush against the prior session's flush.

**Observations:**
- Back-to-back Update sessions bump version on cosmetic edits with no scope-of-change check — `SKILL.md:186` (enhancement, N1)

### 2. Second-invocation ergonomics: partial-reply short-circuit and crash-recovery audit signal (medium — 2 observations)

Two related findings cluster on the second time a user invokes the skill against an existing workspace. The Stage 1b short-circuit prose says skip 1e "if the open-floor reply already specifies mode, scope, sources, and diagram type unambiguously" — but a three-of-four reply with one silent dimension will likely pattern-match as "covers everything" and quietly commit the workflow default for the silent dimension. Separately, the discover script collapses two genuinely different states (no prior workspace; prior workspace existed but `stepsCompleted == []` from a pre-stage-1 crash) into a single `recommended_intent: Fresh`, with no `discarded_partial` signal anywhere. **Fix:** Tighten the short-circuit clause to require all four dimensions explicit (pre-fill what was given, ask the rest); emit `resume_state.discarded_partial: true` when primary existed but stepsCompleted was empty, and require the Stage 1a headless decision-log line to cite the flag.

**Observations:**
- 1b partial-reply short-circuit will read three-of-four as "covers everything" — `SKILL.md:121` (enhancement, N2)
- Fresh-with-discarded-partial is indistinguishable from clean Fresh in the audit log — `scripts/discover-planning-artifacts.py:170` (enhancement, N3)

### 3. Carved-file contract surface drift — single-source-of-truth choices (medium — 2 observations)

Round 4 carved the headless contract to `references/headless-contract.md` correctly (reference table, not procedure), but introduced two surface-drift items. The Overview line 12 ("Sits between PRD and Architecture ... Downstream Architecture / UX / Story workflows consume the produced flows") duplicates Stage 5 line 228's authoritative downstream-consumer list — adding a new consumer updates one and not the other. And three later stages cite specific `reason` values by name that are only defined inside the carved file, so an LLM hitting a `blocked` path after context compaction sees the name with no anchor to its meaning. The "carved files must survive context compaction" principle cuts both ways: critical instructions shouldn't live exclusively in the carve-out OR exclusively in SKILL.md. **Fix:** Pick one source of truth per artifact — drop the Overview "Sits between" sentence and let Stage 5's named list speak, or have Stage 5 say "hand off to the downstream workflows named in the Overview." For reason values, inline the six-row closed-set table at `## Headless Mode` or cite the carved file at each point of use.

**Observations:**
- Downstream-consumers list duplicated between Overview and Stage 5 — `SKILL.md:12` (architecture, M-1)
- Stage references to reason values only defined in carved headless contract — `SKILL.md:57` (architecture, M-2)

### 4. Carryover edge cases on rare-but-real workflow inputs (low — 4 observations)

Four still-open items from round 3. None of them regressed and none are new in round 4 — they were deferred deliberately as rare-but-real long-tail inputs and remain low-impact. Zero-actor PRDs (data-pipeline / batch / cron only) produce `System -> System` self-loops that pass Mermaid validation vacuously. `--mode=migration` on a greenfield PRD will fabricate an empty AS-IS section; no reverse heuristic. Targeted single-flow Update has no `--update-flow=<name>` path. The `"prd" in d.name.lower()` heuristic still matches `apprd/`. **Fix:** Tackle in the next polish round, smallest first. Tighten the PRD-dir heuristic to `\bprd\b`. Add one Stage 2 line on promoting cron / event triggers. Add `--update-flow=<name>` to the Stage 3 Update path. Add a Stage 2 reverse heuristic on empty-AS-IS-under-migration.

**Observations:**
- Zero-actor PRD produces shapeless diagram with vacuous validation — `SKILL.md:163` (enhancement, SO1)
- `--mode=migration` on greenfield PRD fabricates AS-IS with no reverse heuristic — `SKILL.md:169` (enhancement, SO2)
- No targeted single-flow update path — `SKILL.md:89` (enhancement, SO3)
- PRD-dir heuristic matches `apprd/` and similar — `scripts/discover-planning-artifacts.py:228` (enhancement, L3)

### 5. Polish-the-polish: residual prose drift introduced by the round-4 carve-out (low — 4 observations)

Four small surface items the round-4 polish introduced or left behind. The carved `references/headless-contract.md` opens with a meta-explanation of why it was carved out ("What Doesn't Earn Its Keep" anti-pattern). SKILL.md still carries a three-line `## Headless Mode` block that only explains the carved file exists (same anti-pattern, applied to a carve-out announcement rather than to a section pattern). The `## Parallel-lens menu (used at end of Stage 3 and Stage 4)` heading parenthetical duplicates the in-stage pointers and reads oddly compared to sibling stage sections. The Stage 4 sentence "If FR coverage was not requested..." is stale since `--prd` is now `required=True`. **Fix:** Cut the first sentence of `references/headless-contract.md:3`; delete the three-line block at `SKILL.md:57-59`; trim the parallel-lens heading; tighten the Stage 4 sentence to "If the PRD declares no FR identifiers, `uncovered` and `phantom` are both empty (valid pass)."

**Observations:**
- Carved headless-contract.md opens with a meta-explanation of why it was carved — `references/headless-contract.md:3` (architecture, N-1)
- `## Headless Mode` block is three lines of meta-explanation about the carve-out — `SKILL.md:57` (enhancement, N4)
- Parallel-lens heading is over-long for a level-2 — `SKILL.md:61` (architecture, N-3)
- Stage 4 "If FR coverage was not requested..." sentence is stale — `SKILL.md:204` (architecture, N-4)

### 6. Script-side residuals: frontmatter robustness and walk-exclusion completeness (low — 5 observations)

Five low-severity script residuals. The `stepsCompleted` regex matches only inline-list YAML, treating block-style as empty and routing a block-style partial-frontmatter primary to `recommended_intent: Fresh` instead of `Resume` — exactly the round-3 user-visible failure this script was built to prevent (the unit test only exercises the inline form, so the regression isn't caught). Empty-quoted frontmatter values survive in the JSON with quotes intact (`primary_last_step: "''"`). The `auto_fixable` typo-vs-add ambiguity isn't documented in `fix_hint`. `EXCLUDE_DIRS` is missing `.analysis`, `.claude`, `_bmad`, `dist`, `build`, `out`, `vendor`, `.venv`, `.tox`, cache and tmp dirs. Subprocess tests use `sys.executable` rather than `uv run --script` — not a defect today (scripts are stdlib-only), but would silently break the day a non-stdlib dependency is added. **Fix:** Extend the regex with a block-style pattern (or adopt pyyaml via PEP 723 — confirm with team first per script-standards.md); post-strip outer quote pairs; append "verify not a typo of an existing participant" to fix_hint; expand EXCLUDE_DIRS.

**Observations:**
- stepsCompleted regex doesn't match block-style YAML — `scripts/discover-planning-artifacts.py:140` (determinism, L1)
- Empty-quoted frontmatter values survive with quotes in JSON — `scripts/discover-planning-artifacts.py:144` (determinism, L2)
- `auto_fixable` typo-vs-add ambiguity undocumented in fix_hint — `scripts/validate-mermaid.py:136` (determinism, L3)
- EXCLUDE_DIRS missing project-meta and build/cache dirs — `scripts/check-fr-coverage.py:40` (determinism)
- Tests invoke scripts via sys.executable, not uv run — `scripts/tests/test_*.py:1` (determinism, L5)

### 7. Localization vs control-word collision in decision-log (low — 1 observation)

The Language Rules say "translate all prose (section headings, table headers ...)" but `discover-planning-artifacts.py:154` extracts the last session block via a literal English `^##\s+Session\s+([^\n]+)$` regex. A Japanese-language project that follows the Language Rules literally gets `## セッション ...` headings, and the next session's resume-state extractor silently returns `last_session_summary: None`. The `## Session ...` heading isn't in the carve-out list of preserved-English forms at `SKILL.md:29`. **Fix:** Add "Session" (or the full date-stamped heading pattern) to the preserved-English list — smaller diff — or switch the script regex to a date-based anchor.

**Observations:**
- Decision-log Session heading regex collides with Language Rules translation — `scripts/discover-planning-artifacts.py:154` (enhancement, N5)

### 8. Cleanup: stale __pycache__ from test-file rename (low — 1 observation)

`scripts/tests/__pycache__/` carries both old-name (`test_check_fr.cpython-314.pyc` etc.) and new-name (`test_check-fr-coverage.cpython-314.pyc` etc.) compiled files from the round-4 test rename. Indicates no `.gitignore` covering `__pycache__/` and `*.pyc`. **Fix:** Add `__pycache__/` and `*.pyc` to `.gitignore` at the skill or repo root; `git rm -r --cached scripts/tests/__pycache__/`.

**Observations:**
- Stale `__pycache__` files from test-file rename — `scripts/tests/__pycache__/:0` (architecture, N-2)

## Strengths

- **Decision-Log Workspace + Resume state machine lives in the script, not the prompt.** `discover-planning-artifacts.py:118-182` computes `recommended_intent` deterministically from primary frontmatter and the last decision-log session block; SKILL.md:89 consumes by key. The textbook intelligence-placement split applied to state — set-membership in the script, judgement in the prompt — saves ~200-500 tokens per Resume/Update activation.
- **Auto-fix gating moved out of prose and into the script.** `validate-mermaid.py:140-147` emits per-issue `auto_fixable: bool` + `fix_hint`. The M-7 prose-leak is fully closed: judgement lives in tested code, the prompt is mechanical.
- **Stage 2 compaction-flush.** Actor list + flow inventory get written to both primary frontmatter AND `.decision-log.md` before the workflow continues (`SKILL.md:171-176`). The single highest-value piece of the workflow — compaction can't drop work.
- **Headless contract carved to `references/headless-contract.md` with a closed-set reason enum.** Six and only six reason values, with an explicit "automators rely on the closed-set guarantee" promise. Real downstream contract.
- **customize.toml is now an exemplar.** Four scalars (every one wired, every one commented, default path stable for re-run resume) plus the three always-present arrays. The round-4 drop of `{date}` from the output-path default was the last real abuse on the surface. Every declared scalar is referenced from SKILL.md as `{workflow.<name>}` — no silent-noop overrides.
- **Wrong-skill off-ramp positioned before scripted ingestion.** `SKILL.md:119` fires the off-ramp inside 1b, after the open-floor reply but before any heavier work. Matches "intent-before-ingestion" and explicitly names alternative skills.
- **Description quoted-trigger discipline including Vietnamese.** `SKILL.md:3` carries `'vẽ sơ đồ luồng nghiệp vụ'` and `'vẽ D-06'` alongside English triggers; none vague enough to hijack unrelated conversations.
- **22-test scripts/tests/ suite with PEP 723 inline metadata.** importlib path-based loader for hyphenated filenames; all scripts carry `# /// script` blocks. Full pass on the round-5 run.

## Detailed Analysis

### Architecture

The round-4 pass cleanly resolves all nine round-3 themes and the skill now reads as a mature, deliberately-built Decision-Log Workspace workflow with first-class headless and a sound script-prompt split. Architecture scanner verdict: **Excellent**. The four medium/low findings it surfaces are polish-the-polish — M-1 and M-2 are real architectural calls (single-source-of-truth for downstream consumers and for blocker semantics); N-1/N-3/N-4 are 1-line edits; N-2 is a `.gitignore` line. None threatens execution or violates a stated promise.

### Determinism & Distribution

Intelligence placement is **Excellent**. The script-vs-prompt boundary is honoured both ways: the scripts contain no meaning-judgements (regex, set-diff, glob, count), and SKILL.md contains no deterministic operations the scripts already own. The five round-5 findings (L1-L5) are honest residuals — frontmatter parsing brittleness against block-style YAML, latent quote-stripping bug, `auto_fixable` typo-edge, test-runner-hack-as-documented-pattern (accept), and a future-proofing note on subprocess-vs-`uv run`. None are intelligence leaks; none reopen the in-prompt determinism wound. Estimated token savings against an in-prompt implementation: ~2.6k–5.2k, plus ~200–500 tokens per Resume/Update activation via the new resume_state shortcut. The pre-pass pattern at §1a is now textbook-quality and worth lifting into `script-opportunities-reference.md` as the reference example.

### Customization Surface

**Exemplary.** Surface is four workflow-specific scalars (`business_flow_template`, `business_flow_output_path`, `diagram_type`, `on_complete`) plus the three always-present arrays. The round-4 drop of `{date}` from the output-path default aligned the customization surface with the workflow's own resume protocol. Customization scanner explicitly recommends this file as a reference exemplar for future scans of the `*_template` / `*_output_path` / `on_<event>` patterns. The scanner verified absent: per-skill `communication_language` / `document_output_language` overrides, identity/persona/tone fields, boolean toggles, migration-vs-greenfield default, or any toml-level extension of the closed-set `reason` enum. All correct calls.

### User Experience

**Good, very close to Excellent.** Round 4 did the hard work of cleaning up the round-3 ordering + silent-default theme. The remaining items cluster on a new theme that round 4 surfaced: **state transitions on the second-and-later invocation**. Update-then-Update version bumps (N1, the High), partial-open-floor reads (N2), crash-recovery vs no-prior collapse (N3), localised Session heading (N5). The first invocation is now textbook; the second-invocation ergonomics are where polish would land. Headless is structurally ready: `--review-lenses` flag + return field, `--no-prd-ok` opt-in for greenfield, `recommended_intent` server-side, auto-fix scoped to validator-emitted flags. The JSON return contract is the smallest set of paths the caller needs plus `review_lenses_run`; the closed-set reason table covers six named failures.

## Recommendations

1. **Add a scope-of-change gate at Stage 3 Update entry** (polish vs semantic) — closes the one finding the enhancement scanner cited as gating Good → Excellent. (resolves 1, effort: low)
2. **Tighten the Stage 1b short-circuit clause** to require all four dimensions explicit, AND emit `resume_state.discarded_partial` from the discover script to distinguish crash-recovery Fresh from clean Fresh. (resolves 2, effort: low)
3. **Pick single source of truth** for downstream-consumers list (Overview vs Stage 5) and for headless reason names (inline at `## Headless Mode` vs cite-in-stage). Two coherent decisions. (resolves 2, effort: low)
4. **Polish-the-polish:** delete the carved-file meta-explanation preamble; delete the three-line `## Headless Mode` block; trim the parallel-lens heading; tighten the stale Stage 4 FR-coverage sentence. (resolves 4, effort: low)
5. **Script-side robustness:** extend the `stepsCompleted` regex for block-style YAML; expand `EXCLUDE_DIRS`; post-strip empty-quoted frontmatter values; document the `auto_fixable` typo-vs-add edge in `fix_hint`. (resolves 5, effort: low)
6. **Address the four round-3 carryover edge cases** (zero-actor PRD, forced-migration on greenfield, targeted single-flow update, eager prd-dir heuristic) in the next polish round. (resolves 4, effort: medium)
7. **Add "Session"** (or the full date-anchored heading pattern) to the Language Rules preserved-English list to resolve the decision-log heading collision in non-English projects. (resolves 1, effort: low)
8. **Add `__pycache__/` and `*.pyc` to `.gitignore`**, then `git rm -r --cached scripts/tests/__pycache__/`. (resolves 1, effort: low)

---

## Round-5 verdict tóm tắt (cho user)

Independent regrade: **Good (ceiling)**. Tất cả 9 themes round 3 đã được close với độ tin cậy cao — L1 architecture và L3 customization đều rate Excellent. Lý do duy nhất chưa lên Excellent là enhancement scanner phát hiện 1 new High mới + 1 tightening:

- **N1 (High)** — Update-then-Update version bump không có scope-of-change gate. Sửa 1.0 typo → 1.1, sửa typo nữa → 1.2 → 1.3 trên cùng ngày, audit reader không phân biệt được polish vs semantic.
- **N2 (Medium)** — Stage 1b short-circuit clause "if reply specifies mode, scope, sources, AND diagram type unambiguously" có thể bị loose-read khi reply chỉ cover 3/4 dimensions.

Fix 2 cái đó → Excellent. Các finding khác đều polish/cosmetic.

---

## Round 6 — All 13 round-5 findings resolved (2026-05-14)

User confirmed scope "fix hết luôn đi". All 1 high + 4 medium + 4 low + 4 carryover items addressed in one comprehensive pass. Lint pipeline still clean.

### Resolution table

| # | Round-5 finding | Severity | Fix |
|---|---|---|---|
| N1 | Update-then-Update version bump undefined | high | Added scope-of-change gate at Stage 3. Headless: `--scope-of-change=polish\|semantic\|auto` flag (default `auto`). Auto-mode diffs `stage_2_actors`/`stage_2_flows` vs prior session's flush block — identical = polish (append note to prior row, no version bump), different = semantic (new row, minor bump). Interactive prompt for ambiguous case. |
| N2 | Stage 1b short-circuit loose with partial reply | medium | Tightened clause to "strict gate. Only skip 1e when the open-floor reply *explicitly* covers **all four** of: mode, scope, sources, diagram type. A partial reply falls through to 1e." Logs which dimensions were inferred vs confirmed. |
| N3 | Fresh-new vs Fresh-after-crash collapse | medium | Added `fresh_reason` field to `resume_state` JSON. Values: `no_workspace`, `crashed_no_progress`, `stale_artifact`. SKILL.md Stage 1a surfaces the distinction; headless logs it explicitly. Test `test_resume_state_recommends_fresh_when_workspace_empty` and `test_resume_state_recommends_fresh_when_steps_empty_post_crash` confirm. |
| M-1 | Overview duplicates Stage-5 downstream list | medium | Overview line "Sits between PRD and Architecture" replaced with "Stage 5 enumerates the canonical downstream consumers." Single source of truth restored. |
| M-2 | Reason values reachable only in carved file | medium | Added a brief closed-set reason values list directly in SKILL.md "## Headless Mode" section (compaction-survival mirror). Full table stays in `references/headless-contract.md`. |
| N-1 | Meta-explanation in references/headless-contract.md | low | Replaced first paragraph from "Carved out of SKILL.md per principle…" to a content-only "Authoritative reference for `--headless`..." opener. |
| N-3 | "## Parallel-lens menu (used at end of Stage 3 and Stage 4)" overlong heading | low | Shortened to "## Parallel-lens menu". Usage note stays in lead paragraph. |
| N-4 | Stale "If FR coverage was not requested" sentence | low | Removed dead-code phrasing; sentence now reads "If the PRD has no FR identifiers, `uncovered` and `phantom` will both be empty." `--prd` flag is `required=True`, so "not requested" branch was impossible. |
| N-2 | Stale __pycache__ + no .gitignore | low | Created `.gitignore` at skill root (excludes `__pycache__/`, `.scan/`, `*.pyc`, etc.). Deleted stale `__pycache__` carrying old test names. |
| N5 | Decision-log Session heading regex English-only | low | Decision-log template heading changed from `## Session yyyy-mm-dd…` to `## yyyy-mm-dd… — Session:` (date-first). Discover script regex changed from `^##\s+Session\s+([^\n]+)$` to `^##\s+([^\n]*\d{4}-\d{2}-\d{2}[^\n]*)$` — language-agnostic, anchored on the date. Test `test_session_heading_regex_matches_vietnamese_log` confirms it parses `## 2026-05-14T10:23 — Phiên: Cập nhật`. |
| SO1 | Zero-actor PRD renders vacuous diagram | low (carryover) | Stage 2 has explicit zero-actor branch: do not render System-talks-to-itself; promote trigger (cron/queue/webhook) to first-class actor and explain in decision log. |
| SO2 | Forced `--mode=migration` on greenfield PRD | low (carryover) | Stage 1e adds migration-vs-AS-IS sanity check. If mode resolves to migration but no PRD source has AS-IS/現状/"current state" markers → warn (interactive) or `blocked` with new `reason: "migration_without_as_is"` (headless). New `--allow-migration-without-as-is` flag to acknowledge intentional cases. Headless-contract.md updated with the new flag + reason. |
| SO3 | Targeted single-flow update missing | low (carryover) | Stage 1a Update menu now offers `[U1] Update all flows` vs `[U2] Update a single named flow`. Headless: `--update-flow=<name>` flag. Stage 3 honours the flag: re-renders only the named flow, leaves others untouched. |
| L3 | Eager `"prd" in name.lower()` matches non-PRD files | low (carryover) | Tightened to word-boundary regex `\bprd\b` (case-insensitive). Test `test_prd_directory_match_uses_word_boundary` confirms `approved/` no longer matches while `prd/` and `prd-customer/` still do. |

### Lint pipeline at end of round 6

| Scanner | Status |
|---|---|
| `scan-path-standards.py` (skill source) | pass — structure 0, frontmatter 0; all findings are inside historical `.analysis/` reports |
| `scan-scripts.py` | **pass — 0 findings** |
| `python scripts/tests/run-tests.py` | **25 pass / 1 skip** (was 22; +3 tests for fresh_reason, Vietnamese session heading, word-boundary prd) |

### File layout at end of round 6

```
src/hbc-create-business-flow-diagram/
├── .gitignore                                (NEW — round 6)
├── SKILL.md                                  (258 lines)
├── customize.toml
├── assets/
│   └── decision-log-template.md              (date-first Session heading)
├── references/
│   └── headless-contract.md                  (drop meta-paragraph; +scope-of-change, +update-flow, +migration_without_as_is)
└── scripts/
    ├── discover-planning-artifacts.py        (fresh_reason, date-anchored Session regex, word-boundary prd match)
    ├── validate-mermaid.py
    ├── check-fr-coverage.py
    └── tests/
        ├── __init__.py
        ├── run-tests.py
        ├── test_discover-planning-artifacts.py    (11 tests, was 8)
        ├── test_validate-mermaid.py               (7 tests)
        └── test_check-fr-coverage.py              (7 tests)
```

### Expected next grade

L1 (Excellent) and L3 (Excellent) verdicts from round 5 should hold. L4's lone blocker N1 is now closed with the scope-of-change gate; the four medium edge cases (N2/N3/SO1/SO2) and the carryover items are all addressed. A round-7 LLM scanner pass should confirm Excellent.
