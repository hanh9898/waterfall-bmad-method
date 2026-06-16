# How to Run a Phase Gate

> 🌐 **English** · [Tiếng Việt](../../vi/how-to/run-a-phase-gate.md)
>
> 🔧 **How-to** — do one specific task: run and handle the result of a Phase Gate. To understand *what a Gate is*, see [Core Concepts](../explanation/concepts.md#3-phase-gate--a-control-checkpoint-between-phases).

## Goal

Check whether a phase is complete enough to advance to the next.

## Run the gate

Always **pass the phase number** (1–4) with the command:

```
PG 2
```

or run non-interactively:

```
PG 2 -H
```

**Required** arg: `1` | `2` | `3` | `4` (the phase number); add `-H` to run headless.

## Read the result

The gate runs two layers — **automated checks** (are required deliverables present, is the format correct) + **LLM evaluation** (is content clear, complete, consistent) — then returns a **PASSED** or **FAILED** report.

The report is saved under `{output_folder}/gates` (default `_bmad-output/gates`), named like `phase-<n>-gate*`.

## When it's FAILED

1. Open the gate report and read the list of unmet items.
2. Fix the exact deliverable called out (e.g. D-02 missing acceptance criteria → open `REQ` in `update` mode).
3. Re-run `PG <n>`.
4. Repeat until **PASSED** before advancing.

> 💡 A "FAILED" gate isn't your fault — it's blocking an error from leaking into a later phase (where the fix is far more expensive).

## Tips

- Run the gate **before every phase transition**, don't leave it to the end.
- Before running `PG`, run `TRU` to update traceability — the gate also inspects `gate_status` in the matrix.
- Use `-H` when running inside CI/automation scripts.

## Related

- 🔗 [Manage Traceability](manage-traceability.md)
- 🗺️ [Workflow Map](../tutorials/workflow-map.md)
