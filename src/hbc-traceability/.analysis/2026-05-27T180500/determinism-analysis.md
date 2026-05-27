# Determinism & Distribution Analysis — hbc-traceability

**Scanner:** quality-scan-determinism  
**Date:** 2026-05-27  
**Skill:** `src/hbc-traceability`  
**Pre-pass:** execution-deps-prepass.json — 0 issues, no stage dependency graph (single SKILL.md workflow, no carved-out stage files)

---

## Existing Scripts Inventory

| Script | Purpose | Mode |
|--------|---------|------|
| `scripts/extract-trace-ids.py` | Glob-scan source files, regex-match IDs (REQ-xxx, TC-xxx), return deduplicated JSON array | Deterministic — Python stdlib only |
| `scripts/trace-report.py` | Parse matrix markdown table; generate coverage stats, phase detection, or structural validation | Deterministic — Python stdlib only |

Both scripts are well-scoped: they handle plumbing (parse, count, validate, detect) and return compact JSON. Tests exist for both under `scripts/tests/`. No duplicates to avoid.

---

## Assessment

Intelligence placement is largely correct. The two existing scripts cover the fully deterministic operations — ID extraction, coverage counting, phase detection, and structural validation — and SKILL.md routes to them with exact invocations. The LLM is reserved for the genuinely judgment-requiring operations: mapping design entities to requirements, linking code references to REQ IDs, and gap remediation advice. Two medium-weight findings exist: Phase 4's gate-status population reads raw gate report files without a script pre-pass, and the Audit capability's gap-severity classification could be delegated to the already-present `trace-report.py` rather than being re-derived by the LLM from prompt-side logic.

---

## Script Findings

### SF-01 — Phase 4 gate-status population reads raw gate reports without a pre-pass
**Severity:** Medium (LLM tax: moderate, ~150–300 tokens per invocation)  
**Location:** `SKILL.md` line 66 — _"Read gate reports from `{project-root}/_hbc_output/gates/phase-*-gate.md`. Set `gate_status` per REQ."_

**Current behaviour:** The LLM reads one or more gate report markdown files wholesale to extract per-REQ gate status values. Gate reports are structured documents; extracting a pass/fail or status token per REQ ID is fully deterministic given a consistent report format.

**What a script would do:** Extend `trace-report.py` (or add a sibling `extract-gate-status.py`) with a `--gate-reports` flag. The script globs `phase-*-gate.md`, parses each for REQ-ID + status pairs using regex, and returns a JSON map `{req_id → gate_status}`. The LLM then only writes the populated column — no reading.

**Estimated token savings:** ~150–300 tokens per Phase 4 update (eliminated file reads).  
**Language:** Python (stdlib, consistent with existing scripts).  
**Pre-pass potential:** Yes — same JSON-feed pattern used by `extract-trace-ids.py`. Would be a natural `--mode gate-status` flag on the existing report script.

---

### SF-02 — Audit severity classification duplicates logic already expressible in the script
**Severity:** Low (LLM tax: light, ~50–80 tokens)  
**Location:** `SKILL.md` lines 101–104 — severity rules for CRITICAL / HIGH / INFO gap classification.

**Current behaviour:** The LLM applies the phase-context severity rules (CRITICAL = empty test_ref after Phase 4, HIGH = empty code_ref after Phase 3, INFO = earlier phase) inline, reading them from the prompt. `trace-report.py` already detects `next_phase` and returns `gap_details` with `missing_columns`. The severity mapping is a pure function of `(missing_column, next_phase)`.

**What a script would do:** Add a `--classify-gaps` flag to `trace-report.py`. Given the detected phase, return each gap entry with a `severity` field computed from the deterministic rule table. The LLM receives pre-classified gaps and focuses only on the remediation language per gap.

**Estimated token savings:** ~50–80 tokens per Audit invocation.  
**Language:** Python (3-line addition to `trace-report.py`).  
**Pre-pass potential:** Low — gap_details already returned; this is an incremental field addition.

---

## Distribution Findings

### DF-01 — Phase 2 Update reads three documents before delegating judgment
**Severity:** Medium  
**Location:** `SKILL.md` line 62 — _"Read D-02, D-19, D-27. Use LLM judgment to extract design entities from D-19 and map each REQ to entities and test cases."_

