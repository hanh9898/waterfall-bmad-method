---
name: hbc-acceptance-check
description: "Final acceptance evaluation with ACCEPTED/REJECTED/DEFERRED/PENDING decisions. Use when user says 'acceptance', 'nghiệm thu', or agent menu [AC]."
---

# Acceptance Check

## Overview

Final acceptance evaluation — review all lifecycle artifacts, test execution results, and traceability for sign-off. Produces a formal acceptance report with one of four decisions: ACCEPTED, REJECTED, DEFERRED, or PENDING. The `acceptance_owner` (from config) makes the decision; this workflow presents evidence. Acceptance runs *before* the Phase 4 gate — it gathers evidence and records the decision, then the formal Phase 4 gate (`hbc-phase-gate` [PG]) runs afterward to close the project. That is why the checklist verifies the Phase 1/2/3 gates, not Phase 4.

Four-stage workflow: Prerequisites → Review → Decide → Report. Supports headless mode. Requires Python 3.10+ for validation scripts.

**Args:** `review` (default — full acceptance review), `status` (check current decision without re-review). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> **Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask (headless: required, if missing → blocked `feature_required`). Substitute `{feature}` in every workflow path.

## Stage 1: Prerequisites

Load all evidence for the acceptance review:
- **Test execution report** from `{workflow.input_test_report}`.
- **Traceability matrix** from `{workflow.input_traceability}`.
- **Gate reports** from `{workflow.input_gates}/phase-*-gate.md`.
- **D-02 Requirements** from `{workflow.input_requirements}/D-02-*.md` (requirement count + the guard authority for stale-citation/matrix-completeness).
- For the hard guards (Stage 2): **D-19** + the feature **code root** (model-match), the **matrix** (completeness), **D-27/D-26** (stale citation). Resolve under `{workflow.input_requirements}` / the feature code dir; each is optional but a guard only runs when its inputs are present.

If test execution report missing, block with warning. Other artifacts are recommended but not blocking.

## Stage 2: Review

Walk through acceptance criteria checklist:

| Criterion | Check Method |
|-----------|-------------|
| All requirements traced | Traceability matrix — every REQ has design_ref, code_ref, test_ref |
| All tests passed | Test execution report — 0 failed |
| Coverage meets threshold | Test execution report — coverage_pct ≥ `{workflow.coverage_threshold}` |
| Phase 1 gate passed | Gate report exists with PASSED status |
| Phase 2 gate passed | Gate report exists with PASSED status |
| Phase 3 gate passed | Gate report exists with PASSED status |
| No open critical defects | Test execution report — no unresolved critical defects |

For each criterion, produce: status (PASS/FAIL/SKIP), evidence (file path + relevant metric).

**Hard acceptance guards (B16-1, B16-2, B16-3) — run before any ACCEPT.** A green checklist is necessary-but-not-sufficient: the cardinal sin is ACCEPTing a feature that "passed" against the WRONG model, or whose slice is untraced, or whose evidence rests on a superseded spec. The guard engine does NOT trust the checklist; it reconciles design↔code↔matrix↔spec-version via the shared primitives:

```
python3 {workflow.guards_script} [--d02 <D-02>] [--d19 <D-19> --code-dir <feature code root>] \
  [--matrix <matrix>] [--d27 <D-27>] [--d26 <D-26>] [--coverage <pct> --threshold {workflow.coverage_threshold}]
```

A non-empty `blocking` array (`model_drift` B16-1 — code never built the designed model; `missing_from_matrix` B16-1 — a D-02 REQ with no trace row; `stale_citations` B16-3 — D-27/D-26 on a stale D-02) means **ACCEPT is forbidden** — the decision is REJECTED or PENDING, never a fabricated green. `accept_allowed: true` only *clears the structural floor*; it does not by itself license ACCEPT. Coverage at/above threshold (B16-2) is reported as necessary-but-not-sufficient; structural sanity that a fixture truly activates the branch under test stays a human/LLM judgement.

**UX acceptance (B16-4) — advisory forward-ref.** When the applicability catalog enables **Part-D (UX)** for this feature, an additional acceptance criterion applies: each UX requirement must be checked against its mockup (visual / E2E parity). Note it in the checklist as an open criterion; **full visual/E2E enforcement lands with T3.14** (the UX engine is not built here). Do not silently mark UX-accepted without that evidence.

