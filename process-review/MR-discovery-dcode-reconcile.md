# MR — feat(hbc): trục B + discovery-spike + D-code reconcile + P1-11

**Source → Target:** `feat/hbc-discovery-dcode-reconcile` → `main`
**Tạo MR:** https://git.hblab.vn/stc/erp/stc-erp-bmad-custom/-/merge_requests/new?merge_request%5Bsource_branch%5D=feat%2Fhbc-discovery-dcode-reconcile
**Quy mô:** 77 files, +4882/−67 · 3 commit (`0166e2a` mermaid-fix · `d0ad83f` trục B · `dcd6690` discovery + reconcile + P1-11 + docs)

> ℹ️ Nhánh này **chứa luôn** commit trục-B (`d0ad83f`) và mermaid-fix (`0166e2a`) → MR này **gộp** và có thể thay cho các MR lẻ của các nhánh đó (đóng chúng nếu đang mở).

---

## Title (dán vào GitLab)
```
feat(hbc): trục B framework + discovery-spike [DSC] + D-code reconcile + gate P1-11
```

## Tóm tắt
Hoàn thiện **khung framework HBC** (trục B của mô hình 3 trục) + bổ sung **chốt kiểm chứng model** vá đúng lỗi gốc RCA, kèm tài liệu song ngữ. Gồm:
1. **Trục B** — thêm các tầng/deliverable còn thiếu: D-09 Architecture, D-16 Behavioral, D-14 UX + applicability-catalog + adapter-registry + folds (D-01→D-02, use-case→D-06) + gate P1-09 model-validation. *(commit d0ad83f)*
2. **D-code reconcile** — căn HBC về numbering canonical HBLAB (`templates/`): Architecture **D-08→D-09**, Behavioral **D-17→D-16** (giải phóng D-08/D-17 cho nghĩa canonical Basic Design / Sequence Diagram).
3. **IMP-10** — skill mới `hbc-discovery-spike` `[DSC]`: kiểm chứng rẻ giả định model rủi ro nhất so với ground-truth TRƯỚC khi thiết kế.
4. **IMP-09** — risk-classifier `discovery_risk` + gate **P1-11** (uncertain → bắt buộc discovery-note VALIDATED đã ký).

## Vì sao
RCA case `resource-plan-billable`: domain model bị "gate PASSED" trước khi kiểm chứng → khi model đổi, phải viết-lại-tại-chỗ toàn bộ stack (D-02 13 version…). MR này vá tầng kiểm-chứng-model (DSC + P1-09 + P1-11), bổ sung các tầng thiết kế còn thiếu, và căn lại numbering D cho nhất quán với bộ chuẩn HBLAB.

## Thay đổi chính

**Trục B (d0ad83f):** 3 skill mới (architecture/behavioral/ux) + `deliverable-catalog.yaml` (facet + maturity) + `adapter-registry.yaml` (không hardcode framework) + folds + gate P1-09 + 5 agent + đăng ký.

**D-code reconcile:** rename 2 template (`D-09_architecture-design_template.md`, `D-16_behavioral-design_template.md`); sweep có-ngữ-cảnh D-08→D-09 / D-17→D-16 trên src+docs+README (giữ nguyên D-17=sequence ở er-diagram off-ramp); ghi `process-review/hbc-dcode-reconcile-2026-06-21.md`.

**IMP-10 `hbc-discovery-spike` `[DSC]`** (Phase 1, per-feature, conditional `discovery_risk=uncertain`): full anatomy (SKILL + customize + template + validator structure-only + 9 pytest + headless-contract). Verdict **VALIDATED/RESHAPE/KILL** + **USER sign-off bắt buộc** (LLM không tự chứng nhận); validate vào **ground-truth** (code/DB/flow thật · ví dụ stakeholder), không vào bản nháp. Deliverable **non-mã-D** `discovery-note`. Đăng ký 3 nơi (v2.2.0, 20 workflows).

**IMP-09 risk-classifier + P1-11:** field `discovery_risk: known|uncertain` ở frontmatter D-02 (BA gợi ý, USER chốt); gate Phase-1 item **P1-11** (must-tier): uncertain → đòi discovery-note VALIDATED đã ký; RESHAPE/KILL/thiếu → FAIL; known/vắng → N/A. Pair với P1-09.

**Docs:** song ngữ (VI canonical + EN mirror) cho toàn bộ deliverable-set trục B, reconcile, và DSC/P1-11/discovery_risk — reference + tutorial + how-to + explanation + MAINTAINING + README.

## Kiểm thử
- pytest toàn repo: **331 passed, 1 skipped**
- `bmad-module-builder` validate-module: **0 findings**
- doc-check: links + anchors resolve (32 file) · **24 mermaid block parse**
- skill mới: token SKILL.md 1857 ≤ 3000 · path-standards clean · template trống fail đúng (chứng minh anti-false-green)

## Ngoài phạm vi (backlog)
- **Trục A** (enforcement bằng máy): gate scoring engine + Recycle state-machine + 100%-rule coverage + v_pair edges + WIP — gated bởi **spike kernel** (`process-review/hbc-improvement-spec-2026-06-21.md` Wave 2).
- Các item Wave 1 còn lại (vertical-slice task catalog, constitution.md, Quick-Plan/bugfix lane…) — đợt riêng.
- `_bmad-output/` (research doc + dogfood) **không** commit (generated).

## Rủi ro & rollback
- Skill mới + D-09/D-16 đều **conditional theo facet/discovery_risk** → feature không dính facet/known → N/A, không ảnh hưởng luồng hiện hữu.
- Reconcile là rename + sweep token có-ngữ-cảnh (er-diagram D-17=sequence giữ nguyên); validator cũ pass. Rollback = revert commit.

## Lưu ý sau merge
Runtime nạp từ `.claude/skills/` → **re-install** để đồng bộ `src/` (mã D mới + skill DSC):
`npx bmad-method install --directory . --yes --action update --custom-source --next hbc --modules <modules-đang-cài>`

## Checklist
- [x] pytest xanh (331) · [x] module-validate 0 · [x] doc-check xanh · [x] đăng ký 3 nơi · [x] source English · [x] reconcile theo canonical HBLAB
- [ ] đóng MR lẻ của nhánh trục-B/mermaid nếu đang mở (MR này đã gộp)
- [ ] re-install sau merge để đồng bộ runtime
