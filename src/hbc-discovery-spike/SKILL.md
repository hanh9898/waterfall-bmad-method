---
name: hbc-discovery-spike
description: Cheaply validate an uncertain feature's riskiest domain-model assumptions against ground-truth BEFORE producing the full design stack. Produces a discovery-note with a VALIDATED / RESHAPE / KILL verdict (USER sign-off). Use when user says 'discovery spike', 'kiểm chứng model', 'walking skeleton', 'spike', or agent menu [DSC].
---

# Discovery Spike (discovery-note)

## Overview

Generate a **discovery-note** — a *cheap, pre-freeze* validation of a feature's **riskiest domain-model assumptions** against ground-truth, run BEFORE the expensive design→test→build stack. One per feature, **only for features whose model is uncertain**. Output is a light, throwaway-friendly note carrying a verdict:

- **VALIDATED** — assumptions hold against ground-truth → proceed design-first.
- **RESHAPE** — an assumption is wrong → name the `REQ-<FEAT>-NNN` to revise, route back to `hbc-create-requirements` [REQ] `update`.
- **KILL** — the feature premise doesn't hold → stop, don't build.

**Why this exists (RCA root):** the framework's worst failures came from a domain model "gated PASSED" *before* it was ever validated — discovered wrong only *after* code, forcing full-stack rewrites. This step is the cheap kill/reshape gate that the lifecycle lacked. See `process-review/process-retrospective-rca-2026-06-20.md`.

> ⚠️ **Load-bearing discipline (don't repeat the failure modes):**
> 1. **Validate against GROUND-TRUTH, not the draft.** A spike that re-derives the model from the same assumptions catches nothing. Brownfield → check against real **code / DB schema / business-flow**; greenfield → against **concrete stakeholder examples** (example-mapping). (RCA F-4: the spike is a *hypothesis* — its value is only as good as what it tests against.)
> 2. **USER signs off the verdict — the LLM never self-certifies.** Present the evidence; the human decides VALIDATED/RESHAPE/KILL. No sign-off → not done.
> 3. **Stay light.** This is pre-freeze. No version churn, no heavy traceability, no polish. If the model is still moving, that's the point — don't build the stack yet.
> 4. **ASK at every domain decision** (which assumption is riskiest, which method, the verdict). Missing data → stop and ask; never fabricate a default.

## Applicability (conditional — off-ramp first)

Runs **only when the feature is `discovery_risk: uncertain`** (set by the Phase-1 risk-classifier in D-02 frontmatter). If D-02 says `known` (or the user confirms the model is well-understood, low-ambiguity) → **say discovery-spike is N/A, stop, and proceed to design-first.** If D-02 carries no `discovery_risk`, **ASK the user to classify** (known vs uncertain) — don't assume. Wrong-skill off-ramp: this validates *model assumptions*, not data design (→ [ERD]), behaviour (→ [BD]), or requirements text (→ [REQ]).

## Conventions

- Bare paths resolve from skill root. `{skill-root}` / `{project-root}` / `{skill-name}` as usual.
- Communicate in `{communication_language}`; document prose in `{document_output_language}`; file/folder names + Mermaid keywords English.

## On Activation

Resolve customization (`python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`; on failure hand-merge `customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `.user.toml`). Load persistent facts + config. **Resolve feature (B):** `feature=<slug>` → session → ask (headless: required → blocked `feature_required`); validate slug `^[a-z0-9][a-z0-9-]*$`. Written per-feature at `{workflow.output_dir}/discovery-note-{feature}.md`.

## Stage 1: Prerequisites + applicability gate

1a. **Source scan.** Read `D-02` (draft REQ set + `discovery_risk`) and `D-06` (flows) for this feature.
1b. **Applicability check.** If `discovery_risk != uncertain` → off-ramp (N/A, stop). If absent → ASK to classify; `known` → stop.
1c. **Ground-truth inventory.** Brownfield: locate the real **code / DB schema / models / migrations / endpoints** the feature touches (the assumptions will be checked against these). Greenfield: gather **concrete stakeholder examples** (real scenarios with real numbers/edge cases), not hypotheticals.

## Stage 2: Name the riskiest assumptions (ASK — trục C)

Elicit the **domain-model assumptions** the feature rests on (entities, lifecycle/states, invariants, cross-entity timing, key business rules). **Ask the user which are most uncertain / highest-cost-if-wrong** — don't auto-rank. Record each as `ASM-NN` with: the assumption, why it's risky, and what would falsify it. Keep to the few that actually matter (a discovery-note is not a requirements doc).

## Stage 3: Validate against ground-truth (ASK method)

For each `ASM-NN`, pick (ask) a **cheap validation method** and run it against the ground-truth from 1c — never against the draft alone:

- **Walking skeleton / tracer-bullet** — thinnest end-to-end path linking the real components, to confirm the model wires up.
- **Example-mapping** — concrete stakeholder examples exercise the rule/lifecycle; an example that breaks the assumption is a falsification.
- **Code/DB reality-check** — does the existing schema/behaviour contradict the assumption?
- **Domain review** — a stakeholder confirms/refutes with a real case.

Record **evidence** (what was checked, what was found) — grounded references, not LLM assertions. An assumption with no falsification attempt is **not** validated.

## Stage 4: Verdict + USER sign-off

Synthesize per-assumption findings into ONE verdict: **VALIDATED / RESHAPE / KILL**. **Present the evidence and ask the USER to sign off** — the LLM must not self-certify (anti-rubber-stamp). On **RESHAPE/KILL**, name the affected `REQ-<FEAT>-NNN` and the impact; RESHAPE routes to [REQ] `update` (then re-spike if still uncertain), KILL stops the feature. Headless: a sign-off cannot be fabricated → blocked `signoff_required`.

## Stage 5: Generation

Populate `{workflow.template_path}` → `{workflow.output_dir}/discovery-note-{feature}.md`. Ensure: each `ASM-NN` has why-risky + falsifier; Validation Method + Evidence non-empty and grounded; Verdict is one of the three tokens; **Signed-off-by filled** (not a placeholder); if RESHAPE/KILL, the REQ Impact section names ≥1 REQ. Keep it short — resist polishing.

## Stage 6: Validation

```
python3 {workflow.validation_script} "{workflow.output_dir}/discovery-note-{feature}.md" --project-root {project-root}
```

Structural checks: required sections present + non-empty; ≥1 `ASM-NN`; verdict token valid; sign-off present; RESHAPE/KILL ⇒ REQ Impact present. Returns JSON; fix loop / headless apply+block.

**LLM judgment (not the script):** was the validation actually against ground-truth (not the draft)? Is the evidence a real falsification attempt? Is the verdict honestly supported?

## Stage 7: Save and Handoff

Finalize frontmatter (`verdict`, `signed_off_by`, `lastStep = complete`, `updated`). Handoff by verdict: **VALIDATED** → proceed design-first (the Phase-1 gate's model-validation item can cite this note); **RESHAPE** → `hbc-create-requirements` [REQ] `update`; **KILL** → stop. Headless: JSON per `references/headless-contract.md`.

## Validate / Update modes

- **validate:** run Stage 6 only.
- **update:** load baseline, present what changed (new evidence / new verdict), re-validate; a new verdict needs a fresh sign-off.
