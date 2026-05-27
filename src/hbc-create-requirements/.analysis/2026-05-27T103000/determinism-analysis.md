# Determinism & Distribution Analysis — hbc-create-requirements

**Scanner:** determinism-analysis
**Skill:** `src/hbc-create-requirements`
**Date:** 2026-05-27
**Pre-pass status:** execution-deps pass (0 issues), prompt-metrics info (1228 tokens SKILL.md), workflow-integrity pass (0 issues)

---

## Existing Scripts Inventory

| Script | Purpose | Coverage |
|--------|---------|----------|
| `scripts/validate-requirements.py` | REQ ID uniqueness/sequencing, vague term detection, required section presence, empty section check, NFR measurability check | 11 tests in `scripts/tests/test-validate-requirements.py` |

The validation script is well-scoped: it handles all the deterministic checks mentioned in Stage 4, returns structured JSON with `auto_fixable` flags, and is configurable via `--vague-terms` CLI and `customize.toml`. No duplicate proposals needed for anything it already covers.

---

## Assessment

Intelligence placement is strong. The skill correctly offloads all structural validation (REQ ID integrity, section presence, vague terms, NFR criteria) to `validate-requirements.py` and reserves LLM judgment for ambiguity detection, contradiction analysis, and testability assessment. The SKILL.md is compact (96 lines, ~1228 tokens) with no inline deterministic operations leaking into prompt space. The main opportunities are a missing pre-pass script for Stage 1 source inventory and a lightweight template-section counter that could feed Stage 3 generation as compact JSON instead of raw template parsing.

---

## Script Findings

### S-1: Source inventory pre-pass (Stage 1b)

- **Severity:** medium (LLM tax: moderate, ~200-400 tokens per invocation)
- **Location:** SKILL.md:37-38 (Stage 1, "Source inventory")
- **Current behavior:** The LLM reads the project tree to discover existing documents, `project-context.md`, interview notes, and prior D-02 artifacts. It must scan file paths, check existence, and determine file types — all deterministic.
- **Script alternative:** A Python script that scans `{project-root}` for known HBC document patterns (`D-01*.md`, `D-02*.md`, `project-context.md`, `_hbc_output/` contents), checks for partial D-02 frontmatter (`lastStep`), and returns a compact JSON manifest: `{ "existing_d02": { "path": "...", "lastStep": "...", "version": "..." }, "source_docs": [...], "project_context": "path|null" }`.
- **Estimated token savings:** 200-400 tokens/invocation (file scanning + existence checks + frontmatter parsing).
- **Language:** Python (PEP 723, stdlib only — `pathlib`, `re`, `json`).
- **Pre-pass potential:** High. The LLM receives a compact JSON manifest instead of needing to call multiple file-read tools to discover what exists. Resume detection (1a) also benefits — the script can report `lastStep` directly.

### S-2: Template section counter for generation guidance (Stage 3)

- **Severity:** low (LLM tax: light, ~50-100 tokens)
- **Location:** SKILL.md:57 (Stage 3, "Populate template")
- **Current behavior:** The LLM reads `{workflow.template_path}` to understand which sections to populate, their ordering, and their expected table formats. The template is 89 lines and mostly structural scaffolding.
- **Script alternative:** Extend `validate-requirements.py` (or a small companion) to emit a template manifest: section names, expected table schemas (column headers), and section count. The LLM receives `{"sections": [{"name": "プロジェクト概要", "subsections": [...], "has_table": true, "columns": [...]}], "total_sections": 6}` instead of the raw template.
- **Estimated token savings:** 50-100 tokens (template is only 89 lines, so savings are modest).
- **Language:** Python.
- **Pre-pass potential:** Low-medium. Marginal savings; the template is small enough that raw reading is not expensive. Worth considering only if the template grows.

### S-3: Revision history diff detection (Stage 3, Update mode)

