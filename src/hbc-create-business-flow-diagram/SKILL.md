---
name: hbc-create-business-flow-diagram
description: "Generate D-06 Business Flow Diagram with Mermaid (AS-IS/TO-BE) from PRD or interactive input. Use when user says 'create business flow diagram', 'create D-06', 'tạo sơ đồ luồng nghiệp vụ', 'vẽ sơ đồ luồng nghiệp vụ', or 'vẽ D-06'."
---

# Create Business Flow Diagram (D-06)

## Overview

Produces a D-06 Business Flow Diagram following HBLab document conventions — Mermaid `sequenceDiagram` (default), `flowchart`, or `stateDiagram`, with AS-IS / TO-BE sections where applicable. Reads PRD / UX / research artifacts from `{planning_artifacts}` when available, falls back to interactive elicitation when none exist. Output is a single per-feature D-06 file; the session decision log (`.decision-log.md`) and scan artifacts (`.scan/`) are shared peers in the feature workspace `{ws}` (see Stage 1a) that carry identity across runs.

Supports `-H` / `--headless`. Two reference files carry the detail this control sheet points at:

- [`references/stage-guide.md`](references/stage-guide.md) — full per-stage detail (On Activation steps, Conventions, Language Rules, Parallel-lens menu, Stage 1–5 prose, Semantic Review, Sync Handoff). **Read it before executing any stage.**
- [`references/headless-contract.md`](references/headless-contract.md) — the full `--headless` flag set, defaults table, and JSON return contract.

Carve-outs preserved verbatim everywhere: Mermaid keywords/identifiers and `AS-IS` / `TO-BE`. Communicate in `{communication_language}`; translate output prose to `{document_output_language}`; file/folder names always English. Full Language Rules + path/placeholder Conventions: stage-guide.

## On Activation

> **Resolve active feature (B):** arg `feature=<slug>` → active feature trong phiên → hỏi (headless: bắt buộc, thiếu → blocked `feature_required`). Thay `{feature}` trong mọi path workflow (D-06 ghi per-feature).

Execute the activation sequence per [`references/stage-guide.md`](references/stage-guide.md) § *On Activation (detail)*:

1. **Resolve the workflow block** — run `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`; on failure hand-merge `customize.toml` → team → user TOML (base → team → user order). Keep `{workflow.*}` (incl. `{workflow.on_complete}`) in memory all session.
2. **Execute** `{workflow.activation_steps_prepend}` in order.
3. **Load** `{workflow.persistent_facts}` (`file:` entries = load contents; others = verbatim facts).
4. **Load config** from `{project-root}/_bmad/config.yaml`(+`.user`) → `config.toml` → legacy `bmm/config.yaml`. Resolve `{user_name}`, `{communication_language}`, `{document_output_language}`, `{planning_artifacts}`, `{project_knowledge}`, `{project_name}`.
5. **Greet** `{user_name}` and execute `{workflow.activation_steps_append}` in order.

## Headless Mode

`-H` / `--headless` runs without user prompts. Full contract: [`references/headless-contract.md`](references/headless-contract.md). Closed-set of blocker `reason` values (compaction-survival mirror — extend this list and the contract file together):

- `template_missing` — `{workflow.business_flow_template}` not found on disk.
- `no_prd_and_no_interactive_in_headless` — no PRD, no `--prd-path`, no `--no-prd-ok`.
- `planning_artifacts_unreadable` — `{planning_artifacts}` missing or unreadable.
- `mermaid_validation_failed` — `validate-mermaid.py` returned issues not all `auto_fixable: true`.
- `fr_coverage_gap` — `check-fr-coverage.py` reported uncovered or phantom FRs.
- `migration_without_as_is` — `--mode=migration` but no AS-IS / "current state" markers in any PRD source.
- `resolver_missing` — customization resolver failed and the hand-merge fallback could not complete.
- `feature_required` — headless invocation with no resolvable feature.

## Parallel-lens menu

Used at the end of Stage 3 and Stage 4 (`[A]` advanced-elicitation, `[P]` party-mode, `[C]` continue). Headless: `--review-lenses=skip|advanced|party` (default `skip`), each fire appended to `review_lenses_run`. Full menu + mapping: stage-guide § *Parallel-lens menu*.

## Workflow

Each stage below is a one-line index. **Read [`references/stage-guide.md`](references/stage-guide.md) for the full instructions before executing** — do not act from these summaries alone.

### 1. Prerequisites and Scope