Present review summary (incl. the guard result) to user (or `acceptance_owner` if different from user).

## Stage 3: Decide

Record the acceptance decision:

| Decision | Meaning |
|----------|---------|
| `ACCEPTED` | All criteria met — project deliverable complete |
| `REJECTED` | Blocking issues found — return to specific phase for fixes |
| `DEFERRED` | Acceptable with known issues — document and proceed with caveats |
| `PENDING` | Insufficient information — need more data before deciding |

If `REJECTED`: specify which phase to return to based on defect type (Phase 1 for spec issues, Phase 2 for test gaps, Phase 3 for code bugs).

The `acceptance_owner` (from `{workflow.acceptance_owner}` config) decides. In interactive mode, present evidence and ask for decision. In headless mode, auto-decide based on criteria: all PASS → ACCEPTED; any FAIL → REJECTED; missing/insufficient evidence (a criterion cannot be evaluated) → PENDING. **DEFERRED is interactive-only** — accepting known issues requires human judgment, so headless never emits it.

**A blocking guard overrides the checklist (B16-1/B16-3).** If the guard engine's `blocking` array is non-empty, ACCEPTED is forbidden regardless of how green the checklist looks: in interactive mode present the blocking findings and let the owner choose REJECTED (default) or, with explicit rationale, DEFERRED; in headless mode → REJECTED (never ACCEPTED, never DEFERRED). A blocking guard is the exact false-ACCEPT this skill exists to prevent.

## Stage 4: Report

Write to `{workflow.output_dir}/acceptance-report.md`:

```markdown
---
title: "{project_name} Acceptance Report"
decided_at: ""
decided_by: "{acceptance_owner}"
decision: "ACCEPTED | REJECTED | DEFERRED | PENDING"
---

## Acceptance Criteria Checklist

| Criterion | Status | Evidence |
|-----------|--------|----------|

## Traceability Summary

| Metric | Value |
|--------|-------|
| Total Requirements | {total_reqs} |
| Designed | {designed} |
| Implemented | {implemented} |
| Tested | {tested} |
| Trace Coverage | {coverage_pct}% |

## Decision

**Status:** {decision}
**Decided by:** {acceptance_owner}
**Reason:** {reason}

## Action Items (if REJECTED or DEFERRED)

| Item | Phase | Description | Priority |
|------|-------|-------------|----------|
```

Run validation:

```
python3 {workflow.validation_script} "{workflow.output_dir}/acceptance-report.md"
```

Finalize. If ACCEPTED: _"Project accepted. Run Phase 4 gate [PG] to finalize."_ If REJECTED: _"Rejected — {n} blocking issues. Return to Phase {x} for fixes."_

## Autonomy (A5)

Separate **mechanical** from **domain** decisions. Mechanical — locating the evidence, running the guard engine, formatting the report, computing checklist PASS/FAIL from the metrics — decide and proceed. The guard verdict is mechanical: a non-empty `blocking` array forbids ACCEPT, full stop — never soft-pedal a real drift/missing-trace/stale-spec into a green sign-off (that soft-pedal *is* the false-ACCEPT this skill prevents).

Domain — the ACCEPTED / REJECTED / DEFERRED / PENDING judgement is itself a domain decision that needs the `acceptance_owner`'s ratification. **ASK; never fabricate a green.** A DEFERRED (accepting known issues) always needs a human with explicit rationale.

Headless resolves this two ways:
- `--strict` — stop and return `blocked` (with the question) at the first point a domain ratification is needed rather than auto-deciding.
- `--assumptions-allowed` (default in CI) — auto-decide the *safe* way: any FAIL or any blocking guard → REJECTED; un-evaluable criterion → PENDING; never ACCEPTED-by-assumption and never DEFERRED. Log that no human ratification occurred. CI never emits a false ACCEPT.

## Churn / semantic-review (T2.11 / T2.12) — N/A

An acceptance report records a **decision**, not a versioned D-xx deliverable that evolves over revisions. It is produced once per acceptance run, so there is no revision-history churn to assess (T2.11 N/A) and no document-semantics to gate via `semanticReview` frontmatter (T2.12 N/A). The meaning layer here is the accept JUDGEMENT (a domain decision, ASK) plus the hard guards (B16-1/B16-2/B16-3) — not a churn/semantic-review record.
