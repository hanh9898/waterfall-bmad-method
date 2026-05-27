# Architecture Analysis — hbc-create-requirements

**Scanner:** quality-scan-architecture v1.0
**Skill:** `src/hbc-create-requirements`
**Date:** 2026-05-27

## Assessment

A solid, well-proportioned skill. SKILL.md is 96 lines (~1228 tokens) — comfortably within the target range for an inline multi-stage workflow. The five stages flow logically, each consuming what the prior stage produces. The validation script is a clean example of intelligence placement done right: determinism in the script, judgment in the LLM. Two findings warrant attention: a workflow-type misclassification from the prepass, and the `references/.decision-log.md` sitting in an unusual location that conflates build-time artifact with runtime workspace.

## Findings

### HIGH — Workflow type misclassification in prepass metadata

- **File:** `workflow-integrity-prepass.json`, `metadata.workflow_type`
- **What:** Prepass classified this as `simple-utility`. The skill has 5 named stages with resume state, headless mode, parallel-lens review, and a decision-log workspace pattern. This is a Complex Workflow by any reasonable measure.
- **Why it matters:** Downstream tooling relying on the prepass classification (size thresholds, scan expectations) will apply the wrong bar. Per principles: "Simple Utilities (no decisions to log; the input/output IS the contract)" — this skill has extensive decision logging and multi-turn interaction.
- **Fix:** This is a prepass script issue, not a SKILL.md issue. The SKILL.md itself does not claim a workflow type in its prose, which is correct. No action needed in the skill; flag to the prepass script maintainer that stage-counting heuristics need to account for inline `## Stage N:` sections.

### MEDIUM — Build-time decision log in `references/`

- **File:** `references/.decision-log.md`
- **What:** This is a build-time decision log documenting authorial decisions (Wave 2 context, why 5 stages, why deterministic validation). It lives in `references/` alongside `headless-contract.md`, which is runtime-loaded content.
- **Why it matters:** Per principles, `references/` is for "prompt content carved out of SKILL.md" — workflow content the LLM loads during execution. A build-time decision log is not consumed at runtime; it is project documentation. Mixing the two creates ambiguity about what gets loaded into context. The dotfile prefix (`.decision-log.md`) suggests awareness of this tension.
- **Fix:** Move to a dedicated build metadata location (e.g., `.build/decision-log.md` or the `.analysis/` folder) or keep it but ensure SKILL.md never routes to it. Currently SKILL.md does not reference it, so the contamination risk is low — this is medium, not high.

### MEDIUM — `headless-contract.md` in references may not need to be separate

- **File:** `references/headless-contract.md` (30 lines, ~204 tokens)
- **What:** The headless contract is a 30-line file defining the return JSON schema and blocked reasons. SKILL.md line 95 references it: "return JSON per `references/headless-contract.md`."
- **Why it matters:** At 204 tokens, this could inline into SKILL.md without meaningfully increasing its size (96 lines + ~20 lines = ~116, still under the 130 ceiling). Principles: "Multiple files that could be a single instruction" is listed under "What Doesn't Earn Its Keep." Counter-argument: the contract is a schema definition that might be shared across skills, and carving it out keeps it maintainable as a single-source-of-truth.
- **Fix:** Judgment call. If other skills reference this same contract pattern, keep it carved out. If this is the only consumer, consider inlining the schema and blocked reasons into a `## Headless Contract` section in SKILL.md. Either way, not broken.

### LOW — Stage sections use numbered prefixes in headings

- **File:** `SKILL.md`, lines 31-89
- **What:** Stages are named `## Stage 1: Prerequisites`, `## Stage 2: Discovery`, etc. The principles file says "Descriptive filenames. Never numbered prefixes... the carve-out is a section, not a 'step.'" This guidance targets carved-out filenames, not inline section headings. Numbered inline headings are conventional and aid navigation.
- **Why it matters:** Minimal. The numbered-prefix rule targets filenames (`01-discover.md`), not inline `## Stage N:` headings. Inline numbering is load-bearing here: it signals execution order and the resume state mechanism references stage numbers implicitly via `lastStep`.
- **Fix:** No action needed. This is correctly applied convention for inline stages.

### LOW — Template uses bare `{project_name}` without config resolution marker

- **File:** `templates/D-02_requirements_template.md`, lines 3, 11
- **What:** The template uses `{project_name}` in the title and heading. This looks like a template placeholder, not a `{workflow.*}` config-resolved variable.
- **Why it matters:** Per principles, "SKILL.md must reference resolved values as `{workflow.<name>}`." However, this is a template file in `templates/`, not SKILL.md itself. Template placeholders are expected to use their own substitution syntax. The SKILL.md correctly references `{workflow.template_path}` and `{workflow.output_path}`.
- **Fix:** Clarify in SKILL.md or the template itself what substitutes `{project_name}` (LLM fills it during generation, which is the natural interpretation). No functional issue.

### LOW — `{document_output_language}` and `{communication_language}` usage

- **File:** `SKILL.md`, line 29
- **What:** SKILL.md line 29 says "Output in `{document_output_language}`, communicate in `{communication_language}`." This is correct placement. However, the carved-out `references/headless-contract.md` does not mention either variable.
- **Why it matters:** Per principles, "Each carved file uses `{communication_language}` (and `{document_output_language}` if it produces a doc)." The headless contract is a schema definition, not a document-producing stage, so the omission is acceptable.
- **Fix:** No action needed.

## Strengths

1. **Right-sized SKILL.md.** 96 lines, 1228 tokens. Every section earns its place. No defensive padding, no meta-explanation, no scoring formulas. The Overview establishes role and mission in 7 lines — clean.

2. **Intelligence placement is correct.** The validation script handles deterministic checks (REQ ID uniqueness, sequencing, vague term detection, section presence, NFR measurability). The LLM handles judgment checks (testability, contradictions, ambiguity, scope clarity). No intelligence leaks in either direction.

3. **Validation script is well-engineered.** Clean separation of concerns across `check_req_ids`, `check_vague_terms`, `check_sections`, `check_nfr_measurable`. The `auto_fixable` flag per issue enables the headless/interactive split cleanly. Tests cover 11 cases including edge cases (no REQ IDs, empty sections, custom vague terms, file output).

4. **Customization surface is minimal and correct.** Three workflow-specific scalars (`template_path`, `output_path`, `vague_terms`) plus the standard BMad triple. No boolean toggles, no permutation forest. The `vague_terms` scalar is a good example of domain-appropriate configurability.

5. **Outcome-based prose.** Stage 2 says "Elicit requirements through structured conversation" rather than prescribing a question script. Stage 3 says "Populate template with discovered content" with outcome constraints (unique IDs, measurable NFRs) rather than step-by-step instructions. This is the right level of freedom.

6. **Resume and update modes handled in one natural block.** Stage 1 covers fresh/resume/update as three states of the same check, not three separate workflows. Compact and clear.

7. **Compaction-aware design.** Stage 2 explicitly flushes discovered requirements to the decision log at end of stage ("This survives compaction"). Stage 5 appends a closing session. The decision-log workspace pattern is applied lightly — principle stated once, reads at the moments that matter.

8. **Parallel-lens menu.** Offered at two natural transition points (post-generation, post-validation) without over-prescribing what each lens does. Matches the "parallel review lenses" pattern from principles.

9. **Headless contract is clean.** Schema, status values, and blocked reasons — nothing extraneous. The three blocked reasons cover the actual failure modes.

10. **Template is well-structured.** Japanese section headers with English parentheticals match the project convention noted in the decision log. Required sections in the template align exactly with what the validation script checks.
