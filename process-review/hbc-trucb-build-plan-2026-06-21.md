---
title: "Build Plan — HBC Trục B (Framework Structure)"
doc_type: implementation-plan
date: "2026-06-21"
owner: "HanhNT2"
feature: "hbc-framework-augmentation"
basis:
  - "process-review/hbc-buildgraph-redesign-2026-06-21.md (§10 execution map)"
  - "_bmad-output/features/hbc-framework-augmentation/planning-artifacts/D-02-hbc-framework-augmentation.md (16 REQ-HFA)"
  - "CLAUDE.md §Developing a skill"
  - "bmad-technical-research: implementation-plan / incremental-delivery / spike best practices (2026-06-21)"
method: "Foundation-thin → tracer-bullet → scale → integrate; spike-gated trục A"
---

# Build Plan — HBC Trục B

> Plan để **thực thi trục B** (khung framework: 3 skill mới + catalog + adapter-registry + folds + tích hợp agent). **Trục A (enforcement bằng máy) = backlog** (spike-gated). Plan giữ *gọn & linh hoạt* — không cứng hóa chi tiết (chống anti-pattern over-detail).

## 1. Objective & Scope

**Objective:** HBC có đủ *khung* (tầng/deliverable/catalog) để vận hành lifecycle tái thiết — mỗi skill chỉn chu tối thiểu, framework-agnostic, elicitation-discipline (trục C).

**In-scope (16 REQ-HFA):** 3 skill mới (D-08/D-17/D-14) · applicability-catalog · adapter-registry · 2 fold · model-validation gate-item · 5 agent update · maturity flag.

**Out-of-scope (backlog — chống creep):** enforcement trục A (matrix-as-view · reconcile machine-floor · gate two-stage · code_ref-coverage · visual-regression) · spike kernel · 4 item ST-4 (D-19-3tier/D-26-technique/task-breakdown-vertical-slice/mandatory-review). *(Nguồn: D-02 §2.2.)*

## 2. Success Metrics (nêu trước)

- 3 skill mới chạy được trên input thật + qua Analyze (token-budget ≤3000, lint sạch).
- 16/16 REQ-HFA có `design_ref`/`code_ref`/`test_ref` trong matrix khi xong (hiện 0).
- Mỗi skill: validator PASS + pytest xanh + semanticReview passed + đăng ký đủ 3 file.
- 0 literal framework-specific trong core (ngoài adapter-registry).
- Dogfood: feature `hbc-framework-augmentation` chạy hết Phase 2 bằng chính skill mới.

## 3. Work Breakdown + Dependency Graph

```
B0 (foundation-thin) ──┬──> B1 folds ──────────────┐
   catalog schema      │                            ├──> B3 integrate
   adapter-registry    ├──> B2 skills (vertical)    │     (agents · maturity ·
   register mechanism  │     D-08 → D-17 → D-14      │      model-validation item)
                       │                            │
                       └──> (mỗi skill khai catalog entry + adapter qua B0)
BACKLOG (spike-gated): trục A enforcement · spike kernel
```
- **B0 là foundation "predictive"** (hạ tầng ổn định, làm đủ-tối-thiểu trước). Skills/folds đi **vertical-slice incremental** trên nền đó.
- Phụ thuộc: B1, B2 cần B0 (catalog để đăng ký entry; adapter-registry để khai reconcile-seam — dù chưa enforce). B3 cần B2.

## 4. Sequencing (foundation-thin → tracer-bullet → scale)

Không foundation-first cực đoan (chống horizontal). Thứ tự:

- **M0 — B0 tối thiểu:** chỉ đủ để đăng ký 1 skill (catalog schema + 1 entry mẫu + adapter-registry stub + reference adapter CSS-vars). KHÔNG build trọn catalog ngay.
- **M1 — Tracer-bullet (1 skill end-to-end):** xây **`hbc-create-architecture` (D-08)** trọn vẹn qua *toàn bộ* DoD (anatomy → validator → tests → đăng ký → semantic-review → dogfood). Lát mỏng kept-not-throwaway — *validate cả quy trình authoring + tích hợp catalog/adapter trước khi nhân ra*.
- **M2 — Scale:** xây `hbc-create-behavioral-design` (D-17) + `hbc-create-ux` (D-14) + 2 fold, theo pattern M1 đã chứng minh. Hoàn thiện catalog đủ entry.
- **M3 — Integrate:** model-validation gate-item · maturity flag · cập nhật 5 agent điều phối.
- **Backlog:** spike kernel (walking-skeleton trục A) → nếu xác nhận 5/5, mở enforcement.

