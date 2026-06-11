---
name: hbc-create-requirements
description: "Generate D-02 Requirements Specification with REQ-xxx IDs. Use when user says 'requirements', 'yêu cầu', or agent menu [REQ]."
---

# Create Requirements

## Overview

Generate D-02 (Requirements Specification) — structured requirements with unique REQ-xxx IDs, scope boundaries, user roles, functional and non-functional requirements. REQ IDs are the foundation of the entire traceability chain.

Five-stage workflow: Prerequisites → Discovery → Generation → Validation → Save. Supports resume state, headless mode, and parallel-lens review. Requires Python 3.10+ for validation scripts.

**Args:** `create` (default), `update` (revise existing D-02), `validate` (check existing D-02). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (input args, return schema, blocked reasons).

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

## Stage 1: Prerequisites

1a. **Source scan.** Run pre-pass to discover project state and sources:

```
python3 {workflow.scan_script} --project-root {project-root}
```

Returns JSON with `state` (fresh/resume/update), `existing_d02` (path + frontmatter), `source_docs` list, and `project_context` path. Use this to route:
   - **Fresh** — no prior D-02. Proceed to Stage 2.
   - **Resume** — partial D-02 found (`lastStep` < `complete`). Show summary, offer resume or restart.
   - **Update** — complete D-02 exists. Show what to update, load as baseline.

1b. **Source inventory.** Supplement scan results with user-provided inputs (interview notes, descriptions). In headless mode, sources are required via `--sources` arg.

1c. **Intent gate.** Confirm user wants to create/update requirements (not a different artifact). If wrong skill: product brief → `hbc-create-prd`, brainstorming → `hbc-brainstorming`, project setup → `hbc-project-setup`.

1d. **Brainstorming suggestion** (interactive only, Fresh state only). If the domain is complex or the user seems uncertain about scope, suggest: _"Domain này có vẻ phức tạp — muốn chạy `bmad-brainstorming` trước để khám phá problem space và phát hiện requirements ẩn không? Kết quả brainstorming sẽ feed trực tiếp vào D-02."_ If declined or in headless mode, proceed to Stage 2. If accepted, pause this workflow — the user runs brainstorming in a separate context window, then resumes here (the resume-state in 1a will detect the partial D-02). If a brainstorming session file exists in `{output_folder}/brainstorming/`, note it as an available source in the source inventory.

## Stage 2: Discovery

Pre-populate fields from `project-context.md` where available (stakeholders, timeline, tech stack) — present as defaults for confirmation. Open with an invitation for the user to share everything else — goals, constraints, concerns, prior art. If source documents already contain structured requirements (tables, numbered lists with IDs), present them for confirmation and skip to gaps. Then identify which areas still need elicitation:

- **Project background** — purpose, stakeholders, timeline constraints.
- **Scope** — explicit in-scope and out-of-scope boundaries. Out-of-scope is as important as in-scope.
- **User roles** — actors who interact with the system. Each gets a name and description.
- **Functional requirements** — each gets a unique `REQ-xxx` ID (sequential from REQ-001). Must be specific and testable.
- **Non-functional requirements** — performance, security, availability, usability. Each with measurable criteria.
- **Constraints and assumptions** — technical, business, legal constraints.

At each area boundary, soft-gate: _"Anything else on [area], or move to [next]?"_ Silently capture glossary-worthy terms and business-flow processes mentioned during Discovery — surface them in Stage 5 handoff.

**Compaction flush:** Write discovered requirements to decision log at end of Stage 2 — actor list, REQ count, scope boundaries. This survives compaction.

## Stage 3: Generation

Populate `{workflow.template_path}` with discovered content. Write to `{workflow.output_dir}/D-02-{project_name}.md`. Ensure:
- Every functional requirement has a unique sequential REQ-xxx ID.
- Scope section explicitly lists out-of-scope items.
- Non-functional requirements have measurable criteria (not "fast" but "< 2s response time").
- Cross-reference user roles with requirements that mention them.

**Revision history:** If Update mode, detect scope-of-change:
- Same requirements, polish only → append note, no version bump.
- New/changed requirements → new row, bump version.

**Compaction flush:** Write generated REQ count, scope summary, and version to decision log.

**Parallel-lens menu:** After generation, offer `[A]` Advanced Elicitation (deeper probing on weak areas) / `[P]` Party Mode (multi-agent lateral review) / `[C]` Continue. If subagents unavailable, apply lens perspective directly.

## Stage 4: Validation

Run deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-02-{project_name}.md" --project-root {project-root} --vague-terms "{workflow.vague_terms}"
```

Script checks: REQ IDs unique and sequential, no vague terms (configurable word list), all required sections present, no empty sections. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable (Python not installed), fall back to LLM-only validation and note the limitation in the decision log.

**LLM judgment checks:**
- Requirements are testable and unambiguous.
- No contradictions between requirements.
- Non-functional requirements have measurable criteria.
- Scope boundaries are clear.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable issues, return `blocked` for non-fixable.

**Compaction flush:** Write validation results summary (issue counts, auto-fixed items) to decision log.

**Parallel-lens menu:** `[A]` Advanced (challenge vagueness, find gaps) / `[P]` Party Mode (multi-reviewer perspective) / `[C]` Continue.

## Stage 4b: Semantic Review (Lớp 2)

Structural validation only proves cấu trúc. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`). Apply the **facet-split discipline** per REQ (read/write · api/admin · lifecycle): flag any REQ with a write/admin/lifecycle facet so downstream D-21/D-26/D-27 know it must be designed and tested — don't let a facet be implied but unowned (the seam). Confirm requirements are testable, unambiguous, non-contradictory; NFRs measurable. Record `semanticReview` frontmatter (A-3: `status` passed only when `openFacets` empty, else `pending` + list). The Phase 2 gate REVIEW item (#5) reads it.

## Stage 5: Save and Handoff

Finalize document — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). Audit decision-log entries against D-02: every logged decision reflected in the document, captured in addendum, or explicitly set aside. Append closing session.

Suggest next steps: _"D-02 complete. Recommended: create D-03 Glossary (`hbc-create-glossary` [GLO]), then D-06 Business Flow (`hbc-create-business-flow-diagram` [BF]). After all three, run Phase 1 gate (`hbc-phase-gate` [PG])."_

Headless: return JSON per `references/headless-contract.md`.
