---
name: hbc-create-test-spec
description: "Generate D-27 Test Specification with detailed test cases. Use when user says 'test spec', 'đặc tả test', or agent menu [TS]."
---

# Create Test Specification

## Overview

Generate D-27 (Test Specification) — detailed test cases with steps, expected results, severity, traceability to requirements. Each REQ-xxx from D-02 needs ≥1 TC. The heaviest document workflow — potentially hundreds of TCs.

Test design is **specification-based**: each TC maps to the right technique for its source (B3-5, `references/technique-map.md`). Test data is grounded in the real D-19 schema (B3-2); when code exists, TCs are reconciled against real behavior (B3-7). Facet + edge in/out-scope is **confirmed per-REQ before generation** (B3-4, hard gate). Critical-path severity is **LLM-proposed, user-ratified** (B3-6).

Workflow: Prerequisites → Per-REQ scope confirm → Discovery → Generation → Grounding → Validation → Review → Save. Resume, headless, parallel-lens. Python 3.10+.

**Args:** `create` (default), `update` (revise existing D-27), `validate` (check existing D-27). Optional: `--headless` / `-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- Bare paths resolve from the skill root; `{skill-root}` = this skill's installed dir; `{project-root}`-prefixed paths resolve from the project working directory; `{skill-name}` = the skill directory's basename.

## Autonomy (A5)

Separate **mechanical** from **domain** decisions. Mechanical — TC numbering, formatting, which technique a clearly-rule-shaped REQ uses — decide and proceed. Domain — **facets/edges in vs out of scope per REQ** (B3-4), a **critical-path TC's severity** (B3-6), whether a TC's assertion matches real behavior when they diverge (B3-7) — **ASK; never invent a default**.

Headless: `--strict` stops at the first unresolved domain decision and returns `blocked` with the question; `--assumptions-allowed` (CI default) takes the most defensible option, logs it as an `ASSUMPTION`, and continues — never blocks on the first turn.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (args, return schema, blocked reasons); domain decisions follow the Autonomy mode above.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> **Resolve active feature (B):** arg `feature=<slug>` → active feature in session → ask (headless: required; if missing → blocked `feature_required`). Substitute `{feature}` in every workflow path.

## Open Floor

Before structured discovery, invite the user to share testing priorities, known edge cases, and domain test concerns. Absorb before Stage 1.

## Stage 1: Prerequisites

1a. **Source scan.** Run the pre-pass:

```
python3 {workflow.scan_script} --project-root {project-root} --output-dir {workflow.output_dir}
```

Returns JSON: `state` (fresh/resume/update), `existing_d27`, `d26_path`, `d02_path`, `d19_path`, `d06_path`, `req_ids`. Route by `state`: fresh → 1b; resume/update → read `.decision-log.md` first, then (resume) show progress + offer resume/restart, or (update) load baseline. If the scan is unavailable, ask for source paths and detect state manually.

1b. **Source inventory.** D-02 (requirements) is primary; missing D-02 (headless) → blocked `no_requirements`. D-26 (test plan) gives the technique-per-area hand-off. Load **D-19** (schema, for EP/BVA + test-data grounding) and **D-06** (flows, for use-case TCs) selectively. If a code tree exists, note its path for Stage 3a (B3-7).

1c. **Intent gate.** Confirm test specification (detailed cases), not test plan (strategy → `hbc-create-test-plan` [TP]) nor code-level scaffolding (unit-test files → `hbc-implement` [IM]). Then initialize `.decision-log.md` alongside the output — create if absent, else append a session heading. Canonical memory for this workflow.

## Stage 1e: Per-REQ Scope Confirmation (B3-4 — HARD pre-gate)

**Before any TC is generated**, confirm the test scope **per REQ**. For each REQ, from D-02 + Open Floor draft: its **facets** (read/write · api/admin/ui/batch · lifecycle), and which **edge cases** are **in-scope** vs **explicitly out-of-scope** (with the reason each is excluded — unchanged legacy path, deferred perf…). Out-of-scope matters as much as in-scope. Present per REQ (batch by `{workflow.req_batch_size}`), get explicit confirmation — a domain decision, never inferred silently. Headless: Autonomy mode (`--strict` → blocked `scope_unconfirmed`; `--assumptions-allowed` → log the drafted boundary as `ASSUMPTION`, continue). Record the confirmed boundary; Stages 2/3 fill only within it.

## Stage 2: Discovery

For each REQ, derive scenarios within the confirmed boundary, choosing the **technique per source** (`references/technique-map.md`, B3-5): Decision-Table←rules · State-Transition←lifecycle (**cover wrong/illegal transitions**) · EP/BVA←D-19 fields · Use-Case←D-06 flows · Example-Mapping for ambiguous rules. Cover positive, negative, boundary, integration.

**Depth per maturity (B3-3, advisory).** Scale TC depth to maturity: `exploratory` → happy path + key negatives; `stable`/critical → full boundary + adversarial + lifecycle wrong-transitions (forward-ref T3.16).

Group by REQ; at each batch boundary soft-gate: _"More cases for these REQs, or proceed?"_ Capture cross-cutting insights to the decision log.

**Compaction flush:** Write discovered TC count per REQ batch; flush after every batch — survives compaction.

## Stage 3: Generation

Populate `{workflow.template_path}` → `{workflow.output_dir}/D-27-{project_name}-test-spec.md`. Ensure:

- Every in-scope REQ has ≥1 TC with preconditions, steps, expected result, **Facets**, severity, linked REQ. TC IDs sequential from TC-001.
- **Test data grounded in D-19 (B3-2)** — fixture values use real model/field names + the field's real type/constraint, not invented tokens.
- **Sensitive TCs carry a sanity step (B3-1)** — a TC that must FAIL on a business branch (Critical, or idempotent/overwrite/snapshot/rollback/race) has a structural assertion **and** a step proving the fixture activates the branch (e.g. snapshot value ≠ generate-lines default). A green run without it is not evidence.
- **Severity is a draft (B3-6)** — propose each TC's severity; for **critical-path** TCs present it to the user to ratify, never as fact. Unratified stays flagged (headless: Autonomy mode).

**Compaction flush:** Write TC count, coverage, version to the decision log.

**Parallel-lens menu:** `[A]` Advanced / `[P]` Party Mode / `[C]` Continue. If subagents unavailable, apply lenses inline. Headless: skip to Stage 3a.

## Stage 3a: Grounding reconcile (B3-1 / B3-2 / B3-7)

Reconcile the TCs against the real schema + code — advisory, not a hard gate (the blocking cross-doc gate is [IR]). If unavailable, skip.

```
python3 {workflow.grounding_script} "{workflow.output_dir}/D-27-{project_name}-test-spec.md" --project-root {project-root} [--d19 "{d19_path}"] [--code-dir "<code>"]
```

It returns:
- **`model_drift` (B3-7)** — with `--code-dir`: `design_only` = a D-19 model no code defines (a TC asserting on it tests a phantom — **reconcile the TC vs real behavior, warn on the wrong assumption**); `code_only` = a model code has but D-19/TCs miss.
- **`ungrounded_testdata` (B3-2)** — Test-Data tokens naming a model/field absent from D-19 + code. Ground or correct each.
- **`sanity_gaps` (B3-1)** — sensitive TCs with no sanity step. Add one or confirm unneeded.

Whether a TC's *assertion* matches code behavior, and whether a technique *fits*, stay LLM judgment (Stage 4b). Headless: `--strict` blocks if non-empty; `--assumptions-allowed` logs and continues.

## Stage 4: Validation

Run the deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-27-{project_name}-test-spec.md" --d02 "{d02_path}"
```

