# D-27 Technique Map (B3-5) — specification-based test design

Each test case must map to the **right technique for its source artifact**. This is
the specification-based test-design discipline: the technique is chosen from what
the requirement *is*, not improvised. Use this map during Discovery (Stage 2) to
pick a technique per REQ, and during Semantic Review (Stage 4b) to verify each TC's
technique↔source pairing is sound.

| Technique | Use when the REQ is… | Source artifact | What the TCs must cover |
|-----------|----------------------|-----------------|--------------------------|
| **Decision Table** | a set of business **rules** / conditions → actions (e.g. "month committed AND role X ⇒ guard") | D-02 rule text, D-06 gateways | one TC per rule combination; the predicate asserted by **enum/structured value**, never by parsing a localized message |
| **State Transition** | a **lifecycle** / state machine (submitted→approved_l1→approved_l2; reject terminal) | D-02 lifecycle, D-06 swimlane | every valid transition **and** the **wrong/illegal transitions** (skip-level, transition from a terminal state) — wrong-transition coverage is mandatory, not optional |
| **Equivalence Partitioning / Boundary Value (EP/BVA)** | a **data field** with ranges / constraints (MM ≥ 0, 8-month window, effort_ratio 0–100%) | **D-19** field types + CHECK constraints | one TC per partition + the boundaries (0, max, just-over, negative, non-numeric); ground the partitions in the **real D-19 column type/constraint** |
| **Use-Case / Scenario** | an **end-to-end flow** spanning actors/steps | **D-06** business flow paths | happy path + each alternate + each exception path from the D-06 diagram |
| **Example Mapping** | an ambiguous rule needing **concrete examples** to pin behavior | D-02 + Open Floor | rule → examples → questions; surface the open questions as `openFacets` rather than guessing |

## Pairing rules

- **EP/BVA grounds to D-19** — a boundary TC for a numeric field must use the field's
  real type and constraint from D-19 (e.g. `effort_mm` CHECK ≥ 0), not an invented
  range. `check-test-spec-grounding.py` (B3-2) flags Test-Data tokens absent from the
  schema; reconcile them here.
- **State-Transition must cover wrong transitions** — a lifecycle REQ whose TCs only
  walk the happy state path is incomplete; add the illegal-transition TCs (these are
  also the negative-facet TCs the facet metric expects).
- **Decision-Table predicates assert structured values** — assert the enum/flag
  (`committed_reason = locked`), not a Vietnamese/localized string, so the TC is not
  brittle to wording.
- A single REQ may legitimately need **several** techniques (a lifecycle REQ with a
  numeric field needs State-Transition + BVA). Map each TC to the one technique it
  embodies; the REQ's facet set (read/write·api/admin·lifecycle) is the cross-check.