## 5. Milestones & Exit-criteria

| Milestone | Exit-criteria |
|---|---|
| **M0** B0-min | catalog YAML parse được + 1 entry mẫu; adapter-registry có structure + 1 reference adapter; cơ chế đăng ký (3 file) thông |
| **M1** tracer D-08 | `hbc-create-architecture` qua đủ DoD §6; dogfood sinh được D-08 cho 1 REQ thật; Analyze lint sạch |
| **M2** scale | D-17 + D-14 + 2 fold qua DoD; catalog đủ entry cho mọi D-node; pytest toàn repo xanh |
| **M3** integrate | 5 agent điều phối bước mới; maturity flag đọc được; model-validation item có trong gate P1 |

## 6. Definition-of-Done mỗi work-item (skill)

Một skill DONE khi (theo CLAUDE.md §Developing a skill):
1. SKILL.md ≤3000 tokens, lean, stages testable; frontmatter name+description(trigger).
2. customize.toml (nếu cần override) — ref `{workflow.*}`, không hardcode-no-op.
3. scripts/ structure-only + JSON-stdout; **pytest** `scripts/tests/test_*.py` xanh.
4. Đăng ký đủ **3 file**: marketplace.json · module.yaml · module-help.csv.
5. semanticReview frontmatter `passed` (openFacets rỗng).
6. **Dogfood:** chạy trên ≥1 input thật (REQ của feature này) ra artifact hợp lệ.
7. Source English; output theo `{document_output_language}`; framework-agnostic (adapter, 0 literal).

## 7. Risk Register + Spike placement

| Risk | Mức | Mitigation |
|---|---|---|
| Quy trình authoring chưa kiểm chứng → 3 skill lệch chuẩn | TB | **M1 tracer-bullet** 1 skill trước khi nhân ra (front-load) |
| Catalog/adapter shape sai khi gặp skill thật | TB | B0 *tối thiểu* + sửa qua M1 trước khi hoàn thiện ở M2 |
| Build trục B mà kernel (trục A) chưa chứng minh → enforcement sau không khớp | TB | Khai sẵn reconcile-seam/hook trong catalog (data, chưa enforce); **spike kernel** trước khi build enforcement |
| Skill mới hardcode framework (Odoo) | Cao nếu lơ là | DoD §7: 0 literal + adapter-registry; review mỗi skill |
| Scope creep (kéo trục A/ST-4 vào) | TB | Out-of-scope §1 tường minh; gate mỗi milestone |

**Spike (de-risk, đúng F-3/F-4):** build-graph kernel spike trên `resource-plan-billable` là *throwaway experiment* validate giả thuyết trục A — **chỉ chạy trước khi đầu tư enforcement**, KHÔNG chặn trục B.

## 8. Anti-pattern đã tránh (theo research)

- ❌ Big-bang (xây cả 3 skill + enforcement cùng lúc) → ✅ tracer-bullet rồi scale.
- ❌ Horizontal/foundation-first cực đoan (build trọn catalog/adapter trước khi có skill nào) → ✅ B0-tối-thiểu + vertical-slice.
- ❌ Plan cứng/quá chi tiết → ✅ milestone + exit-criteria, chi tiết để mở.
- ❌ Thiếu DoD → ✅ DoD §6 rõ per-skill.
- ❌ Để rủi ro tích hợp tới cuối → ✅ M1 dogfood end-to-end sớm.

## 9. Bước kế tiếp ngay

**M0 + M1**: dựng B0-tối-thiểu rồi tracer-bullet `hbc-create-architecture` (D-08) qua bmad-workflow-builder (Build intent) theo CLAUDE.md.

<!-- END -->
