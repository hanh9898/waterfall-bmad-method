---
name: hbc-create-test-spec
description: "Generate D-27 Test Specification with detailed test cases. Use when user says 'test spec', 'đặc tả test', or agent menu [TS]."
---

# Create Test Specification

## Overview

Generate D-27 (Test Specification) — detailed test cases with steps, expected results, severity, and traceability to requirements. Each REQ-xxx from D-02 must have at least one test case. This is the heaviest document workflow — potentially hundreds of test cases for complex projects.

Five-stage workflow: Prerequisites → Discovery → Generation → Validation → Save. Supports resume state, headless mode, and parallel-lens review. Requires Python 3.10+ for validation scripts.

**Args:** `create` (default), `update` (revise existing D-27), `validate` (check existing D-27). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (input args, return schema, blocked reasons).

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

Before structured discovery, invite the user to share testing priorities, known edge cases, and domain-specific test concerns. Absorb this context before proceeding.

## Stage 1: Prerequisites

1a. **Source scan.** Run pre-pass to discover project state:

```
python3 {workflow.scan_script} --project-root {project-root} --output-dir {workflow.output_dir}
```

If the scan script is unavailable, ask the user for source document paths and proceed with manual state detection.

Returns JSON with `state` (fresh/resume/update), `existing_d27`, `d26_path`, `d02_path`, `d19_path`, `d06_path`, and `req_ids` (extracted from D-02). Route by `state`: fresh → Stage 2, resume → read `.decision-log.md` first then show progress and offer resume/restart, update → read `.decision-log.md` first then load baseline.

1b. **Source inventory.** Load D-02 (requirements) and D-26 (test plan) as primary context. Load D-19 (database design) and D-06 (business flow) selectively — only when generating data-driven or integration test cases, not upfront.

1c. **Intent gate.** Confirm test specification (detailed cases), not test plan (strategy). If user wants strategy: redirect to `hbc-create-test-plan`. If user wants code-level test scaffolding (unit test files, fixtures): redirect to `hbc-implement` [IM]. Once intent is confirmed, initialize `.decision-log.md` alongside the output — create if absent, append session heading if present. Canonical memory for this workflow.

## Stage 2: Discovery

For each REQ-xxx, derive test scenarios covering positive, negative, boundary, and integration cases. Group by requirement category and present in batches for confirmation. For large sets, show progress: "Batch 2/4: REQ-011 → REQ-020". For large requirement sets (>20 REQs), offer to work in chunks of 5-10 requirements at a time.

At each batch boundary, soft-gate: _"Any additional cases for these requirements, or proceed to the next batch?"_ Capture any cross-cutting insights (concerns spanning other REQs, architecture issues) to decision log without interrupting the batch flow.

**Compaction flush:** Write discovered TC count per REQ batch to decision log. For large documents, flush after every batch — this survives compaction.

## Stage 3: Generation

Populate `{workflow.template_path}` with discovered content. Write to `{workflow.output_dir}/D-27-{project_name}-test-spec.md`. Ensure every REQ-xxx has at least one TC-xxx with preconditions, steps, expected result, severity, and linked REQ. TC IDs are sequential from TC-001, test data uses realistic domain values, and severity distribution is reasonable.

**Revision history:** If Update mode, detect scope-of-change:
- Same cases, polish only → append note, no version bump.
- New/changed cases → new row, bump version.

**Compaction flush:** Write TC count, coverage summary, and version to decision log.

**Parallel-lens menu:** After generation, offer `[A]` Advanced (find coverage gaps, challenge boundary conditions) / `[P]` Party Mode (multi-agent test thoroughness review) / `[C]` Continue.

## Stage 4: Validation

Run deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-27-{project_name}-test-spec.md" --d02 "{d02_path}"
```

Script checks: TC IDs unique and sequential, every REQ-xxx has ≥1 TC-xxx, no orphan TCs (TC referencing non-existent REQ), all required fields present per test case. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable, fall back to LLM-only validation.

**LLM judgment checks:**
- Test steps are specific and reproducible.
- Expected results are verifiable (not vague like "works correctly").
- Negative and boundary cases cover common failure modes.
- No contradictions between test cases.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

**Compaction flush:** Write validation results summary to decision log.

**Parallel-lens menu:** `[A]` Advanced (coverage gap analysis) / `[P]` Party Mode / `[C]` Continue.

## Stage 4b: Semantic Review (Lớp 2)

Structural validation (Stage 4) only proves cấu trúc. Before saving, run the **semantic review** per the shared rubric: `.claude/skills/hbc-shared/references/semantic-review-rubric.md`.

Apply the **facet-split discipline** to every REQ this D-27 covers: for each REQ, ask which facets apply (read/write · api/admin · lifecycle) and whether **each applicable facet** has a TC — not just "≥1 TC exists". This is the seam-catching step (e.g. a REQ whose admin/write facet was cut from REST must still be tested or explicitly out-of-scope).

**Automated check (M-1):** declare each TC's facets (`**Facets:**` field) and each REQ's required facets (Coverage Matrix `Facets` column), then run:
```
python3 {skill-root}/scripts/check-facet-coverage.py --d27 "{workflow.output_dir}/D-27-{project_name}-test-spec.md" [--d02 "{d02_path}"]
```
`facet_covered: false` ⇒ list `uncovered_facets` in `openFacets` and keep `status: pending`. The metric only checks declared facets — your LLM judgment still decides whether the declared facet set is COMPLETE.

Record the outcome in the D-27 frontmatter (A-3):

```yaml
semanticReview:
  status: passed        # passed only when openFacets is empty; else pending
  reviewedBy: llm
  date: "{date}"
  openFacets: []        # e.g. ["REQ-013 admin/write facet has no TC"]
```

Headless: if any facet is uncovered, set `status: pending`, list `openFacets`, and return `blocked`. The Phase 2 gate REVIEW item (#5) reads this status.

## Stage 5: Save and Handoff

Finalize document — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `tc_count`, `coverage`, `semanticReview`). Audit decision-log entries against D-27. Append closing session.

Write `test-spec-distillate.json` alongside D-27 — `{"tc_count": N, "coverage_pct": N, "req_tc_map": {"REQ-001": ["TC-001","TC-002"], ...}, "severity_dist": {"High": N, "Medium": N, "Low": N}}` for downstream consumption by Phase 3 agents.

Suggest next steps: _"D-27 complete with {tc_count} test cases covering {coverage}% of requirements. Next: run the inter-document readiness check (`hbc-check-implementation-readiness` [IR]) — the seam gate that reconciles D-02/D-21/D-26/D-27 + matrix — then run Phase 2 gate (`hbc-phase-gate` [PG]) to close the design phase."_

Headless: return JSON per `references/headless-contract.md`.

## Sync Handoff (hbc-sync integration)

Applies only in `update` mode. Full contract: `hbc-sync/references/skill-integration.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest: _"Tài liệu đã cập nhật. Chạy `hbc-sync` để đồng bộ các tài liệu/test/code phụ thuộc?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-sync` directly (it will cascade downstream). Default is false.
