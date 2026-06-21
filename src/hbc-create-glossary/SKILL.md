---
name: hbc-create-glossary
description: "Generate D-03 Glossary with domain terms and definitions. Use when user says 'glossary', 'thuật ngữ', or agent menu [GLO]."
---

# Create Glossary

## Overview

Generate D-03 (Glossary) — the project's **ubiquitous language** (DDD): domain terms, abbreviations, and project-specific definitions that bridge business vocabulary and the real model names in code. Terms extracted from existing artifacts (D-02, D-06, D-19, project-context.md, code) and user input. The glossary keeps terminology consistent across every downstream document.

Workflow: Prerequisites → Discovery → Generation → Ubiquitous-language reconcile → Semantic review → Save. Supports resume state, headless mode, and parallel-lens review. Requires Python 3.10+ for the scripts.

**Args:** `create` (default), `update` (add terms to existing D-03), `validate` (check existing D-03). Optional: `--headless` / `-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Autonomy (A5)

Separate **mechanical** decisions from **domain** decisions. Mechanical — sort terms, dedup, table formatting, which section a row belongs to — decide and proceed. Domain — the *meaning* of a term, a definition not grounded in any source, whether an orphan term should be dropped, how to resolve a duplicate-definition conflict — **ASK; never invent a default**.

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision and return `blocked` with the question.
- `--assumptions-allowed` (default in CI) — take the most defensible option, log it to the decision log as an `ASSUMPTION`, and continue. Never block on the first question.

## Headless Mode

When `--headless`: all stages run non-interactively. Source documents are required via `--sources` arg. Domain decisions follow the Autonomy mode above. Returns JSON per `references/headless-contract.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`. If `{workflow.glossary_output_path}` exists with `lastStep` not `complete`, surface it with its `updated` timestamp and offer to resume before proceeding to Stage 1.

> **Scope: SHARED** — this deliverable is shared project-wide (created in Phase 0 via `hbc-project-init`), does **not** take `feature`; writes to `shared/`.

## Stage 1: Prerequisites

1a. **Intent gate.** Confirm user wants to create/update glossary. If wrong skill: requirements → `hbc-create-requirements` [REQ], entity relationships → `hbc-create-er-diagram` [ER], business flows → `hbc-create-business-flow-diagram` [BFD]. Headless: skip — intent is given by invocation.

1b. **Source scan.** Run pre-pass to discover project state:

```
python3 {workflow.scan_script} --project-root {project-root} --project-knowledge {project_knowledge}
```

Headless: forward `--sources` arg if provided: `python3 {workflow.scan_script} --project-root {project-root} --sources "{sources}"`. (`--sources` skips ALL auto-discovery, including project-knowledge, for back-compat.)

**Brownfield ingest (#7).** `--project-knowledge {project_knowledge}` points at the `bmad-document-project` output (typically `{project-root}/docs`); when present its domain docs are ingested as extra sources so D-03 reflects the **real documented vocabulary**, not just project-context.md. Greenfield (dir absent) is a no-op.

Returns JSON with `state` (fresh/resume/update), `existing_d03`, `source_docs` (D-02, project-context, project-knowledge domain docs, etc.), and `raw_candidates` (each with `term` and `method`: quoted/abbreviation). Candidates are raw structural extractions — filter for domain relevance using LLM judgment in Stage 2. Use `state` to route:
   - **Fresh** — no prior D-03. Proceed to Stage 2.
   - **Resume** — partial D-03 found (`lastStep` < `complete`). Show summary, offer resume or restart. Restart: overwrite with fresh template, reset frontmatter, append restart note to decision log.
   - **Update** — complete D-03 exists. Show current term count, proceed to Update Mode.

After routing: initialize `.decision-log.md` as a peer of `{workflow.glossary_output_path}` — create if absent, append a date-stamped session heading if present. If scan script fails or Python is unavailable, ask the user to provide source paths directly and proceed with empty candidates.

## Stage 2: Discovery

Open with an invitation for the user to share domain-specific terms, abbreviations, and jargon they consider essential for this project. Then filter `raw_candidates` from scan for domain relevance — discard common abbreviations (API, SQL, HTML, etc.) and generic terms. Present filtered candidates for confirmation: _"Here's what we also found in your documents — confirm, modify, or discard."_ If `candidate_count == 0` and `source_count > 0`, note that auto-extraction found no marked terms. Capture term, project-specific definition (not generic dictionary definitions), and optional category (e.g., business, technical) for each.

**Ground every definition (B11-1).** A definition must come from a real source — the term's usage in D-02/D-06/D-19, project-context, or code — not a generic dictionary gloss. Note where each definition came from. When no source defines a term and you must **infer** it, do not write it silently: present the inferred definition and **ask the user to confirm or correct it before it goes in** (ASK-before-generate, a domain decision).

At each batch of terms, soft-gate: _"Any more terms, or shall we finalize?"_

Silently capture any requirements or business-flow insights mentioned — surface in Stage 4 handoff.

**Compaction flush:** Write all discovered terms (term + definition + category for each) and total count to decision log.

## Stage 3: Generation

Using `{workflow.template_path}` as the base, write the populated document to `{workflow.glossary_output_path}`. Ensure:
- Terms sorted alphabetically within each category (if categorized) or overall.
- No duplicate terms.
- Every definition is project-specific (flag generic definitions for revision).
- Cross-reference terms that appear in D-02 requirements.

Run deterministic validator:

```
python3 {workflow.validation_script} {workflow.glossary_output_path} --project-root {project-root}
```

Script checks: no duplicate terms, no empty definitions, minimum term count > 0. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable, fall back to LLM-only validation.

**LLM judgment checks:** definition quality and cross-doc concept coverage are reviewed in Stage 3b (semantic). Here, only: if no abbreviations were collected, add a single "N/A" row to the abbreviations table or omit the section — never leave an empty table.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

**Compaction flush:** Write term count and validation summary to decision log.

**Parallel-lens menu:** `[A]` Advanced (challenge definitions, find missing D-02 terms) / `[P]` Multi-lens (terminology specialist, domain expert, end user perspectives) / `[C]` Continue. If subagents unavailable, apply lens perspectives directly. Headless: skip to Stage 3a.

## Stage 3a: Ubiquitous-language reconcile (B11-2 / B11-3)

Reconcile the glossary against design and code so it speaks the system's names — advisory, not a hard gate (the blocking cross-doc gate is `hbc-check-implementation-readiness` [IR]). If the script/Python is unavailable, skip the reconcile and proceed. Pass whichever inputs exist:

```
python3 {workflow.consistency_script} {workflow.glossary_output_path} --project-root {project-root} [--design <D-19 path>] [--code-dir <model source dir>] [--sources "<D-02,D-06,…>"]
```

Resolve `--design` (D-19) and `--code-dir` (model source) from Stage 1b / config. It returns:
- **`missing_from_glossary` (B11-3)** — D-19 / code model names the glossary does not reflect, the DDD gap. For each, propose adding the term *with its physical name* or recording why it is out of scope. **Do not auto-add** — confirm the business meaning with the user (domain decision).
- **`orphan_terms` (B11-2)** — glossary terms used in none of the `--sources` business docs. Surface each: keep with rationale, or drop.

The reverse direction (a prose term the glossary lacks) stays an LLM judgment over the Stage 1b candidates — the script does not decide what counts as a domain term. Headless: include both lists in the return; `--strict` blocks if either is non-empty, `--assumptions-allowed` logs them and continues.

## Validate Mode

When invoked with `validate` arg: run Stage 1b scan to locate existing D-03, then run the validation script against it. Present results (interactive) or return headless JSON with validation object. No discovery or generation stages run. If no D-03 found, return `blocked` with `reason: "no_existing_d03"`.

## Update Mode

When `state: update` from scan or `update` arg: read the scan JSON for the existing D-03 path and new candidates. Present diff — candidates not yet in the existing glossary. Merge non-duplicate terms; surface duplicates (same term, different definition) for user resolution. Auto-append a new row to the "Lịch sử sửa đổi" (Revision History) table with today's date and change summary. Then proceed to Stage 3 (Generation) for validation. Headless: auto-merge non-conflicting terms, return `blocked` with `reason: "duplicate_conflict"` when definitions clash.

**Anti-churn (T2.11).** Bump the version **once per session**, not per edit. The validator returns `churn` (`revisions` vs `threshold`); when `churn.high_churn` is true the model isn't frozen yet — surface it and suggest `maturity: exploratory` or a `[DSC]` model-spike instead of another bump.

## Stage 3b: Semantic Review (Layer 2)

Structural validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** — challenge each definition: is it grounded in a source, unambiguous, project-specific? Any contradiction between definitions? Any key D-02/D-19 concept unrepresented? List every unresolved concern in `openFacets`. Set `semanticReview.status: passed` **only when `openFacets` is empty AND the user signs off** (headless follows the Autonomy mode); otherwise `pending`. The shared `semantic_review_status` is the single structural read of this block; the Phase 2 gate REVIEW item (#5) enforces it.

## Stage 4: Save and Handoff

Save document to `{workflow.glossary_output_path}` — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). On create: fill the blank date in the pre-seeded "Lịch sử sửa đổi" (Revision History) row. On update: revision row already appended in Update Mode. Audit decision-log entries against D-03: every logged decision reflected in the document or explicitly set aside. Append closing session to decision log.

Write `glossary-distillate.json` alongside D-03 — `{"terms": [{"term": "...", "definition": "...", "category": "..."}], "abbreviations": [{"abbr": "...", "full_name": "...", "definition": "..."}]}` for downstream skill consumption.

If `{workflow.on_complete}` is a non-empty string, run it as a shell command after saving. Then suggest next steps: _"D-03 complete ({term_count} terms). Recommended: create D-06 Business Flow (`hbc-create-business-flow-diagram` [BFD]) if not done, then run Phase 1 gate (`hbc-phase-gate` [PG])."_

Headless: return JSON per `references/headless-contract.md`.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest: _"Document updated. Run `hbc-traceability impact` to sync the dependent documents/tests/code?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly (it will cascade downstream). Default is false.
