---
project_name: "HBLAB BMad Custom (HBC)"
kind: brownfield
date: "2026-06-19"
---

# Project Context for AI Agents — HBC (self-hosting)

_HBC is a BMad expansion module developed using its own incremental + TDD lifecycle. This file is the persistent context every HBC skill loads. Focus: unobvious rules an agent must follow when changing this repo._

## What the product is

A BMad **expansion module**: a set of **skills** (Markdown `SKILL.md` + `customize.toml` + `references/` + `assets/templates` + Python `scripts/`) that drive an incremental, per-feature, TDD-gated development lifecycle (Phase 0 → 4 phases per feature), plus the `hbc-setup` installer skill. There is **no database and no REST API** — so D-19 (ERD) and D-21 (API) baselines are **N/A** for this project.

## Technology Stack & Versions

- Skills/docs: Markdown (CommonMark + Mermaid). Bilingual onboarding docs under `docs/{vi,en}/` (Divio).
- Scripts: **Python ≥ 3.10** (stdlib only; validators + scan/report engines under `src/<skill>/scripts/`). Shared lib `src/hbc-shared/lib/hbc_validation.py`.
- Tests: **pytest** (hyphenated `test-*.py` need explicit paths; run all via `find src _bmad/scripts -name "test-*.py" -o -name "test_*.py"`). `PYTHONUTF8=1` required on Windows.
- Doc checks: `npm run check:docs` (`check_doc_links.py` + `check_mermaid.mjs`).
- Distribution: `npx bmad-method install` from `.claude-plugin/marketplace.json` (skills[] array) + `src/hbc-setup/assets/{module.yaml,module-help.csv}`.

## Critical Implementation Rules (unobvious)

1. **Skill SOURCE is English** (SKILL body, customize comments, references, script docstrings, help-csv, module.yaml). Vietnamese ONLY in `description:` trigger phrases + genuine runtime output via `{communication_language}`.
2. **Lean — every line earns its place.** Would a capable model do this without being told? If yes, cut it. `SKILL.md` ≤ ~3000 tokens (lift branch-specific detail to `references/`).
3. **Deterministic vs LLM boundary.** Scripts assert STRUCTURE only (presence, ids, counts); semantic adequacy is the LLM Layer-2 review (`hbc-shared/references/semantic-review-rubric.md`). Don't make a script judge meaning; don't make the LLM redo what a script can check.
4. **Bilingual matching.** Section/label detection matches English canonical + configured-language alias (`find_section`, `check_required_sections`). NEVER hardcode a single language in a content matcher — docs render in `{document_output_language}`.
5. **ID namespaces.** `REQ-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-)?\d{3,}` (multi-segment feature codes supported) + `REQ-SHARED-NNN`; TC is numeric `TC-\d{3,}` (NOT namespaced).
6. **Skill scripts ship in `src/<skill>/scripts/`** (referenced via `{skill-root}/scripts/`). `_bmad/scripts/` is this repo's own install — NOT distributed. New skill must be listed in `marketplace.json` skills[] or the installer drops it silently.
7. **Output layout v2:** per-feature `_bmad-output/features/<feature>/{planning-artifacts,implementation-artifacts,gates,traceability}/` + shared `_bmad-output/shared/{coding-standards,glossary,erd,api}/`.
8. **Verify before asserting / before deleting.** Check git + look at the target; output dirs (`_bmad-output`) hold real dev history — never blind-delete.

## Brownfield note

Codebase is small and fully known; a full `bmad-document-project` scan is unnecessary here — this file captures the AS-IS understanding directly. The existing-system anchors for brownfield requirement grounding are: the **skills** (features) and the **D-xx deliverables/scripts** (entities-equivalent), not DB tables/endpoints.
