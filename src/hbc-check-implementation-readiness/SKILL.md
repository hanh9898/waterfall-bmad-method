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

## When to use

- Right before `hbc-phase-gate` Phase 2 (gate item **P2-11** expects this).
- Anytime after D-02 changes, to confirm downstream docs are still in sync.

## Inputs

Resolve from `{planning_artifacts}` (default `_bmad-output/planning-artifacts`):
- `D-02` requirements (required — the source of truth)
- `D-27` test spec, `D-26` test plan, `D-21` API spec (optional, reconciled if present)
- traceability matrix (optional)

## Process

1. Locate the documents under `{planning_artifacts}` (glob `D-02-*`, `D-27-*`, …, dir-aware).
2. Run the deterministic engine:

```
python3 {skill-root}/scripts/check-readiness.py \
  --d02 <D-02 path> [--d27 <path>] [--d26 <path>] [--d21 <path>] [--matrix <path>] \
  -o {planning_artifacts}/readiness-report.json
```

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

`readiness-report.json` (honest verdict + reconciliation sets). Headless: return the
JSON and exit non-zero when `ready: false`.

## Limitations

Deterministic structural reconciliation only — REQ id presence, not semantic
adequacy. Automated facet-level counting is tracked separately (M-1). This skill
requires the shared `hbc-shared/lib`.
