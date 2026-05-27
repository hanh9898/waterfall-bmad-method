# Determinism & Distribution Analysis — hbc-create-requirements

**Scanner:** determinism-analysis
**Skill:** `src/hbc-create-requirements`
**Date:** 2026-05-27
**Session:** 2026-05-27T193000
**Pre-pass status:** execution-deps pass (0 issues), prompt-metrics info (1529 tokens SKILL.md, 108 lines), workflow-integrity pass (0 issues)
**Prior analysis:** 2026-05-27T103000

---

## Changes Since Prior Analysis

| Finding | Prior status | Current status |
|---------|-------------|----------------|
| S-1: Source inventory pre-pass | Open — missing script | **Resolved** — `scan-sources.py` added; Stage 1a invokes it exactly |
| D-2: Stage 1 sequential substeps | Open — two tool-call rounds | **Resolved** — scan-sources.py collapses resume detection + source inventory into one pass |
| S-2: Template section counter | Open — low priority | Unchanged — still a marginal opportunity; template is 89 lines |
| S-3: Revision diff detection | Open — low priority | Unchanged — still fires only in Update mode |
| D-1: Subagent return constraints | Open — low priority | Unchanged — parallel-lens menu does not specify return format |
| `output_dir` scalar unread in SKILL.md | Not previously noted | **New finding** — customize.toml declares `output_dir` but SKILL.md never references `{workflow.output_dir}` (hardcoded downstream assumption) |
| `scan-sources.py` missing tests | Not previously noted | **New finding** — `scripts/tests/` contains only `test-validate-requirements.py`; `scan-sources.py` has no test coverage |

---

## Existing Scripts Inventory

| Script | Purpose | Coverage |
|--------|---------|----------|
| `scripts/validate-requirements.py` | REQ ID uniqueness/sequencing, vague term detection, required section presence, empty section check, NFR measurability check | 11 tests in `scripts/tests/test-validate-requirements.py` |
| `scripts/scan-sources.py` | Project state scan — discovers D-02 frontmatter (resume/update routing), source docs, project-context path; returns compact JSON manifest | No tests |

---

## Assessment

Intelligence placement is excellent. Both deterministic operations (structural validation, source scanning) are correctly offloaded to scripts; SKILL.md reserves LLM judgment for elicitation, contradiction detection, and testability assessment. The main resolution since the prior session is S-1 and D-2 — the source inventory pre-pass script is implemented and correctly wired into Stage 1a, collapsing two prior sequential tool-call rounds into one. Three remaining findings are low-severity carry-overs. One new gap: `output_dir` is declared in customize.toml but SKILL.md never reads it, making the scalar an override-that-does-nothing; and `scan-sources.py` has no tests, leaving the routing logic (fresh/resume/update branching) without a regression net.

---

## Script Findings

### S-2: Template section counter for generation guidance (Stage 3) — carry-over

- **Severity:** low (LLM tax: light, ~50-100 tokens)
- **Location:** SKILL.md:65 (Stage 3, "Populate template")
- **Current behavior:** The LLM reads `{workflow.template_path}` (89-line template) to understand which sections to populate. The template is structural scaffolding; the LLM extracts section names, column headers, and order.
- **Script alternative:** A small companion to `validate-requirements.py` that emits a template manifest: section names, expected table schemas, column headers. LLM receives JSON instead of raw template.
- **Estimated token savings:** 50-100 tokens (template is only 89 lines; savings are modest at current template size).
- **Language:** Python.
- **Pre-pass potential:** Low-medium. Only worth implementing if the template grows significantly.
- **Priority:** Low — template is small; cost of tooling outweighs savings at current scale.

### S-3: Revision history diff detection (Stage 3, Update mode) — carry-over

- **Severity:** low (LLM tax: light, ~50-100 tokens)
- **Location:** SKILL.md:71-74 (Stage 3, "Revision history")
- **Current behavior:** In Update mode, LLM determines whether changes are "same requirements, polish only" vs "new/changed requirements" by reading and comparing two documents. REQ ID extraction and set-diff is deterministic.
- **Script alternative:** Script diffs two D-02 files by REQ IDs and reports: `{"added": ["REQ-004"], "removed": [], "modified_lines": 3, "scope": "content_change|polish_only"}`.
- **Estimated token savings:** 50-100 tokens per update invocation.
- **Language:** Python.
- **Pre-pass potential:** Medium — only fires in Update mode, but eliminates a full document read-and-compare when it does.
- **Priority:** Low — Update mode is less frequent than Create; acceptable as LLM judgment for now.

### S-4: `scan-sources.py` missing test coverage — new

