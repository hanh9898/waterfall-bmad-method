# Code Structure

## Build System
- **Type**: npm (metadata only) + Python 3.10+ (scripts)
- **Configuration**: `package.json` (module metadata), `src/module.yaml` (BMad module manifest), per-skill `customize.toml`
- **Install**: `npx bmad-method install` (tương tác — an toàn) hoặc non-interactive kèm `--modules` để không gỡ module khác: `npx bmad-method install --directory . --modules bmm,bmb --custom-source <git> --tools claude-code --yes` → skills cài vào `.claude/skills/hbc-*/`

## Skill Directory Structure (canonical)
```
src/hbc-<skill-name>/
├── SKILL.md              # LLM instructions (frontmatter: name + description với trigger phrases)
├── customize.toml        # [workflow] hoặc [agent] config block
├── scripts/              # Python deterministic (scan, validate, extract)
├── assets/               # Templates (D-xx skeletons, decision-log-template)
└── references/           # headless-contract.md (input args + JSON return schema)
```

## Existing Files Inventory

### Agents (5)
- `src/hbc-agent-ba/` — Phase 1 coordinator (menu: REQ, GLO, BFD, PG, TR)
- `src/hbc-agent-architect/` — Phase 2 Design coordinator
- `src/hbc-agent-qa/` — Phase 2 Test Design coordinator
- `src/hbc-agent-dev/` — Phase 3 coordinator
- `src/hbc-agent-tester/` — Phase 4 coordinator

### Phase 1 Skills
- `src/hbc-create-requirements/` — D-02 (REQ-xxx)
- `src/hbc-create-glossary/` — D-03
- `src/hbc-create-business-flow-diagram/` — D-06

### Phase 2 Skills
- `src/hbc-create-er-diagram/` — D-19
- `src/hbc-create-coding-standards/` — D-12
- `src/hbc-create-api-spec/` — D-21 (optional)
- `src/hbc-create-test-plan/` — D-26
- `src/hbc-create-test-spec/` — D-27
- `src/hbc-check-implementation-readiness/` — readiness gate (P-1)

### Phase 3 Skills
- `src/hbc-task-breakdown/` — task-breakdown.md
- `src/hbc-implement/` — TDD code generation

### Phase 4 Skills
- `src/hbc-test-execution/` — test-execution-report.md
- `src/hbc-acceptance-check/` — acceptance-report.md

### Cross-cutting
- `src/hbc-phase-gate/` — gate evaluation engine
- `src/hbc-traceability/` — living matrix (init/update/report/audit)
- `src/hbc-shared/lib/hbc_validation.py` — shared structural validation
- `src/hbc-setup/` — config bootstrap

## Design Patterns

### Pattern: 3-Layer Config Override
- **Location**: mọi customize.toml
- **Purpose**: cho phép team/user override mà không sửa skill gốc
- **Implementation**: `{skill-root}/customize.toml` → `_bmad/custom/{skill-name}.toml` → `.user.toml`. Scalars override, arrays append, arrays-of-tables keyed by code/id replace.

### Pattern: Scan/Resume State
- **Location**: scan scripts mỗi skill
- **Purpose**: detect fresh/resume/update state, support compaction recovery
- **Implementation**: pre-pass script trả JSON state + frontmatter `stepsCompleted` + `.decision-log.md`

### Pattern: Honest Verdict (máy lo cấu trúc, người lo ngữ nghĩa)
- **Location**: hbc_validation.py `verdict()`
- **Purpose**: tách biệt structural validation (script) vs semantic review (LLM Lớp 2)
- **Implementation**: `passed = structure_ok AND semantic_review != pending`

### Pattern: Headless Contract
- **Location**: references/headless-contract.md mỗi create skill
- **Purpose**: cho phép skill-to-skill automation
- **Implementation**: JSON return `{status: complete|blocked, ..., reason}` với closed-set blocked reasons

## Critical Dependencies
- **Python 3.10+**: scripts dùng `str | None` union syntax
- **BMM module**: bắt buộc cài trước
- **resolve_customization.py**: `_bmad/scripts/` — resolver cho config
