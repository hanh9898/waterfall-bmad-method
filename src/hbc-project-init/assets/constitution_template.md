---
title: "{project_name} — Project Constitution (HBC cross-phase invariants)"
docType: constitution
scope: shared
version: "1.0"
created: ""
updated: ""
stepsCompleted: []
lastStep: ""
semanticReview:
  status: pending        # pending | passed  — passed only when openFacets empty AND user signs off
  openFacets: []
  reviewedOn: ""
---

# Project Constitution

> The **cross-phase invariant principles** of this project. Unlike a per-feature
> deliverable, the constitution is written **once** in Phase 0 and stays stable —
> it is the contract every phase, every persona, and every generated document
> inherits. The five HBC personas (`hbc-agent-{ba,architect,qa,dev,tester}`)
> reference it; a phase that violates a principle below is wrong even if its own
> gate is green.
>
> Mark any value you cannot yet confirm with a needs-clarification marker (the
> bracketed `NEEDS CLARIFICATION:` form used in the placeholders below) — never
> silently invent it. The validator and the semantic review cannot pass while any
> such marker remains; resolve or delete every one before completing Phase 0.

## 1. Test-First (TDD)

Every behavior change is driven by a failing test written **before** the
implementation. No production code lands without a test that first failed for the
right reason. The Phase-3 `hbc-implement` cycle (red → green → refactor) is the
mechanism; this principle is *why* it is non-negotiable.

- Test level follows the V-pair of the deliverable (D-02→acceptance, D-19→integration, D-27→unit).
- Coverage is judged by **facet** (read/write · api/admin · lifecycle), not line count.

_Project-specific stance:_ [NEEDS CLARIFICATION: any area exempt from test-first, e.g. throwaway spikes?]

## 2. Language Policy

- **Source / identifiers / file names: English**, always.
- **Document prose / generated output: `{document_output_language}`** (from `_bmad/config.toml`).
- **Chat / communication: `{communication_language}`.**
- NO hardcoded third language anywhere in source or validators.

This split is invariant: a generated D-xx document is English-named but its body
follows `{document_output_language}`; code comments follow the project's
configured comment language (see D-12), never an ad-hoc choice.

## 3. Separation of Duties (SoD)

Each phase has an **owner persona**, and that persona does not self-certify the
gate it is judged by:

| Phase | Owner | Produces |
|---|---|---|
| 0 | (this skill) | shared baselines + constitution |
| 1 Analysis | `hbc-agent-ba` | D-02, D-03, D-06 |
| 2 Design / Test-Design | `hbc-agent-architect` / `hbc-agent-qa` | D-09/D-19/D-12/D-21/D-14/D-16, D-26/D-27 |
| 3 Implementation | `hbc-agent-dev` | code (TDD) |
| 4 Testing | `hbc-agent-tester` | execution, acceptance |

A gate is enforced by `hbc-phase-gate` / `hbc-acceptance-check`, **not** by the
producing persona. Sign-off on meaning (semantic review, model validation) is a
human/independent-lens decision — the producer presents evidence, never grades itself.

## 4. Handoff Through Artifact

Phases communicate **only through committed D-xx artifacts and the traceability
matrix** — never through ephemeral chat context. If a downstream phase needs a
fact, that fact lives in an artifact with a stable id (`REQ-`, `TC-`, a D-xx
section). **Change a spec ⇒ regenerate the downstream artifacts** (cascade-sync,
`hbc-traceability`) — this is the antidote to silent SDD/waterfall drift, and is
itself a load-bearing invariant, not a convenience.

## 5. Simplicity Caps

Default to the simplest thing that satisfies the requirement and its facets;
complexity must be **justified against a requirement**, not added speculatively.

- The applicability-catalog decides which deliverables a feature needs — an
  unneeded layer is marked **N/A with a reason**, never produced "just in case".
- `maturity: exploratory` loosens the *required* node-set and ASK-volume; it
  **never** loosens the correctness floor (a red reconcile is still a FAIL).
- Caps the project commits to (max nesting, max file size, no premature
  abstraction, etc.): [NEEDS CLARIFICATION: project-specific simplicity caps, if any beyond the defaults]

## Amendment

The constitution is stable, not frozen. To change a principle, record the change
here with a date and rationale (it ripples to every in-flight feature — treat it
as a cascade event). Re-running `hbc-project-init` detects drift between this file
and the live config/baselines and proposes an update in place.

| Date | Principle | Change | Rationale |
|---|---|---|---|
|  |  | Initial version |  |
