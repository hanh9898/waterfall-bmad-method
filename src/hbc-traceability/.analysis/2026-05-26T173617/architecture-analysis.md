# Architecture Analysis — hbc-traceability

**Scanner:** architecture (structural integrity + prose craft + cohesion)
**Skill path:** `src/hbc-traceability`
**Date:** 2026-05-26

## Assessment

A well-structured simple workflow skill with clear intelligence placement — scripts handle deterministic extraction and reporting while LLM judgment is reserved for semantic mapping. The four-capability routing (init/update/report/audit) is cohesive and the data flow is sound. Main issues are moderate: SKILL.md at 161 lines exceeds the ~130 hard ceiling for a simple workflow, and the `## On Complete` section functions as an exit hook that won't reliably fire. Scripts are clean and purposeful.

## Findings

### HIGH

**H-1. SKILL.md exceeds size ceiling for simple workflow**
- **File:** `SKILL.md` (161 lines / ~1792 tokens)
- **Issue:** Principles file sets ~130 lines as the hard ceiling for a non-multi-branch SKILL.md. At 161 lines, this is 24% over.
- **Why it matters:** Longer files increase compaction risk and reduce scanability. The Update section alone (lines 93-121) runs 29 lines with detailed per-phase sub-procedures that could be tightened.
- **Fix:** Compress the On Activation boilerplate (Steps 1-5 follow the standard BMad activation pattern — collapse into a single step or reference the pattern by name). Tighten Update sub-steps by using outcome language rather than step-by-step regex invocations already specified as script calls. Target: ~120 lines.

**H-2. `## On Complete` is a de facto exit hook**
- **File:** `SKILL.md:158-161`
- **Issue:** The principles file explicitly states "There are NO exit hooks in the system. Don't add `## On Exit` sections — they'd never run." `## On Complete` behaves identically — it fires "after the workflow finishes," which is the exit-hook pattern under a different name. There is no reliable mechanism to trigger this.
- **Fix:** Remove `## On Complete`. If post-workflow chaining is needed, document it as a user-facing suggestion at the end of each capability's report output (e.g., _"Next: run phase gate"_), or handle it in the calling orchestrator.

### MEDIUM

**M-1. On Activation is prescriptive where it could be outcome-based**
- **File:** `SKILL.md:48-76` (Steps 1-5)
- **Issue:** The five numbered activation steps are the standard BMad activation sequence. Every BMad skill runs them. Re-specifying "Resolve the Workflow Block," "Execute Prepend Steps," "Load Persistent Facts," "Load Config" is prescriptive procedure for something the executing agent already knows (principles: "Outcome vs Prescriptive" table). Only Step 5 (capability determination) is skill-specific.
- **Why it matters:** 28 lines of On Activation on boilerplate that doesn't add value, contributing to the size overage in H-1.
- **Fix:** Collapse Steps 1-4 into: "Resolve customization, load persistent facts and config per standard BMad activation." Keep Step 5 (capability routing) as the skill-specific logic.

**M-2. Headless mode JSON schema is over-specified**
- **File:** `SKILL.md:23-46`
- **Issue:** The Headless Mode section specifies a full JSON response schema (10 lines of fenced JSON). The principles file guidance for headless says the JSON return is "the smallest set of paths the caller needs" with status. The full coverage breakdown and gap list in the schema duplicates what the Report/Audit capabilities already produce. The LLM can construct the appropriate response shape.
- **Fix:** Reduce to: "Return JSON with `status`, `capability`, `matrix_path`, and summary stats. On `blocked`, include `reason`." Let the LLM construct the shape from the capability's output.

**M-3. `on_complete` scalar in customize.toml supports the removed exit hook**
- **File:** `customize.toml:29`
- **Issue:** Corresponds to the `## On Complete` section flagged in H-2. If On Complete is removed, this scalar has no consumer.
- **Fix:** Remove `on_complete` from customize.toml when removing `## On Complete` from SKILL.md.

**M-4. Update section mixes script invocation with LLM judgment in a way that could confuse boundaries**
- **File:** `SKILL.md:103-107`
- **Issue:** Phase 2 update tells the agent to run `extract-trace-ids.py` for entity names and TC IDs, then "use LLM judgment to match design entities and test cases." The regex pattern for entity names (`(?:テーブル|Table|Entity)[\s:：]*(\w+)`) is fragile — `\w+` won't match multi-word entity names, and hard-coding Japanese alongside English is locale-dependent. This pattern is better suited to LLM judgment than regex. Per the intelligence placement principle: "Script using regex to decide what content MEANS = intelligence leak into the script."
- **Fix:** Consider extracting entity names via LLM judgment alongside the REQ-to-entity mapping, rather than using a regex pattern that only partially works. Keep `extract-trace-ids.py` for the well-structured ID patterns (REQ-xxx, TC-xxx) where regex is reliable.

### LOW

**L-1. `{communication_language}` and `{document_output_language}` not referenced in SKILL.md body**
- **File:** `SKILL.md`
- **Issue:** Step 4 loads these config values, but the capability sections don't reference them. The matrix template and report output language are implicitly whatever the agent defaults to.
- **Fix:** Add a note in the Initialize or Report sections that output language follows `{document_output_language}`. Minor — the agent will likely do this anyway from config context.

**L-2. `__pycache__` directory present in scripts/**
- **File:** `scripts/__pycache__/`
- **Issue:** Build artifact committed or present in source tree. Should be gitignored.
- **Fix:** Add `__pycache__/` to `.gitignore` and remove the directory.

## Strengths

1. **Clean intelligence placement.** Scripts handle the deterministic work (regex extraction, markdown parsing, statistics) while LLM judgment is reserved for semantic mapping (REQ-to-design, REQ-to-code). This is exactly the split the principles file recommends.

2. **Four capabilities, one skill.** The decision to keep Init/Update/Report/Audit as capabilities within a single skill rather than four separate skills is correct — they all operate on the same living document and share context.

3. **Phase detection from column state.** Inferring which phase's data to populate by reading which columns are empty is elegant — reduces user friction without losing clarity. The confirmation prompt ("Inferred 'update' from Dev context. Proceed?") is the right balance.

4. **Headless mode designed in from the start.** The decision log notes this was a lesson learned from phase gate (O3 finding). Including it upfront prevents retrofitting later.

5. **Decision log is well-reasoned.** Documents key architectural choices with clear rationale and rejected alternatives. The "incremental update, never remove" principle and "fully deterministic mapping rejected" entries show thoughtful design.

6. **customize.toml follows BMad conventions.** Correct fields (`activation_steps_prepend/append`, `persistent_facts`), descriptive scalar names (`matrix_path`, `source_code_path`), proper merge-rule comments.

7. **Scripts are focused and well-structured.** Both `extract-trace-ids.py` and `trace-report.py` are single-purpose, use proper argument parsing, return structured JSON, and handle edge cases (missing files, no matches).
