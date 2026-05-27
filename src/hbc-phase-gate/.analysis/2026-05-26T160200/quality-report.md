# Quality Report: hbc-phase-gate

**Date:** 2026-05-26  
**Grade:** B  

---

## Executive Summary

**hbc-phase-gate** earns a **B** -- a solid, well-architected phase-gate validation engine with strong structural integrity, clean customization surface, and tight promises-vs-behavior alignment. The skill is downgraded from A by two broken items (misplaced decision-log file, unwired on_complete hook) and meaningful opportunities in deterministic scripting, re-evaluation transparency, and headless integration that would elevate it to production-grade. All identified gaps are additive improvements requiring no architectural rework.

---

## Broken Items

### B1: Decision-log file at skill root instead of references/ [HIGH]

Path standards scanner flagged `.decision-log.md` at skill root. BMad conventions require all progressive-disclosure content except SKILL.md to live in `references/`.

**Fix:** Move `.decision-log.md` to `references/.decision-log.md` and update any internal references.

### B2: on_complete hook declared but not wired [HIGH]

`customize.toml` declares an `on_complete` hook and SKILL.md references `{workflow.on_complete}` in the On Complete section, but no execution step actually invokes the hook. The field is a dead placeholder that will silently do nothing if teams override it.

**Fix:** Either add an execution step in the On Complete section that runs the hook script (documenting the contract: available args/env), or remove the field from `customize.toml` to avoid confusion.

---

## Opportunities

### Determinism

| ID | Title | Impact |
|----|-------|--------|
| O1 | Script-based FILE/CONTENT/METRIC evaluation | High |
| O7 | Enhanced evidence reporting for complex artifacts | Medium |
| O8 | Parallel QUALITY review lenses | Low |

**O1** is the highest-value opportunity: FILE and CONTENT checks are deterministic (glob, regex) but currently performed by the LLM inline. A Python script would save ~1,000-1,750 tokens per gate invocation (~2.4-4.2M tokens/year at scale) and improve reliability. **O7** improves evidence granularity (top 3 matches with line numbers for CONTENT; specific criticisms for QUALITY). **O8** addresses single-reviewer bias on QUALITY items via optional parallel subagent review.

### User Experience

| ID | Title | Impact |
|----|-------|--------|
| O2 | Decision-Log Workspace for re-evaluation transparency | High |
| O4 | Artifact discovery for failed FILE checks | Medium |
| O5 | Explicit phase inference confirmation | Medium |
| O6 | Remediation skill links in checklist items | Medium |

**O2** is the gatekeeper's missing tool: gate reports are regenerated each run with no history, so reviewers cannot track fix progress or see deltas between evaluations. **O4** prevents dead-ends when artifact globs fail by offering fallback search and alternative path suggestions. **O5** surfaces inferred phase for confirmation to avoid accidental wrong-phase evaluation. **O6** links failed checklist items to the skills that create the missing artifacts.

### Integration

| ID | Title | Impact |
|----|-------|--------|
| O3 | Headless mode with JSON output | High |

**O3** enables CI/pipeline and cross-skill integration by providing structured JSON output alongside the human-readable markdown report. Currently, other agents must regex-parse markdown to extract gate status.

### Customization

| ID | Title | Impact |
|----|-------|--------|
| O9 | gate_mode not exposed in customize.toml | Low |
| O10 | Phase checklist override discoverability | Low |

**O9** and **O10** are documentation improvements: explain why `gate_mode` is excluded from the customization surface, and add a comment clarifying how phase skills can override checklist paths.

---

## Strengths

1. **Scalable four-tier evaluation schema** -- FILE, CONTENT, METRIC, and QUALITY types cover the full spectrum from deterministic to judgment-based, each with specific evidence requirements.

2. **Configuration-driven, not hardcoded** -- Phase checklists, output paths, and hooks resolve from customize.toml, enabling downstream overrides without modifying SKILL.md.

3. **Tight promises-vs-behavior alignment** -- Every claim in the Overview (strict reviewer, evidence-based, gate_mode controls) is enforced in execution steps. Architecture analysis found zero gaps.

4. **Compact, focused prompt** -- 82 lines / 1,158 tokens with no waste patterns, no pedagogical padding, and direct imperatives throughout.

5. **Clean customization surface** -- Six scalars and three arrays proportionate to scope. No abuse patterns. Clear field semantics and proper path resolution.

6. **Correct intelligence placement design** -- Decision log explicitly documents deterministic vs. judgment classification, mapping perfectly to the "script where possible, LLM where needed" principle.

---

## Recommendations (Priority Order)

1. Move `.decision-log.md` to `references/.decision-log.md` to fix the path-standards violation
2. Wire or remove the `on_complete` hook -- add execution logic or delete the dangling field
3. Implement deterministic FILE/CONTENT/METRIC evaluation script (~1,000-1,750 tokens saved per gate)
4. Add Decision-Log Workspace pattern for re-evaluation delta visibility and audit trail
5. Add Headless Mode section with JSON output schema for CI/pipeline integration
6. Enhance FILE check failures with fallback search and remediation skill suggestions
7. Surface inferred phase to user for confirmation when not explicitly provided
8. Add `skill_to_create` column to checklist items linking failures to generating skills
9. Improve evidence detail for CONTENT and QUALITY checks
10. Document `gate_mode` exclusion rationale and override mechanism in customize.toml comments

---

## Pre-pass Notes

- **Workflow integrity prepass** flagged a missing stage `1-gate-checklist.md` (critical). Architecture analysis investigated and determined this is a **false positive**: SKILL.md references `{workflow.phase_1_checklist}` which resolves via customize.toml to `assets/phase-1-gate-checklist.md`, which exists. The prepass scanner used naive filename matching and did not respect variable resolution.
- **Scripts prepass** passed (no scripts directory -- expected for MVP).
- **Execution deps prepass** passed (no cycles, no redundancies).
- **Prompt metrics prepass** reported healthy metrics: 82 lines, 1,158 tokens, zero waste patterns, zero back-references.