Script checks: required sections; TC IDs unique + sequential; every D-02 REQ covered (trailing-number identity, so canonical-vs-bare spellings reconcile); no orphan REQ refs; required fields per TC. Returns per-issue `auto_fixable` + a `churn` block. If unavailable, fall back to LLM-only.

**LLM judgment:** steps reproducible; expected results verifiable (not "works correctly"); negative + boundary cover failure modes; no contradictions; each TC's technique↔source pairing sound (B3-5).

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

**Compaction flush:** Write the validation summary to the decision log.

## Stage 4a + 4b: Adversarial + Semantic review (B3-9 / B3-8)

Before saving, run the two review stages detailed in `references/review-stages.md`:
- **Stage 4a (B3-9)** — `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` over the TCs, with an **availability-check fallback** (apply inline + record "ran inline", never hard-block).
- **Stage 4b (B3-8 / T2.12)** — semantic review per the shared rubric with an **independent skeptic lens** + **facet-split discipline**; run the M-1 `check-facet-coverage.py` metric; record `semanticReview` `status: passed` **only when `openFacets` empty AND the user signs off** (headless: Autonomy mode). The Phase 2 gate REVIEW item (#5) reads it.

## Validate Mode

When invoked with `validate`: run the Stage 1a scan to locate the existing D-27, then run the validation (and optionally grounding) script against it. Present results (interactive) or return headless JSON — no discovery/generation. No D-27 found → `blocked`, `reason: "no_existing_d27"`.

## Update Mode

When `state: update` or `update` arg: load the existing D-27 as baseline. Present what changes; re-confirm per-REQ scope (Stage 1e) for any REQ whose scope shifts. Then Stage 3 → 3a → 4 → 4a → 4b.

**Anti-churn (T2.11 / B3-10).** Bump the version **once per session**, not per edit; append a single Revision-History row. The validator returns `churn` (`revisions` vs `threshold`); when `high_churn` is true the spec isn't frozen — surface it and suggest `maturity: exploratory` or a `[DSC]` model-spike instead of another bump.

## Stage 5: Save and Handoff

Finalize — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `tc_count`, `coverage`, `semanticReview`). On create: fill the blank date in the pre-seeded Revision-History row; on update: the session row was appended in Update Mode. Audit decision-log entries against D-27. Append the closing session.

Write `test-spec-distillate.json` alongside D-27 — `{"tc_count", "coverage_pct", "req_tc_map": {...}, "severity_dist": {...}}` for downstream Phase 3 consumption.

Suggest next steps: _"D-27 complete ({tc_count} TCs, {coverage}% coverage). Next: readiness check (`hbc-check-implementation-readiness` [IR]) — the seam gate over D-02/D-21/D-26/D-27 + matrix — then Phase 2 gate (`hbc-phase-gate` [PG])."_ Headless: return JSON per `references/headless-contract.md`.

## Sync Handoff (hbc-traceability impact integration)

`update` mode (full contract: `hbc-traceability/references/impact-capability.md`; BR-13 `--invoked-by-sync` → skip, prevents update→sync loop). Suggest `hbc-traceability impact`; auto-chain when `{workflow.auto_sync_after_update}`. **Matrix column (B7-2):** on save run `hbc-traceability update feature={feature}` (self-write `test_ref` TC↔REQ; gate blocks if missing).
