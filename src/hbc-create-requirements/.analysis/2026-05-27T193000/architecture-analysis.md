# Architecture Analysis — hbc-create-requirements

**Scanner:** quality-scan-architecture v1.0
**Skill:** `src/hbc-create-requirements`
**Date:** 2026-05-27T19:30:00
**Prior analysis:** `.analysis/2026-05-27T103000/architecture-analysis.md`

---

## Assessment

The skill is well-structured and the most significant prior finding (workflow-type misclassification in the prepass) is resolved. However, a new HIGH finding has emerged from the current SKILL.md: `{output_file}` is used as a script argument in Stage 4 but is never defined — neither as a `{workflow.*}` variable nor as a locally-constructed value — and `output_dir` is declared in `customize.toml` but never consumed in SKILL.md, meaning the override mechanism silently no-ops. The two prior MEDIUM findings (build-time decision log in `references/`, headless-contract carve-out size) remain open and are reclassified per current evidence.

---

## Delta from Prior Analysis

| Prior Finding | Status |
|---|---|
| HIGH — Workflow type misclassification in prepass | **RESOLVED** — prepass now correctly classifies as `multi-stage-workflow` |
| MEDIUM — Build-time decision log in `references/` | **OPEN** — unchanged |
| MEDIUM — `headless-contract.md` may not need to be separate | **OPEN** — file grew 30→41 lines; judgment still applies |
| LOW — Numbered stage headings | **CLOSED** — correctly not actioned |
| LOW — Template `{project_name}` placeholder | **OPEN** — unchanged, still low |
| LOW — `{document_output_language}` / `{communication_language}` in carved files | **CLOSED** — correctly not actioned |

**New findings this pass:** 1 HIGH (undefined `{output_file}` / missing `output_dir` consumption), 1 MEDIUM (headless contract grew and now warrants inline consolidation more than before).

---

## Findings

### HIGH — `{output_file}` undefined; `output_dir` declared but never consumed

- **File:** `SKILL.md` line 84; `customize.toml` line 24
- **What:** Stage 4 runs the validation script as:
  ```
  python3 {workflow.validation_script} {output_file} --project-root {project-root} --vague-terms "{workflow.vague_terms}"
  ```
  `{output_file}` is not a `{workflow.*}` variable, not a standard BMad template variable, and is never assigned anywhere in SKILL.md. The LLM cannot resolve it mechanically; it must guess. Meanwhile, `customize.toml` declares `output_dir = "{project-root}/_hbc_output/plan"` but SKILL.md contains no `{workflow.output_dir}` reference anywhere — neither in Stage 3 (where the document is written) nor in Stage 5 (where it is finalized). The override path silently does nothing.
- **Why it matters:** Two separate failure modes from the principles file collide here. First: "SKILL.md must reference resolved values as `{workflow.<name>}`. Hardcoded paths next to a declared scalar = override silently no-ops." Second: the validation script invocation is listed under "fragile operations" (exact script commands, exact API calls — one right way) yet the positional argument is undefined. In headless mode, where the LLM cannot recover interactively, this produces an untestable script call.
- **Fix:** Define how the output path is constructed. Options:
  1. Add `output_path` as a `customize.toml` scalar (full file path pattern, e.g. `"{project-root}/_hbc_output/plan/D-02-{project_name}.md"`) and reference it as `{workflow.output_path}` in Stage 3, Stage 4's script call, and Stage 5.
  2. Or, if the filename is always derived at runtime (project name not known at config time), document the derivation rule explicitly in Stage 3: "Write to `{workflow.output_dir}/D-02-{slugified_project_name}.md`; this path is `{output_file}` for the Stage 4 script call." Either way, `{output_file}` must be a named, defined value before it is passed to the script.

---

### MEDIUM — Build-time decision log mixed with runtime-loaded references

- **File:** `references/.decision-log.md`
- **What:** This file documents authorial decisions (5-stage rationale, bilingual template rationale, REQ-xxx as traceability anchor). It lives alongside `references/headless-contract.md`, which is a runtime-loaded schema definition.
- **Why it matters:** Per principles, `references/` is for "prompt content carved out of SKILL.md" — content the LLM loads during execution. A build-time decision log is project metadata; its dotfile prefix signals the tension. SKILL.md does not reference it, so no contamination risk today — but the folder semantics are ambiguous for anyone maintaining this skill. The prior analysis noted this as MEDIUM; it remains so.
- **Fix:** Move to `.build/decision-log.md` or keep in the `.analysis/` folder alongside quality reports. No runtime behavior change required.

