# Code Quality Assessment

## Test Coverage
- **Overall**: Fair — không có visible unit test cho Python scripts trong source tree
- **`.pytest_cache/`** tồn tại ở root → pytest đã chạy, có thể có test ngoài source hoặc trong CI
- **Validation logic**: mỗi skill có validation script (deterministic) + LLM semantic review layer — đây là "test" chính của output documents
- **Skill self-validation**: create skills có mode `validate` để check output

## Code Quality Indicators
- **Consistency**: Cao — mọi skill theo cùng pattern (frontmatter, conventions, 5-stage, headless contract, customize.toml)
- **Documentation**: Tốt — SKILL.md rất chi tiết, có conventions section, language rules
- **Separation of concerns**: Rõ — máy (script) lo cấu trúc, người/LLM lo ngữ nghĩa (honest verdict pattern)
- **Config flexibility**: Cao — 3-layer override không phá skill gốc

## Good Patterns
- **Honest verdict** — tách biệt structural vs semantic, không cho phép false-positive "passed"
- **Headless contract với closed-set blocked reasons** — automation-friendly, predictable
- **Scan/resume state** — chịu được compaction, resume mid-stage
- **Shared lib single source of truth** — tránh duplicate parsing logic
- **Language-aware (no hardcoded language)** — i18n từ thiết kế

## Anti-patterns / Risks
- **Không có visible automated test cho scripts** — refactor scripts có rủi ro
- **Coupling ngầm giữa skills qua document paths** — nếu đổi output path convention, nhiều skill ảnh hưởng
- **Manual sync hiện tại** — chính là gap mà hbc-sync giải quyết: thay đổi upstream không tự propagate

## Findings Relevant to hbc-sync
1. **Dependency thực tế là DAG, không phải tree** — D-27 (parents: D-26, D-02), task-breakdown (parents: D-19, D-27) có nhiều parents. → **Cần điều chỉnh Application Design** từ "tree" sang "DAG with shared nodes".
2. **Mọi skill đã có mode `update` + `--headless`** — foundation sẵn sàng cho cascade orchestration.
3. **Headless contract đã chuẩn hóa** — hbc-sync có thể parse JSON return `{status, reason}` để biết skill thành công/blocked.
4. **`.decision-log.md` + frontmatter `updated`** — nguồn cho ChangeDetector auto-detect.
5. **Pattern `on_complete` hook** (thấy ở phase-gate) — có thể tái dùng cho auto-chain trigger (REQ-005).
