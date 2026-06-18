# Brownfield requirements grounding

Runs only when the project is brownfield — the Stage 1a scan reported `brownfield: true` (a `project_context` exists). A general customer ask is not a requirement until it states *what it changes* in the existing system. Greenfield: this step does not apply.

## Gap-analysis per ask

For each functional ask, classify and anchor it against AS-IS:

- **Change Type** — `NEW` (no AS-IS), `CHANGE` (alters existing behavior), or `REMOVE`.
- **Existing System Ref** — the existing feature/flow/entity it touches, picked from the scan's `existing_system` catalog (`entities` / `endpoints`). Read `project-context.md` for tech stack/rules; enrich flows from a `D-06` AS-IS section if one exists.
- For every `CHANGE` / `REMOVE`, write a `Change Spec — <REQ>` block: `AS-IS → TO-BE · invariants · out-of-scope`. `NEW` needs none.

If the catalog's `hint` is set, the AS-IS is sparse — tell the user and suggest running `bmad-document-project` / creating the Phase 0 baselines (shared D-19/D-21) before eliciting.

**NFRs too.** A non-functional requirement that tightens an existing guarantee is also a CHANGE: state the **current baseline → target** in its measurable criteria (e.g. "p95 5s → < 2s"), not just the target. (NFRs have no Change Type column; the grounding lives in the criteria text.)

**TO-BE vs Acceptance Criteria.** In a Change Spec, *TO-BE* is the target **behavior** (what changes); the D-02 *Acceptance Criteria* column is **how to verify** it (the testable condition). They are not duplicates — TO-BE describes the delta, AC proves it.

## Output

Use the D-02 **brownfield table variant** (adds `Change Type` + `Existing System Ref`) and add the Change Spec blocks. The deterministic backstop is `validate-requirements.py --brownfield`; the meaningful-vs-vacuous judgment is the Stage 4b semantic facet.

## Compaction flush

After classifying, append one line per probed ask to the decision log — `<REQ-id> · <Change Type> · <Existing System Ref>` (e.g. `REQ-auth-002 · CHANGE · flow:login`). A mid-probe compaction otherwise loses these human-confirmed classifications and forces re-interrogating the user.

## Headless

With `--headless`: derive `Change Type` / `Existing System Ref` from the `existing_system` catalog where the anchor is unambiguous. Where an ask cannot be grounded (no matching anchor, or the delta needs judgment), append the assumption to the decision log and return `blocked` with reason `brownfield_ungrounded` — do not emit an ungrounded `CHANGE`/`REMOVE`. See `references/headless-contract.md`.
