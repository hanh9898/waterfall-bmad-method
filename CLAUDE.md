# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

**HBLAB BMad Custom (HBC)** — an expansion module for the [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) (requires `core` + `bmm`). It is **not an application**; it is a library of BMad **agents + workflow skills** that drive an incremental, per-feature, TDD development lifecycle. End users install it via `npx bmad-method install` and invoke the skills from inside an AI coding agent (Claude Code, Cursor), not a terminal.

The deliverables HBC generates are `D-xx` documents (D-02 Requirements, D-03 Glossary, D-12 Coding Standards, D-19 ERD, D-21 API Spec, D-26 Test Plan, etc.) plus a requirements **traceability matrix** linking every `REQ-<FEAT>-NNN` ID through design → code → test.

## Repo layout

| Path | Role |
| --- | --- |
| `src/hbc-*/` | **Source of truth** — the HBC skills authored here. Each is one skill. |
| `src/hbc-shared/` | Shared library + references imported by every skill. |
| `.claude-plugin/marketplace.json` | Declares the plugin and lists which `src/hbc-*` dirs ship as skills. |
| `_bmad/` | The **installed** BMad runtime in this working copy (`core`, `bmm`, `bmb`, config). Treat as generated/vendored — edit `src/`, not here. |
| `.claude/skills/bmad-*` | Installed/compiled BMad skills (from `bmm`/`core`/`bmb`). Not the HBC source. |
| `_bmad-output/` | Where generated D-xx artifacts land at runtime. |
| `docs/vi`, `docs/en` | User docs, organized by the [Divio](https://docs.divio.com) system (tutorials / how-to / reference / explanation). Vietnamese is canonical; English is a mirror. |
| `templates/` | BMad workflow templates. |

When authoring a new skill it goes in `src/`, **never** in a top-level `skills/` dir, and a skill's `.decision-log.md` lives under that skill's `references/`.

## Skill anatomy

Every `src/hbc-*/` skill follows the same shape:

- `SKILL.md` — frontmatter (`name`, `description` with trigger phrases incl. the agent-menu code like `[REQ]`) + the workflow prose. Skills support `create` (default) / `update` / `validate` intents and most accept `--headless` / `-H` (contract in `references/headless-contract.md`).
- `customize.toml` — **DO NOT hand-edit for behavior**; it is the regenerated customization surface. It declares resolvable paths (`template_path`, `output_dir`, `validation_script`, `scan_script`), `persistent_facts`, and append-merge arrays. Team/user overrides go in `_bmad/custom/<skill>.toml`.
- `scripts/` — Python 3.10+ helpers (scan, validate). Path placeholders in SKILL.md like `{workflow.scan_script}` resolve through `customize.toml`.
- `scripts/tests/test_*.py` — pytest tests for those scripts.
- `references/` — supporting prose loaded on demand. `assets/` — D-xx templates.

## Validator architecture (important)

Validators are **3-layer** and deliberately split structure from meaning:

1. **Structural layer** — Python scripts (`scripts/validate-*.py`) check structure only: required sections present, tables parse, IDs well-formed.
2. **Shared primitives** — `src/hbc-shared/lib/hbc_validation.py` is the single source of truth for table parsing, column extraction, and **language-aware** section detection. Validators import it via a sys.path bootstrap relative to skill root:
   ```python
   sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
   from hbc_validation import parse_table, extract_column, find_section, verdict
   ```
3. **Semantic layer** — "is this *meaningful enough*" judgement is **out of scope for Python**; it belongs to the LLM review layer. The `verdict` helper encodes this honestly with semantic states `n/a` / `pending` / `passed`.

**Language policy (load-bearing):** NO hardcoded Japanese anywhere. Section detection passes the English canonical label *plus* the configured `document_output_language` label, e.g. `find_section(text, "Scope", "Phạm vi")`. Never hardcode language-specific section names in a validator.

## Commands

```bash
# Doc checks (used in CI / before commit)
npm run check:links     # python _bmad/scripts/check_doc_links.py .
npm run check:mermaid   # validate mermaid diagrams via jsdom + mermaid
npm run check:docs      # both of the above

# Python tests (pytest; no config file — discovery is path-based, run from repo root)
python3 -m pytest                     # all ~237 tests
python3 -m pytest src/hbc-shared      # just the shared validation lib
python3 -m pytest src/hbc-create-requirements/scripts/tests   # one skill's tests
python3 -m pytest src/hbc-shared/lib/tests/test_hbc_validation.py::test_extract_column   # single test
```

There is no JS/TS build step — `package.json` only carries the doc-check scripts and their devDependencies.

## Lifecycle model (context for what the skills do)

Phase 0 (`PI`, run once for the whole project, idempotent, no `feature`) produces **shared** deliverables. Then each feature runs sequentially through 4 gated phases, each producing **per-feature** deliverables under `_bmad-output/features/<feature>/`:

- Phase 1 Analysis (`BA`): `REQ`, `GLO`, `BFD`
- Phase 2 Design (`ARCH`) + Test Design (`QA`): `ERD`, `CS`, `API`, `TP`, `TS`, `IR`
- Phase 3 Implementation (`DEV`): `TB`, `IM` (TDD)
- Phase 4 Testing (`TST`): `TE`, `AC`
- Cross-cutting: `PG` (Phase Gate, always carries `feature=`) and `TRI`/`TRU`/`TRR`/`TRA`/`SYNC` (traceability + cascade sync)

Scope of a deliverable is **shared** (whole project), **per-feature**, or **dual** (shared baseline + optional per-feature override) — check the `output_dir` in each skill's `customize.toml`.
