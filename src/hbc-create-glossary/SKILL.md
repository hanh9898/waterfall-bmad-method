---
name: hbc-create-glossary
description: "Generate D-03 Glossary with domain terms and definitions. Use when user says 'glossary', 'thuật ngữ', or agent menu [GLO]."
---

# Create Glossary

## Overview

Generate D-03 (Glossary) — a living reference of domain terms, abbreviations, and project-specific definitions. Terms extracted from existing artifacts (D-02, project-context.md, interview notes) and user input. The glossary ensures consistent terminology across all downstream documents.

Four-stage workflow: Prerequisites → Discovery → Generation → Save. Supports resume state, headless mode, and parallel-lens review. Requires Python 3.10+ for validation script.

**Args:** `create` (default), `update` (add terms to existing D-03), `validate` (check existing D-03). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively. Source documents are required via `--sources` arg. Returns JSON per `references/headless-contract.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`. If `{workflow.glossary_output_path}` exists with `lastStep` not `complete`, surface it with its `updated` timestamp and offer to resume before proceeding to Stage 1.

## Stage 1: Prerequisites

1a. **Intent gate.** Confirm user wants to create/update glossary. If wrong skill: requirements → `hbc-create-requirements` [REQ], entity relationships → `hbc-create-er-diagram` [ER], business flows → `hbc-create-business-flow-diagram` [BF]. Headless: skip — intent is given by invocation.

1b. **Source scan.** Run pre-pass to discover project state:

```
python3 {workflow.scan_script} --project-root {project-root}
```

Headless: forward `--sources` arg if provided: `python3 {workflow.scan_script} --project-root {project-root} --sources "{sources}"`.

Returns JSON with `state` (fresh/resume/update), `existing_d03`, `source_docs` (D-02, project-context, etc.), and `raw_candidates` (each with `term` and `method`: quoted/abbreviation). Candidates are raw structural extractions — filter for domain relevance using LLM judgment in Stage 2. Use `state` to route:
   - **Fresh** — no prior D-03. Proceed to Stage 2.
   - **Resume** — partial D-03 found (`lastStep` < `complete`). Show summary, offer resume or restart. Restart: overwrite with fresh template, reset frontmatter, append restart note to decision log.
   - **Update** — complete D-03 exists. Show current term count, proceed to Update Mode.

After routing: initialize `.decision-log.md` as a peer of `{workflow.glossary_output_path}` — create if absent, append a date-stamped session heading if present. If scan script fails or Python is unavailable, ask the user to provide source paths directly and proceed with empty candidates.

## Stage 2: Discovery

Open with an invitation for the user to share domain-specific terms, abbreviations, and jargon they consider essential for this project. Then filter `raw_candidates` from scan for domain relevance — discard common abbreviations (API, SQL, HTML, etc.) and generic terms. Present filtered candidates for confirmation: _"Here's what we also found in your documents — confirm, modify, or discard."_ If `candidate_count == 0` and `source_count > 0`, note that auto-extraction found no marked terms. Capture term, project-specific definition (not generic dictionary definitions), and optional category (e.g., business, technical) for each.

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

**LLM judgment checks:**
- Definitions are unambiguous and project-specific.
- No contradictions between term definitions.
- Key domain concepts from D-02 are represented.
- If no abbreviations were collected, add a single row "N/A" to the abbreviations table or omit the section entirely. Do not leave an empty table.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

**Compaction flush:** Write term count and validation summary to decision log.

**Parallel-lens menu:** `[A]` Advanced (challenge definitions, find missing D-02 terms) / `[P]` Multi-lens (terminology specialist, domain expert, end user perspectives) / `[C]` Continue. If subagents unavailable, apply lens perspectives directly. Headless: skip to Stage 4.

## Validate Mode

When invoked with `validate` arg: run Stage 1b scan to locate existing D-03, then run the validation script against it. Present results (interactive) or return headless JSON with validation object. No discovery or generation stages run. If no D-03 found, return `blocked` with `reason: "no_existing_d03"`.

## Update Mode

When `state: update` from scan or `update` arg: read the scan JSON for the existing D-03 path and new candidates. Present diff — candidates not yet in the existing glossary. Merge non-duplicate terms; surface duplicates (same term, different definition) for user resolution. Auto-append a new row to the "Lịch sử sửa đổi" (Revision History) table with today's date and change summary. Then proceed to Stage 3 (Generation) for validation. Headless: auto-merge non-conflicting terms, return `blocked` with `reason: "duplicate_conflict"` when definitions clash.

## Stage 3b: Semantic Review (Lớp 2)

Structural validation only proves cấu trúc. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`): confirm every definition is unambiguous and project-specific, no contradictions, and key D-02 domain concepts are represented. Record `semanticReview` frontmatter (A-3: `status` passed only when no open concerns, else `pending`). The Phase 2 gate REVIEW item (#5) reads it.

## Stage 4: Save and Handoff

Save document to `{workflow.glossary_output_path}` — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). On create: fill the blank date in the pre-seeded "Lịch sử sửa đổi" (Revision History) row. On update: revision row already appended in Update Mode. Audit decision-log entries against D-03: every logged decision reflected in the document or explicitly set aside. Append closing session to decision log.

Write `glossary-distillate.json` alongside D-03 — `{"terms": [{"term": "...", "definition": "...", "category": "..."}], "abbreviations": [{"abbr": "...", "full_name": "...", "definition": "..."}]}` for downstream skill consumption.

If `{workflow.on_complete}` is a non-empty string, run it as a shell command after saving. Then suggest next steps: _"D-03 complete ({term_count} terms). Recommended: create D-06 Business Flow (`hbc-create-business-flow-diagram` [BF]) if not done, then run Phase 1 gate (`hbc-phase-gate` [PG])."_

Headless: return JSON per `references/headless-contract.md`.
