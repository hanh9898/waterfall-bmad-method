# Enhancement Analysis: hbc-phase-gate

## Skill Understanding

**hbc-phase-gate** is a deterministic quality gate engine for the HBC Waterfall-TDD lifecycle. It evaluates projects against phase-specific checklists (Analysis, Design, Implementation, Testing), each with typed evaluation criteria (file existence, content patterns, metrics, LLM judgment). Reports pass/fail status to block or warn progression based on `gate_mode` config. Acts as a strict, evidence-based reviewer with no discretionary pass-through.

**Primary user:** Phase gate reviewers (architects, QA leads, dev leads) invoking from agent context menus. **Key assumption:** Projects follow HBC structure (`_hbc_output/` artifact conventions, `_bmad/config.yaml` centralization) and generate artifacts matching expected patterns.

---

## User Journey Analysis

### Archetype 1: The Gatekeeper (Phase Reviewer)
**Context:** Architect at phase transition, needs to block/allow progression.

**Journey:**
1. Invoke `hbc-phase-gate` (inferred from agent context — smooth)
2. Skill loads checklist, evaluates artifacts
3. Report appears with summary and per-item failures
4. If PASSED → proceed; if FAILED (strict) → read failures and plan fixes

**Friction points:**
- **No re-evaluation context:** If gate was run once, failed, and is re-run after fixes, there's no visual delta between the first and second report. The gatekeeper sees only the current state, not "these 3 items were fixed, 1 still failing." Decision log would help.
- **Evidence readability:** Evidence field is free-form text. For complex artifacts (large D-02 with 50+ requirements), evidence like "match count: 47" doesn't tell the reviewer which requirements are missing or which business flows they trace to.
- **No actionable next steps:** FAILED report lists items but doesn't suggest which skill to invoke to fix each (e.g., "missing D-12 Coding Standards" → suggest invoking design-build or point to d-12-create skill if it exists).

**Bright spots:**
- Clear overall status (PASSED/FAILED/WARNING)
- Structured table format is scannable
- Strict mode blocks progression (intended behavior)

---

### Archetype 2: The Builder (First-Time User)
**Context:** Dev or architect not familiar with HBC gate structure, accidentally invokes `hbc-phase-gate` or asked to "check if we're ready."

**Journey:**
1. User says "check if we're ready" — skill infers phase from context (good)
2. Report appears
3. User sees checklist of documents (D-02, D-19, D-26, etc.) they've never heard of
4. Confused: "What is D-19? Where do I get it?"

**Friction points:**
- **No discovery of what's needed:** Report assumes user knows what D-02, D-19, D-26 are and where to create them. No links to skills that generate them.
- **Silent phase inference:** User doesn't see which phase was evaluated (inferred silently). If context is ambiguous (e.g., both BA and Dev roles), which phase won?
- **No remediation path:** Failed items list documents but not "invoke hbc-bmb-setup to configure" or "run bmad-create-prd to generate D-02."

**Bright spots:**
- Warnings are clear (FAILED blocks progression in strict mode)

---

### Archetype 3: The Automator (Headless / Pipeline Invoker)
**Context:** Another agent (e.g., CI, sprint-planning skill) wants to check gate status programmatically.

**Journey:**
1. Headless agent tries to invoke with phase + project-root parameters
2. Response is a markdown report (human-readable, not structured)
3. Caller has no way to parse gate status without regex on markdown

**Friction points:**
- **No machine-readable output:** Decision-log workspace would enable this. Headless mode with JSON/YAML return would be better. Currently, no headless path exists.
- **No explicit inputs:** SKILL.md says "Args: Phase number (1-4), or inferred from calling agent context" but doesn't document the exact parameter format for headless invocation.
- **No exit code or status field:** Report is always markdown, no structured return format for automated parsing.

**Bright spots:**
- Deterministic evaluation (no ambiguity in PASSED/FAILED)

---

### Archetype 4: The Edge-Case User
**Context:** Project doesn't follow exact HBC structure or artifact naming.

**Journey:**
1. Gate evaluates FILE checks with glob patterns
2. Artifact not found (slightly different naming, path structure, etc.)
3. Report says "FAIL: D-02 artifact not found"
4. User doesn't know how to rename/move file, or thinks gate is broken

**Friction points:**
- **Brittle artifact patterns:** Checklist uses `_hbc_output/plan/D-02-*` — if D-02 is in a slightly different path, gate fails silently with no guidance.
- **No fallback search:** Gate doesn't suggest "I looked in X but couldn't find D-02. Check if it's at Y or Z."
- **No path configuration UI:** User has no easy way to tell gate "D-02 is actually at this custom path." Would need to edit customize.toml manually.

**Bright spots:**
- None specific to this archetype

---

## Headless Assessment

**Current level:** **Fundamentally interactive**

