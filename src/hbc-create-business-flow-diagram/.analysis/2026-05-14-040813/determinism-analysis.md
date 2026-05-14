# Determinism & Distribution Scan — Round 7 (Post-Round-6 Polish)

**Target:** `C:/Users/HanhNT2/stc-erp-bmad-custom/src/hbc-create-business-flow-diagram`
**Date:** 2026-05-14
**Scanner:** L2 (Determinism / Distribution)
**Round:** 7 (judging post-round-6 changes)

---

## Existing Script Inventory

| Script | Purpose | Tests | Lines |
|---|---|---|---|
| `discover-planning-artifacts.py` | Stage 1 pre-pass — PRD/UX/use-case inventory + resume_state | 9 | 263 |
| `validate-mermaid.py` | Stage 4 syntactic validator with `auto_fixable` flags | 7 | 245 |
| `check-fr-coverage.py` | Stage 4 FR-id covered / uncovered / phantom sets | 7 | 161 |
| `tests/run-tests.py` | importlib runner for hyphen-named test files | — | 50 |

`scan-scripts.py` (pre-pass) reports `status: pass, 0 findings`. `python scripts/tests/run-tests.py` returns `Ran 25 tests, OK (skipped=1)`.

---

## Assessment

**Verdict: Excellent.**

The round-6 polish closes the three loose ends round 5 left: an audit-trail ambiguity (no-workspace vs crashed-workspace collapsed into a single `Fresh` label), a regex that quietly assumed an English heading word ("Session"), and a sloppy substring match that would have matched directories named `approved/` or `notes-on-the-prd/`. Each change is paired with a focused new test, the determinism boundary in `_extract_resume_state` is still clean (regex captures structure, classifier maps to a closed-set enum, no semantic inference), and the JSON contract gained a single nullable field rather than a new shape. Intelligence placement, contract clarity, and regex hygiene are all where they should be for a skill of this size.

The remaining live judgement call — **whether the Stage-3 auto-detect scope-of-change diff should be lifted into a script** — is treated explicitly in the "Specific Assessments" section below, with a recommendation.

---

## What Round 6 Got Right (Strengths to Preserve)

### 1. `fresh_reason` closes a real audit-trail gap

Per `skill-quality-principles.md` ("Headless mode" section):

> *"The decision log absorbs every assumption made without the user… `status` is `complete` or `blocked`; on `blocked`, include a one-line `reason` and still return the log path so the caller can read the detail. Without this discipline, headless silently buries its calls and the audit trail breaks on the next session."*

Round 5 had a single `recommended_intent: "Fresh"` value covering two semantically different states ("never started" vs "started but crashed before stage-1 write"). The audit trail conflated a clean first-run with recovery from a crash. The new `fresh_reason` field (`no_workspace` | `crashed_no_progress` | `stale_artifact` | `null`) is exactly the discrimination headless callers need, and the test at lines 169-187 of `test_discover-planning-artifacts.py` asserts `null` when the intent isn't `Fresh` — i.e., the field doesn't bleed into unrelated states.

This is correctly script-side: it's a closed-set classifier driven by structural inputs (does primary exist? is `stepsCompleted` empty? does it contain `stage-5`?). No prompt would compute this faster or more reliably.

### 2. Date-anchored session-heading regex is the right generalization

Old: `^##\s+Session\s+([^\n]+)$` — encodes the English word "Session" as load-bearing.
New: `^##\s+([^\n]*\d{4}-\d{2}-\d{2}[^\n]*)$` — encodes the **shape** (a date-stamped H2).

This is a textbook structure-not-meaning improvement per `skill-quality-principles.md` "Intelligence placement":

> *"Script using regex to decide what content MEANS = intelligence leak into the script."*

The old regex was on the verge of that leak — it was using the English word "Session" as a meaning anchor. The new regex anchors on `YYYY-MM-DD`, which is a stable structural marker imposed by the workflow itself ("date-stamped session headings" — `skill-quality-principles.md` Decision-Log Workspace pattern, line 180). Vietnamese log headings (`Phiên`), Japanese (`セッション`), or any other translation now parse without the script needing to know any of them. The new test at lines 189-211 exercises the Vietnamese case directly.

