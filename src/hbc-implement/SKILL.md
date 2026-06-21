---
name: hbc-implement
description: "Implement code via TDD cycle per task. Use when user says 'implement', 'triển khai', 'coding', or agent menu [IM]."
---

# Implement

## Overview

Implement code via TDD cycle (RED → GREEN → REFACTOR) per task from the task breakdown. For each task, write failing tests first (from D-27 specs), then implementation code, then refactor to meet D-12 coding standards. This skill produces **code**, not a versioned D-xx document.

Per-task workflow: Pre-flight (stale-design + brownfield) → Load → RED → GREEN → REFACTOR → Update + reconcile. Supports batch mode (`all`) and headless mode. The most interactive workflow — Dev agent pairs with the user throughout.

**Args:** `task <TASK-xxx>` (single task), `all` (batch remaining), `coverage` (check only); **`feature=<slug>`** (required in headless; interactive uses the active feature). Optional: `--headless` / `-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Autonomy (A5 / B5-10)

Separate **mechanical** decisions from **domain** decisions. Mechanical — variable names, helper extraction, test-file layout, applying D-12 formatting, which existing module a file belongs in — decide and proceed. Domain — a business rule the spec leaves ambiguous, a field/relation not in D-19, a NEW-vs-CHANGE call on existing code, how a state-machine branch should behave, an interpretation that changes observable behavior — **ASK; never invent a default**. In a `all`/batch run the batch **STOPS at the domain decision and asks** — it does not guess and continue (a guessed business rule is how the RCA case shipped the wrong model).

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision and return `blocked` with the question (do not write code on a guess).
- `--assumptions-allowed` (default in CI) — take the most defensible option, log it to the decision log / ADR as an `ASSUMPTION`, and continue. Never block on the first turn (a complex feature must not deadlock CI).

## Headless Mode

When `--headless`: batch-implement all TODO tasks sequentially per `references/headless-contract.md`. Domain decisions follow the Autonomy mode above.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

**Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask. Required in headless (missing → `blocked` `feature_required`). All paths (`{workflow.task_breakdown_path}`, `{workflow.tdd_evidence_dir}`) are namespaced by `{feature}`.

Load `task-breakdown.md` from `{workflow.task_breakdown_path}`. Show task status summary: X TODO, Y IN_PROGRESS, Z DONE. If no task specified, suggest the next TODO task.

## Pre-flight (run BEFORE the first task — block, don't slip)

### Stale-design block (B5-4 — a REAL block, not advisory)

The task-breakdown must be built on the **current** design. Run:

```
python3 {skill-root}/scripts/validate-implementation.py --tasks <task-breakdown> --stale-design <D-19 path> --stale-design <D-02 path>
```

If a `DESIGN_STALE` issue appears (the breakdown cites e.g. `D-19 v1.3` while the live D-19 is `v2.3`), **HALT implementation** — the upstream design has moved past what the breakdown describes; re-derive the task-breakdown (`hbc-task-breakdown` [TB]) against the current design before writing any code. This is the RCA failure mode (code built on a stale model) and is a hard block here regardless of the kernel STALE engine (forward-ref T2.4). Headless: return `blocked` `reason: "stale_design"`.

### Brownfield grounding (B5-8 — NEW vs CHANGE, explicit)

Before writing, **read the existing code** the task touches (models, views, tests already in the module). For each task decide, explicitly: is this **NEW** (no current implementation) or a **CHANGE** to existing code? Reuse what exists — never duplicate a model/method that is already there. A NEW-vs-CHANGE call that is ambiguous (does this field already exist under another name? is there an existing method to extend?) is a **domain decision → ASK** (Autonomy). Record the classification per task so the matrix `code_ref` points at the real file (extended or created), not a phantom.

## Per-Task TDD Cycle

### Step 1: Load Context

Load the task's `design_ref` (D-19 entity or D-21 endpoint), `test_refs` (TC-xxx cases from D-27), and D-12 coding standards. Read `project-context.md` for framework-specific patterns. Confirm the NEW/CHANGE classification from Pre-flight for this task.

### Step 2: RED — Write Failing Tests

Based on D-27 test cases for this task:
- Write test file(s) following D-12 test organization conventions. **Do NOT embed spec ids** (`REQ-`/`TC-`/`NFR-`) in test code — name the behavior, not the spec row (B5-2; the closeout lint blocks leaks).
- Tests must be specific and match D-27 expected results.
- Run the tests — they should FAIL (RED). **The failure must be for the RIGHT business-branch reason** (B5-3): an `ImportError`/`AttributeError` because the symbol doesn't exist yet is fine; a test that passes, errors on a typo in the test itself, or fails on an unrelated branch is NOT valid RED — fix the test. Add a sanity check that the fixture actually activates the branch under test (not a vacuous `assert True`).
- **If a test PASSES immediately (green without RED):** that is a signal something is wrong — the behavior already exists (possible duplication → revisit Pre-flight NEW/CHANGE), or the test is too weak to fail. **STOP and investigate** before proceeding; in a batch run, this is a checkpoint stop (B5-5), not a skip.
- **Save RED-evidence (soft process enforcement):** record the FAIL test run into `{workflow.tdd_evidence_dir}/<TASK-xxx>.md` (the command + output containing a `FAIL` line). **HALT — do not write GREEN code until RED-evidence exists.** *(RED-evidence stays a **SOFT** signal: the Phase 3 gate only checks the evidence **exists / shows a FAIL**, not a tamper-proof proof. This is intentional — soft TDD; B5-3 keeps it soft, adding only the FAIL-for-the-right-reason + sanity conditions, never a hard cryptographic gate.)*

Present test code to user for review before proceeding.

### Step 3: GREEN — Implement

Write minimal implementation code to pass all tests from Step 2:
- Follow D-12 naming and formatting conventions; use patterns from `project-context.md`.
- **A GREEN that needs a new model field/relation → update D-19 FIRST** (B5-6 / T1.1): do not add a persistent field in code that the design does not reflect. Update D-19 (`hbc-create-er-diagram` [ERD], or flag it for the architect), then implement — so code and design never silently diverge (the MODEL_DRIFT the closeout catches).
- Run tests after implementation — they should now PASS (GREEN). If still failing, iterate.

### Step 4: REFACTOR

With green tests as safety net:
- Clean up: extract helpers, improve naming, remove duplication. Apply D-12 strictly.
- Run tests again — must stay GREEN after refactoring.

### Step 5: Update and Check (DONE-sanity)

- **DONE-sanity (B5-9):** a task is DONE only when (a) it names a test in `test_refs`, (b) that test exists and **actually activates the branch** (the fixture drives the business path, assertions are structural — not `assert True`/`assert not None`), and (c) the test was RED before GREEN. The structural floor (names a test) is script-checked at closeout; the "fixture activates the branch" half is your judgment — verify it before flipping status.
- Update task status to DONE in `task-breakdown.md`.
- Update the traceability matrix `code_ref` for the REQ this task implements (living matrix, not back-filled at Phase 4) — point at the **real** file (NEW created or CHANGE extended).
- **Coverage is necessary-but-not-sufficient (B5-7):** check `{workflow.coverage_command}`. A number ≥ `{workflow.coverage_threshold}` does NOT prove correctness — it proves lines ran, not that the right branch/edge was exercised. Treat coverage as a floor, then confirm the sanity above. If below threshold, suggest tests; if at threshold but sanity is weak, that is still not DONE.
- Return to agent menu or proceed to next task.

### Closeout: reconcile implementation reality (D2)

Before considering Phase 3 complete (and at the Phase 3 gate, item P3-02b), run the full reconciliation:

```
python3 {skill-root}/scripts/validate-implementation.py --tasks <task-breakdown> --matrix <matrix> \
  --tdd-evidence-dir {workflow.tdd_evidence_dir} --project-root <root> \
  --code-dir <code dir> --design <D-19 path> \
  --stale-design <D-19 path> --stale-design <D-02 path> --require-sanity