---

### MEDIUM — `headless-contract.md` has grown to inline-worthy size and content overlap

- **File:** `references/headless-contract.md` (41 lines, 314 tokens)
- **What:** The headless contract grew from 30→41 lines between passes, now including an Input Args table and a usage example. The `## Headless Mode` section in SKILL.md (lines 23–26) already states the core contract ("Sources required via args. Returns JSON with `status`, `output_path`, validation summary. On `blocked`, includes `reason`"). The carved-out file restates this and adds the arg table and example.
- **Why it matters:** SKILL.md at 108 lines is approaching (but not yet at) the ~130 ceiling. The carved file is 41 lines. If inlined, SKILL.md would be ~149 lines — just over the ceiling. However, the principles flag "Multiple files that could be a single instruction" as wasteful. The current arrangement means the headless contract is described twice (summary in `## Headless Mode`, full schema in the reference). On compaction, the LLM executing Stage 5 headless return may have lost `## Headless Mode` but have `headless-contract.md` — or vice versa. Neither is a full specification alone.
- **Why it's medium, not high:** The duplication is partial, not total. The reference adds the arg table which is genuinely additive. The dual-description is a cohesion risk, not a breakage.
- **Fix:** Collapse `## Headless Mode` in SKILL.md to a routing line ("Headless mode: run all stages non-interactively, return JSON per `references/headless-contract.md`.") and move all headless specification into the reference file — making it self-contained and eliminating the dual-description. This also keeps SKILL.md under 130 lines.

---

### LOW — Template `{project_name}` substitution undocumented

- **File:** `templates/D-02_requirements_template.md` lines 3, 11
- **What:** The template uses `{project_name}` as a placeholder. No instruction in SKILL.md or the template itself specifies what provides this value (LLM substitution at generation time is the natural reading, but the substitution syntax is identical to `{workflow.*}` variable syntax).
- **Why it matters:** Low risk — the LLM will fill it from context. But a maintainer adding a `project_name` scalar to `customize.toml` would get unexpected double-substitution behavior. Clarifying the distinction (template placeholder vs. config variable) costs one sentence.
- **Fix:** Add a comment in the template: `<!-- {project_name}: filled by LLM from project context at generation time — not a workflow config variable. -->`

---

## Strengths

Preserved from prior analysis; no regressions observed:

1. **Workflow-type prepass now correct.** The HIGH misclassification from the prior pass is resolved. The prepass correctly identifies five inline stages.

2. **Right-sized SKILL.md for its complexity.** 108 lines, 1529 tokens — the growth from 96 lines is explained by a second fenced block (the validation script command), not padding. No defensive language, no meta-explanation, no scoring formulas.

3. **Intelligence placement holds.** Deterministic checks stay in the Python script; judgment stays with the LLM. The `auto_fixable` flag enables the headless/interactive split without either the script or the LLM overstepping.

4. **Outcome-based prose throughout.** Stage 2 elicitation, Stage 3 generation, and Stage 4 judgment checks all express outcomes with constraints, not step-by-step procedures.

5. **Compaction-aware design.** Three compaction flush points (end of Stage 2, end of Stage 3, end of Stage 4) anchor the decision log with durable state. The resume/update/fresh routing in Stage 1 is compact and correct.

6. **Customization surface is minimal and correct.** Three domain-specific scalars — `template_path`, `output_dir`, `validation_script` — plus the vague-terms array and the BMad standard triple. No boolean toggles. The `vague_terms` array append-merge is a well-chosen configurability point.

7. **Parallel-lens menu placement.** Offered at two natural transition points (post-generation, post-validation) without prescribing what each lens produces. Matches the principles pattern without ceremony.

8. **`{workflow.validation_script}` and `{workflow.template_path}` correctly referenced.** Two of the three workflow scalars are consumed correctly. The gap is `output_dir` (see HIGH finding).
