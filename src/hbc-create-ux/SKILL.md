---
name: hbc-create-ux
description: Generate D-14 UX / Screen Design — screens, components, states, interactions, traced to REQ and DESIGN.md tokens, with optional Claude Design integration. Use when user says 'UX design', 'screen design', 'thiết kế UX', 'tạo D-14', or agent menu [UX].
---

# Create UX / Screen Design (D-14)

## Overview

Generate D-14 (UX / Screen Design) for a feature — the **screens**, **components**, **states**, and **interactions** of the user-facing surface, each traced to `REQ-<FEAT>-NNN` and to `D-06` flow paths, with visual tokens referenced (not duplicated) from a shared **DESIGN.md** by `{path.to.token}`. D-14 is the *spec-of-record* for what/how-it-works; DESIGN.md owns how-it-looks; a Claude Design mockup (optional) is a realization that conforms to both. This closes the "mockup-island / E2E pending-design" gap: every screen/component is traceable.

Stage flow: Prerequisites → Discovery → Generation → Validation. `create` / `update` / `validate` + `--headless`. Python 3.10+.

**Applicability:** required only when the feature has the `has-ui` facet (per the applicability-catalog). Pure back-end / no UI → N/A.

## Conventions

- Bare paths from skill root. `{skill-root}` / `{project-root}` / `{skill-name}`.
- Communicate in `{communication_language}`; document prose in `{document_output_language}`; file/folder names + token paths English.

## On Activation

Resolve customization (`resolve_customization.py`; fallback hand-merge). Load persistent facts + config. **Resolve feature (B):** `feature=<slug>` → session → ask (headless: required → blocked `feature_required`). Written per-feature at `{workflow.output_dir}/D-14-{feature}-ux.md`.

## Stage 1: Prerequisites

1a. **Source scan.** Read `D-02` (UI-facing REQs), `D-06` (flow paths each screen serves), and the shared `DESIGN.md` (token contract) if present.
1b. **Applicability check.** If the feature has no `has-ui` facet (catalog instance marks D-14 N/A) → say so and stop unless overridden.
1c. **Claude Design gate (ASK — trục C):** ask whether the user uses **Claude Design** for this feature. The answer is the user's, not assumed:
   - **Yes** → D-14 links to it: tokens resolve from DESIGN.md (shared contract); the committed mockup path is referenced per screen; sync rides Claude Code `/design-sync` push/pull (spec-of-record D-14+DESIGN.md wins on conflict; a canvas edit pulled back makes D-14 stale → user updates D-14, never silent).
   - **No** → D-14 stands alone in text (screens/components/states), tokens written/derived from code; traceability + structural reconcile still apply (visual-regression-vs-mockup skipped).
1d. **Intent gate.** UX, not architecture (→ `hbc-create-architecture` [AD]).

## Stage 2: Discovery (ASK every domain decision — trục C)

Derive a proposal from D-02/D-06, present it, let the user confirm/override (headless: derive + log). Capture:

- **Screens** (`SCR-NN`) — each named, the REQ(s) + D-06 path it serves.
- **Components** (`CMP-NN`) — reusable units per screen; visual props reference DESIGN.md tokens by `{path.to.token}` (don't inline hex/px).
- **States** — per component: default / loading / empty / error / disabled (and any feature-specific).
- **Interactions** — behaviour on user action (transitions, validation, feedback).
- **Dev notes** — non-obvious implementation constraints.

Soft-gate per screen.

## Stage 3: Generation

Populate `{workflow.template_path}` → `{workflow.output_dir}/D-14-{feature}-ux.md`. Ensure: every screen/component has a unique id; every screen names its REQ + D-06 path; component visuals reference DESIGN.md tokens (not inline values); states enumerated; no empty sections. When Claude Design is used, reference the committed mockup path (e.g. `_bmad-output/features/{feature}/ux/`) per screen so the build graph can see it. Ids stable across updates (matrix references them — append, don't renumber).

## Stage 4: Validation

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-14-{feature}-ux.md" --project-root {project-root}
```

Structural checks: required sections present + non-empty; ≥1 screen (`SCR-NN`); screen/component ids well-formed + unique; ≥1 REQ reference; component visual values use `{path.to.token}` refs (flag inline hex/px as a warning). JSON with `auto_fixable`. Fix loop / headless apply+block.

**LLM judgment:** screens cover every UI-facing REQ; states are complete (not only happy path); tokens referenced are coherent; (Claude Design) D-14 ↔ mockup consistent.

## Stage 4b: Semantic Review (Layer 2)

Per `.claude/skills/hbc-shared/references/semantic-review-rubric.md`. Facet-split: flag any UI-facing REQ with no screen, or a screen with only the happy state while D-02 implies error/empty/admin variants. Record `semanticReview` frontmatter (`passed` only when `openFacets` empty).

## Stage 5: Save and Handoff

Finalize frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). Suggest next: D-26/D-27 (UI-acceptance / E2E derive from screens), and traceability matrix extension REQ→screen→component→token→code→test. Headless: JSON per `references/headless-contract.md`.

## Validate / Update modes

- **validate:** Stage 4 only.
- **update:** load baseline, diff changed screens/components, re-validate; append new ids; bump version on semantic change. When Claude Design used and a canvas edit was pulled, surface the delta and require D-14 update (spec wins).

## Sync Handoff

`update` only. Skip if `--invoked-by-sync`. Default: suggest `hbc-traceability impact`. Contract: `hbc-traceability/references/impact-capability.md`.
