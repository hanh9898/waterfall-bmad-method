# Determinism & Distribution Analysis — hbc-traceability

**Scanner:** determinism-analysis
**Skill:** hbc-traceability
**Date:** 2026-05-26
**SKILL.md:** 161 lines, ~1792 tokens

## Existing Scripts Inventory

| Script | Purpose | Deterministic? |
|--------|---------|---------------|
| `scripts/extract-trace-ids.py` | Regex-based ID extraction from artifacts (REQ-xxx, TC-xxx, entity names) via glob + pattern | Yes |
| `scripts/trace-report.py` | Parse matrix markdown table, compute per-column fill counts, gap list, coverage stats | Yes |

Both scripts are well-scoped: pure plumbing (fetch, parse, count). No intelligence leak — neither script interprets meaning. This is strong intelligence placement.

## Assessment

This skill has unusually good intelligence placement for its category. The two hardest-to-get-right script opportunities — ID extraction and coverage reporting — are already implemented as deterministic scripts with structured JSON output. The LLM is correctly reserved for the one operation that genuinely requires judgment: semantic mapping of requirements to design entities and code references (Phase 2 and Phase 3 Update). The remaining findings are minor and concentrated on two areas: a matrix-write validation script that would catch structural errors cheaply, and a phase-detection operation that the LLM currently performs by reading the full matrix when a script could return a compact summary.

## Script Findings

### S1 — Phase detection reads entire matrix into LLM context

- **Severity:** medium
- **LLM tax:** high (500+ tokens per invocation — full matrix read)
- **Location:** SKILL.md:96-102 (Update capability, steps 1-2)
- **Current behavior:** The LLM reads the full matrix from `{workflow.matrix_path}`, then inspects which columns are empty to determine Phase 2/3/4 context. This is a counting/emptiness-check operation — identical inputs always produce identical output.
- **Script alternative:** Extend `trace-report.py` (or add a `--detect-phase` flag) to return the empty-column analysis as JSON. Example output: `{"next_phase": 2, "empty_columns": ["design_ref", "test_ref"], "total_rows": 23}`. The LLM receives ~50 tokens instead of reading a potentially large matrix table.
- **Estimated saving:** 400-2000 tokens per Update invocation (scales with matrix size).
- **Pre-pass potential:** High — this is exactly the "pre-pass that hands the LLM compact JSON instead of raw files" pattern. The LLM still needs the matrix content later for the semantic mapping step, but the phase-detection decision can be made from compact stats alone.
- **Language:** Python (extend existing `trace-report.py`)

### S2 — Matrix structural validation after write

- **Severity:** low
- **LLM tax:** low (<100 tokens — validation is implicit, not explicitly coded)
- **Location:** SKILL.md:88 (Initialize step 2), SKILL.md:118 (Update step 6)
- **Current behavior:** After writing/updating the matrix, there is no explicit validation that the markdown table structure is well-formed (correct column count, no missing pipes, req_ids not duplicated). If the LLM makes a formatting error, the next `trace-report.py` invocation will silently parse wrong data.
- **Script alternative:** A `--validate` flag on `trace-report.py` that checks: (1) every row has exactly 7 columns, (2) no duplicate `req_id`, (3) no empty `req_id` cell. Return pass/fail JSON. Run as a post-write check.
- **Estimated saving:** Minimal token savings, but prevents cascading errors. Value is correctness, not token economy.
- **Language:** Python (extend existing `trace-report.py`)

### S3 — Audit gap classification is partially deterministic

- **Severity:** low
- **LLM tax:** moderate (100-500 tokens)
- **Location:** SKILL.md:146-155 (Audit capability, steps 2-3)
- **Current behavior:** The LLM classifies gap severity by comparing empty columns against the current phase. The rules are fully deterministic: empty `test_ref` after Phase 4 = CRITICAL, empty `code_ref` after Phase 3 = HIGH, earlier phase = INFO. No judgment needed.
- **Script alternative:** Extend `trace-report.py` with a `--audit --current-phase N` flag that classifies each gap by severity and returns the sorted list. The LLM's role reduces to presenting the results and suggesting remediation skills (which does require judgment about context).
- **Estimated saving:** 100-300 tokens per Audit invocation.
- **Language:** Python (extend existing `trace-report.py`)

## Distribution Findings

### D1 — Phase 2 Update runs three sequential script calls

- **Severity:** low
- **Location:** SKILL.md:105-107 (Update Phase 2 steps)
- **Current pattern:** Three sequential `extract-trace-ids.py` invocations:
  1. Extract entity names from D-19
  2. Extract TC IDs from D-27
  3. (Implicit) Read D-02 for context
  
  These are independent reads — D-19 extraction doesn't depend on D-27 extraction.
- **Efficient alternative:** Batch both `extract-trace-ids.py` calls in a single message (parallel tool calls). The LLM already has the right tool calls specified; this is a prompt-level hint to batch them. Alternatively, extend the script to accept multiple `--source`/`--pattern` pairs in one invocation.
- **Estimated impact:** Wall-clock time reduction only (both calls are fast). Token cost is unchanged since script output is already compact JSON.

### D2 — No implicit-read trap detected

- **Severity:** N/A (positive finding)
- **Details:** The skill correctly avoids the implicit-read trap. The Update capability instructs the LLM to read the matrix (necessary for semantic mapping), but does not pre-read artifacts that the scripts will parse. Scripts do the file scanning; the LLM receives JSON summaries.

### D3 — Audit calls Report internally — correct chaining, no wasted work

- **Severity:** N/A (positive finding)
- **Location:** SKILL.md:143
- **Details:** Audit reuses the Report script output rather than re-parsing the matrix independently. Good dependency awareness.

## Aggregate Token Savings Estimate

| Finding | Per-Invocation Savings | Frequency | Net Impact |
|---------|----------------------|-----------|------------|
| S1 — Phase detection pre-pass | 400-2000 tokens | Every Update | **High** |
| S2 — Post-write validation | ~0 tokens (correctness gain) | Every Init/Update | Low |
| S3 — Audit gap classification | 100-300 tokens | Every Audit | Low |
| D1 — Parallel extraction | ~0 tokens (wall-clock only) | Phase 2 Update | Low |

**Total estimated savings:** 500-2300 tokens per invocation cycle, concentrated in the Update path. The Phase detection pre-pass (S1) is the highest-value opportunity.

## Strengths

1. **Exemplary intelligence placement.** The skill correctly identifies that ID extraction and coverage counting are deterministic, delegates them to scripts, and reserves LLM judgment only for semantic requirement-to-artifact mapping. This is the pattern the principles document calls for.

2. **Scripts return structured JSON.** Both scripts output well-formed JSON with status fields, counts, and lists. The LLM consumes compact structured data, not raw file content. This is the "pre-pass" pattern already applied.

3. **Capability routing avoids unnecessary work.** Init, Update, Report, and Audit are distinct paths — the skill doesn't load resources for all four when only one is active.

4. **Headless mode with defined JSON contract.** Enables cross-skill invocation (e.g., phase gate calling traceability) without interactive overhead.

5. **No reference file sprawl.** Everything lives in SKILL.md (161 lines, well within the multi-branch ceiling of ~250). No unnecessary carve-outs.

6. **customize.toml is clean.** Only meaningful scalars (`matrix_path`, `source_code_path`, `on_complete`) plus the standard arrays. No boolean toggles, no permutation forest.
