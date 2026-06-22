---
name: hbc-create-ux
description: Generate D-14 UX / Screen Design — screens, components, states, interactions, traced REQ→screen→component→test, visuals from a single design-token source, with optional Claude Design integration. Use when user says 'UX design', 'screen design', 'thiết kế UX', 'tạo D-14', or agent menu [UX].
---

# Create UX / Screen Design (D-14)

## Overview

Generate D-14 (UX / Screen Design) for a feature — the **screens**, **components**, **states**, and **interactions** of the user-facing surface, each traced `REQ-<FEAT>-NNN → screen → component → test`, with visual values referenced (not duplicated) from a **single design-token source** (e.g. DESIGN.md) by `{path.to.token}`. D-14 is the spec-of-record for what/how-it-works; the token source owns how-it-looks; a Claude Design mockup (optional) is a realization that conforms to both. This closes the "mockup-island / E2E pending-design" gap: every screen/component is traceable to a requirement and to a (named-first) test.

Stage flow: Prerequisites → Discovery → Generation → Validation → Semantic review → Save. `create` / `update` / `validate` + `--headless`. Python 3.10+.

**Applicability (framework-complete, N/A is catalog-decided).** D-14 is `required if has-ui else n-a` (catalog). A feature with no UI is N/A **by the per-feature applicability instance**, never by trimming this layer — the full UX capability always exists; the catalog decides whether a given feature uses it.

## Conventions

- Bare paths from skill root. `{skill-root}` / `{project-root}` / `{skill-name}`.
- Communicate in `{communication_language}`; document prose in `{document_output_language}`; file/folder names + token paths English. NO hardcoded section names in any other language.

## Autonomy (A5)

Separate **mechanical** decisions (id assignment, table formatting, sort order, which section a row belongs to — decide and proceed) from **domain** decisions (which screens/components are in scope, whether a screen needs a non-happy state, whether a REQ is genuinely UI-facing, whether to adopt Claude Design — **ASK; never invent a default**). The Claude Design gate (1c) and per-screen scope (Stage 2) are domain decisions. Headless: `--strict` blocks at the first unresolved domain decision (`scope_unconfirmed`); `--assumptions-allowed` (CI default) logs the most defensible option to `.decision-log.md` as an `ASSUMPTION` and continues.

## Headless Mode

`--headless` / `-H` runs every stage non-interactively. Full contract + flag set + return JSON: `references/headless-contract.md`. The Claude Design gate defaults to frontmatter `uses_claude_design` / `--uses-claude-design` (default false).

## On Activation

Resolve customization (`resolve_customization.py`; fallback hand-merge — keep `{workflow.*}` in memory all session). Load persistent facts + config. **Resolve feature (B):** `feature=<slug>` → session → ask (headless: required → blocked `feature_required`). Written per-feature at `{workflow.output_dir}/D-14-{feature}-ux.md`. If a partial D-14 exists (`lastStep` ≠ `complete`), surface it with its `updated` stamp and offer resume.

## Stage 1: Prerequisites

1a. **Source scan.** Read `D-02` (UI-facing REQs), `D-06` (flow paths each screen serves), and the shared design-token source (DESIGN.md) if present.
1b. **Applicability check.** If the feature's applicability instance marks D-14 N/A (no `has-ui` facet) → say so and stop unless overridden (headless: blocked `not_applicable`, not an error). Do **not** fabricate screens for a non-UI feature.
1c. **Claude Design gate (UX-1 — ASK before generate, trục C).** Ask whether the user uses **Claude Design** for this feature. The answer is the user's, never assumed:
   - **Yes** → D-14 **links** to it: set `uses_claude_design: true` and `design_token_source` (UX-6 — one source); reference the committed mockup path per screen (UX-2); sync rides Claude Code `/design-sync` push/pull — **spec-of-record D-14 + token source wins on conflict**; a canvas edit pulled back makes D-14 stale → user updates D-14, never silent.
   - **No** → D-14 stands alone in text (screens/components/states); tokens written/derived from code; traceability + structural reconcile still apply (visual-regression-vs-mockup is N/A, not skipped silently — note it).
1d. **Intent gate.** UX, not architecture (→ `bmad-create-architecture` [AD]) or requirements (→ `hbc-create-requirements` [REQ]).

## Stage 2: Discovery (ASK every domain decision — trục C)

Derive a proposal from D-02/D-06, present it, let the user confirm/override (headless: derive + log). Capture:

