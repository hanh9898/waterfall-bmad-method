# Determinism & Distribution Analysis — hbc-create-glossary

**Scan date:** 2026-05-27  
**Skill path:** `src/hbc-create-glossary`  
**Prepass status:** pass (0 issues detected by automated prepass)

---

## Existing Scripts Inventory

| Script | Purpose | Returns |
|--------|---------|---------|
| `scripts/scan-glossary-sources.py` | Pre-pass: discovers project state, existing D-03, source documents, and extracts term candidates via regex | JSON: `state`, `existing_d03`, `source_docs`, `term_candidates`, `candidate_count` |
| `scripts/validate-glossary.py` | Post-generation: checks duplicates, empty definitions, missing sections, zero-term count | JSON: `valid`, `issues[]` with `auto_fixable` flag per issue |

Tests: `scripts/tests/test-validate-glossary.py` — 8 cases covering all check types, cross-table duplicates, file-output mode, and missing-document error path.

---

## Assessment

Intelligence placement is well-executed for a document-generation skill of this type. Deterministic checks (duplicate detection, empty definitions, section presence, term counting, state routing) are delegated to scripts; the LLM is reserved for judgment work (definition quality, project-specificity, semantic coherence, category decisions). The two scripts together form a tight pre-pass / post-pass bracket that keeps the LLM context lean. The only meaningful finding is a partial intelligence leak in `scan-glossary-sources.py` where regex pattern matching is used to decide what text *means* (i.e., whether a quoted or capitalized phrase constitutes a domain term) — a judgment call embedded in a script. No distribution or parallelism problems were found; the workflow has no multi-stage dependency graph to over-constrain.

---

## Script Findings

### SF-1 — Intelligence Leak: Term-candidate classification in scan script

**Severity:** MEDIUM (moderate LLM tax avoided, but wrong layer for the judgment)  
**File:** `scripts/scan-glossary-sources.py`, lines 18–70  
**LLM tax band:** Low — the candidates list is short; the cost is a correctness issue, not a token issue.

**Current behavior:** `extract_candidates()` uses three regex patterns to decide which quoted strings and capitalized sequences constitute domain terms worth surfacing. It also makes the call on which uppercase tokens are *not* generic abbreviations (via a static `COMMON_ABBREVIATIONS` deny-list). This is semantic classification — whether a string is a relevant project term — which cannot be answered deterministically from surface form alone. A pattern like `"([A-Z][A-Za-z]{2,}...)"` will surface proper nouns, product names, and random capitalized words equally. The deny-list approach for abbreviations is a heuristic that will both over- and under-fire on any real project.

**Impact:** Low-quality candidate lists reaching the LLM in Stage 2, requiring the LLM to silently filter noise the script should not have emitted. More importantly, it buries a judgment call (what counts as a term?) in a deterministic layer where the principles file says it doesn't belong ("Script using regex to decide what content MEANS = intelligence leak into the script").

**Fix:** Constrain the script to structural extraction only — return every quoted string and every all-caps token. Let the LLM decide in Stage 2 which candidates are real domain terms. Alternatively, annotate the JSON output with a `heuristic_confidence` field (`quoted` vs. `capitalized_sequence` vs. `abbreviation`) so the LLM can weight candidates itself. The script should count and collect; the prompt should filter.

**Pre-pass potential:** Not applicable — the script already serves as a pre-pass. The issue is about what it decides vs. what it should hand off.

---

### SF-2 — Missing: scan-glossary-sources.py has no test coverage

**Severity:** LOW  
**File:** `scripts/scan-glossary-sources.py`  
**LLM tax band:** N/A

**Current behavior:** `scripts/tests/test-validate-glossary.py` covers `validate-glossary.py` comprehensively (8 tests). No corresponding test file exists for `scan-glossary-sources.py`. The scan script performs non-trivial logic: frontmatter parsing, state routing (fresh/resume/update), multi-directory glob ordering, and candidate extraction.

**Impact:** Regressions in state routing (e.g., `lastStep` comparison, search directory ordering) or frontmatter parsing go undetected. The `update` vs. `resume` branch is load-bearing for Stage 1 routing.

**Fix:** Add `scripts/tests/test-scan-glossary-sources.py` covering at minimum: fresh project (no D-03), resume state (`lastStep != complete`), update state (`lastStep == complete`), and candidate extraction from a fixture document. Pattern follows the existing subprocess-based test style in `test-validate-glossary.py`.

---

## Distribution Findings

No distribution issues found. The workflow does not define named stages in the dependency graph (prepass confirmed `stages: []`), all script invocations are sequential by necessity (scan → generate → validate), and no parent-reads-then-delegates pattern was identified. Stage 2 correctly instructs the LLM to use pre-populated candidates from the scan JSON rather than re-reading source files itself. The headless contract is compact and well-specified with `status: complete | blocked` and a `reason` field on blocked returns.

One minor observation not rising to a finding: Stage 3's parallel-lens menu (`[A] / [P] / [C]`) is described inline as a menu choice but no distribution concern exists since it's an interactive branch, not a subagent fan-out.

---

## Aggregate Token Savings

Current architecture is already efficient. The two scripts together replace what would otherwise be:
- ~300–600 tokens per invocation for the source scan (reading multiple files and routing state)
- ~200–400 tokens per invocation for post-generation validation

**SF-1** addresses a correctness issue rather than a token savings opportunity; the candidates list is compact regardless. No additional script opportunities identified that would yield meaningful savings.

---

## Strengths

- **Pre-pass bracket is complete.** Both a pre-generation scan and a post-generation validator exist, which is the ideal bracket for a document-generation skill. The LLM sees compact JSON summaries at both ends rather than raw file content.
- **Validation `auto_fixable` flag is well-designed.** Returning per-issue fixability gives the workflow a clean branch: interactive fix loop vs. headless `blocked` return. The principles are correctly separated — deterministic fixes (duplicates) are flagged `auto_fixable: True`, judgment fixes (empty definitions) are `False`.
- **Script does not leak state into the prompt.** `scan-glossary-sources.py` returns a `state` routing signal (`fresh/resume/update`) rather than making the LLM infer it from raw file presence. This is exactly the right pattern.
- **`customize.toml` variables are properly consumed in SKILL.md.** `{workflow.template_path}` and `{workflow.validation_script}` are referenced correctly; no hardcoded paths found next to declared scalars.
- **Headless contract is minimal and correct.** Returns only the paths the caller needs (`output_path`, `decision_log`), with a `validation` sub-object summarizing script output. `blocked` includes a `reason` string.
- **Test coverage for the validator is thorough.** Cross-table duplicate detection, per-column empty-definition checks, missing sections, and the file-output mode are all tested.
