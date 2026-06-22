---
name: hbc-rebaseline
description: "Re-baseline cross-feature khi một model lõi/shared đổi sau Phase 3 — tính blast-radius (feature/artifact bị ảnh hưởng) bằng build-graph rollup, lập kế hoạch re-baseline per-feature ở cấp epic/baseline-change. dry-run plan → confirm → apply; idempotent. Use when user says 'rebaseline', 'tái lập baseline', 'đổi model lõi/shared', 'blast radius', 'thay đổi xuyên feature', or agent menu [RBL]."
---

# Re-baseline cross-feature (shared-model change)

## Overview

A shared / core model changing **after Phase 3** — shared D-19, shared D-12, or a core model like `project.project` that several features build on — leaves every in-flight feature that derives from it potentially **STALE**. This skill answers the one question per-feature tooling cannot: **which features, and which artifacts inside them, are in the BLAST RADIUS of this shared change?** — then routes a re-baseline plan per affected feature.

It is a **NEW engine, NOT an extension of `hbc-migrate`** (B14-6). Migrate is a one-time layout/D-code upgrade *within* the per-feature shape; rebaseline is the **cross-feature ripple** of a shared-model change *above* the feature level. Same discipline (dry-run → confirm → apply, idempotent); separate code.

**Args:** `plan` (default — dry-run, writes nothing) · `apply` (write the baseline-change envelope). Required for a plan: `changed=<model.token>` (the shared model that changed, e.g. `project.project`). Optional: `change-id=<id>` (names the baseline-change epic), `-H`/`--headless` with `--strict` or `--assumptions-allowed` (see Autonomy).

Engine: `{workflow.rebaseline_script} --root {workflow.features_dir} --out-root {workflow.baseline_change_dir}` (+ `--changed`, `--change-id`, `--apply`, `--json`). Determinism (load per-feature graphs, extract model surface, compute blast-radius rollup, write envelope, idempotency) lives in the script; judgment (is this token truly shared? which features re-baseline first? how deep does the re-derive go?) lives in the skill. The engine's `--json` shape is the **single source of truth** for `references/headless-contract.md`.

## The epic / baseline-change level (A6)

A shared change is a **unit-of-work that spans features** — not a per-feature task. The engine introduces an explicit **baseline-change** record (an epic ABOVE the feature in the layout): one envelope holding the changed shared node, the computed blast-radius, and one re-baseline row per affected feature.

```
_bmad-output/baseline-change/<change-id>/
    rebaseline-plan.json   # the dry-run plan, frozen at apply time
    .decision-log.md       # appended on apply
```

This level is **data the engine emits**, not just a concept — it is where cross-feature change is tracked when no single feature owns it.

## Conventions

Bare paths resolve from the skill root. `{skill-root}` = installed dir; `{project-root}`-prefixed from project. Output written in `{document_output_language}`; communicate in `{communication_language}`.

## Autonomy (A5)