- **Severity:** low (LLM tax: light, ~50-100 tokens)
- **Location:** SKILL.md:63-65 (Stage 3, "Revision history")
- **Current behavior:** In Update mode, the LLM determines whether changes are "same requirements, polish only" vs "new/changed requirements" to decide on version bump. This requires comparing current REQ IDs against baseline — a deterministic diff.
- **Script alternative:** A script that diffs two D-02 files, extracting REQ IDs from each and reporting: `{"added": ["REQ-004"], "removed": [], "modified_lines": 3, "scope": "content_change|polish_only"}`. The LLM then just reads the verdict.
- **Estimated token savings:** 50-100 tokens per update invocation.
- **Language:** Python.
- **Pre-pass potential:** Medium. Only fires in Update mode, but when it does, it replaces a multi-step comparison the LLM would otherwise perform by reading two full documents.

---

## Distribution Findings

### D-1: Stage 4 parallel-lens review could use explicit subagent return constraints

- **Severity:** low
- **Location:** SKILL.md:86-87 (Stage 4, "Parallel-lens menu")
- **Current pattern:** The parallel-lens menu offers `[A]` Advanced Elicitation / `[P]` Party Mode / `[C]` Continue with "validation-focused lenses (challenge vagueness, find gaps, reviewer clarity)." If these spawn subagents, the SKILL.md does not specify return format constraints.
- **Efficient alternative:** When parallel review lenses are invoked, each subagent prompt should include "Return ONLY a bulleted list of findings with REQ-xxx references. No preamble." to prevent verbose prose responses.
- **Impact:** Prevents context bloat from verbose subagent returns. Without explicit constraints, each lens could return 500+ tokens of preamble and explanation when 50-100 tokens of findings would suffice.

### D-2: Stage 1 combines resume detection + source inventory + intent gate sequentially

- **Severity:** low
- **Location:** SKILL.md:31-40 (Stage 1, substeps 1a-1c)
- **Current pattern:** Prerequisites runs three substeps sequentially: resume detection (check existing D-02), source inventory (scan project), intent gate (confirm user intent). Resume detection and source inventory are independent reads.
- **Efficient alternative:** If S-1 (source inventory pre-pass) were implemented, a single script invocation could handle both 1a (resume detection via frontmatter check) and 1b (source inventory) in one pass, feeding the LLM a single JSON manifest. The intent gate (1c) genuinely requires LLM judgment and stays in the prompt.
- **Impact:** Collapses two sequential tool-call rounds into one script invocation.

---

## Aggregate Token Savings Estimate

| Finding | Per-invocation savings | Frequency | Annualized estimate |
|---------|----------------------|-----------|-------------------|
| S-1: Source inventory pre-pass | 200-400 tokens | Every activation | High value |
| S-2: Template section counter | 50-100 tokens | Every generation | Low value |
| S-3: Revision diff detection | 50-100 tokens | Update mode only | Low value |
| D-1: Subagent return constraints | 200-500 tokens avoided | When lenses used | Medium value |

**Total estimated savings:** ~300-600 tokens per typical create invocation; up to ~800-1000 tokens when parallel lenses or update mode are used. The source inventory pre-pass (S-1) accounts for the majority.

---

## Strengths

1. **Validation script is exemplary.** `validate-requirements.py` handles all structural checks with proper JSON output, `auto_fixable` flags, configurable vague terms, and comprehensive test coverage (11 tests). This is exactly how intelligence placement should work — the LLM never touches REQ ID sequencing or section-presence checks.

2. **SKILL.md is compact and outcome-oriented.** At 96 lines / ~1228 tokens, it stays well within size guidance. Stages describe outcomes, not step-by-step procedures. The LLM has room to adapt its approach within each stage.

3. **Validation before generation.** The workflow correctly places the expensive generation step (Stage 3) after prerequisites and discovery, and the deterministic validation (Stage 4) catches structural issues before the user reviews. Fail-fast ordering is sound.

4. **customize.toml surface is well-scoped.** Three meaningful scalars (`template_path`, `output_path`, `vague_terms`) — no boolean toggles, no permutation forest. Vague terms as a comma-separated string is a practical override surface.

5. **Headless contract is clean.** `references/headless-contract.md` defines a minimal return schema with clear `status` values and blocked reasons. Decision log discipline is referenced in the build decision log.

6. **Script invocation is exact.** Stage 4 provides the precise command line `python3 scripts/validate-requirements.py {output_file} --project-root {project-root}` — fragile-operation invocation done right.
