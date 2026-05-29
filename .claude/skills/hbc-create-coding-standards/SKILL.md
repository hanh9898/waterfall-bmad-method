---
name: hbc-create-coding-standards
description: "Generate D-12 Coding Standards adapted to project framework. Use when user says 'coding standards', 'コーディング規約', 'chuẩn code', or agent menu [CS]."
---

# Create Coding Standards

## Overview

Generate D-12 コーディング規約 (Coding Standards) — per-project coding conventions adapted to the project's framework, language, and team preferences. The resulting document is the reference standard for all implementation work in Phase 3.

Four-stage workflow: Prerequisites + Discovery → Generation → Validation → Save. Supports resume state, headless mode. Requires Python 3.10+ for validation scripts.

**Args:** `create` (default), `update` (revise existing D-12), `validate` (check existing D-12). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (input args, return schema, blocked reasons).

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

## Stage 1: Prerequisites + Discovery

1a. **Source scan.** Check `{workflow.output_dir}` for existing D-12 artifacts:

```
python3 scripts/scan-coding-standards.py --project-root {project-root} --output-dir {workflow.output_dir}
```

Returns JSON with `state` (fresh/resume/update), `existing_d12` (path + frontmatter), `framework` (detected from project-context.md), and `project_context_path`. Use this to route:
   - **Fresh** — no prior D-12. Proceed to discovery.
   - **Resume** — partial D-12 found (`lastStep` < `complete`). Show summary, offer resume or restart.
   - **Update** — complete D-12 exists. Show what to update, load as baseline.

1b. **Framework detection.** Read `project-context.md` (loaded via persistent_facts) to detect the primary framework and language. If not detectable, ask the user. Common stacks: Odoo (Python), Django (Python), Next.js (TypeScript), React (TypeScript/JavaScript), Laravel (PHP), Spring Boot (Java).

1c. **Team preferences.** Ask the user about preferences not derivable from framework conventions — these vary per team even within the same framework:
- Indentation style (tabs/spaces, width)
- Naming convention overrides (if deviating from framework default)
- Comment language (Japanese, Vietnamese, English)
- Error handling philosophy (fail-fast vs defensive)
- Import ordering preferences
- Any existing linting config (.eslintrc, .flake8, ruff.toml, etc.) to align with

Pre-populate defaults from framework conventions — present as confirmations, not open questions. In headless mode, use framework defaults for unspecified preferences.

**Compaction flush:** Write detected framework, language, and key preference decisions to decision log.

## Stage 2: Generation

Populate `{workflow.template_path}` with discovered content. Write to `{workflow.output_dir}/D-12-{project_name}-coding-standards.md`. Ensure:

- Every section is populated with framework-specific conventions, not generic platitudes.
- Naming conventions match the framework's idiomatic style (e.g., `snake_case` for Python/Odoo, `camelCase` for JavaScript/TypeScript).
- Code examples use the project's actual framework syntax, not abstract pseudocode.
- Error handling section reflects the framework's patterns (e.g., try/except chains in Python, error boundaries in React).
- Security section addresses framework-specific risks (e.g., `@api.model` access control in Odoo, CSRF in Django, XSS in React).

**Framework-specific adaptation examples:**
- **Odoo:** `@api.model`/`@api.multi` decorators, `_inherit` patterns, XML view conventions, `ir.model.access.csv` formatting, jQuery widget patterns for older versions.
- **Django:** PEP 8 base, class-based view patterns, model field ordering, migration naming, template tag conventions.
- **Next.js/React:** ESLint + Prettier config alignment, hook rules, server component vs client component boundaries, file naming (`kebab-case` files, `PascalCase` components).

**Revision history:** If Update mode, detect scope-of-change:
- Polish only → append note, no version bump.
- New/changed conventions → new row, bump version.

**Compaction flush:** Write section count and version to decision log.

## Stage 3: Validation

Run deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-12-{project_name}-coding-standards.md" --framework {detected_framework}
```

Script checks: all required sections present and non-empty, no internal contradictions (e.g., "use tabs" then "use 2 spaces"), framework-specific conventions present for detected framework. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable, fall back to LLM-only validation and note the limitation in the decision log.

**LLM judgment checks:**
- Conventions are actionable and specific, not vague ("write clean code").
- Code examples match the stated conventions.
- No contradictions between sections.
- Framework-specific patterns are accurate for the framework version.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable issues, return `blocked` for non-fixable.

**Compaction flush:** Write validation results summary to decision log.

## Stage 4: Save and Handoff

Finalize document — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`). Audit decision-log entries against D-12: every preference decision reflected in the document. Append closing session.

Suggest next steps: _"D-12 complete. Recommended: create D-21 API Spec (`hbc-create-api-spec` [API]) if project exposes APIs, or proceed to Phase 2 gate (`hbc-phase-gate` [PG]) if all design artifacts are ready."_

Headless: return JSON per `references/headless-contract.md`.