### 3. Word-boundary `\bprd\b` eliminates a real false-positive class

`approved/`, `notes-on-the-prd/`, `prd-approval-process/` were all matched by the old `"prd" in d.name.lower()` substring check. Now only directories with `prd` as a word atom match — `prd/`, `prd-customer/`, `prd-v2/`, `prd_legacy/`. The test at lines 213-225 codifies the boundary by explicitly excluding `approved/`.

### 4. Test count and shape

22 → 25 tests, all three additions targeting the specific regressions the round-6 changes were meant to prevent. The pattern (subprocess invocation against the CLI, JSON parse, structural assertion) is consistent across every test file. No mocking, no fixtures-by-side-channel. This is what "could you write a unit test for it?" looks like when the answer is "yes, and they did."

---

## Specific Assessments (Round-7 Probe Questions)

### Q1: Are the scripts now firmly Excellent? (intelligence placement, contract clarity, regex hygiene, test coverage)

**Yes** on all four sub-axes:

- **Intelligence placement.** Every regex parses structure (frontmatter shape, date-stamped headings, Mermaid block shape, FR-id pattern, word-boundary directory names). No regex tries to decide what content means. Classification (`fresh_reason`, `recommended_intent`, `auto_fixable`) is closed-set enum mapping from structural inputs — not semantic interpretation.
- **Contract clarity.** Every script accepts a target path, writes JSON to `-o`, prints a one-line JSON summary to stdout, returns documented exit codes (0=pass, 1=fail, 2=error). Every script's JSON output has `passed`/`status` at top level. `--help` is the single source of truth for each interface.
- **Regex hygiene.** Patterns use named groups (`?P<src>`, `?P<dst>`, `?P<quoted>`, `?P<bare>`, `?P<display>`, `?P<targets>`, `?P<name>`) where they capture more than one alternative. The hyphenated `\bprd\b` is correctly anchored. The Mermaid arrow regex correctly handles `->>`, `-->>`, `--)`, `--x`, `--X` and activation prefixes (`+`/`-`). The frontmatter parser is a simple top-of-file slice rather than trying to be a real YAML parser, which is fine because the contract is narrow.
- **Test coverage.** 25 tests covering CLI contract (subprocess invocation, exit codes), happy path, edge cases (Japanese filenames, sharded PRDs, symlinks, quoted Mermaid aliases, Note participants, activation prefixes, NFR identifiers, excluded directories, multiple PRD paths), and the three new round-6 regressions. The symlink test correctly skips on Windows. No tests rely on shared state — each uses `TemporaryDirectory`.

### Q2: Should Stage-3 scope-of-change auto-detect be lifted into a new script?

The question is fair — the operation is "array set-membership against the prior flush block," which fits the "Comparison" category in `script-opportunities-reference.md`:

> *"Diff, cross-reference, verify consistency"*

**Recommendation: keep it in the prompt for now, but document the boundary.** Three reasons:

1. **Both inputs are already in conversation context.** `stage_2_actors` and `stage_2_flows` were just written by the LLM at the end of Stage 2 (compaction-flush). The prior session's flush block is in `.decision-log.md`, which has already been read by the resume protocol. Lifting the diff into a script means re-serialising context the LLM already holds, just to deserialise it on the other side. Net zero token savings, plus a script-launch round trip.
2. **The diff is genuinely "is the array equal" — no judgement.** Per `skill-quality-principles.md` "The Core Test": *"would an LLM do this correctly without being told?"* For two short flat string arrays in active context, yes. The risk profile of a 2025-era LLM mis-comparing two short arrays it just generated is materially below the risk profile of any script bug.
3. **`scope-of-change` is one decision per Update-mode invocation, not a hot path.** The token cost is low and one-shot. The scripts that exist today earn their keep by handling repeated work (every Mermaid block, every PRD shard, every FR-id) or by extracting compact JSON from large files. The scope-of-change diff is neither.

