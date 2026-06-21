# How to Run a Phase Gate

> 🌐 **English** · [Tiếng Việt](../../vi/how-to/run-a-phase-gate.md)
>
> 🔧 **How-to** — do one specific task: run and handle the result of a Phase Gate for **one feature**. To understand *what a Gate is*, see [Core Concepts](../explanation/concepts.md#4-phase-gate--a-control-checkpoint-between-phases).

## Goal

Check whether a phase of **one feature** is complete enough to advance to the next. Phase Gates now run **per-feature**: each feature has its own gate set, controlled independently of other features.

## Run the gate

Always **pass the phase number** (1–4) plus the **feature slug** via `feature=`:

```
PG 2 feature=auth
```

or run non-interactively (headless):

```
PG 2 feature=auth -H
```

**Required** args:

- `1` | `2` | `3` | `4` — the phase number
- `feature=<slug>` — the feature slug to gate
- add `-H` to run headless

> ⚠️ In headless mode, `PG` **requires** `feature=`. Without it, the gate is blocked with code `feature_required`.

## Read the result

The gate runs two layers — **automated checks** (are required deliverables present, is the format correct) + **LLM evaluation** (is content clear, complete, consistent) — then returns a **PASSED** or **FAILED** report.

The gate reads and writes its report inside **that feature's own** folder:

```
_bmad-output/features/<feature>/gates/phase-<n>-gate*.md
```

For example with `feature=auth`, the Phase 2 gate writes to `_bmad-output/features/auth/gates/phase-2-gate.md`.

### Phase-specific conditions

- The **Phase 1 gate** has a **`P1-09` — model-validation** item: the USER **signs off** that the domain model (entities, states, rules) has been validated before closing Analysis. This item is **greenfield-adaptive** (with no code yet to reconcile against, confirm on assumptions/PRD). Its purpose: stop a "wrong model that still got PASSED" error from leaking down into design.
- The **Phase 1 gate** also has a **`P1-11`** item (only when D-02 sets `discovery_risk: uncertain`): it requires a **discovery-note** with verdict **VALIDATED** + signed off (run `DSC` / `hbc-discovery-spike`). RESHAPE/KILL — or missing/unsigned — means the model is **not ready** → **FAIL** until it is re-spiked to VALIDATED. `known`/absent → N/A. For an uncertain feature, this is the *path* that validates P1-09 (not a bare attestation).
- The **Phase 2 gate** additionally requires **`IR` (readiness check)** to have PASSED — `IR` reconciles D-02 ↔ D-21/D-26/D-27 and the traceability matrix before allowing advance to Phase 3.
- The **Phase 3 gate** checks for **RED evidence** — a recorded failing test must exist *before* code was written (test-first, per soft TDD).

## When it's FAILED

1. Open the gate report in `features/<feature>/gates/` and read the list of unmet items.
2. Fix the exact deliverable called out (e.g. D-02 missing acceptance criteria → open `REQ` in `update` mode with the same `feature`).
3. Re-run `PG <n> feature=<feature>`.
4. Repeat until **PASSED** before advancing.

> 💡 A "FAILED" gate isn't your fault — it's blocking an error from leaking into a later phase (where the fix is far more expensive).

## Tips

- Run the gate **before every phase transition**, don't leave it to the end.
- Before running `PG`, run `TRU` to update the feature's traceability — the gate also inspects `gate_status` in the `features/<feature>/traceability/` matrix.
- For Phase 2, run `IR feature=<feature>` to PASSED first, then run `PG 2`.
- Use `-H` when running inside CI/automation scripts (always include `feature=`).
- Not sure what's next? Ask `bmad-help` for a suggestion.

## Per-feature gate flow

```mermaid
flowchart TD
    A["PG n feature=slug"] --> B{"Headless with feature=?"}
    B -->|"No"| C["Blocked: feature_required"]
    B -->|"Yes"| D["Read the feature's deliverables"]
    D --> E["Automated checks + LLM evaluation"]
    E --> F{"Result"}
    F -->|"FAILED"| G["Fix deliverable, re-run"]
    G --> D
    F -->|"PASSED"| H["Write gates/phase-n-gate.md, advance"]
```

## Related

- 🔗 [Manage Traceability](manage-traceability.md)
- 🤖 [Headless Mode](use-headless-mode.md)
- 🗺️ [Workflow Map](../tutorials/workflow-map.md)
- 📖 [Skills Catalog](../reference/skills-catalog.md)
```
