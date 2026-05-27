# Determinism & Intelligence Placement Analysis
## hbc-phase-gate

**Timestamp:** 2026-05-26T16:02:00  
**Analyst:** Determinism Scanner  
**Classification:** Engine pattern, simple workflow

---

## Existing Scripts Inventory

No scripts found. Checklist evaluation is performed entirely in-prompt.

---

## Assessment

The hbc-phase-gate skill implements a validation engine for phase-gate checks with clear separation of concerns: FILE and CONTENT checks are deterministic operations suitable for scripting, while QUALITY checks require LLM judgment. The current design keeps all evaluation inline in SKILL.md, which is acceptable for MVP scope but creates opportunities for misclassification and brittleness in FILE/CONTENT matching. The decision log correctly identified script-based validation as a future enhancement; this analysis identifies the specific scope and token cost.

---

## Script Findings

### [HIGH] FILE and CONTENT checks can be deterministic

**File:Line:** SKILL.md, lines 60–63  
**Severity:** HIGH (LLM tax ~200–400 tokens per invocation)  
**Current pattern:**
- LLM reads checklist markdown
- LLM uses glob patterns (artifact_pattern) to scan project root
- LLM applies regex to matched files (criteria field)
- LLM determines PASS/FAIL

**What a script would do:**
- Parse checklist from markdown into structured form
- Execute glob and regex matching against project root (bash + Python)
- Return JSON with matched paths, match counts, and sample excerpts
- LLM receives pre-processed results and focuses on interpretation

**Script scope:**
```python
# determinism-gate-eval.py
# Input: checklist JSON, project root, evaluation type (FILE/CONTENT/METRIC)
# Output: structured evaluation results with matched artifacts, counts, samples
# Deterministic: glob, regex, file reads, string matching
```

**Token savings estimate:** 
- Per checklist invocation: ~250–350 tokens saved (LLM no longer does glob/regex work)
- Typical gate has ~12 items; ~4–5 FILE/CONTENT items per phase
- Per gate execution: ~1,000–1,750 tokens saved
- Annual (50 gates/phase × 4 phases × 12 projects): ~2.4M tokens saved

**Pre-pass potential:** YES (highest value)
- Script returns compact JSON: `{item_id, type, artifact_matches[], line_samples[], status}`
- LLM reads JSON summary, not raw files or glob results
- Eliminates multi-kilobyte artifact content from prompt for FILE checks

**Language:** Python  
**Recommendation:** Implement before production. FILE/CONTENT evaluation is objective and repeatable; moving it to script improves reliability and cost.

---

### [MEDIUM] METRIC type evaluation

**File:Line:** SKILL.md, lines 62  
**Severity:** MEDIUM (LLM tax ~100–200 tokens per item)  
**Current pattern:**
- LLM reads artifact and extracts numeric value per criteria instruction
- LLM compares extracted value against threshold

**What a script would do:**
- Receive artifact path and extraction instruction
- Use regex or structured parsing to extract numeric value
- Return value + comparison result

**Script scope:**
- Designed into the same script as FILE/CONTENT
- Script supports type-specific paths: `file:/path`, `json:path.to.field`, `regex:pattern`

**Token savings estimate:** ~100–150 per METRIC item  
**Recommendation:** Include in FILE/CONTENT script; lower priority than FILE/CONTENT since METRIC items are fewer and extraction logic varies by type.

---

## Distribution Findings

### [LOW] Implicit activation steps not batched

**File:Line:** SKILL.md, lines 26–50  
**Severity:** LOW  
**Current pattern:**
- Five sequential activation steps (resolve customization, prepend steps, load persistent facts, load config, append steps, determine phase)
- Each step is described as a numbered instruction

**What a better pattern would do:**
- Group independent steps (resolve + load config) into a single parallel block
- Prepend and append steps are user-defined; maintain sequence
- Phase determination can run after config load

**Impact:** Negligible token cost; improves readability  
**Recommendation:** Defer (no measurable efficiency gain at present).

---

### [MEDIUM] Parent implicit-read risk in evaluation stage

**File:Line:** SKILL.md, lines 52–73  
**Severity:** MEDIUM (context-bloat risk on large projects)  
**Current pattern:**
- Step 1: Load checklist from file (LLM reads markdown table)
- Step 2: Check previous report (LLM reads prior gate report if exists)
- Step 3: "Evaluate each checklist item" — LLM then reads referenced artifacts inline for QUALITY checks

