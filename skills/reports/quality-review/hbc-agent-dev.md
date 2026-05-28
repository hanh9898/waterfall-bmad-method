---
skill: hbc-agent-dev
reviewed_at: "2026-05-28"
verdict: NEEDS_WORK
---

# Quality Review: hbc-agent-dev

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 80 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **NEEDS_WORK** |

## Checklist
- [x] Description format
- [x] Conventions block (4 canonical lines)
- [x] customize.toml required fields
- [x] Path references ({workflow.*} not hardcoded)
- [~] Size within guidance (80 lines — underdeveloped for agent)
- [ ] Outcome-based instructions — several sections too sparse
- [x] Intelligence placement correct
- [~] Core test passes — missing specifics the LLM needs
- [x] Headless mode documented
- [x] Lint clean

## Findings

### HIGH: Scan Implementation State section thieu scan script va fallback

Line 66: "Load `task-breakdown.md` from the configured path."

- **Khong co scan script** trong `scripts/` directory (trong khi hbc-agent-ba, hbc-agent-architect, hbc-agent-qa deu co).
- **Khong co fallback instructions** khi script khong available.
- **Khong co configured path** cho task-breakdown.md trong customize.toml — chi co `output_path` chung.
- Thu muc `scripts/` chi chua `tests/` (rong).

Cac agent khac (ba, architect, qa) deu co pattern: run script → fallback manual check. hbc-agent-dev thieu ca hai.

### HIGH: Embody Persona section qua sparse

Line 58: "Adopt the Developer identity from the Overview, layered with `{agent.role}`, `{agent.identity}`, `{agent.communication_style}`, and `{agent.principles}`. Load persistent facts and config."

So voi hbc-agent-ba (lines 59-61) va hbc-agent-architect (lines 59-61) co day du instructions ve:
- Execute `{agent.activation_steps_prepend}`
- Load `persistent_facts` voi glob handling
- Load config.yaml va config.user.yaml
- Resolve `{user_name}` va `{communication_language}`

hbc-agent-dev gom tat ca thanh 1 cau "Load persistent facts and config." — khong du chi tiet de LLM biet load gi, tu dau, xu ly loi the nao.

### MEDIUM: Greet section thieu detail so voi cac agent khac

Line 70-72 chi co 3 dong greet instructions. Cac agent khac co:
- If user's initial message maps to menu item → skip menu and dispatch
- If substantive context → absorb before menu
- Surface timestamps va offer resume/start fresh
- Flag staleness

hbc-agent-dev khong co bat ky feature nao trong so nay.

### MEDIUM: Menu Dispatch section thieu context capsule passing

Line 76: "When dispatching [IM], pass the next TODO task ID."

Cac agent khac (ba, architect, qa) deu co instructions ve context capsule — read predecessor content va pass digest. hbc-agent-dev chi pass task ID, khong co D-12 coding standards context, D-19 database schema, hay D-27 test spec context.

### MEDIUM: Khong co tests

`tests/` directory rong. Cac agent khac deu co test suite cho scan scripts.

### LOW: Khong co references/ directory

Cac agent khac co references/ chua headless contract va/hoac decision log. hbc-agent-dev khong co.

## Recommendations

1. **Tao scan script** `scripts/scan-impl-state.py` — scan task-breakdown.md, count tasks by status, return JSON tuong tu cac agent khac. Them fallback instructions trong SKILL.md.
2. **Them `task_breakdown_path`** vao customize.toml — de team co the override vi tri cua task-breakdown.md.
3. **Expand Embody Persona section** — them full activation flow: activation_steps_prepend, persistent_facts glob handling, config.yaml loading, user_name/communication_language resolution.
4. **Expand Greet section** — them: initial intent dispatch, context absorption, timestamp surfacing, staleness flagging, resume/fresh offer.
5. **Them context capsule instructions** trong Menu Dispatch — khi dispatch [IM], pass D-12 coding standards summary va D-27 test spec cho task hien tai.
6. **Viet tests** cho scan script sau khi tao.
7. **Tao references/ directory** voi decision-log neu can.

Estimated effort: phat trien them ~20-30 dong SKILL.md + tao scan script + tests.