- **Severity:** medium
- **Location:** `scripts/scan-sources.py` (no test file)
- **Current behavior:** No regression coverage for routing logic. The `state` determination (`fresh` / `resume` / `update`) is a pure function of filesystem state + frontmatter parsing — fully deterministic and unit-testable. If the scan returns wrong state, Stage 1 routing silently misbehaves (e.g., treating a complete D-02 as fresh, discarding existing work).
- **Script alternative (fix):** Add `scripts/tests/test-scan-sources.py` mirroring the structure of `test-validate-requirements.py`. Key cases: (1) empty directory → `fresh`; (2) D-02 with `lastStep: complete` → `update`; (3) D-02 with partial `lastStep` → `resume`; (4) project-context.md discovery; (5) source_docs deduplication.
- **Estimated impact:** Regression protection for routing decisions that have no LLM fallback — if `scan-sources.py` returns wrong state, Stage 1 proceeds with silent bad data.
- **Priority:** Medium — the script is now load-bearing (invoked at every activation); absence of tests is a gap for the kind of deterministic logic that is cheapest to test.

---

## Distribution Findings

### D-1: Parallel-lens menu lacks subagent return constraints — carry-over

- **Severity:** low
- **Location:** SKILL.md:77 (Stage 3 parallel-lens menu), SKILL.md:99 (Stage 4 parallel-lens menu)
- **Current pattern:** Both `[A]` Advanced Elicitation / `[P]` Party Mode / `[C]` Continue menus are offered without specifying return format for subagent invocations. If lenses spawn subagents, the prompt contains no "ONLY return X" constraint.
- **Efficient alternative:** When parallel review lenses are invoked, include "Return ONLY a bulleted list of findings with REQ-xxx references. No preamble or explanation." Prevents each lens from returning 500+ tokens of prose when 50-100 tokens of findings would suffice.
- **Impact:** Prevents context bloat from verbose subagent returns. Worth addressing before Party Mode sees heavy use.
- **Priority:** Low — the lens menu is user-initiated; token impact is bounded per invocation.

### D-3: `output_dir` scalar declared but never read — new

- **Severity:** medium
- **Location:** `customize.toml:24` declares `output_dir = "{project-root}/_hbc_output/plan"`; SKILL.md never references `{workflow.output_dir}`
- **Current pattern:** Stage 5 save step mentions updating frontmatter but does not reference the configured output path. The LLM will infer or hardcode a path, meaning a team override to `output_dir` silently does nothing.
- **Efficient alternative:** Stage 5 should reference `{workflow.output_dir}` as the save destination: "Save to `{workflow.output_dir}/D-02-{project_name}.md`." This matches the pattern correctly used by `{workflow.template_path}` and `{workflow.validation_script}`.
- **Impact:** Override silently no-ops is a documented failure mode in the principles file. The fix is one line in SKILL.md Stage 5.
- **Priority:** Medium — affects any team that customizes output location.

---

## Aggregate Token Savings Estimate

| Finding | Per-invocation savings | Frequency | Value |
|---------|----------------------|-----------|-------|
| S-1: Source inventory pre-pass (resolved) | 200-400 tokens | Every activation | Captured |
| S-2: Template section counter | 50-100 tokens | Every generation | Low |
| S-3: Revision diff detection | 50-100 tokens | Update mode only | Low |
| S-4: scan-sources.py test coverage | 0 token savings | Regression protection | Risk mitigation |
| D-1: Subagent return constraints | 200-500 tokens avoided | When lenses used | Medium |
| D-3: output_dir unread | 0 token savings | Correctness fix | Override reliability |

**Remaining token opportunity:** ~250-600 tokens per invocation (D-1 dominant when lenses are used; S-2/S-3 marginal). The high-value S-1 finding was fully captured in this session.

---

## Strengths

1. **S-1 resolution is clean.** `scan-sources.py` returns the exact compact JSON manifest proposed in the prior analysis — `state`, `existing_d02` (path + frontmatter fields), `source_docs` list, `project_context` path. Stage 1a invokes it with the exact command-line pattern. This is the highest-value improvement; it eliminates the LLM's file-scanning work and folds resume detection and source inventory into one pre-pass.

2. **Validation script remains exemplary.** `validate-requirements.py` handles all structural checks with proper JSON output, `auto_fixable` flags, configurable vague terms, and 11-test coverage. Intelligence placement here is the reference model for the skill.

3. **SKILL.md grew modestly.** 96 → 108 lines (+12 lines for Stage 1a scan invocation and related routing detail). Still within size guidance (~130 hard ceiling). The added lines are load-bearing — exact script command, state-routing logic, and headless mode source requirement.

4. **Three customize.toml scalars now all meaningfully configurable.** `template_path`, `validation_script`, and `vague_terms` are all read via `{workflow.*}` in SKILL.md. Only `output_dir` remains broken (D-3).

5. **Headless contract is clean and unchanged.** `references/headless-contract.md` specifies a minimal return schema; the return values (`status`, `output_path`, `decision_log`, `validation`) are unambiguous with no verbose prose required.

6. **Compaction flush discipline.** All three data-heavy stages (2, 3, 4) write compact state to the decision log before advancing — actor list, REQ count, scope summary, version, validation results. This correctly defends against compaction-induced context loss.
