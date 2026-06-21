<!-- {project_name}: filled by LLM from project context at generation time. -->
---
document_id: discovery-note
feature: "{feature}"
title: "{project_name} — Discovery Note — feature: {feature}"
status: draft
verdict: ""
signed_off_by: ""
lastStep: ""
updated: ""
---

# {project_name} — Discovery Note — {feature}

## 1. Overview

<!-- Why this feature is discovery_risk=uncertain: what about the domain model is
     not yet understood / unproven. 1 short paragraph. This is a PRE-FREEZE note —
     keep it light; do not turn it into a requirements doc. -->

## 2. Riskiest Assumptions

<!-- Only the few assumptions that actually matter (highest cost if wrong). Each
     row: the assumption, why it's risky, and what concrete observation would
     FALSIFY it. -->

| ID | Assumption | Why risky | What would falsify it |
|----|------------|-----------|------------------------|
| ASM-01 | | | |

## 3. Validation Method

<!-- Per assumption, the cheap method used AND the ground-truth it was checked
     against. Brownfield → real code / DB schema / business-flow; greenfield →
     concrete stakeholder examples. NOT the draft. -->

| ASM | Method (walking-skeleton / example-mapping / code-DB reality-check / domain-review) | Ground-truth checked against |
|-----|--------------------------------------------------------------------------------------|-------------------------------|
| ASM-01 | | |

## 4. Evidence

<!-- What was actually observed — grounded references (file:line, schema, a real
     example), not assertions. An assumption with no falsification attempt is NOT
     validated. -->

- ASM-01: …

## 5. Verdict

**Verdict:** VALIDATED

<!-- One of: VALIDATED (assumptions hold → proceed design-first) /
     RESHAPE (an assumption wrong → revise REQ) / KILL (premise fails → stop). -->

**Signed-off-by:** <!-- USER name/role + date. The LLM must NOT fill this. -->

## 6. REQ Impact

<!-- REQUIRED only when Verdict is RESHAPE or KILL: name the REQ-<FEAT>-NNN to
     revise/drop and the impact. For VALIDATED, write "None". -->

None

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial discovery spike |