**Current pattern:** The parent explicitly reads three documents (D-02 requirements, D-19 ER/design, D-27 test spec) in full before performing the mapping judgment. `extract-trace-ids.py` already extracts TC IDs from D-27, so only D-19 and D-02 content genuinely require LLM judgment. D-02 REQ IDs were already extracted by `init` — they are in the matrix, not needing a re-read of D-02.

**Efficient alternative:** Remove the D-02 re-read instruction — REQ IDs are already in the matrix, which the LLM has from Step 1's phase detection. Read only D-19 for entity extraction. D-27 TC IDs are already in the JSON from the `extract-trace-ids.py` call above. Net reduction: one file read eliminated entirely; D-27 is already script-handled.

**Estimated impact:** ~200–500 tokens saved per Phase 2 Update (D-02 re-read eliminated; D-27 already covered by script output).

---

### DF-02 — No explicit "don't read" guard before the mapping confirmation step
**Severity:** Low  
**Location:** `SKILL.md` line 62 — _"present proposed mappings as a table and confirm with user"_ — no implicit-read trap risk here because this is the parent doing the judgment, not a sub-delegation. However, the Update section lacks a note that gate report files (referenced in Phase 4) should not be pre-read during Phase 2 or 3 steps.

**Current pattern:** Not a true implicit-read trap (no subagent delegation in this skill). Low-risk because all four phases are sequential and capability-scoped — a Phase 2 Update does not load Phase 4 files. No fix required; noting for completeness.

**Estimated impact:** Negligible — no subagent delegation path in this skill.

---

### DF-03 — Audit runs report then reclassifies gaps in a second LLM pass
**Severity:** Low  
**Location:** `SKILL.md` lines 96–104 — Audit step 1 runs `trace-report.py` (correct), then step 2 applies per-gap classification and remediation in the same LLM turn using the JSON output.

**Current pattern:** This is actually reasonable — the script feeds compact JSON, the LLM adds judgment (remediation language, severity). The two passes (script → LLM classification) are already well-structured. Only partially improvable via SF-02 above.

**Estimated impact:** Low — pattern is already efficient; SF-02 addresses the deterministic slice.

---

## Aggregate Token Savings Estimate

| Finding | Per-invocation savings | Frequency |
|---------|----------------------|-----------|
| SF-01 (gate-status pre-pass) | ~200 tokens | Each Phase 4 Update |
| SF-02 (gap severity in script) | ~65 tokens | Each Audit |
| DF-01 (eliminate D-02 re-read) | ~300 tokens | Each Phase 2 Update |

**Total addressable:** ~565 tokens across a typical lifecycle run (one of each). For projects with many REQs or multiple Audit/Update cycles, savings compound proportionally with matrix size.

---

## Strengths

- **Script-first design is consistent.** Both the Initialize and Update/Report capabilities open with deterministic script calls that hand the LLM compact JSON. The pattern is applied correctly: `extract-trace-ids.py` feeds the ID list to Initialize; `trace-report.py --detect-phase` feeds phase context to Update. No cases of the LLM counting rows or scanning files for IDs that a script already covers.

- **State marker pattern is well-placed.** The interrupted-update detection (`.trace-state.json` read before starting, cleared on completion) is an exact-operation invocation appropriately specified in SKILL.md. This is the kind of fragile, consequence-bearing operation that earns its procedural detail.

- **`customize.toml` scalar discipline is correct.** `matrix_path`, `matrix_template`, and `source_code_path` are declared scalars; SKILL.md references them as `{workflow.matrix_path}` and `{workflow.matrix_template}` consistently. No hardcoded paths alongside declared scalars.

- **Headless mode is cleanly specified.** The JSON return contract (`status`, `capability`, `matrix_path`, summary stats) is explicit. Decision logging via `.trace-decisions.md` is scoped to non-obvious LLM mappings only — not over-logged.

- **`trace-report.py` is genuinely broad.** The `--validate`, `--detect-phase`, and full-report modes cover the natural inspection surface without requiring additional scripts. The existing test suite in `scripts/tests/` confirms determinism is taken seriously.
