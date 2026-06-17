---
name: hbc-check-implementation-readiness
description: "HBC inter-document readiness gate — reconcile D-02 requirements against D-21/D-26/D-27 and the traceability matrix before closing Phase 2. Use when user says 'check readiness', 'kiểm tra sẵn sàng', 'readiness', or agent menu [IR]."
---

# HBC Check Implementation Readiness (P-1)

## Purpose

The seam-catching gate. Per-document validators each prove their own document's
structure, but no single one can see whether **every D-02 requirement is actually
carried through** the design and test documents. This skill reconciles them, so a
requirement can't silently fall through the cracks between D-02 → D-21/D-26/D-27 →
matrix. Run it **before closing the Phase 2 gate** (`hbc-phase-gate`).

> Principle: máy lo cấu trúc · người/LLM lo ngữ nghĩa. This skill does the
> deterministic **cross-document structural** reconciliation; semantic adequacy
> (is each REQ *meaningfully* covered, every facet handled) stays with the Lớp-2
> semantic review + the facet rubric (`hbc-shared/references/semantic-review-rubric.md`).

## Conventions

- Bare paths (e.g. `references/foo.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## When to use

- Right before `hbc-phase-gate` Phase 2 (gate item **P2-11** expects this).
- Anytime after D-02 changes, to confirm downstream docs are still in sync.

## Feature scope (v2)

Readiness is evaluated **per feature** — a feature can close Phase 2 independently of others. Resolve `{feature}` first: a `feature=<slug>` arg wins; else an active-feature value carried in the session; else ask (interactive). **Headless with no resolvable feature → block** with `reason: "feature_required"` (the inputs are per-feature paths and can't be located otherwise). The Phase 2 gate invokes this skill with the active `feature=`.

## Inputs

Resolve from `{workflow.input_dir}` = `{output_folder}/features/{feature}/planning-artifacts`:
- `D-02` requirements (required — the source of truth, with `REQ-<FEAT>-NNN` ids)
- `D-27` test spec, `D-26` test plan (per-feature; optional, reconciled if present)
- `D-21` API spec — **DUAL scope**: prefer the per-feature override (`{workflow.api_feature_path}/D-21-{feature}-api-spec.md`) if it exists, else the shared baseline (`{workflow.api_shared_path}/D-21-*-api-spec.md`) — path-existence precedence
- the **per-feature** traceability matrix `{workflow.matrix_path}` (optional). Pass the per-feature matrix, NOT the rollup — a rollup carries other features' REQ ids and would surface them as false orphans.

## Process

1. Resolve `{feature}` (above) and locate the documents under `{workflow.input_dir}` (glob `D-02-*`, `D-27-*`, …, dir-aware); resolve D-21 by the DUAL precedence and the matrix at `{workflow.matrix_path}`.
2. Run the deterministic engine:

```
python3 {skill-root}/scripts/check-readiness.py \
  --d02 <D-02 path> [--d27 <path>] [--d26 <path>] [--d21 <resolved D-21 path>] [--matrix <per-feature matrix>] \
  -o {workflow.output_path}
```

The engine matches namespaced ids (`REQ-<FEAT>-NNN`) and legacy `REQ-NNN` alike.

It reports, for every REQ DEFINED in D-02's functional table (not prose):
- `uncovered_by_test` / `uncovered_by_plan` / `uncovered_by_api` — REQs no downstream doc references
- `missing_from_matrix` — REQs absent from the traceability matrix
- `orphan_reqs_downstream` — REQs referenced downstream but never defined in D-02
- honest verdict (`ready`/`passed` only when all sets are empty)

3. **Interpret + escalate.** If `ready: false`, present each gap and which document
   owns the fix. Do NOT close Phase 2. If the engine can't run, fall back to the
   manual reconciliation in gate item P2-11 (`trace-report.py --d02` + `check-fr-coverage.py`).
4. **Facet layer.** Even when structurally `ready`, apply the facet rubric: a REQ
   referenced by a TC may still have an unhandled write/admin facet. Surface those
   as semantic findings (they belong in each doc's `semanticReview.openFacets`).

## Output

`readiness-report.json` (honest verdict + reconciliation sets) at `{workflow.output_path}`.
Headless: return the JSON and exit non-zero when `ready: false`. Full input args,
return schema, exit codes, and the closed-set of blocked `reason` values live in
[`references/headless-contract.md`](references/headless-contract.md).

## Limitations

Deterministic structural reconciliation only — REQ id presence, not semantic
adequacy. Automated facet-level counting is tracked separately (M-1). This skill
requires the shared `hbc-shared/lib`.