The skill is built HITL-only. However, parts are **easily adaptable** to headless:

### Headless-Ready Path
- **Input:** `phase: 2`, `project_root: /path/to/project`, `output_format: json` (optional)
- **Processing:** Same evaluation logic, but return structured data instead of markdown
- **Output:** `{"status": "PASSED|FAILED|WARNING", "phase": 2, "items": [{id, description, status, evidence}], "decision_log_path": "..."}`
- **Changes needed:** 
  1. Document exact parameters in SKILL.md (`##Headless Mode` section)
  2. Add conditional output logic: if `output_format=json`, return structured; else render markdown
  3. Support `skip_confirmation=true` to bypass any phase-confirmation step

### Non-Headless Aspects
- **QUALITY judgment calls** inherently need nuance and user context. A headless invocation can defer these to the human-readable evidence and let the caller decide, or skip QUALITY items.

### Recommendation
Add a **Headless Mode** section to SKILL.md documenting parameter format and JSON return schema. Add conditional logic to return machine-readable format on demand. This would enable CI/pipeline integrations without breaking the interactive flow.

---

## Facilitative Pattern Check

Checking against `skill-quality-principles.md` institutional patterns:

| Pattern | Present? | Notes |
|---------|----------|-------|
| **Open-floor opening** | No | Gate is deterministic, not exploratory. Not applicable. |
| **Soft-gate elicitation** | No | No branching decision points or re-entry prompts. Phase is inferred or asked once. |
| **Intent-before-ingestion** | No | Gate assumes intent is "evaluate this phase" already confirmed by user/context. Not a discovery workflow. |
| **Capture-don't-interrupt** | N/A | Not a multi-turn workflow. |
| **Dual-output** | No | **OPPORTUNITY:** Markdown report + structured JSON/CSV export for analytics (which phases pass/fail over time, trend analysis). |
| **Parallel review lenses** | No | **OPPORTUNITY:** For QUALITY items, could fan out 2-3 subagents (strict auditor, lenient reviewer, domain expert) before finalizing judgment. Currently single LLM evaluation. |
| **Three-mode architecture** | Partial | Interactive HITL only. Guided / Headless paths not implemented. |
| **Graceful degradation** | No | If artifact not found, gate fails. No fallback search, no "use cached result" path. |
| **Decision-Log Workspace** | No | Reports are ephemeral (regenerated each run). Archetype 1 (gatekeeper) would benefit from a persistent log tracking re-evaluations and fix history. |

### Most Valuable to Add

1. **Decision-Log Workspace** (HIGH IMPACT)
   - Gatekeeper needs to see "phase 2 gate was FAILED on 2026-05-24, re-evaluated 2026-05-26, now PASSED." Current report shows only current state.
   - Workspace: `_hbc_output/gates/phase-2-gate.md` (report) + `.decision-log.md` (history) + `addendum.md` (prior failures and fixes).
   - Enables resume protocol: on re-eval, offer to compare against previous run and highlight deltas.

2. **Parallel QUALITY Review Lenses** (MEDIUM IMPACT)
   - QUALITY items rely on single LLM evaluation (current `Be strict — vague or incomplete artifacts fail` note). Fan out 2-3 reviewers (skeptic, domain expert, lenient) in parallel, then consolidate. Prevents single-reviewer bias.
   - Example: P2-08 "every REQ has at least one TC" could use 3 lenses (pessimist flags every borderline TC, optimist accepts reasonable mappings, domain expert decides). Reduces false positives and negatives.

3. **Graceful Degradation + Artifact Search** (MEDIUM IMPACT)
   - When FILE check fails, don't just say "not found." Offer to search nearby directories, suggest alternative names, ask user to provide path.
   - Prevents dead-end user experience (Archetype 4).

---

## Findings

### High-Opportunity Issues

#### 1. **No Re-evaluation Transparency**
**Location:** SKILL.md § "On Activation" and "Evaluate Gate"  
**What:** Gate report is regenerated on each run with no history. If a gate was FAILED on day 1 and PASSED on day 3, gatekeeper sees only the day-3 result. No way to see "we fixed P2-08 and P2-10, still failing on P2-04."

**Concrete suggestion:**  
Implement Decision-Log Workspace pattern:
- Gate report lives at `{workflow.gate_output_path}/phase-{N}-gate.md`
- Decision log at `{workflow.gate_output_path}/phase-{N}-.decision-log.md` (append-only)
- On re-evaluation: read previous report, compare current results against prior, call out which items changed status
- SKILL.md: One sentence per phase: "Compare against prior gate report if present, noting which items improved or regressed."

**Impact:** Gatekeeper can track fix progress without manually comparing two markdown files.

---

