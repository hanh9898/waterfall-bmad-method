# Brownfield requirements grounding

Runs only when the project is brownfield — the Stage 1a scan reported `brownfield: true` (a `project_context` exists). A general customer ask is not a requirement until it states *what it changes* in the existing system. Greenfield: this step does not apply.

## Gap-analysis per ask

For each functional ask, classify and anchor it against AS-IS:

- **Change Type** — `NEW` (no AS-IS), `CHANGE` (alters existing behavior), or `REMOVE`.
- **Existing System Ref** — the existing feature/flow/entity/module/service it touches. Source the anchor pick-list **generically** (any project type, not just DB/API):
  - (a) the scan's `existing_system` catalog — `entities` (←D-19) / `endpoints` (←D-21), for DB/API products;
  - (b) the **documented AS-IS** listed in the catalog's `sources_present` — read a named *Components / Modules / Services* section of `project-context.md` or the `bmad-document-project` docs for module/service/component anchors. (Don't read the whole doc — go to the inventory section.)
  Enrich flows from a `D-06` AS-IS section if one exists.
- For every `CHANGE` / `REMOVE`, write a `Change Spec — <REQ>` block: `AS-IS → TO-BE · invariants · out-of-scope`. `NEW` needs none.

If the catalog's `hint` is set (no structured D-19/D-21 anchors), **don't stop** — derive anchors from the documented AS-IS in `sources_present` (their modules/services/components). **Degraded mode:** if there is no documented AS-IS at all, recommend running `bmad-document-project` and do NOT fabricate anchors (headless: `blocked: brownfield_ungrounded`). Creating D-19/D-21 baselines is one option for DB/API products, not the only path.

**NFRs too.** A non-functional requirement that tightens an existing guarantee is also a CHANGE: state the **current baseline → target** in its measurable criteria (e.g. "p95 5s → < 2s"), not just the target. (NFRs have no Change Type column; the grounding lives in the criteria text.)

**TO-BE vs Acceptance Criteria.** In a Change Spec, *TO-BE* is the target **behavior** (what changes); the D-02 *Acceptance Criteria* column is **how to verify** it (the testable condition). They are not duplicates — TO-BE describes the delta, AC proves it.

## Output

Use the D-02 **brownfield table variant** (adds `Change Type` + `Existing System Ref`) and add the Change Spec blocks. The deterministic backstop is `validate-requirements.py --brownfield`; the meaningful-vs-vacuous judgment is the Stage 4b semantic facet.

## Compaction flush

After classifying, append one line per probed ask to the decision log — `<REQ-id> · <Change Type> · <Existing System Ref>` (e.g. `REQ-auth-002 · CHANGE · flow:login`). A mid-probe compaction otherwise loses these human-confirmed classifications and forces re-interrogating the user.

## Headless

With `--headless`: derive `Change Type` / `Existing System Ref` from the `existing_system` catalog where the anchor is unambiguous. Where an ask cannot be grounded (no matching anchor, or the delta needs judgment), append the assumption to the decision log and return `blocked` with reason `brownfield_ungrounded` — do not emit an ungrounded `CHANGE`/`REMOVE`. See `references/headless-contract.md`.
