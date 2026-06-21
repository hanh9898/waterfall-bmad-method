# Headless Contract — hbc-project-init

Phase 0 is **project-wide**: it creates the shared deliverables (incl. the constitution) once before any feature, and loads/initializes the applicability-catalog. It takes **no `feature` arg** (per-feature D-19/D-21 overrides and catalog instances are made later via `hbc-create-er-diagram` / `hbc-create-api-spec` and the BA agent).

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `create` | No | Default. Understand the project (brownfield-aware), load the catalog, create the constitution + any missing mandatory shared deliverables (D-12, D-03) and the catalog-needed ones (D-19, D-21 baselines), and reconcile drift on re-run. Idempotent — existing deliverables are never silently overwritten. |
| `status` | No | List which shared deliverables, constitution, and project-context exist vs. are missing vs. drifted, then stop (no generation). |
| `-H`, `--headless` | No | Run `create`/`status` non-interactively. Brownfield vs greenfield is detected deterministically (codebase presence). |
| `--strict` | No | Stop at the first unresolved domain decision (classification, stack/conventions, a facet flip, an ungroundable constitution value) and return `blocked` with the question. |
| `--assumptions-allowed` | No | **CI default.** Take the most defensible option, log it to the decision log as an `ASSUMPTION`, and continue — never block the first turn. |

No `feature` arg — Phase 0 writes shared artifacts under `_bmad-output/shared/...`.

Example: `hbc-project-init --headless --assumptions-allowed create`

## Return Schema

```json
{
  "status": "complete | blocked",
  "project_type": "brownfield | greenfield",
  "is_rerun": false,
  "project_context": "present | created | missing",
  "documented": true,
  "catalog_loaded": true,
  "constitution": "present | created | drifted | missing",
  "created": ["constitution", "D-12", "D-03"],
  "skipped": ["D-19"],
  "drifted": [{ "deliverable": "D-12", "signal": "incomplete" }],
  "missing": ["D-21"],
  "reason": "string (only when status=blocked)"
}
```

Field notes:
- `project_type` — deterministic brownfield (source code outside `_bmad`/`docs`/`_bmad-output`) vs greenfield.
- `is_rerun` — true when at least one shared deliverable already existed at scan time (drift reconciliation path, B15-1).
- `project_context` — state of `project-context.md`: present, generated this run via `bmad-generate-project-context`, or still missing.
- `documented` — whether brownfield project docs (`{project_knowledge}/index.md`, output of `bmad-document-project`) exist.
- `catalog_loaded` — whether the applicability-catalog (`deliverable-catalog.yaml`) was loaded; the node-set drives which deliverables are needed.
- `constitution` — state of `constitution.md` (T3.13a): present, created this run, drifted (re-run, needs update), or missing.
- `created` / `skipped` / `missing` — deliverables generated this run, skipped because already present (idempotent), or still missing.
- `drifted` — present deliverables flagged stale on a re-run; each proposed for an `update`-mode re-run of its owning create-skill.

## Status Values

- **complete** — Phase 0 finished; the constitution and all mandatory shared deliverables exist (created or already present); drift, if any, surfaced.
- **blocked** — a mandatory deliverable is still missing and cannot be generated (only under `--strict`); `reason` describes the blocker.

## Blocked Reasons

Closed set:
- `"missing_sources"` — a mandatory deliverable (constitution, D-12, or D-03) is still missing and there are insufficient sources to generate it (no `project-context.md`, no codebase, no PRD/brief). Under `--assumptions-allowed` this does NOT block — it continues with a logged limitation note.
