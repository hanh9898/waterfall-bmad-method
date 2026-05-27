---
name: hbc-create-glossary
description: "Generate D-03 Glossary with domain terms and definitions. Use when user says 'glossary', 'thuật ngữ', '用語集', or agent menu [GLO]."
---

# Create Glossary

## Overview

Generate D-03 用語集 (Glossary) — a living reference of domain terms, abbreviations, and project-specific definitions. Terms extracted from existing artifacts (D-02, project-context.md, interview notes) and user input. The glossary ensures consistent terminology across all downstream documents.

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

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

## Stage 1: Prerequisites

1a. **Intent gate.** Confirm user wants to create/update glossary. If wrong skill, suggest the right one (e.g., if user wants API reference, suggest `hbc-create-requirements` [REQ]). Headless: skip — intent is given by invocation.

1b. **Source scan.** Run pre-pass to discover project state:

```
python3 {workflow.scan_script} --project-root {project-root}
```

Returns JSON with `state` (fresh/resume/update), `existing_d03`, `source_docs` (D-02, project-context, etc.), and `raw_candidates` (each with `term` and `method`: quoted/abbreviation). Candidates are raw structural extractions — filter for domain relevance using LLM judgment in Stage 2. Use `state` to route:
   - **Fresh** — no prior D-03. Proceed to Stage 2.
   - **Resume** — partial D-03 found (`lastStep` < `complete`). Show summary, offer resume or restart.
   - **Update** — complete D-03 exists. Load as baseline, show current term count.

## Stage 2: Discovery

Filter `raw_candidates` from scan for domain relevance — discard common abbreviations (API, SQL, HTML, etc.) and generic terms. Present filtered candidates as defaults for confirmation. If `candidate_count == 0` and `source_count > 0`, note that auto-extraction found no marked terms and ask the user to provide terms directly.

Open with an invitation for the user to share domain-specific terms, abbreviations, and jargon beyond what was auto-extracted. Capture term, project-specific definition (not generic dictionary definitions), and optional category (e.g., business, technical) for each.

At each batch of terms, soft-gate: _"Any more terms, or shall we finalize?"_

Silently capture any requirements or business-flow insights mentioned — surface in Stage 4 handoff.

**Compaction flush:** Write all discovered terms (term + definition + category for each) and total count to decision log.

## Stage 3: Generation

Populate `{workflow.template_path}` with discovered terms. Ensure:
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

**Parallel-lens menu:**
- `[A]` Advanced — challenge definitions for ambiguity, find missing terms from D-02
- `[P]` Multi-lens review — multiple reviewer perspectives (terminology specialist, domain expert, end user)
- `[C]` Continue — proceed to save

## Update Mode

When invoked with `update` arg or when scan returns `state: update`: load existing D-03 as baseline. Run scan script to extract new term candidates from updated source documents. Present diff — new candidates not in existing glossary, existing terms with changed source context. Merge non-duplicate terms; surface duplicates (same term, different definition) for user resolution. Auto-append a new row to 改訂履歴 with today's date and change summary. Headless: auto-merge non-conflicting terms, return `blocked` with `reason: "duplicate_conflict"` when definitions clash.

## Stage 4: Save and Handoff

Save document to `{workflow.glossary_output_path}` — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`). Populate the Revision History row's date with today's date. Append closing session to decision log.

Write `glossary-distillate.json` alongside D-03 in the same directory — a flat `{"terms": {"term": "definition", ...}, "abbreviations": {"abbr": "full_name", ...}}` map for downstream skill consumption.

If `{workflow.on_complete}` is set, run it after saving. Then suggest next steps: _"D-03 complete ({term_count} terms). Recommended: create D-06 Business Flow (`hbc-create-business-flow-diagram` [BF]) if not done, then run Phase 1 gate (`hbc-phase-gate` [PG])."_

Headless: return JSON per `references/headless-contract.md`.
