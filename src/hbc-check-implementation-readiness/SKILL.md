---
name: hbc-check-implementation-readiness
description: "HBC inter-document readiness gate — reconcile D-02 requirements against D-21/D-26/D-27 and the traceability matrix before closing Phase 2. Use when user says 'check readiness', 'kiểm tra sẵn sàng', 'readiness', or agent menu [IR]."
---

# HBC Check Implementation Readiness (P-1)

## Purpose

The seam-catching gate. Per-document validators each prove their own document's
structure, but no single one can see whether **every D-02 requirement is actually
carried through** the design, test, and implementation-planning documents. This
skill reconciles them, so a requirement can't silently fall through the cracks
between D-02 → D-19/D-21/D-26/D-27 → task-breakdown → matrix → code. Run it
**before closing the Phase 2 gate** (`hbc-phase-gate`).

This gate is a **hard gate** — blocking is its job. It legitimately refuses to close
Phase 2 when a seam is broken (that is the failure it exists to prevent). It was
LET-THROUGH a half-failed feature in the RCA case (a task-breakdown stale on an old
D-02 reading "green" while the requirement set had moved on); the overhaul makes it
catch that half-failure.

> Principle: the machine handles structure · the human/LLM handles semantics. This skill does the
> deterministic **cross-document structural** reconciliation; semantic adequacy
> (is each REQ *meaningfully* covered, every facet handled) stays with the Layer-2
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
- `D-19` ER diagram (under `{workflow.input_dir}`) + the feature `{workflow.code_dir}` (per-feature; optional) — **both** are needed to run the model-drift check (B13-3); pass only persistent-model code (the script globs `models/**/*.py` by default)
- the **task-breakdown** at `{workflow.task_breakdown_path}` (per-feature; optional) — drives the 3-way REQ↔TASK↔design reconcile (B13-2)
- `D-21` API spec — **DUAL scope**: prefer the per-feature override (`{workflow.api_feature_path}/D-21-{feature}-api-spec.md`) if it exists, else the shared baseline (`{workflow.api_shared_path}/D-21-*-api-spec.md`) — path-existence precedence
- the **per-feature** traceability matrix `{workflow.matrix_path}` (optional). Pass the per-feature matrix, NOT the rollup — a rollup carries other features' REQ ids and would surface them as false orphans.

Identity across documents is the REQ's **trailing number**, so a downstream doc that
writes ids in bare form (`REQ-040`) reconciles with the canonical D-02 id
(`REQ-<FEAT>-040`) — they are the same requirement, not orphans of each other.

## Process

1. Resolve `{feature}` (above) and locate the documents under `{workflow.input_dir}` (glob `D-02-*`, `D-27-*`, …, dir-aware); resolve D-21 by the DUAL precedence and the matrix at `{workflow.matrix_path}`.
2. Run the deterministic engine:

```
python3 {skill-root}/scripts/check-readiness.py \
  --d02 <D-02 path> [--d27 <path>] [--d26 <path>] [--d21 <resolved D-21 path>] \
  [--matrix <per-feature matrix>] [--task-breakdown <path>] [--d19 <path> --code-dir <feature code root>] \
  -o {workflow.output_path}
```

The engine matches namespaced ids (`REQ-<FEAT>-NNN`) and legacy `REQ-NNN` alike.

It reports, for every REQ DEFINED in D-02's functional table (not prose):
- `uncovered_by_test` / `uncovered_by_plan` / `uncovered_by_api` — REQs no downstream doc references (D-27 is TC-scoped: a `### TC-` block must bind the REQ, not a pasted appendix — B13-5)
- `missing_from_matrix` — REQs with no matrix row; `matrix_coverage_gaps` — REQs whose row has a blank `design_ref`/`code_ref`/`test_ref` (B13-1)
- `reqs_without_task` / `orphan_tasks` — the 3-way REQ↔TASK↔design reconcile: a REQ with no task, or a task for a REQ no longer in D-02 (B13-2)
- `stale_citations` — a downstream doc / task-breakdown that pins a STALE D-02 version (`D-26 cites v2.2 while D-02 is v2.3`; `task-breakdown sources: D-02 v1.8`) — TASK-stale (B13-2) + seam-stale (B13-4)
- `model_drift` (`design_only` / `code_only`) — model declared in D-19 but absent from code, or vice-versa (B13-3); needs **both** `--d19` and `--code-dir`
- `orphan_reqs_downstream`, `test_ref_drift` — undefined-REQ seams + matrix↔D-27 staleness
- honest verdict (`ready`/`passed` only when all gating sets are empty AND ≥1 gating doc was reconciled)

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

## Autonomy (A5)

Separate **mechanical** decisions from **domain** decisions. Mechanical — which paths
resolve to which document, how to glob the code dir, formatting the report, running
the engine — decide and proceed. The gate verdict itself is mechanical: a non-empty
gating set BLOCKS, full stop — never soft-pedal a real gap into a pass (that soft-pedal
*is* the RCA failure this gate exists to prevent).

Domain — for a gate, the one genuine domain decision is **whether a surfaced gap is an
acceptable, deliberate deferral** (e.g. REQ-042 is intentionally out-of-scope for this
phase, so its missing task/coverage is by design) versus a real omission. **ASK; never
fabricate that a gap is "fine" to make the gate green.** A deferral that the user
confirms is recorded as an explicit waiver (with rationale) — it does not silently
flip `ready`.

Headless resolves this two ways:
- `--strict` — stop at the first gap that might be a deliberate deferral and return `blocked` with the question; do not assume.
- `--assumptions-allowed` (default in CI) — treat every surfaced gap as a real gap (the safe, non-green default for a gate), log that no deferral was confirmed, and return `ready: false` rather than blocking the first turn. CI never gets a false green from an unconfirmed deferral.

## Limitations

Deterministic structural reconciliation only — REQ id presence, not semantic
adequacy. Automated facet-level counting is tracked separately (M-1). This skill
requires the shared `hbc-shared/lib`.