```

Must be clean — no `DESIGN_STALE` (B5-4), `MODEL_DRIFT` (B5-1 / T1.1), `SPEC_REF_LEAK` (B5-2 / T1.2), `DONE_NO_SANITY` (B5-9), `DONE_TASK_NO_TEST`, `NO_RED_EVIDENCE`, `RED_EVIDENCE_NO_FAIL`, `MISSING_CODE_FILE`, or `REQ_NOT_IMPLEMENTED`. The **Phase 3 gate reads this verdict** (P3-02b) — `MODEL_DRIFT` or `DESIGN_STALE` is a blocking gap, not a warning. The structural check is honest: whether the code actually fulfils the task and whether a fixture really activates its branch stay with the LLM review / acceptance layer (see the JSON `not_checked`).

## Batch Mode

When `all` arg: iterate through remaining TODO tasks in dependency order. Pause between tasks for a user checkpoint (skip pause in headless). **Stop the batch at a checkpoint** when: a test passes without ever going RED (B5-5), a domain decision arises (Autonomy / B5-10), or a GREEN needs a D-19 field not yet designed (B5-6). Do not power through a guessed business rule.

## Coverage Check

When `coverage` arg: run the coverage command and report results without implementing. Report it as a floor (B5-7), not as proof of correctness.

## Sync Handoff (hbc-traceability impact integration)

Applies when re-implementing due to an upstream change. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop. (hbc-traceability impact invokes this skill as the `code` cascade node per BR-08.)
- **Hybrid trigger (default):** after a successful implementation change, suggest: _"Code updated. Run `hbc-traceability impact` to sync the traceability matrix?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly. Default is false.
