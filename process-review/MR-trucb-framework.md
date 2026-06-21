# MR — feat(hbc): trục B framework

**Title:**
feat(hbc): trục B — bổ sung khung framework (D-08/D-17/D-14 + catalog + adapter-registry + folds)

**Source → Target:** `feat/hbc-trucb-framework` → `main`

---

## Tóm tắt
Bổ sung **khung (framework structure — "trục B")** của HBC: thêm các tầng/deliverable còn thiếu mà RCA case `resource-plan-billable` phơi bày, theo `process-review/hbc-buildgraph-redesign-2026-06-21.md` (mô hình 3 trục) + `process-review/hbc-trucb-build-plan-2026-06-21.md`. Đây là phần *cấu trúc/format/elicitation*; phần *enforcement bằng máy* (trục A — build-graph kernel) để **backlog**, gated bởi spike.

## Vì sao
RCA: domain model bị "gate PASSED" trước khi kiểm chứng; thiếu tầng kiểm-chứng-model, thiết-kế-hành-vi, kiến-trúc, UX, và catalog deliverable canonical. MR này vá các lỗ hổng tầng đó.

## Thay đổi chính
**3 skill MỚI** (full anatomy: SKILL.md + customize.toml + template + validator structure-only + pytest + headless-contract):
- `hbc-create-architecture` — D-08 `[AD]` (conditional: has-integration/has-algorithm)
- `hbc-create-behavioral-design` — D-17 `[BD]` (conditional: facet phi-CRUD; 4 block ST/DR/INV/SEQ + element-ID)
- `hbc-create-ux` — D-14 `[UX]` (conditional: has-ui; Claude Design optional + DESIGN.md token)

**B0 nền** (`src/hbc-shared/references/`): `deliverable-catalog.yaml` (catalog + facet + maturity) · `adapter-registry.yaml` (token→style·entity·component; không hardcode framework).

**Folds:** D-01 overview → header D-02; use-case + BPMN swimlane + path-ID → D-06.

**Integrate:** gate item **P1-09** model-validation (USER sign-off, greenfield-adaptive); `maturity`+`facets` ở D-02 frontmatter; 5 agent (architect menu AD/BD/UX; BA/QA/Dev/Tester notes).

**Tests:** +pytest cho 4 skill cũ (api-spec/coding-standards/test-plan/test-spec) → 11/11 create-skill có test.

**Registration + docs:** marketplace.json + module.yaml + module-help.csv (v2.1.0, 19 workflows) + hbc-shared LIB; CLAUDE.md §Developing-a-skill; process-review/.

## Kiểm thử
- pytest toàn repo: **322 passed, 1 skipped**
- module-builder validate: **0 findings**
- 3 SKILL.md mới: frontmatter hợp lệ; token 1481/1382/1403 ≤ 3000
- Validator mới: structure-only + hbc_validation bootstrap + JSON-stdout + honest verdict

## Ngoài phạm vi (backlog)
- Enforcement trục A (matrix-as-view, reconcile machine-floor, gate two-stage, code_ref-coverage, visual-regression) → chờ spike kernel.
- Nâng-chuẩn ST-4 (D-19 3-tier, D-26 technique-per-scope, task-breakdown vertical-slice, mandatory review) → đợt riêng.

## Rủi ro & rollback
- Skill mới conditional (applicability-catalog) — feature không có facet → N/A, không ảnh hưởng luồng hiện hữu.
- Chủ yếu thêm-mới + guidance/template; validator cũ không đổi. Rollback = revert commit.

## Lưu ý sau merge
Runtime nạp từ `.claude/skills/` → cần re-install đồng bộ `src/`:
`npx bmad-method install --directory . --yes --action update --custom-source --next hbc --modules <modules-đang-cài>`

## Ghi chú
Nhánh base từ HEAD → diff cũng gồm commit `0166e2a` (fix mermaid `;`) nếu chưa merge riêng.

## Checklist
- [x] pytest xanh (322) · [x] module-validate 0 · [x] token ≤3000 · [x] đăng ký 3 nơi · [x] source English
- [ ] re-install sau merge để đồng bộ runtime