#### 2. **No Artifact Discovery for Failed FILE Checks**
**Location:** SKILL.md § "Evaluate Gate" (FILE evaluation logic)  
**What:** When `artifact_pattern` glob fails, report just says "no file found." User has no next step except "try harder to find the file" or guess where it should be.

**Concrete suggestion:**  
Enhance FILE check with optional fallback:
- If primary glob fails, do a broader search: `find {project-root} -name "*D-02*"` or `find {project-root} -path "**/D-02*"`
- If found, offer path(s) and ask "is this the file?" If yes, suggest checklist to re-evaluate
- If not found, suggest: "Missing D-02 (Requirements). Invoke hbc-bmb-setup or suggest the user create it with bmad-create-prd"
- In report evidence: show search path and what was found vs what was expected

**Impact:** Archetype 2 (builder) no longer dead-ends on "file not found." Archetype 4 (non-standard structure) gets a path to recovery.

---

#### 3. **QUALITY Evaluation Has No Parallel Review Guard**
**Location:** SKILL.md § "Evaluate Gate" (QUALITY type)  
**What:** QUALITY items depend on single LLM judgment with note "Be strict — vague or incomplete artifacts fail." Single reviewer can be lenient or harsh depending on mood. No cross-check.

**Concrete suggestion:**  
For high-stakes QUALITY items (those marked `required=yes`), optionally fan out a subagent review:
- Subagent 1 (skeptic): "Find every way this artifact could be incomplete or wrong"
- Subagent 2 (domain expert): "Does this meet the actual HBC standard for this phase?"
- Consolidate: PASS only if both agree, or FAIL if either is skeptical
- Can be gated with a `{workflow.quality_parallel_review}` flag (default: false for speed, true for critical gates)

**Impact:** Reduces single-reviewer bias on QUALITY checks; higher confidence in gate decision.

---

#### 4. **No Headless Mode or Machine-Readable Return**
**Location:** SKILL.md (no headless documentation)  
**What:** Archetype 3 (automator / pipeline agent) cannot invoke gate programmatically. Report is always markdown; no JSON/structured return. Other agents can't parse gate status without text regex.

**Concrete suggestion:**  
Add Headless Mode section to SKILL.md:
```
## Headless Mode

Parameters:
- `phase` (int 1-4): Phase to evaluate. If omitted, inferred from context or ask user.
- `project_root` (path): Explicit project root. If omitted, use current working directory.
- `output_format` (string): `markdown` (default, human-readable) or `json` (structured for automation).
- `skip_phase_confirmation` (bool): If true and phase is explicit, don't confirm. Default false.

JSON output format:
{
  "status": "PASSED|FAILED|WARNING",
  "phase": <int>,
  "gate_mode": "strict|lenient",
  "timestamp": "ISO8601",
  "summary": {
    "total_items": <int>,
    "passed": <int>,
    "failed": <int>,
    "skipped": <int>
  },
  "items": [
    {
      "item_id": "P2-01",
      "description": "...",
      "type": "FILE|CONTENT|METRIC|QUALITY",
      "required": true|false,
      "status": "PASS|FAIL|SKIP",
      "evidence": "..."
    }
  ],
  "report_path": "{workflow.gate_output_path}/phase-{N}-gate.md",
  "decision_log_path": "{workflow.gate_output_path}/phase-{N}-.decision-log.md"
}
```

When `output_format=json`, return JSON only (no markdown). Markdown report still written to disk for audit.

**Impact:** Enables CI/pipeline integration (sprint-planning agent, traceability tracking, cross-phase dependencies) without custom parsing.

---

#### 5. **Silent Phase Inference Can Confuse Uncertain Context**
**Location:** SKILL.md § "On Activation" (Step 5, Phase inference)  
**What:** Logic says "Agent context → infer: BA→1, Architect/QA→2, Dev→3, Tester→4." If invoked from ambiguous context or no explicit agent context, user may not realize which phase was assumed.

**Concrete suggestion:**  
Always confirm (or at least surface) inferred phase:
- If phase is explicit argument → use it silently
- If inferred from agent context → surface it: "Inferred phase 2 (Design) from Architect context. Proceed?" with [yes]/[change] buttons
- If ambiguous or no context → ask: "Which phase to evaluate? 1 (Analysis) / 2 (Design) / 3 (Implementation) / 4 (Testing)"

Avoids accidental gate evaluation of wrong phase.

**Impact:** Prevents silent evaluation of wrong phase; improves trust.

---

### Medium-Opportunity Issues

#### 6. **Checklist Link to Remediation Skills**
**Location:** Assets (phase checklists)  
**What:** Checklist lists failed items but doesn't link to skills that generate them. User sees "missing D-19 (Database Design)" but doesn't know which skill creates it.

**Concrete suggestion:**  
Add optional `skill_to_create` field to checklist items:
```
| P2-01 | D-19 Database Design document exists | FILE | yes | ... | | hbc-create-db-design |
```

