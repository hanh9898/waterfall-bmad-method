---
name: hbc-create-api-spec
description: "Generate D-21 API Specification with endpoint definitions. Use when user says 'API spec', 'đặc tả API', or agent menu [API]."
---

# Create API Specification

## Overview

Generate D-21 (API Specification) — endpoint definitions, request/response schemas, authentication strategy, and error codes. **This skill is optional** — not all projects expose APIs (e.g., Odoo internal modules).

Five-stage workflow: Prerequisites → Discovery → Generation → Validation → Save. Supports resume state, headless mode, and parallel-lens review. Requires Python 3.10+ for validation scripts.

**Args:** `create` (default), `update` (revise existing D-21), `validate` (check existing D-21). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (input args, return schema, blocked reasons).

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> **Scope DUAL + feature (B):** by default writes/reads the `shared/` baseline; pass `feature=<slug>` to create/read a **per-feature override** (path-existence precedence). Resolved in Stage 1·0 below.

## Stage 1: Prerequisites

**1·0. Resolve DUAL scope (path-existence precedence).** D-21 has two possible homes: the project-wide **shared baseline** (`{workflow.output_dir}`, under `shared/api/`) and a **per-feature override** (`{workflow.api_feature_dir}`, under `features/{feature}/planning-artifacts/`). Before any scan or write, bind the active directory `{api_dir}` and the active output file `{d21_file}`:

1. Resolve `{feature}`: a `feature=<slug>` arg wins; else an active-feature value carried in the session; else — **interactive**: ask whether this D-21 is the shared baseline or a per-feature override (and for which feature); **headless**: if no feature is resolvable, default to the shared baseline (D-21 baseline is legitimately shared — do NOT block).
2. Bind:
   - **Per-feature override** (feature resolved): `{api_dir} = {workflow.api_feature_dir}` (substitute `{feature}`); `{d21_file} = {api_dir}/D-21-{feature}-api-spec.md`.
   - **Shared baseline** (no feature): `{api_dir} = {workflow.output_dir}`; `{d21_file} = {api_dir}/D-21-{project_name}-api-spec.md`.
3. **Path-existence precedence** (resume/read): if a per-feature override already exists for the active feature, it takes precedence for resume/update; a downstream reader resolves D-21 by checking the per-feature path first, then the shared baseline.