- **Screens** (`SCR-NN`) — each named, the REQ(s) + D-06 path it serves; the committed mockup path when Claude Design is used (UX-2).
- **Components** (`CMP-NN`) — reusable units per screen; visual props reference token source by `{path.to.token}` (UX-3/UX-6 — don't inline hex/px); `Code Ref` left `—` until implemented (the component-map ↔ code link, UX-3).
- **States** — per component: default / loading / empty / error / disabled (and feature-specific). Enumerate beyond happy path.
- **Interactions** — behaviour on user action.
- **Traceability rows (UX-4 / UX-7)** — for each screen, name its `Test Ref` (E2E/UI) **now, before code exists** (outside-in ATDD): the test is the executable acceptance of the screen. The living matrix engine is owned by `hbc-traceability` [TR] (forward-ref — do not build it here); D-14's Traceability table is the authoritative UI slice TR ingests.
- **UI acceptance (UX-5)** — per screen: acceptance criteria + a visual-regression baseline reference (the mockup when Claude Design is used; else N/A). The visual-diff **tool is consumer-provided** — record the contract (baseline path + method), do not assume one engine. The actual visual-diff run + verdict is Phase 4 [TE]/[AC].

Soft-gate per screen.

## Stage 3: Generation

Populate `{workflow.template_path}` → `{workflow.output_dir}/D-14-{feature}-ux.md`. Ensure: every screen/component has a unique id; every screen names its REQ + D-06 path; component visuals reference tokens (not inline values); states enumerated; the Traceability table links REQ→screen→component→test; UI-acceptance rows present per screen. When Claude Design is used, set `design_token_source`, `uses_claude_design: true`, and the mockup path per screen. Ids stable across updates (the matrix references them — append, don't renumber).

**Maturity (UX-8, fwd T3.16 — advisory now).** Set frontmatter `maturity`. `exploratory` relaxes which optional rows are mandatory (e.g. full visual-regression) but the correctness floor (REQ→screen→test trace) is invariant. The actual gate-ceremony relaxation is enforced by `hbc-phase-gate` (T3.16); D-14 only records the flag.

## Stage 4: Validation

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-14-{feature}-ux.md" --project-root {project-root}
```

Structural (blocking for save): required sections present + non-empty; ≥1 screen (`SCR-NN`); ids well-formed + unique; ≥1 REQ reference; inline hex/px in Components flagged as advisory; `churn` (T2.11) reported.

Then the **advisory** consistency check (never blocks — the blocking inter-doc gate is [IR]/[PG]):

```
python3 {workflow.consistency_script} "{workflow.output_dir}/D-14-{feature}-ux.md" --project-root {project-root} [--code-dir <ui source dir>] [--uses-claude-design]
```

Surfaces (UX-2/3/4/6/7): `REQ_NO_SCREEN` / `SCREEN_NO_REQ` / `SCREEN_NO_COMPONENT` / `SCREEN_NO_TEST` (coverage), `COMPONENT_NO_TOKEN`, `MOCKUP_MISSING` + `TOKEN_SOURCE_MISSING` (when Claude Design), and `COMPONENT_NOT_IN_CODE` (when `--code-dir` given — component-map↔code reconcile, ground-truth = code). Surface each for the user; never auto-add. If the script/Python is unavailable, fall back to LLM-only review.

**LLM judgment:** screens cover every UI-facing REQ; states complete (not only happy path); tokens coherent; (Claude Design) D-14 ↔ mockup consistent.

**Fix:** interactive loop / headless apply only `auto_fixable` (else blocked `validation_failed`); advisories logged, never block.

## Stage 4b: Semantic Review (Layer 2, T2.12)

Per `.claude/skills/hbc-shared/references/semantic-review-rubric.md` with an **independent skeptic lens** + **facet-split** (read vs write/state-change · UI/admin surface · lifecycle states): flag any UI-facing REQ with no screen, a screen with only the happy state while D-02 implies error/empty/admin variants, an inconsistency between D-14 and the mockup. List every unresolved concern in `openFacets`. Record `semanticReview` frontmatter: `status: passed` **only when `openFacets` is empty AND the user signs off** (headless follows Autonomy); else `pending`.

## Stage 5: Save and Handoff

Finalize frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). On create, fill the blank date in the seeded Revision History row. Suggest next: D-26/D-27 (UI-acceptance / E2E derive from the named tests), Phase-2 gate [PG], and `hbc-traceability` to ingest the REQ→screen→component→test slice. Headless: JSON per `references/headless-contract.md`.

## Validate / Update modes

- **validate:** Stage 4 only (structural + advisory consistency).
- **update:** load baseline, diff changed screens/components, re-validate; append new ids; auto-append a Revision History row. **Anti-churn (T2.11):** bump the version **once per session**, not per edit — the validator returns `churn`; when `churn.high_churn` is true the model isn't frozen — surface it and suggest `maturity: exploratory` or a `[DSC]` spike instead of another bump. When Claude Design used and a canvas edit was pulled, surface the delta and require a D-14 update (spec wins).

## Sync Handoff

`update` only. Skip if `--invoked-by-sync` (BR-13 suppression guard — avoids the update→sync→update loop). Default: suggest `hbc-traceability impact`. Auto-chained when `{workflow.auto_sync_after_update}` is true (default false). Contract: `hbc-traceability/references/impact-capability.md`.

**Matrix column (B7-2):** on save (create or update), run `hbc-traceability update feature={feature}` so this phase self-writes its `design_ref` column (screen/component refs) — don't defer to a manual step (the Phase-2 gate cascade-precheck blocks if missing). Distinct from / lighter than the `impact` cascade.
