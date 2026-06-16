# Business Overview

## Business Description
HBLAB BMad Custom (`hbc`) là một **expansion module** cho BMad Method, triển khai một lifecycle phát triển phần mềm theo mô hình **Waterfall + TDD**. Hệ thống hướng dẫn team đi qua 4 phase, sinh ra các deliverable D-xx, với phase gate và traceability đầy đủ từ requirement đến test.

## Business Transactions
| Transaction | Mô tả |
|-------------|-------|
| Phase 1 — Analysis | Elicit requirements (D-02), glossary (D-03), business flow (D-06) |
| Phase 2 — Design | Database design (D-19), coding standards (D-12), API spec (D-21), test plan (D-26), test spec (D-27) |
| Phase 3 — Implementation | Task breakdown + TDD implementation (RED-GREEN-REFACTOR) |
| Phase 4 — Testing | Test execution, defect triage, acceptance decision |
| Cross-cutting — Phase Gate | Validate completeness mỗi phase boundary |
| Cross-cutting — Traceability | Living matrix: req → design → code → test → gate |

## Business Dictionary
- **D-xx**: Deliverable document có số định danh (D-02 = Requirements, D-27 = Test Spec, v.v.)
- **REQ-xxx / TC-xxx**: Unique IDs cho requirement / test case — nền tảng của traceability
- **Phase Gate**: Cổng kiểm tra strict/lenient giữa các phase
- **Facet-split discipline / "seam"**: Nguyên tắc đảm bảo mỗi facet (read/write, api/admin, lifecycle) của requirement đều được design + test, không để rơi vào khe hở
- **Lớp 2 (Semantic Review)**: Tầng review ngữ nghĩa do LLM/người thực hiện (máy lo cấu trúc, người lo ngữ nghĩa)
- **Distillate**: File JSON tóm tắt document cho downstream consumption

## Component Level Business Descriptions

### 5 Coordinator Agents
- **BA (Business Analyst)**: Điều phối Phase 1
- **ARCH (Architect)**: Điều phối Phase 2 Design
- **QA (QA Engineer)**: Điều phối Phase 2 Test Design
- **DEV (Developer)**: Điều phối Phase 3
- **TST (Tester)**: Điều phối Phase 4

### Cross-cutting Skills
- **Phase Gate**: Quality gate engine
- **Traceability**: Single source of truth cho coverage
- **Check Implementation Readiness**: Seam-catching gate reconcile D-02 ↔ downstream