**Resolve log (#10 — dual-scope):** after binding, append one line to the decision log stating which path was chosen — e.g. `Scope resolved: per-feature override (feature={feature}) → {d21_file}` or `Scope resolved: shared baseline (no feature) → {d21_file}`. Headless: log the same line. This makes the per-feature-override-vs-shared-baseline decision auditable.

Use `{api_dir}` and `{d21_file}` (not the raw `{workflow.output_dir}`) for every scan / write / validate reference below.

1a. **Source scan.** Run pre-pass to discover project state and sources:

```
python3 scripts/scan-api-sources.py --project-root {project-root} --output-dir {api_dir} --project-knowledge {project_knowledge}
```

Returns JSON with `state` (fresh/resume/update/skip), `existing_d21` (path + frontmatter), `d02_path`, `d19_path`, `framework`, `needs_api` (boolean heuristic), and `project_knowledge_docs` (brownfield `bmad-document-project` output — `index.md` + project docs; empty for greenfield). Use this to route:
   - **Skip** — project detected as not needing API (e.g., Odoo internal module with no REST endpoints). Confirm with user before exiting.
   - **Fresh** — no prior D-21. Proceed to Stage 2.
   - **Resume** — partial D-21 found (`lastStep` < `complete`). Show summary, offer resume or restart.
   - **Update** — complete D-21 exists. Show what to update, load as baseline.

1b. **API necessity gate.** If `needs_api` is false or uncertain, ask the user: _"Does this project expose a REST/GraphQL API? If not, D-21 can be skipped."_ Exit gracefully if user confirms no API needed.

1c. **Source inventory.** Load D-02 (requirements) and D-19 (database design) as primary inputs. Supplement with user-provided API design notes, existing OpenAPI/Swagger files, or Postman collections.

   **Brownfield ingest (#7).** When `project_knowledge_docs` is non-empty (existing codebase documented via `bmad-document-project`), treat it as a first-class SOURCE: read `{project_knowledge}/index.md` and the listed project docs for the **real endpoint inventory and existing API surface** (routes, controllers, serializers, auth middleware, error envelopes). Derive D-21 from these actual endpoints — not just the abstract D-02/project-context.md — reconciling discovered routes against D-02 REQ-xxx IDs and flagging any endpoint with no requirement (or any requirement with no endpoint). Greenfield (`project_knowledge_docs` empty) keeps the existing D-02/D-19-driven behavior unchanged.

   In headless mode, sources are required via `--sources` arg.

## Stage 2: Discovery

Pre-populate from D-02 requirements and D-19 entities where available. Open with an invitation for the user to share API design decisions. Then identify:

- **API style** — REST or GraphQL. Defaults to auto-detect from project-context.md; if `{workflow.api_style}` is set, use that value as the default.
- **Base configuration** — base URL, API version strategy (path vs header), content type.
- **Authentication** — strategy (JWT, API key, OAuth2, session), token lifecycle, permission model. Use `{workflow.auth_strategy}` as the default strategy when configured.
- **Endpoints** — derive from D-02 functional requirements. Each endpoint gets: HTTP method, URL pattern, description, linked REQ-xxx IDs.
- **Request/response schemas** — derive entity shapes from D-19. Define common patterns (pagination, error envelope, list vs detail).
- **Error handling** — HTTP status codes, error response format, domain-specific error codes.
- **Rate limiting & versioning** — if applicable.

At each area boundary, soft-gate: _"Anything else on [area], or move to [next]?"_

**Compaction flush:** Write endpoint count, auth strategy, and key decisions to decision log.

## Stage 3: Generation

Populate `{workflow.template_path}` with discovered content. Write to `{d21_file}` (resolved in Stage 1·0). Ensure:

- Every endpoint references at least one REQ-xxx ID from D-02.
- Request/response schemas are consistent with D-19 entity definitions.
- Authentication section is complete (no "TBD" placeholders).
- Error codes are exhaustive for each endpoint.
- Examples use realistic data matching the project domain.

**Revision history:** If Update mode, detect scope-of-change:
- Same endpoints, polish only → append note, no version bump.
- New/changed endpoints → new row, bump version.

**Compaction flush:** Write endpoint count and version to decision log.

**Parallel-lens menu:** After generation, offer `[A]` Advanced (deeper review of edge cases, security) / `[P]` Party Mode (multi-agent API review) / `[C]` Continue.

## Stage 4: Validation

Run deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{d21_file}" --d02 "{d02_path}" --d19 "{d19_path}"
```

Script checks: all endpoints have required fields (method, URL, description), endpoint IDs are unique, REQ-xxx references exist in D-02, response entity names match D-19 entities. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable, fall back to LLM-only validation and note the limitation in the decision log.

**LLM judgment checks:**
- Endpoint naming follows RESTful conventions.
- Authentication flow is secure and complete.
- No missing CRUD endpoints for entities that need them.
- Error responses are helpful and don't leak internal details.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable issues, return `blocked` for non-fixable.

**Compaction flush:** Write validation results summary to decision log.

**Parallel-lens menu:** `[A]` Advanced (security audit, performance concerns) / `[P]` Party Mode (multi-reviewer) / `[C]` Continue.

## Stage 4b: Semantic Review (Layer 2)

Structural validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`). Apply the **facet-split discipline**: when a REQ has an admin/lifecycle/write facet that is deliberately kept out of REST scope, state that explicitly here so downstream D-26/D-27 know to test it elsewhere — do not let the cut-out facet vanish silently (the seam). Record `semanticReview` frontmatter (A-3: `status` passed only when `openFacets` empty). The Phase 2 gate REVIEW item (#5) reads it.

## Stage 5: Save and Handoff

Finalize document — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). Audit decision-log entries against D-21. Append closing session.

Suggest next steps: _"D-21 complete. Next: create D-26 Test Plan (`hbc-create-test-plan` [TP]), then D-27 Test Spec (`hbc-create-test-spec` [TS]) and the readiness check (`hbc-check-implementation-readiness` [IR]). Run Phase 2 gate (`hbc-phase-gate` [PG]) only after the test-design artifacts and IR are complete."_

Headless: return JSON per `references/headless-contract.md`.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

**Matrix column (B7-2):** on save (create or update), run `hbc-traceability update feature={feature}` so this phase self-writes its `design_ref` column — don't defer to a manual step (the Phase-2 gate cascade-precheck blocks if missing). Distinct from / lighter than the `impact` cascade.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest: _"Document updated. Run `hbc-traceability impact` to sync the dependent documents/tests/code?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly (it will cascade downstream). Default is false.
