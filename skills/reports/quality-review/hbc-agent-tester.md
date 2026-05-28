---
skill: hbc-agent-tester
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-agent-tester

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 86 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [~] Description format
- [x] Conventions block (4 canonical lines)
- [x] customize.toml required fields
- [x] Path references ({workflow.*} not hardcoded)
- [x] Size within guidance (86 lines, single-purpose agent)
- [x] Outcome-based instructions
- [x] Intelligence placement correct
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented
- [x] Lint clean

## Findings

### Minor: Description format (LOW)
Description is: `"Phase 4 Testing coordinator for HBC waterfall lifecycle. Use when user says 'tester', 'kiểm thử viên', 'テスター', 'giai đoạn 4', or agent menu [Tester]."`

The first sentence is 8 words -- at the top end of guidance. Acceptable but the description could be tighter. Format otherwise matches: summary sentence + trigger phrase sentence with quoted triggers.

### Note: Agent-type skill uses [agent] block, not [workflow]
This is an agent coordinator skill, so it correctly uses `[agent]` in customize.toml instead of `[workflow]`. The three required fields (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`) are all present. The `agent` block also includes `menu`, `role`, `identity`, `communication_style`, and `principles` -- well-structured.

### Note: Script fallback documented
Line 66-70: If `scan-phase4-state.py` is unavailable, the SKILL.md documents a manual fallback. Good resilience pattern.

## Recommendations

1. Consider tightening the first sentence of the description: e.g., `"Phase 4 Testing coordinator for HBC waterfall."` (6 words).