**However**, the contract should make the determinism floor explicit. Suggested SKILL.md edit at line 206:

> ~~"compare current `stage_2_actors` and `stage_2_flows` against the prior session's flush block in `.decision-log.md`."~~
>
> "compare current `stage_2_actors` and `stage_2_flows` against the prior session's flush block in `.decision-log.md` as **ordered set-membership** (a reordering counts as identical; an added or removed element counts as different). If both arrays' set-membership is identical → polish…"

This pins down what "differs" means — without that, two runs against the same change could disagree if one treats reordering as semantic and the other doesn't. **Severity: low** (medium token tax, no runtime failure, but determinism-across-runs is exactly what this scanner exists to surface).

If the project ever wants the diff scripted anyway (e.g. for headless audit log reproducibility), the script would be ~30 lines: read the latest flush block from `.decision-log.md`, read primary frontmatter, set-compare, emit `{scope: "polish"|"semantic", actors_diff: [...], flows_diff: [...]}`. Trivial. The reason to defer is that the LLM-prose version isn't broken.

### Q3: Should `fresh_reason` be a literal type in the schema/docs?

**Yes — should mirror the closed-set treatment of `reason` in the headless contract.**

The headless-contract table (lines 65-73 of `references/headless-contract.md`) lists every blocker `reason` value with "when it fires." Automators rely on the closed-set guarantee for switch-statement style branching. `fresh_reason` is exactly the same shape (closed set, machine-consumed, audit-trail-relevant), but currently it's only defined implicitly through the SKILL.md prose at lines 99-101:

> *"`Fresh` with `fresh_reason: "no_workspace"` — no primary at all."*
> *"`Fresh` with `fresh_reason: "crashed_no_progress"` — primary exists but `stepsCompleted` is empty."*

