# Technology Stack

## Programming Languages
- **Python** — 3.10+ — deterministic scripts (scan, validate, extract, report). Dùng `str | None` union syntax (yêu cầu 3.10+)
- **Markdown** — SKILL.md instructions, D-xx documents, templates
- **YAML** — module.yaml manifest, config.yaml
- **TOML** — customize.toml config blocks

## Frameworks / Platforms
- **BMad Method** — v6.3.0+ — host framework
- **BMM (BMad Method Module)** — required dependency
- **Claude Code / Kiro** — skill execution environment (`.claude/skills/`)

## Build Tools
- **npm** — package.json metadata, install command (`npx bmad-method install`)
- **bmad-method CLI** — skill installation

## Testing Tools
- **Hiện tại**: Không có test framework rõ ràng trong module (skills là LLM-orchestrated; scripts có validation logic nhưng không thấy unit test cho scripts)
- **Có `.pytest_cache/`** ở root → pytest đã từng chạy (có thể cho validation scripts)
- **Khuyến nghị cho hbc-sync**: pytest + Hypothesis (PBT Partial mode đã opt-in)

## Configuration System
- **resolve_customization.py** — resolver 3-layer override
- **config.yaml** (root + hbc section) — output_folder, document_output_language
- **config.user.yaml** (gitignored) — user_name, communication_language

## Conventions
- Path tokens: `{skill-root}`, `{project-root}`, `{skill-name}`, `{planning_artifacts}`, `{output_folder}`
- JSON output: `ensure_ascii=False` (hỗ trợ tiếng Việt)
- File/folder names: luôn English (kebab-case / snake_case)
- Document prose: theo `{document_output_language}`
