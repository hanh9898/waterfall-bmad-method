# Architecture Analysis — hbc-traceability

**Scanner:** architecture (structural integrity + prose craft + cohesion)
**Skill path:** `src/hbc-traceability`
**Date:** 2026-05-27
**Prior grade:** B (2026-05-26)

## Assessment

The 2026-05-26 analysis yielded a B with three issues resolved since: `## On Complete` (exit hook) is gone, `on_complete` was removed from `customize.toml`, and the five-step prescriptive `## On Activation` has been collapsed into outcome language — dropping SKILL.md from 161 lines to 107, well within the ~130 ceiling. The remaining actionable finding is the fragile entity-extraction pattern that was noted as M-4 in the prior run but is now the sole meaningful gap: LLM judgment is correctly used for semantic REQ-to-entity mapping, but the Update section still reads D-19 with no guidance on what to look for, leaving the agent without the domain framing needed to do this reliably. One low-severity structural item (`__pycache__` in `scripts/`) also persists.

## Findings

### MEDIUM

**M-1. Update Phase 2 delegates entity extraction to LLM judgment without domain framing**
- **File:** `SKILL.md:62`
- **Issue:** "Use LLM judgment to extract design entities from D-19 and map each REQ to entities and test cases." The D-19 artifact in the HBC lifecycle is an ER diagram — a structured document. Without telling the agent what kinds of entities to look for (tables, entities, screens, modules) or what the mapping relationship represents (a requirement is traced to the design element that satisfies it), LLM judgment here is underspecified. Prior analysis (M-4) flagged the original regex as an intelligence leak; the fix removed the regex but left the guidance thin. Per the principles file: "Domain framing and theory-of-mind for interactive workflows — context that enables judgment" earns its keep.
- **Fix:** Add one sentence of domain context: e.g., "D-19 is the ER/component diagram — extract named tables, entities, or modules that implement each REQ. The mapping relationship is: this design element is the structural realization of this requirement." This costs 1-2 lines and prevents the agent from mapping at the wrong granularity (e.g., mapping REQs to column names instead of tables).

### LOW

**L-1. `__pycache__` in `scripts/` persists**
- **File:** `scripts/__pycache__/`
- **Issue:** Build artifact present in source tree. Carries `.cpython-313.pyc` files for both scripts. Noted in prior analysis (L-2) as unresolved.
- **Fix:** Add `scripts/__pycache__/` (or `**/__pycache__/`) to `.gitignore` and remove the directory.

**L-2. `{communication_language}` not referenced in capability output sections**
- **File:** `SKILL.md` (Report and Audit sections)
- **Issue:** The Conventions block and customize.toml load `communication_language` via standard BMad activation, but capability sections specify literal English output strings (e.g., `"Initialized matrix with {count} requirements from D-02"`). In a Vietnamese-language project, these literal strings will be emitted in English. This was L-1 in the prior analysis and remains unaddressed.
- **Why it's low, not higher:** The executing agent will usually infer the correct output language from config context. This is a consistency gap, not a reliability gap.
- **Fix:** Add a single note to the Overview or Conventions block: "Capability report strings follow `{communication_language}`." One line; no per-section change needed.

## Resolved Since Prior Analysis

The following findings from 2026-05-26 are confirmed closed:

- **H-1 (SKILL.md size overage):** 161 → 107 lines. Well within ceiling.
- **H-2 (`## On Complete` exit hook):** Section removed.
- **M-1 (prescriptive On Activation):** Collapsed to one outcome-based sentence at line 33.
- **M-2 (over-specified headless JSON schema):** Reduced to a single prose sentence describing the return shape.
- **M-3 (`on_complete` scalar in customize.toml):** Removed.
- **M-4 (entity-name regex intelligence leak):** Regex removed; LLM judgment used. Domain framing gap is now M-1 in this run.

## Strengths

1. **Clean intelligence placement holds.** Scripts (`extract-trace-ids.py`, `trace-report.py`) handle all deterministic work: regex extraction of structured IDs, markdown table parsing, coverage statistics. LLM judgment is reserved exclusively for semantic mapping. This boundary is clean and the scripts are well-constructed.

2. **SKILL.md is now right-sized.** 107 lines / ~1592 tokens for a four-capability skill with script invocations is appropriate. No section is padded; each carries load-bearing content.

3. **On Activation is outcome-based.** The collapsed form at line 33 ("Resolve customization, load persistent facts and config per standard BMad activation. Then determine capability: ...") is exactly the right treatment — standard steps by reference, skill-specific routing spelled out.

4. **Headless mode is lean and complete.** Three lines covering required capability, suppressed output, and JSON return shape with blocked reason. No schema over-specification.

5. **Interrupted-update recovery is a genuine reliability feature.** The `.trace-state.json` marker written before Update and cleared on completion prevents silent data loss on interruption. This is the kind of fragile-operation detail that earns its place in the prompt.

6. **customize.toml surface is clean.** `matrix_path`, `matrix_template`, `source_code_path` — three well-named scalars with override comments. `source_code_path = ""` with a "leave empty to prompt" note is the right pattern for optional configuration.

7. **Description format is correct.** Quoted trigger phrases in three languages (`'traceability'`, `'ma trận'`, `'truy vết'`) plus agent menu `[TR]`. Conservative explicit triggering per principles.