**Risk:**
- For FILE/CONTENT items, LLM reads artifact content even when script could glob/regex without reading
- For QUALITY items, reading is necessary, but the instruction doesn't distinguish — LLM may read all artifacts upfront
- On large projects (many files, large artifacts), this balloons context

**Efficient alternative:**
- Script produces compact artifact list + match counts
- LLM reads checklist and prior report (unavoidable)
- LLM reads ONLY the artifacts relevant to QUALITY checks (explicitly: "read artifact_pattern files for QUALITY items only")
- File/CONTENT results come from script JSON

**Token savings estimate:** ~300–500 tokens per gate on projects with >10 matched artifacts  
**Recommendation:** Implement alongside FILE/CONTENT script. Add explicit instruction: "For FILE/CONTENT items, use script results; for QUALITY items, read only the specified artifacts."

---

### [LOW] No parallelization of QUALITY checks

**File:Line:** SKILL.md, line 63  
**Severity:** LOW  
**Current pattern:**
- QUALITY checks are sequential ("read referenced artifacts, apply judgment")

**What a subagent pattern could do:**
- Fan out 2–3 QUALITY checks to parallel subagents if gate has >5 QUALITY items
- Parent awaits all results, assembles report

**Current constraint:**
- Skill decision log states "No headless mode" and "Quality checks involve judgment that benefits from user context"
- This is defensible for MVP; parallelization adds complexity

**Recommendation:** Defer for now. Consider if gates grow to >8 QUALITY items.

---

## Aggregate Token Savings Estimate

| Opportunity | Per-Gate Saving | Annual (50 gates/phase × 4 phases × 12 projects) | Priority |
|---|---|---|---|
| FILE/CONTENT to script | 1,000–1,750 | 2.4–4.2M | HIGH |
| METRIC in script | 200–300 | 480M–720M | MEDIUM |
| Implicit-read reduction | 300–500 | 720M–1.2M | MEDIUM |
| **Total** | **1,500–2,550** | **3.6–6.1M tokens/year** | — |

---

## Strengths

1. **Clear evaluation types** — Four-tier system (FILE, CONTENT, METRIC, QUALITY) maps perfectly to "deterministic where possible, LLM judgment where needed" principle from decision log. Good intelligence placement in design.

2. **Checklist-driven, not hardcoded** — Checklists are data (markdown tables), not buried in prompts. Easy for phase skills to override via customize.toml. Follows BMad structural pattern.

3. **Artifact pattern parameterization** — Glob patterns are specified per item, enabling flexible matching without LLM ambiguity.

4. **No prescriptive procedural steps** — SKILL.md states outcomes ("Evaluate each checklist item by type") rather than micro-steps, leaving room for efficient implementation.

5. **Proper error handling** — File-not-found and missing config are addressed (fallbacks, defaults). No silent failures.

6. **Decision log transparency** — Rejected alternatives (script-based validation, HTML output) are documented with rationale, enabling future iterations without confusion.

---

## Recommendations (Priority Order)

1. **Implement FILE/CONTENT/METRIC script (HIGH)** — Creates 2.4–4.2M tokens/year savings, eliminates regex/glob work from prompts, improves determinism.

2. **Add pre-pass JSON to evaluation stage (HIGH)** — Script output feeds directly into SKILL.md as compact input; LLM never sees raw file contents for FILE/CONTENT items.

3. **Clarify implicit-read pattern in QUALITY section (MEDIUM)** — Add sentence: "For FILE/CONTENT items, use script results from step 2. Read artifacts only for QUALITY items."

4. **Consider parallelization of QUALITY checks in Phase 2+ (LOW)** — If gates grow to >8 QUALITY items, implement subagent pattern for parallel evaluation.

---

## Conclusion

The skill demonstrates good intelligence placement: deterministic operations are identified as future candidates for scripting, and QUALITY judgments remain in prompt. The decision-log rationale for deferring scripts is sound for MVP. Implementing the script opportunities identified here would reduce token cost by ~50% per invocation while improving reliability for deterministic checks. No runtime failures or correctness issues detected.
