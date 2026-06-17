# Headless Contract — hbc-project-init

Phase 0 is **project-wide**: it creates the shared deliverables once before any feature. It takes **no `feature` arg** (per-feature D-19/D-21 overrides are made later via `hbc-create-er-diagram` / `hbc-create-api-spec`).

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `create` | No | Default. Understand the project (brownfield-aware), then create any missing **mandatory** shared deliverables (D-12, D-03) and optional ones (D-19, D-21 baselines). Idempotent — existing deliverables are skipped, never overwritten. |
| `status` | No | List which shared deliverables and project-context already exist vs. are missing, then stop (no generation). |
| `-H`, `--headless` | No | Run `create`/`status` non-interactively. Brownfield vs greenfield is detected deterministically (codebase presence); existing project documentation is used as the source. |

No `feature` arg — Phase 0 writes shared artifacts under `_bmad-output/shared/...`.

Example: `hbc-project-init --headless create`

## Return Schema

```json
{
  "status": "complete | blocked",
  "project_type": "brownfield | greenfield",
  "project_context": "present | created | missing",
  "documented": true,
  "created": ["D-12", "D-03"],
  "skipped": ["D-19"],
  "missing": ["D-21"],
  "reason": "string (only when status=blocked)"
}
```

Field notes:
- `project_type` — deterministic brownfield (source code exists outside `_bmad/`, `docs/`, `_bmad-output/`) vs greenfield detection.
- `project_context` — state of `project-context.md` (the persistent fact every HBC skill relies on): already present, generated this run via `bmad-generate-project-context`, or still missing.
- `documented` — whether brownfield project docs (`{project_knowledge}/index.md`, output of `bmad-document-project`) exist; `false`/note when brownfield ran with limited sources.
- `created` / `skipped` / `missing` — shared deliverables (D-12, D-03 mandatory; D-19, D-21 optional baselines) generated this run, skipped because already present (idempotent), or still missing.

## Status Values

- **complete** — Phase 0 finished; all mandatory shared deliverables exist (created or already present).
- **blocked** — a mandatory shared deliverable is still missing and cannot be generated; `reason` describes the blocker.

## Blocked Reasons

Closed set:
- `"missing_sources"` — a mandatory shared deliverable (D-12 or D-03) is still missing and there are insufficient sources to generate it (no `project-context.md`, no codebase, no PRD/brief).
