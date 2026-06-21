# D-02 Intake Pipeline (Stages 1d–2)

The path from a raw idea to a discovery-complete, ready-to-generate D-02. Run the
four ordered stages below **in order** — they are distinct and must never be
collapsed into each other (see the boundary box). Headless behaviour for each is
noted; domain decisions follow the Autonomy mode in SKILL.md.

> ⚠️ **Three concepts — keep them separate (the historical re-merge bug):**
> - **① Feasibility** — *idea vs source+framework* · **MANDATORY · early · every feature** · kills infeasible ideas before effort is spent. It is the early kill-gate.
> - **② Quick Discovery** — *elicit the need* · **ALWAYS** (both source-has-structured-reqs and not). Only deep brainstorming is optional.
> - **③ Model-Spike / [DSC]** — *examine the draft D-19 vs ground-truth* · a Phase-1→Phase-2 seam concern, depth driven by `discovery_risk`. NOT a substitute for Feasibility.
>
> Feasibility decides *should we build this at all*; `discovery_risk`/DSC decides *how deeply to spike the model later*. Do not let DSC stand in for the mandatory Feasibility gate, and do not let `discovery_risk` decide feasibility.

## ① Feasibility — MANDATORY first step, every idea (B1-5)

Before any discovery effort, assess whether the idea is buildable against the
real source material and the project framework. **Read the source first** (B1-10):
the brief, project-context.md, the brownfield `existing_system` catalog from the
scan, the framework/platform constraints. Then judge:

- Does the idea fit the platform/framework and its hard constraints (the Stage 6
  technical-constraint reality)? E.g. a feature requiring real-time push on a
  request/response-only stack.
- Does it conflict with an existing system invariant the catalog reveals?
- Is the core assumption even checkable, or is it pure speculation?

Outcome (record in the decision log):
- **Feasible** → proceed to ② Quick Discovery.
- **Infeasible / blocked** → **kill or park the idea now** — surface the blocking
  reason to the user and stop; do not spend discovery effort. Headless `--strict`:
  return `blocked` (`infeasible`). `--assumptions-allowed`: log the feasibility
  risk as an `ASSUMPTION` and continue (never block the first turn).

This is a *feasibility* judgement, not a model-validation spike — the model spike
([DSC]) happens later against the draft D-19. Note the hand-off (B1-4): if
feasibility hinges on an **unproven domain model / key assumption**, flag
`discovery_risk: uncertain` so the P1→P2 seam runs [DSC] against the D-19 draft.
Feasibility does not run the spike itself.

## ② Quick Discovery — ALWAYS (B1-6)

Always elicit the need — both branches:
- **Source already has structured requirements** (tables, numbered lists with IDs)
  → present them for confirmation, then probe only the gaps.
- **Source is thin** → run the full elicitation below.

Either way Quick Discovery runs; it is never skipped. Pre-populate fields from
`project-context.md` where available (stakeholders, timeline, tech stack) and
present as defaults for confirmation. Open with an invitation for the user to
share everything else — goals, constraints, concerns, prior art. Areas to cover:

- **Overview (folds D-01)** — goal, scope context, stakeholders, timeline → the
  D-02 *Project Overview* header (no separate D-01), anchoring feasibility.
- **Scope** — explicit in-scope and out-of-scope. Out-of-scope is as important.
- **User roles** — actors who interact with the system; each gets name + description.
- **Functional requirements** — each a unique `REQ-<FEAT>-NNN` ID (sequential
  within the feature), written per **EARS** (English keyword + content in the
  document output language: `WHEN … THE SYSTEM SHALL …`). Shared requirements →
  `REQ-SHARED-NNN` (defined in the shared D-02, only **referenced** here). Specific
  and testable.
- **Non-functional requirements** — performance, security, availability,
  usability, each with **measurable criteria**. See *NFR numeric targets* below.
- **Constraints and assumptions** — technical, business, legal.
- **Discovery-risk + facets** (A5 — suggest, user confirms, never auto-set) —
  classify `discovery_risk` (known | uncertain), `facets`, `maturity`. `uncertain`
  drives spike **depth** later; it does NOT replace the Feasibility gate above.
  Headless: derive + log.

**Brownfield grounding** (only when scan reports `brownfield: true`): reconcile
every ask against the existing system — see [`brownfield-grounding.md`](brownfield-grounding.md).

At each area boundary, soft-gate: _"Anything else on [area], or move to [next]?"_
Silently capture glossary-worthy terms and business-flow processes — surface them
in Stage 5 handoff.

### NFR numeric targets (B1-3)

A measurable NFR needs a number, not an adjective. When an NFR implies a numeric
target (response time, throughput, uptime, concurrency), **ASK the user for the
number** — it is a domain decision. If the number is genuinely unknown, **do not
fabricate** a plausible default: record an `ASSUMPTION` in the decision log (or an
ADR when it's a load-bearing decision) and mark the criterion as assumed, e.g.
"p95 < 2s (ASSUMPTION — to confirm with PM)". The validator's `NFR_NO_NUMBER`
advisory flags any criterion with no numeric/unit token so none slip through.

## ③ Deep brainstorming — OPTIONAL (B1-7)

A **mandatory stop, not the model's call**: ask the user whether to run a deeper
`bmad-brainstorming` session, or go straight to generation. Do not decide for them
based on perceived complexity. When you offer brainstorming, give **two suggestion
prompts** to seed it:
1. a **topic** suggestion (the weakest/most-uncertain area surfaced in Quick
   Discovery — e.g. "the approval-workflow edge cases");
2. an **output** suggestion (what the session should produce — e.g. "a list of
   alternative state-machine designs to compare").

If they pick brainstorming, pause — they run it separately and resume (Stage 1a
detects the partial D-02; a file in `{output_folder}/brainstorming/` counts as a
source). Headless: skip brainstorming, proceed.

## ④ Supplementary Discovery after brainstorm — MANDATORY (B1-8)

If brainstorming ran, a brainstorm output is raw material, not requirements. Run a
**mandatory** supplementary Discovery pass to fold its results back in: confirm
which ideas become requirements, update scope/roles/REQs, re-probe gaps the
session opened. Only then is discovery complete. (If brainstorming was skipped,
this stage is a no-op.)

## Compaction flush

At the end of discovery, write to the decision log: feasibility verdict, actor
list, REQ count, scope boundaries, `discovery_risk`/`facets`/`maturity`.
**Brownfield:** also one line per probed ask (`<REQ> · <Change Type> · <Existing
System Ref>`) so the classifications survive a mid-probe compaction.
