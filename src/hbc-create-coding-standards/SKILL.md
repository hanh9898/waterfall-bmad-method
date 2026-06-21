---
name: hbc-create-coding-standards
description: "Generate D-12 Coding Standards adapted to project framework. Use when user says 'coding standards', 'chuẩn code', or agent menu [CS]."
---

# Create Coding Standards

## Overview

Generate D-12 (Coding Standards) — per-project coding conventions **derived from the project's real code** (not invented from framework defaults), adapted to the project's framework, language, and team preferences. D-12 is the reference standard for all Phase-3 implementation work; its machine-checkable rules are what the Phase-3 gate enforces.

Workflow: Prerequisites + Discovery → Generation → Validation → Code-grounding reconcile → Semantic review → Save. Supports resume state, headless mode. Requires Python 3.10+ for the scripts.

**Args:** `create` (default), `update` (revise existing D-12), `validate` (check existing D-12). Optional: `--headless` / `-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Autonomy (A5)

Separate **mechanical** decisions from **domain** decisions. Mechanical — section ordering, table formatting, applying a framework's own idiomatic case to its own constructs — decide and proceed. Domain — a **team preference** not derivable from framework convention (indentation width, fail-fast vs defensive, comment language, import ordering), whether to keep a standard that the real code deviates from, how to resolve a contradiction — **ASK; never silently default** (B10-3).

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision and return `blocked` with the question.
- `--assumptions-allowed` (default in CI) — take the most defensible option (framework default), log it to the decision log as an `ASSUMPTION`, and continue. Never block on the first question.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (input args, return schema, blocked reasons). Domain decisions follow the Autonomy mode above.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> **Scope: SHARED** — this deliverable is shared across the whole project (created in Phase 0 via `hbc-project-init`), does **not** take a `feature`, and is written to `shared/`.

## Stage 1: Prerequisites + Discovery

1a. **Source scan.** Check `{workflow.output_dir}` for existing D-12 artifacts:

```
python3 {workflow.scan_script} --project-root {project-root} --output-dir {workflow.output_dir} --project-knowledge {project_knowledge}
```

Returns JSON with `state` (fresh/resume/update), `existing_d12`, `framework` (detected from project-context.md), `project_context_path`, and `project_knowledge_docs` (brownfield `bmad-document-project` output; empty for greenfield). Route: **Fresh** → discovery · **Resume** (`lastStep` < `complete`) → show summary, offer resume/restart · **Update** → load as baseline (Update Mode).

After routing: initialize `.decision-log.md` as a peer of the output. If the scan script fails or Python is unavailable, ask the user for source paths and proceed.

1a′. **Brownfield ingest (#7).** When `project_knowledge_docs` is non-empty, treat it as a first-class SOURCE: read `{project_knowledge}/index.md` and the listed docs for the **real, already-in-use conventions** (naming, layout, error handling, lint/format configs). Derive D-12 from these so it codifies what the codebase already does, surfaced as confirmations in 1c. Greenfield keeps framework-default behavior.

1b. **Framework detection.** If `{workflow.framework}` is set, use it (skip auto-detection). Otherwise read `project-context.md` to detect framework + language; if undetectable, ask. Common stacks: Odoo (Python), Django (Python), Next.js/React (TS), Laravel (PHP), Spring Boot (Java).

1c. **Team preferences (B10-3).** These vary per team even within one framework — they are **domain decisions, never silently defaulted**. Ask (pre-populating the framework default as a *confirmation*, not an open question): indentation style + width · naming overrides · comment language (default `{workflow.comment_language}` else `{document_output_language}`) · error-handling philosophy · import ordering · any existing lint config (`.eslintrc`/`.flake8`/`ruff.toml`/…) to align with. In headless, the Autonomy mode governs (strict → block; assumptions → framework default logged as ASSUMPTION).

**Compaction flush:** Write detected framework, language, and key preference decisions to decision log.

## Stage 2: Generation

Populate `{workflow.template_path}`, write to `{workflow.output_dir}/D-12-{project_name}-coding-standards.md`. Ensure:

- Every section has framework-specific conventions, not generic platitudes. Naming matches the framework's idiom (`snake_case` Python/Odoo, `camelCase` JS/TS). Code examples use real framework syntax; inline comments in `{workflow.comment_language}` else `{document_output_language}`. Error-handling + Security sections reflect framework patterns/risks (e.g. Odoo `@api.model` access control, Django CSRF, React XSS).
- **§1.4 Code Derivation & Deviations (B10-1).** Record which conventions were read from the real code, and any DEVIATION where a stated standard differs from current code (filled from the Stage 3a reconcile) with its reason/action.
- **§10 Machine-checkable Rules (Lint) (B10-2).** Express every rule that *can* be machine-checked as a lint rule, naming the tool/check and the enforcing gate. The "no spec ids (`REQ-`/`TC-`/`NFR-`) in code/tests" rule is mandatory — the Phase-3 gate (`hbc-implement` spec-ref lint, T1.2) blocks on any leak. Do NOT rebuild that lint/gate; D-12 *emits the rule and references the enforcement*.

**Revision history (Update mode):** see Update Mode (per-session bump, not per-edit).

**Compaction flush:** Write section count and version to decision log.

## Stage 3: Validation

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-12-{project_name}-coding-standards.md" --framework {detected_framework}
```