Separate **mechanical** from **domain** decisions. Mechanical — loading per-feature graphs, extracting the model surface, the blast-radius rollup (who references the changed token, which downstream artifacts go stale), idempotent envelope write — are deterministic; **decide and proceed**. Domain — **is this token genuinely a shared/core model** (vs one feature's internal model the caller mis-named), **which feature re-baselines first**, **how deep** each re-derive goes (D-19 only, or down through code) — **ASK; never silently default**. If the engine warns `not_cross_feature_shared` (only one feature touches the token), confirm with the user before treating it as a cross-feature event.

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision, return `blocked` with the question.
- `--assumptions-allowed` (default in CI) — take the most defensible option (treat `changed=` as authoritative; order affected features alphabetically; re-baseline depth = full downstream rollup), log it as an `ASSUMPTION`, continue. **Never blocks on the first turn.**

## On Activation

Resolve customization, load persistent facts + config per standard BMad activation.

> **Versioned-doc / semantic-review N/A (T2.11/T2.12).** Rebaseline produces **no new versioned D-xx document** and **no `semanticReview` artifact** — it emits a machine plan (the baseline-change envelope) and routes re-derives to the owning skills. So per-session version-bump (T2.11) and `semanticReview` wiring (T2.12) **do not apply**; stated N/A by design. The features that actually re-baseline run their own create-skill validators + semantic review when they regenerate.

## Headless Mode

`-H` runs `plan` (default) / `apply` non-interactively. Full I/O contract — args, return schema, blocked reasons: `references/headless-contract.md`. Headless `apply` requires `changed=<model.token>` + `--apply`; the headless default = plan JSON. Idempotent.

Blocked reasons (closed set): `changed_required` · `empty_blast_radius` · `not_cross_feature_shared` · `root_not_found`.

## Stages

### Stage 1: Discover the shared surface

Run the engine with no `--changed` → it reports `shared_candidates`: model tokens referenced by **≥2 features** (a core model no single feature owns). Present these to the user. This grounds the change in the **real model surface** of the features on disk, not a guess. If the user already names the changed model, skip to Stage 2.

### Stage 2: Compute blast-radius (dry-run plan)

Run the engine with `--changed <model.token>` (no `--apply`) → the **full plan**:
- `affected_features` — every feature whose code/design references the changed token (a feature that does NOT reference it is excluded → **no false flag**).
- `blast_radius[]` — per affected feature: `stale_artifacts` (the downstream nodes that go stale, rolled up in dependency order D-19 → matrix → task-breakdown → gate), `owns_changed`, `code_references_changed` (the feature's code surface moved), `verdict: rebaseline`.
- `owners` — feature(s) that DECLARE the changed model (`_name=`).
- `warnings` — `empty_blast_radius` (nothing references it — verify the token), `not_cross_feature_shared` (only one feature — confirm it is really shared).

**Writes nothing.** The user reviews the radius and confirms before `apply`.

### Stage 3: Route the structural change (B7-5)

For each affected feature, route the re-baseline to the owning skills — this is **declare-shared + a per-feature rebaseline plan**, NOT auto-editing artifacts:
- Re-run `[SYNC]` (`hbc-traceability impact`) on each affected feature so the change is **traced** (cascade enforced — never re-baseline an untraced change).
- Re-derive each stale artifact via its create-skill (D-19 → `[ERD]`, matrix → `[TRU]`, task-breakdown → `[TB]`, gate → `[PG]`) — depth per the user's Stage-2 decision.
- If `code_references_changed`, flag the feature's `hbc-implement` to reconcile code against the moved model surface (MODEL_DRIFT).

### Stage 4: Apply (`apply` / `--apply`)

Only for the `apply` action. The engine writes the **baseline-change envelope** (`baseline-change/<change-id>/rebaseline-plan.json` + `.decision-log.md`) — the epic-level record of the cross-feature change. It records **intent**; it does **not** silently re-open feature gates or edit artifacts (the re-derives in Stage 3 do that, per owning skill). **Idempotent:** an envelope whose recorded plan matches (same `changed_node` + same `affected_features`) is detected and **skipped**, never written twice.

### Stage 5: Verify & Handoff

Confirm each affected feature was routed (Stage 3) and the envelope is written. Report the radius + per-feature re-baseline status.

Handoff (communicate in `{communication_language}`):

_"Re-baseline plan for `<changed>` → affected: `<features>`. Envelope at `baseline-change/<change-id>/`. For each feature: trace via `[SYNC]`, re-derive stale artifacts (`[ERD]`/`[TRU]`/`[TB]`/`[PG]`), reconcile code drift via `[IM]` where flagged."_

Headless: return JSON per `references/headless-contract.md` (`change_id`, `changed_node`, `owners`, `shared_candidates`, `blast_radius`, `affected_features`, `applied`, `warnings`, or `blocked` + `reason`).