The `stale_artifact` value (set when frontmatter exists but `stage-1` isn't in `stepsCompleted` — line 194 of `discover-planning-artifacts.py`) is never mentioned in SKILL.md or headless-contract.md. That's a documentation gap, not a script defect, but it's the kind of asymmetry that bites later when an automator hits the `stale_artifact` branch and can't find it in any reference.

**Recommendation: add a `fresh_reason` table to `references/headless-contract.md`**, mirroring the existing blocker-reasons table:

| Value | When it fires |
|---|---|
| `no_workspace` | Workspace folder absent or contains no primary document. |
| `crashed_no_progress` | Primary exists with parseable frontmatter but `stepsCompleted` is empty (prior run crashed before stage-1 commit). |
| `stale_artifact` | Primary exists with `stepsCompleted` populated but `stage-1` not present (mid-stage-1 crash or hand-edited frontmatter). |
| `null` | Intent is `Resume` or `Update`. |

**Severity: low** (audit-trail completeness, no runtime failure).

### Q4: Does `\bprd\b` handle all HBC-relevant cases?

Let me trace the regex against the obvious cases:

| Directory name | Matches? | Correct? |
|---|---|---|
| `prd/` | ✅ yes (`\b` matches start/end of name) | ✅ |
| `prd-customer/` | ✅ yes | ✅ |
| `prd-customer-v2/` | ✅ yes | ✅ |
| `customer-prd/` | ✅ yes | ✅ |
| `approved-prd/` | ✅ yes | ✅ (this IS a PRD directory by name) |
| `approved/` | ❌ no | ✅ |
| `notes-on-the-prd/` | ✅ yes | ⚠️ debatable — see below |
| `prd_legacy/` | ✅ yes (`_` is `\w`, so `\b` is at the `_`? actually no — let me re-check) | depends |
| `PRD/` | ✅ yes (re.IGNORECASE) | ✅ |
| `prd-v1.2/` | ✅ yes | ✅ |
| `notprd/` | ❌ no (no word boundary inside the word) | ✅ |
| `prds/` | ❌ no | ⚠️ debatable — plural directory wouldn't match |

**Two edge cases worth flagging:**

1. **`prd_legacy/`** — Python's `\b` is the boundary between `\w` and `\W`. Underscore IS `\w`. So `\bprd\b` does NOT match `prd_legacy` (the boundary requires a non-word char on the right; `_` is a word char). If HBC ever uses snake_case PRD directory names, this won't match. Test it: the regex would need to be `(?<!\w)prd(?!\w)` to also exclude underscores. **Severity: low** — HBC's existing convention is kebab-case, and the directory-name match also requires `index.md` to exist (line 245), which acts as a second filter. But this is the kind of regex subtlety worth pinning in a comment.
2. **`notes-on-the-prd/`** — currently matches. Hash-on-the-trail: this is a docs-folder masquerading as a PRD. The `index.md` gate filters out most of these in practice, but a notes folder *could* have an `index.md`. The fix would be a positive-match list (`re.match(r"^prd($|[-_])", d.name)`) rather than a search anywhere in the name. **Severity: low** — wouldn't fire in any real-world HBC layout, but tightening the regex would make the contract clearer.

**Recommendation:** add a one-line comment in `discover-planning-artifacts.py` line 241 noting that underscore-prefixed/suffixed PRD names aren't matched, and that `notes-on-the-prd/` would match if it carries an `index.md`. If the team wants strictness, change to `re.compile(r"^prd($|[-])", re.IGNORECASE)` and adjust the test. Otherwise, leave as-is; the `index.md` gate is doing real work.

### Q5: Date-anchored Session regex robustness

Current pattern: `^##\s+([^\n]*\d{4}-\d{2}-\d{2}[^\n]*)$`

| Heading | Matches? | Notes |
|---|---|---|
| `## 2026-05-14` | ✅ yes | |
| `## 2026-05-14T10` | ✅ yes (the trailing `T10` is `[^\n]*`) | |
| `## 2026-05-14T10:23` | ✅ yes | |
| `## 2026-05-14T10:23 — Session: Update` | ✅ yes | |
| `## 2026-05-14T10:23 — Phiên: Cập nhật` | ✅ yes (covered by test) | |
| `## 2026/05/14` | ❌ no | Slash-delimited date not anchored. |
| `## 14-05-2026` | ❌ no | DD-MM-YYYY not anchored. |
| `## 2026-5-14` (single-digit month) | ❌ no | Strict `\d{2}` requires zero-padding. |

The question asks specifically: *"should it tolerate `YYYY/MM/DD`?"*

**Recommendation: no, keep the regex strict. The skill controls its own emission format.**

Reasoning:

- The decision-log template (`assets/decision-log-template.md`) is what writes the headings. If that template emits `YYYY-MM-DD`, the regex matches it; if it emitted `YYYY/MM/DD`, it wouldn't, and the template would be wrong, not the regex. Looser regex hides template bugs.
- Per `skill-quality-principles.md` "When Procedure IS Value" (low-freedom, exact format): the date format IS the contract. `## 2026-05-14T10:23 — Session: Update` is a stable shape the rest of the workflow assumes. Allowing `2026/05/14` invites future hand-edits that won't round-trip through the parser cleanly (e.g. macOS Finder pasting timestamps differently from Linux).
- ISO 8601 is the universal stable form. `YYYY-MM-DD` is the right level of strictness.

**However:** the comment at line 156 should call out the contract explicitly. Current: `# Language-agnostic.` Suggested: `# Date-anchored on ISO 8601 YYYY-MM-DD. The decision-log template emits this format; do not loosen unless the template changes.`

**Severity: very low** (comment-only). The regex is correct.

### Q6: Headless `--scope-of-change=auto` semantics tightness

The contract (`references/headless-contract.md` line 16):

> *"`auto` (default) diffs `stage_2_actors` and `stage_2_flows` against the prior session's flush block — identical arrays → polish; any difference → semantic."*

And SKILL.md line 206-208:

> *"Auto-detect default: compare current `stage_2_actors` and `stage_2_flows` against the prior session's flush block in `.decision-log.md`. If both arrays are identical → polish… If either differs → semantic."*

The procedure is **mostly** deterministic, but as called out in Q2, there are two unspecified dimensions:

1. **Set vs ordered comparison.** Is `["A", "B"]` vs `["B", "A"]` polish or semantic? Currently ambiguous.
2. **Element-level equality.** Are `"Customer"` and `"customer"` the same? Are `"Order Service"` and `"Order Service "` (trailing space) the same? Currently ambiguous.

For full determinism across runs, the contract should pin these. Suggested addition to headless-contract.md line 16:

> *"…Comparison is unordered set-membership on stripped lowercase strings; reordering or whitespace differences do not count as semantic."*

Or — if the team genuinely wants reordering to count as semantic (e.g. actor ordering carries meaning) — say so explicitly. Either is fine; *unspecified* is the only wrong answer.

**Severity: medium** — this is the determinism scanner's bread-and-butter finding. The same input could classify as polish in one run and semantic in another depending on how the LLM happens to compare the arrays. Headless callers expect deterministic auto-decisions.

If/when this becomes a script (Q2), the comparison rule is encoded in code and the ambiguity vanishes. Until then, document.

---

## Script Findings

### S1 — `auto` scope-of-change diff comparison rule unspecified

- **Severity:** medium (determinism across runs)
- **Location:** `SKILL.md:206-208` and `references/headless-contract.md:16`
- **Issue:** The diff procedure says "identical / differs" but doesn't define equality (set vs list, case, whitespace, normalization). Two runs against the same Update payload could produce different `polish`/`semantic` classifications.
- **Fix:** Either (a) add one sentence to both files pinning the comparison rule (set-membership, stripped, case-insensitive — pick the rule and write it down), or (b) lift the diff into `scripts/scope-of-change.py` so the rule is code rather than prose. Option (a) is cheaper and sufficient; option (b) is overkill for one decision per Update invocation.
- **Token impact:** none directly; the symptom is non-determinism, not LLM tax.

### S2 — `fresh_reason` enum surface not documented as a closed set

- **Severity:** low (audit-trail completeness)
- **Location:** `references/headless-contract.md` (missing table)
- **Issue:** `fresh_reason` is a machine-consumed closed-set field but isn't tabulated like `reason`. The value `stale_artifact` (emitted at `discover-planning-artifacts.py:194`) doesn't appear in any documentation. Automators relying on the closed-set guarantee can't enumerate without reading the script.
- **Fix:** Add a `## fresh_reason values` section to `references/headless-contract.md` mirroring the existing blocker-`reason` table. Cite from SKILL.md line 99-101.
- **Token impact:** none; pure documentation.

### S3 — `\bprd\b` boundary doesn't exclude underscore-adjacent atoms

- **Severity:** very low (no current failure mode)
- **Location:** `discover-planning-artifacts.py:241`
- **Issue:** Python's `\b` is a `\w`/`\W` boundary. Underscore is `\w`. So `\bprd\b` does not match `prd_legacy/`. HBC convention is kebab-case so this is currently not exercised, but a future snake_case directory would silently not match.
- **Fix:** Add a comment noting the underscore exclusion, OR change to `(?<![\w])(?<!_)prd(?![\w])(?!_)` if snake_case PRD dirs should match. Recommend just the comment — the `index.md` gate is doing the real filtering anyway.
- **Token impact:** none.

### S4 — Date-anchored Session regex contract not commented

- **Severity:** very low (documentation polish)
- **Location:** `discover-planning-artifacts.py:154-156`
- **Issue:** The regex anchors on ISO 8601 `YYYY-MM-DD` but the comment doesn't say "ISO 8601" or "must zero-pad" or "do not loosen without changing the template." A future maintainer might "fix" the regex to also match `2026/05/14` or `2026-5-14`, weakening the contract.
- **Fix:** Replace `# Last H2 heading containing a YYYY-MM-DD date — language-agnostic.` with `# ISO 8601 (YYYY-MM-DD) is the contract written by assets/decision-log-template.md. Date-anchored, language-agnostic. Do not loosen the date pattern without also updating the template.`
- **Token impact:** none.

---

## Distribution Findings

None.

The skill correctly:
- Runs the discover script once with both `--template-path` and `--workspace` flags to merge inventory + resume-state into a single JSON (no double-walk).
- Reads validator outputs from `.scan/*.json` rather than passing raw file contents through the prompt.
- Uses subagents only for the Parallel-lens menu (advanced / party), and the parent doesn't read what the subagent will read.
- Stage 2's compaction-flush correctly writes `stage_2_actors` and `stage_2_flows` to frontmatter BEFORE moving on, so a mid-flow compaction doesn't lose state — and the next-run resume comes from disk, not from re-eliciting.
- The `## On Activation` resolver step keeps `{workflow.*}` in memory rather than re-resolving in `## On Complete` (line 37). No redundant script invocations.

`execution-deps-prepass.json` shows zero stages, zero hard/soft dependencies, zero cycles, zero parallel groups — the dependency graph is empty because Stage 4's two validators are the only parallel candidates in the workflow, and they're not actually independent (both write to `.scan/` and feed the same consolidation step). Running them sequentially is fine; the dependency analysis correctly didn't flag a missed parallelization.

---

## Strengths Worth Preserving

1. **Single discover script with merged inventory + resume_state** — the `--workspace` flag pattern avoids a second walk of the workspace. Pre-pass philosophy executed cleanly.
2. **Closed-set blocker `reason` values + closed-set `fresh_reason` values** — automator-facing surface is fully enumerable.
3. **`auto_fixable` flag carried per-issue in `validate-mermaid.py` output** — separates "fix the way the validator suggests" from "this needs a human." Headless can apply the safe class and block on the rest.
4. **EXCLUDE_DIRS in `check-fr-coverage.py`** — `archive/`, `notes/`, `scratch/`, `drafts/` pruned from FR-id walks prevents retired PRDs from polluting `uncovered`. Sensible default, no flag needed.
5. **importlib-based test runner** — the hyphen-in-filename constraint (test files mirror script names per script-standards) is preserved without giving up `unittest discover` compatibility. Clean workaround.
6. **Tests invoke scripts as subprocesses, not by importing internals** — exercises the actual CLI contract. New regressions caught at the contract level, not at a function-internal seam.

---

## Aggregate Token Savings

Round 6 itself didn't add new scripts, so there's no new aggregate saving relative to round 5. The existing scripts (carried over) handle:

- **discover-planning-artifacts.py** — Stage 1 PRD/UX/use-case discovery + resume state. Saves an estimated 1500-3000 tokens per activation (LLM otherwise globs, classifies sharded PRDs by reading `index.md`, parses workspace frontmatter).
- **validate-mermaid.py** — Stage 4 syntactic validation across all Mermaid blocks. Saves an estimated 1000-2000 tokens per Mermaid block (LLM otherwise walks every declaration/arrow/note and tracks the participant universe).
- **check-fr-coverage.py** — Stage 4 FR-id set-diff. Saves an estimated 500-1500 tokens per PRD shard.

**Total per typical invocation: ~4000-8000 tokens saved versus a no-scripts variant.** All of which would also have been less reliable, since FR-id extraction at scale is the kind of mechanical work that the LLM gets right 95% of the time and the script gets right 100% of the time — and that 5% is silently-wrong-with-confidence, the worst failure mode.

---

## Verdict

**Excellent.**

The round-6 polish hit three real seams (audit-trail discrimination, language-coupled regex, sloppy substring match) with focused fixes and matching tests. The four findings above are all severity low-or-below except S1 (medium — the auto-diff comparison rule is unspecified), and S1 is a documentation/contract fix, not a script defect. Nothing about the script layer is below Excellent; the only opportunities left are nips to make the contract surface explicit where it's currently implicit.

Recommend:
- **Land S1** (define the diff comparison rule, one sentence in two files) before the next round.
- **Optionally land S2 / S3 / S4** as a single doc-polish commit; they don't gate anything.
- **Do not** lift Stage-3 scope-of-change into a script — the diff inputs are already in conversation context and the operation is one-shot per Update invocation. Document the comparison rule instead.