Script checks required sections present/non-empty, advisory contradiction pairs, framework coverage, code-example count; returns per-issue `auto_fixable` + a `churn` block (see Update Mode). If unavailable, fall back to LLM-only validation and note the limitation.

**LLM judgment checks:** conventions actionable/specific (not "write clean code"); examples match stated conventions; no real contradictions; framework patterns accurate for the version.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

## Stage 3a: Code-grounding reconcile (B10-1 / B10-2)

Reconcile D-12 against the real code so the standard reflects reality — advisory, not a hard gate (the blocking gates are `hbc-check-implementation-readiness` [IR] and the Phase-3 implement gate). If the script/Python is unavailable, skip and proceed. Resolve `--code-dir` (first-party source) from Stage 1/config:

```
python3 {workflow.consistency_script} "{workflow.output_dir}/D-12-{project_name}-coding-standards.md" --project-root {project-root} --code-dir <source dir>
```

It returns:
- **`deviations` (B10-1)** — a stated standard (indentation, naming case) the real code does NOT follow. For each, the standard is wrong or a deliberate migration: **confirm with the user** (domain decision), then record it in §1.4 Deviations. Do not silently overwrite either side.
- **`spec_ref_leaks` + `spec_ref_leak_count` (B10-2)** — REQ-/TC-/NFR- ids embedded in code/tests. This grounds §10's mandatory lint rule in the real count; the Phase-3 gate is what reduces it to 0.

Headless: include both in the return; `--strict` blocks if either is non-empty, `--assumptions-allowed` logs them and continues.

## Stage 3b: Semantic Review (Layer 2)

Structural validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** — challenge each rule: is it grounded in the real code/framework, actionable, internally consistent, free of contradictory rules? Are the machine-checkable rules actually expressed as lint (§10)? List every unresolved concern in `openFacets`. Set `semanticReview.status: passed` **only when `openFacets` is empty AND the user signs off** (headless follows the Autonomy mode); otherwise `pending`. The shared `semantic_review_status` is the single structural read; the Phase 2 gate REVIEW item (#5) enforces it.

## Stage 4: Save and Handoff

Finalize — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). On create: fill the blank date in the pre-seeded Revision History row. Audit decision-log entries against D-12: every preference decision reflected. Append closing session.

Suggest next steps: _"D-12 complete. Recommended: create D-21 API Spec (`hbc-create-api-spec` [API]) if the project exposes APIs, or proceed to the Phase 2 gate (`hbc-phase-gate` [PG])."_

Headless: return JSON per `references/headless-contract.md`.

## Validate Mode

When invoked with `validate` arg: run Stage 1a scan to locate existing D-12, then run the validation script (and optionally Stage 3a reconcile) against it. Present results (interactive) or return headless JSON. No discovery/generation stages run. If no D-12 found, return `blocked` with `reason: "no_existing_d12"`.

## Update Mode

When `state: update` or `update` arg: load the existing D-12 as baseline. Apply changes; for new/changed conventions add a Revision History row, for polish-only append a note.

**Anti-churn (T2.11).** Bump the version **once per session**, not per edit. The validator returns `churn` (`revisions` vs `threshold`); when `churn.high_churn` is true the conventions aren't settled yet — surface it and suggest `maturity: exploratory` or a `[DSC]` model-spike instead of another bump.

Then proceed to Stage 3 (Validation). Headless: auto-apply non-conflicting changes; return `blocked` with `reason: "preference_conflict"` when a preference change clashes.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section (prevents the update→sync→update loop).
- **Cascade ADVISORY (B10-4).** D-12 is SHARED, so a convention change ripples to every in-flight feature. Enforced cascade is T2.2 (not yet built); until then emit an **advisory note**: after a successful update list the in-flight features and suggest running `hbc-traceability impact` to review whether their code/standards need re-alignment. This is a flag, **not a hard block** (forward-references T2.2 cascade-ENFORCED).
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly. Default false.