When evaluating FILE fails, if `skill_to_create` is present, suggest: "Missing D-19. Create it with `hbc-create-db-design` skill."

**Impact:** Gatekeeper and builder can immediately find the right skill to fix each failure.

---

#### 7. **Evidence Readability for Complex Artifacts**
**Location:** SKILL.md § "Evaluate Gate" (evidence recording)  
**What:** Evidence is free-form text (e.g., "match count: 47"). For CONTENT checks on large files, this is too vague. For QUALITY checks, evidence is descriptive prose but may not show *what* was wrong.

**Concrete suggestion:**  
Enhance evidence format:
- **CONTENT:** Show top 3 matches (excerpt + line number) so reviewer can spot check
- **QUALITY:** Include specific criticisms, not just "artifact incomplete." Example: "P2-08 failed: found 23 requirements (REQ-001 to REQ-023) but only 19 test cases (TC-001 to TC-019). Missing coverage for REQ-002, REQ-015, REQ-021."

**Impact:** Reviewer can diagnose failures faster without re-reading all source artifacts.

---

#### 8. **No Caching or "Skip to Rebuild" Path**
**Location:** SKILL.md (no caching / skip path mentioned)  
**What:** If gate evaluation is expensive (large artifacts, many QUALITY reviews), and user just wants to re-run with fresh artifacts, they have to wait for full re-evaluation. No option to skip QUALITY or use cached results.

**Concrete suggestion:**  
Add optional config flag `{workflow.skip_quality_items}` (default false). If true, skip QUALITY checks and mark as SKIP (not affecting overall status). Useful for fast re-checks after file changes.

**Impact:** Power-user optimization; reduces wait time for repeat runs.

---

### Low-Opportunity Issues

#### 9. **No Revision History in Gate Report Template**
**Location:** assets/gate-report-template.md  
**What:** Template includes "Revision History" section but doesn't show how to populate it. If using Decision-Log Workspace (finding #1), revision history becomes automatic; today it's a dead placeholder.

**Concrete suggestion:**  
Decision-Log Workspace would replace explicit revision history (decision log is the history). On gate report, add one-liner: "See `.decision-log.md` for evaluation history and prior results."

**Impact:** Clarifies where gate history lives; reduces confusion about the placeholder table.

---

#### 10. **Glossary (D-03) Is Checked in Phase 1 But Not Used Later**
**Location:** assets/phase-1-gate-checklist.md (item P1-03)  
**What:** P1-03 checks that D-03 exists, but no later phase validates that design or test documents reference it. It's a orphan requirement.

**Concrete suggestion:**  
Either:
- Remove P1-03 (D-03 optional, not critical to phase progression)
- Or add Phase 2 check: "Design documents reference glossary terms from D-03 when introducing domain concepts"

**Impact:** Removes confusion about why D-03 is required if it's never validated downstream.

---

## Top 2-3 Insights

### Insight 1: **Decision-Log Workspace Is the Gatekeeper's Missing Tool**
The skill is deterministic and reproducible, but gatekeepers need to *understand change over time*. A persistent workspace with append-only decision log transforms the gate from "pass/fail snapshot" to "traceable progression record." This single addition would enable gatekeeper-friendly resume, delta visibility, and audit trail — and is reusable across other HBC workflows.

### Insight 2: **Artifact Discovery, Not Just Existence Checking**
The skill's brittle FILE checks (exact glob patterns) create a common dead-end for Archetype 2 (builder) and Archetype 4 (edge-case user). Adding fallback search, path suggestions, and skill linkage would lower friction by 80% without adding complexity. Most failures would suggest a remediation path instead of a dead-end.

### Insight 3: **Headless + JSON Returns Enable Cross-Skill Integration**
Today, gate is siloed: humans read reports, other agents can't parse results. Structured JSON output with explicit input/output contracts would enable pipeline integration (CI checks, sprint-planning orchestration, traceability dashboards) without breaking the interactive flow. Three-mode architecture (Guided / Headless / Markdown) is a low-cost unlock for ecosystem integration.

---

## Summary

**hbc-phase-gate** is a solid, deterministic engine. Its weaknesses are surface-layer (UX, integration, transparency) rather than structural:

- **Add Decision-Log Workspace** to give gatekeepers progression visibility (HIGH IMPACT, medium effort)
- **Add artifact search & fallback** to prevent dead-ends for non-standard projects (HIGH IMPACT, low effort)
- **Add JSON headless mode** to enable cross-skill integration (MEDIUM IMPACT, low-medium effort)
- **Enhance evidence reporting** for complex artifacts (MEDIUM IMPACT, low effort)
- **Optional: parallel QUALITY review** to reduce single-reviewer bias (MEDIUM IMPACT, medium effort)

Each finding is a small, self-contained addition. No architectural rework needed.
