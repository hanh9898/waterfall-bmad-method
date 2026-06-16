# Extension Opt-In Questions

Các extension sau được phát hiện trong workflow. Vui lòng quyết định enforce hay skip cho project này.

## Question: Security Extensions
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)
B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
X) Other (please describe after [Answer]: tag below)

**[AI Suggestion]: B** — hbc-sync là internal developer tooling (orchestration logic), không xử lý external data, không có authentication/network, không lưu user data. Security baseline ít áp dụng. Tuy nhiên nếu bạn muốn áp dụng secure coding cho scripts (input validation, path sanitization) thì chọn A.

[Answer]: 

## Question: Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components)
B) Partial — enforce PBT rules only for pure functions and serialization round-trips (suitable for projects with limited algorithmic complexity)
C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers with no significant business logic)
X) Other (please describe after [Answer]: tag below)

**[AI Suggestion]: B** — hbc-sync có một số logic đáng test bằng PBT: dependency graph traversal (topological sort phải không có cycle), state serialization round-trip (.sync-state.json), impact analysis (affected set phải đóng dưới quan hệ dependency). Partial PBT cho các pure function này là hợp lý mà không quá nặng.

[Answer]: 