- **1a. Bind workspace + resume state** — bind `{primary} = {workflow.business_flow_output_path}` (single per-feature FILE under `{output_folder}/features/{feature}/planning-artifacts/`, NOT flat `{planning_artifacts}`). Resolve `{feature}` first (headless: required → blocked `feature_required`). `{ws}` = dir of `{primary}`; `.decision-log.md` and `.scan/` are its peers (create if absent); decision-log/`.scan` refs resolve against `{ws}`, source discovery still scans project-level `{planning_artifacts}`. Run `discover-planning-artifacts.py ... --primary {primary} --check-as-is -o {ws}/.scan/artifacts.json`; consume JSON → `template_missing` HALT/block; else branch on `resume_state` (Fresh `no_primary`/`crashed_no_progress` · Resume · Update) and present the resume menu (interactive). Init `.decision-log.md` from `{workflow.decision_log_template}` if absent.
- **1b. Open-floor + intent gate + wrong-skill off-ramp** (interactive only) — invite uncaptured sources; intent check (capture / design / both); off-ramp to `bmad-create-architecture` etc.; strict short-circuit of 1e only when reply covers all four of mode/scope/sources/type.
- **1b′. Brainstorming suggestion** (interactive, Fresh, TO-BE only) — offer `bmad-brainstorming`; load any session file from `{output_folder}/brainstorming/`.
- **1c. Consume source inventory** — `artifacts.json` → PRD set (shards enumerated, don't re-glob) + UX/use-case/research.
- **1d. No-PRD HALT menu** — zero PRDs and no `--prd-path` → menu; headless `--no-prd-ok` → option 3 else blocked `no_prd_and_no_interactive_in_headless`.
- **1e. Inferred-defaults confirmation** (interactive unless 1b short-circuited) — confirm mode/scope/type; migration-vs-AS-IS sanity check (blocked `migration_without_as_is` headless unless `--allow-migration-without-as-is`). Init primary from `{workflow.business_flow_template}` (translate prose); `stepsCompleted += stage-1`; `updated` = today.

### 2. Discovery

Extract actors / triggers / steps / decision points / outcomes; confirm; migration = discover AS-IS + TO-BE with deltas; zero-actor branch promotes trigger to actor. **Compaction-flush (required):** write `stage_2_actors`/`stage_2_flows` frontmatter, append `### Discovery snapshot (Stage 2 flush)` to `.decision-log.md`, `stepsCompleted += stage-2`. Soft gate (interactive). Detail: stage-guide § Stage 2.

### 3. Diagram Generation

One Mermaid block per in-scope flow (`actor` for humans, `participant` for systems; one flow per block; migration = AS-IS then TO-BE; `--update-flow`/U2 re-renders only the named flow). **Revision-history scope-of-change gate:** Create/Fresh → v1.0; Update → run `diff-stage2-flush.py` (`auto`) → polish (note on latest row) vs semantic (new row, minor bump), or `--scope-of-change`/manual override; log scope. `stepsCompleted += stage-3`. Then Parallel-lens menu. Detail: stage-guide § Stage 3.

### 4. Validation

Run both validators in parallel: `validate-mermaid.py {primary} --expected-actors "<stage-2 actors>" -o {ws}/.scan/mermaid.json` and `check-fr-coverage.py --prd <each-prd-or-shard> --d06 {primary} --pattern "{workflow.fr_id_pattern}" -o {ws}/.scan/fr.json`. Inspect `render_check` (ok / failed / `skipped: mmdc not installed` — not verified); handle `vacuous: true`. LLM judgment checks: layout, AS-IS/TO-BE delta clarity, revision history, language consistency. Fix: interactive loop vs headless apply only `auto_fixable: true` (else blocked `mermaid_validation_failed` / `fr_coverage_gap`). `stepsCompleted += stage-4`. Then Parallel-lens menu. Detail: stage-guide § Stage 4.

### 4b. Semantic Review (Lớp 2)

Before saving, run the semantic review per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with **facet-split discipline** (read vs write/state-change · UI/admin/back-office/API/batch surface · lifecycle transitions). Record `semanticReview` frontmatter (`status: passed` only when `openFacets` empty, else `pending` + list). Headless: never blocks (Phase 1 gate enforces); never fabricate coverage. Detail: stage-guide § Stage 4b.

### 5. Save and Handoff

Finalize `{primary}` (`stepsCompleted = stage-1..5`, `lastStep = complete`, `updated` = today, `semanticReview` from 4b). Append closing session block to `.decision-log.md` (sources/mode/scope/type, scope-of-change, headless auto-fixes, lenses run, handoff target). Successor: Phase 1 gate `hbc-phase-gate` [PG]; later Phase 2 consumers: `hbc-create-er-diagram` (D-19), `hbc-create-test-plan` (D-26). Offer `bmad-distillator` for downstream LLM consumers. Headless: emit JSON return contract per [`references/headless-contract.md`](references/headless-contract.md). Detail: stage-guide § Stage 5.

## On Complete

Read `{workflow.on_complete}` from the already-resolved workflow block (kept in memory from On Activation). If non-empty, follow it as the final instruction. Otherwise, invoke `bmad-help`.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md` (and stage-guide § Sync Handoff). Suppression guard (BR-13): if `--invoked-by-sync` / `invoked_by_sync=true`, skip this section. Hybrid trigger (default): suggest `hbc-traceability impact`. Auto-chained: if `{workflow.auto_sync_after_update}` is true, invoke it directly (default false).
