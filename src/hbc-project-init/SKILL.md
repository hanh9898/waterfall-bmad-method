---
name: hbc-project-init
description: "Phase 0 — khởi tạo dự án + tạo các deliverable dùng chung (shared) một lần trước khi làm feature. Use when user says 'project init', 'khởi tạo dự án', 'phase 0', 'tạo shared', or agent menu [PI]."
---

# Project Init (Phase 0)

## Overview

Phase 0 runs **once, mandatory, BEFORE** any feature (or re-run to update in place). It does two things: **(1) understand the project** (especially when installed into an existing codebase — brownfield), then **(2) create the shared deliverables** that serve as the foundation for every feature.

| Deliverable | Mandatory | Location |
| --- | --- | --- |
| **D-12 Coding Standards** | ✅ | `{output_folder}/shared/coding-standards/` |
| **D-03 Glossary** | ✅ | `{output_folder}/shared/glossary/` |
| **D-19 ERD (baseline)** | optional | `{output_folder}/shared/erd/` |
| **D-21 API (baseline)** | optional | `{output_folder}/shared/api/` |

Idempotent: a shared deliverable that already exists is **skipped** (never overwritten), only the missing parts are created. Re-run to update in place when needed.

**Args:** `create` (default — understand the project + create the missing parts), `status` (only list which shared deliverables + project-context exist or are missing). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = installed dir. `{project-root}`-prefixed from project. `{skill-name}` = basename.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> Phase 0 **takes no `feature` arg** — it creates project-wide shared artifacts. Per-feature D-19/D-21 overrides are created later via `hbc-create-er-diagram`/`hbc-create-api-spec` with `feature=<slug>`.

## Headless Mode

`-H` / `--headless` runs `create` / `status` non-interactively (full I/O contract — input args, return schema, blocked reasons: `references/headless-contract.md`). Detects brownfield vs greenfield deterministically (codebase presence), uses any existing project documentation as source, then writes shared deliverables under `_bmad-output/shared/...`. Idempotent — existing deliverables are skipped. No `feature` arg.

Blocked reasons (closed set):

- `missing_sources` — a mandatory shared deliverable is still missing and there are insufficient sources (no project-context, no codebase, no PRD/brief) to generate it.

## Stages

### Stage 1: Status

Scan the project's baseline state:
- **Project context:** does `project-context.md` (BMad AI rules/context) exist yet? Do the project docs `{project_knowledge}/index.md` (output of `bmad-document-project`) exist yet?
- **Shared deliverables:** D-12 `{output_folder}/shared/coding-standards/D-12-*` · D-03 `{output_folder}/shared/glossary/D-03-*` · D-19 baseline `{output_folder}/shared/erd/D-19-*` · D-21 baseline `{output_folder}/shared/api/D-21-*`.

Present a "present / missing" table. If `status` arg → stop here.

**Detect LEGACY (v1) layout.** Also scan for signs of HBC v1 output (flat layout): the presence of `_bmad-output/planning-artifacts/D-*`, or `_bmad-output/traceability/matrix*` WITHOUT a `_bmad-output/features/` directory. If detected → **recommend running `hbc-migrate` ([MIG]) FIRST** before creating any shared deliverable: migrate moves the flat artifacts into `shared/` + `features/<feature>/` and re-prefixes REQ/TC. Creating shared now would cause **double-creation** with what migrate is about to build. Surface this warning, then stop (so the user runs [MIG] first, then returns to PI for the remaining missing shared parts).

### Stage 2: Understand the project (brownfield-aware)

Determine the project type, then ensure there is enough **context** to seed the shared deliverables — instead of creating them from scratch:

1. **Classify brownfield vs greenfield.** Brownfield = a codebase already exists (source code outside `_bmad/`, `docs/`, `_bmad-output/`). Greenfield = a new project, no code yet.
2. **Ensure `project-context.md`.** If missing, orchestrate `bmad-generate-project-context` to create it (AI rules + project context). This is the persistent fact every HBC skill relies on.
3. **Brownfield — document the project first.** If brownfield and the project docs (`{project_knowledge}/index.md`) are missing, orchestrate **`bmad-document-project`** to scan the codebase (architecture, DB schema, endpoints, code conventions) → context docs. These are the **source** for deriving the shared deliverables: code conventions → D-12, schema → baseline D-19, endpoints → baseline D-21.
4. **Greenfield — get context from other sources.** Use PRD/brief/`project-context.md` if available; otherwise ask the user briefly about stack + domain.

Headless: classify automatically; if brownfield but project docs are missing, still continue but note the limited sources; missing every source for a mandatory deliverable → `blocked` (`missing_sources`).

### Stage 3: Create missing (idempotent)

For each **missing** shared deliverable, orchestrate the corresponding create-skill, **passing the context from Stage 2** (brownfield: derived from the codebase/project docs; greenfield: from PRD/brief/choices):
- D-12 → `hbc-create-coding-standards` (mandatory) — brownfield: extract conventions from existing code.
- D-03 → `hbc-create-glossary` (mandatory) — from the domain/project docs.
- D-19 baseline → `hbc-create-er-diagram` (optional) — brownfield: reverse-engineer from the existing DB schema.
- D-21 baseline → `hbc-create-api-spec` (optional) — brownfield: from existing endpoints.

**Never overwrite** a deliverable that already exists. Headless: create the missing mandatory deliverables if sources suffice, otherwise `blocked` (`missing_sources`).

### Stage 4: Handoff

Communicate the handoff in `{communication_language}`:

_"Phase 0 done — the project now has project-context + shared deliverables. Start the first feature: open `hbc-agent-ba` ([BA]) with a feature slug, then `hbc-create-requirements` (feature=<slug>)."_

Headless: return JSON `{status, project_type, project_context, documented, created, skipped, missing}`.
