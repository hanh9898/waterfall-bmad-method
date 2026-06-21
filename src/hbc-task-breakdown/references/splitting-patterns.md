# Splitting Patterns — vertical slices, INVEST, SPIDR, test-list (B4-1)

Loaded on demand by `hbc-task-breakdown` Stage 2 when a candidate task is too large
or looks like a horizontal layer. The goal of every split is a **vertical slice**:
a task that cuts through model + behavior + (where relevant) UI to deliver one
testable increment of REQ value — never a horizontal layer ("all models", then
"all services", then "all views"), which defers integration risk and produces tasks
that cannot be demonstrated.

## INVEST test (apply to every task)

A task should be:

- **I**ndependent — minimal ordering coupling; can be built without waiting on an
  unrelated slice. (Dependencies on foundation slices are fine and explicit.)
- **N**egotiable — describes the outcome, not a frozen implementation recipe.
- **V**aluable — delivers a slice of REQ behavior a stakeholder can recognize, not
  an internal-only layer.
- **E**stimable — small and clear enough to size (≤ `{workflow.max_hours_per_task}` h).
- **S**mall — one TDD cycle's worth of work.
- **T**estable — has a concrete test list (below). If you cannot write the tests,
  the task is under-specified — split or clarify, do not guess.

A task failing **V** or **T** is usually a horizontal layer — re-slice it vertically.

## SPIDR — five ways to split a too-big slice

When a task is too large, split along the **first** axis that yields independently
valuable slices (not the one that yields the most tasks):

| Axis | Split a big slice by… | Example |
|------|----------------------|---------|
| **S**pike | Carving out an unknown into a separate time-boxed investigation | "Validate the rate-currency model assumption" → `[DSC]` spike, then the build slice |
| **P**ath | Distinct flow paths through the same feature (happy / alt / exception) | Create plan (happy) vs reject-and-resubmit (alt) vs concurrent-edit conflict (exception) |
| **I**nterface | One UI/entry-point or one channel at a time | Form entry first; grid/pivot view as a later slice; import wizard later still |
| **D**ata | One data variant / boundary at a time | Single-currency line first; multi-currency line as a later slice |
| **R**ules | One business rule per slice | Approval-L1 slice, then approval-L2 slice, then self-approve guard |

Prefer **Rules** and **Path** splits — they keep each slice vertical and demoable.
**Interface** and **Data** splits risk drifting horizontal; keep the model+behavior+UI
for the chosen variant together in one slice.

## Vertical-slice patterns (composition)

- **Walking skeleton** — the thinnest end-to-end slice that exercises every layer for
  one trivial case; later slices thicken it. Good first task for a new feature.
- **CRUD-then-behavior** — a bare entity CRUD slice, then separate slices for each
  non-trivial behavior on it (validation, state transition, derived field, key
  generation). Do NOT bundle complex behavior into the CRUD slice.
- **Workflow-by-state** — one slice per lifecycle transition (draft→submit,
  submit→approve, approve→sync), each independently testable, ordered by dependency.
- **Policy-as-slice** — a cross-cutting policy (security rule, audit, re-entrancy
  guard) is a first-class slice when it carries real logic, not a footnote on another.

## Kent-Beck-style test list (per task) — B4-1

Every task carries a short **test list**: the concrete tests the slice must pass,
written before the slice. This is the to-do list a TDD cycle works through. Keep it
behavioral and specific:

```
TASK-00X — <slice>
test list:
  - <happy-path assertion>           e.g. submitting a draft plan sets state=submitted
  - <boundary / edge>                e.g. effort_mm = 0 is rejected with a validation error
  - <exception / negative>           e.g. approving someone else's plan without rights raises AccessError
  - <rule>                           e.g. a locked month is not overwritten on re-sync
```

Map each test-list item to a `TC-xxx` from D-27 where one exists; where D-27 has no
case for a real behavior, surface the gap (do not silently drop it). The test list is
the bridge between the slice and `hbc-implement`'s RED→GREEN→REFACTOR cycle: each
item is one RED.

## Anti-patterns to reject

- **Horizontal layers** — "all models" / "all services" / "all views" as separate
  tasks. No slice is demoable until the last; integration risk is deferred. Re-slice.
- **Entity-only thinking** — forcing every piece of work into an "entity" task and
  losing UI/admin screens, schedulers, and lifecycle operations as first-class slices.
- **A task with no test list** — fails INVEST-**T**; it is a wish, not a slice.
- **A REQ with no slice** — the B4-7 coverage hole; the exact RCA failure
  (`resource-plan-billable` shipped without slices for REQ-040/041/042).
