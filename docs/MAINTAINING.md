# Maintaining the HBC docs

This is a meta-document for **doc maintainers**, not end users. It records the
conventions that keep the bilingual documentation correct and in sync, and the
v2 model the docs must reflect.

> **Authority note.** When the docs, this file, or `module-help.csv` disagree about
> the HBC model, the **v2 documentation contract** (`.v2-doc-contract.tmp.md` at the
> repo root) wins. It is the single source of truth for the *model* (phases, scope,
> IDs, skill set). `module-help.csv` remains the source of truth for the *mechanics*
> a single skill exposes (menu codes, args, `required` flags) — see §2.

## 1. Bilingual mirror rule

Docs live in two mirrored trees:

```
docs/vi/   (source language — write here first)
docs/en/   (translation — mirror of vi/)
```

- **Vietnamese is the source.** Write or change `docs/vi/...` first, then mirror
  the change into the matching `docs/en/...` file.
- The two trees must stay **structurally symmetric**: every file under `vi/` has a
  counterpart at the same path under `en/`, and vice versa.
- The same applies to the front door: `README.md` (VI — the default/source) ↔ `README.en.md` (EN).

The current Divio file set (mirror these exactly across `vi/` and `en/`):

- `tutorials/`: `quickstart.md`, `getting-started-hbc.md`, `workflow-map.md`
- `explanation/`: `concepts.md`, `why-incremental-tdd.md`
- `how-to/`: `run-a-phase-gate.md`, `manage-traceability.md`, `use-headless-mode.md`, `customize-config.md`
- `reference/`: `concept-glossary.md`, `skills-catalog.md`, `deliverables-glossary.md`

Each `{lang}/index.md` routes to its four Divio sections; `docs/index.md` routes to
`{vi,en}/index.md`. Keep every file's language-switch header and "Liên quan / Related"
cross-links intact when you edit.

## 2. The v2 model the docs must reflect

HBC is an expansion module for the BMad Method. Delivery is **incremental, per-feature
(staged delivery)**: each feature runs four gated phases + soft-TDD, then ships
independently. "Waterfall" describes a *delivery model* (how scope is sliced), not HBC's
architecture — keep that reframing wherever it appears; do not delete the word, frame it
as contrast. Every doc must be consistent with the following.

### 2.1 Phases & the run-once init

- **Phase 0 — Project Init (`PI`, `hbc-project-init`):** run **once, project-wide**,
  before any feature. Creates the SHARED deliverables (D-12 Coding Standards, D-03
  Glossary, baseline D-19 ERD / D-21 API). Idempotent (skips what exists); takes no
  `feature` arg.
- Per feature: **Phase 1 Analysis → Phase 2 Design + Test Design → Phase 3
  Implementation → Phase 4 Testing**, each closed by a **Phase Gate** (`PG <n>`) that
  carries `feature=`.

### 2.2 Output layout (per-feature / shared / dual)

The old flat `_bmad-output/planning-artifacts/...` layout is **gone**. Path examples in
the docs must use the per-feature or shared form:

```
_bmad-output/features/<feature>/{planning-artifacts, implementation-artifacts, gates, traceability}/
_bmad-output/shared/{coding-standards, glossary, erd, api}/
```

Scope of each deliverable:

| Scope | Deliverables | Location |
| --- | --- | --- |
| **Per-feature** | D-02, D-06, D-26, D-27 | `features/<feature>/planning-artifacts/` |
| **Shared** | D-03 (glossary), D-12 (coding-standards) | `shared/glossary/`, `shared/coding-standards/` |
| **Dual** | D-19 (erd), D-21 (api) | shared baseline `shared/erd\|api/` + optional per-feature override — **path-existence precedence** (override wins if it exists) |

Implementation artifacts (task-breakdown, code, test-execution-report, acceptance-report)
→ `features/<feature>/implementation-artifacts/`. Gates → `features/<feature>/gates/`.
Matrix → `features/<feature>/traceability/`.

### 2.3 IDs

- Requirements: **`REQ-<FEAT>-NNN`** (e.g. `REQ-AUTH-001`) per feature, plus
  **`REQ-SHARED-NNN`** for shared requirements. Legacy `REQ-NNN` still parses.
- Test cases: `TC-NNN`, sequential **within each feature's** D-27.
- EARS keyword syntax stays English (`WHEN … THE SYSTEM SHALL …`); surrounding prose
  follows `{document_output_language}`.

### 2.4 Soft TDD & traceability

- Phase 3 `IM` runs **RED → GREEN → REFACTOR**. Enforcement is *soft*: failing-test
  (**RED**) evidence is recorded before code is written, and the Phase 3 gate checks for
  it (self-attested, not crypto-proof). Frame this as "test-first with RED evidence", not
  merely "tests exist".
- The traceability matrix has **8 columns**:
  `feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp`.
  Coverage counts `design_ref`/`code_ref`/`test_ref`. The matrix is per-feature; `TRR`
  can roll up across features (shared rows counted once).
- **`SYNC` (Cascade Sync)** proposes downstream updates to docs/tests/code when a source
  doc changes — document it as the impact-analysis step, not an auto-edit.

### 2.5 Canonical skill / agent set

Five coordinator agents: `BA` (P1), `ARCH` (P2 Design), `QA` (P2 Test Design),
`DEV` (P3), `TST` (P4).

| Phase | Codes |
| --- | --- |
| **0 · Project Init** | `PI` (hbc-project-init) — shared D-12/D-03 + baseline D-19/D-21, run once |
| **1 · Analysis** | `REQ` D-02 (per-feature, required) · `GLO` D-03 (shared) · `BFD` D-06 (per-feature) |
| **2 · Design** | `ERD` D-19 (dual, required) · `CS` D-12 (shared, required) · `API` D-21 (dual) |
| **2 · Test Design** | `TP` D-26 (per-feature, required) · `TS` D-27 (per-feature, required) · `IR` readiness gate (per-feature, required) |
| **3 · Implementation** | `TB` task-breakdown (per-feature, required) · `IM` implement TDD/RED (per-feature, required) |
| **4 · Testing** | `TE` test-execution (per-feature, required) · `AC` acceptance (per-feature, required) |
| **Cross-cutting** | `PG` phase-gate (per-feature, `feature=`) · `TRI/TRU/TRR/TRA` traceability (8-col) · `SYNC` cascade sync |

New since the first doc pass: **`PI`**, **`IR`** (hbc-check-implementation-readiness — the
Phase-2 seam gate reconciling D-02 ↔ D-21/D-26/D-27 + matrix), and **`SYNC`**. Required
for gates: D-02, D-12, D-19, D-26, D-27. Optional: D-03, D-06, D-21.

### 2.6 Headless

Per-feature skills require `feature=<slug>` in headless, else they are blocked with
`feature_required`. Dual skills (ERD/API): `feature` optional (baseline shared default).
Shared skills (GLO/CS) and Phase 0 (PI): no `feature` arg.

## 3. Single source of truth for skill mechanics

The authoritative data for **skill codes, menu args, deliverable IDs, `required` flags,
and per-skill output locations** is:

```
_bmad/hbc/module-help.csv
```

Several docs **copy** this data by hand (a deliberate trade-off — see §5):

- `docs/{vi,en}/reference/skills-catalog.md`
- `docs/{vi,en}/reference/deliverables-glossary.md`
- `docs/{vi,en}/tutorials/workflow-map.md`
- tutorials that show commands (`getting-started-hbc.md`, `quickstart.md`, `how-to/*`)

> **Caveat — CSV can lag the model.** `module-help.csv` describes *mechanics*; the v2
> *model* (Phase 0/`PI`, `IR`, `SYNC`, per-feature/shared/dual output paths,
> `REQ-<FEAT>-NNN`) lives in the contract (§2). Where the CSV's `output-location` column
> or skill list trails behind the contract, the **contract and the docs lead** — and the
> CSV should be updated to match. Do not "correct" the docs back to a stale CSV value;
> reconcile both toward the contract.

### When `module-help.csv` changes

1. Identify the changed skill code(s) / deliverable(s) / args.
2. Grep the docs tree for each affected token and update **every** hit, in **both** languages:

   ```bash
   grep -rn "IM\b\|task TASK-xxx\|D-19" docs/
   ```

3. Pay special attention to the **"Required" columns** — `required` is a property of a
   *skill*. `PG` and `TRI/TRU/TRR/TRA` are `required = false` and must **not** be marked
   ✅ as deliverables.
4. Re-run the doc checks (below) and re-read the changed pages.

## 4. Doc checks (links + Mermaid)

Two checks, wired as npm scripts (run both with `npm run check:docs`):

```bash
npm run check:links     # python _bmad/scripts/check_doc_links.py .
npm run check:mermaid   # node   _bmad/scripts/check_mermaid.mjs
```

**Link checker** (`check_doc_links.py`, stdlib Python — no install): verifies every
relative Markdown link across `docs/` and the top-level READMEs resolves to an
existing file **and** that every `#anchor` matches a heading in the target file
(GitHub-compatible slugs, incl. Unicode/Vietnamese). Does not validate external
`http(s)` links.

**Mermaid checker** (`check_mermaid.mjs`): extracts every ` ```mermaid ` block and
validates it with the **official `mermaid.parse()`** (mermaid v11) headless via
jsdom — the same grammar GitHub/GitLab render with. Requires `npm install` (the
`mermaid` + `jsdom` devDependencies in `package.json`); no browser/Chromium needed.

Both exit non-zero on failure (CI-friendly).

### Wiring into CI

```yaml
docs:link-check:
  image: python:3.11
  script: [ "python _bmad/scripts/check_doc_links.py ." ]
  rules:
    - changes: [ "docs/**/*", "README*.md" ]

docs:mermaid-check:
  image: node:20
  script:
    - npm ci
    - node _bmad/scripts/check_mermaid.mjs
  rules:
    - changes: [ "docs/**/*", "README*.md" ]
```

## 5. The trade-off we chose (and the exit)

We keep the bilingual mirror and the hand-copied reference data **manually**,
backed by the conventions above + the CI link check. This is the "boring, cheap
now" option; it is correct only as long as maintainers follow §1–§3.

If HBC's skill set starts changing often, the cheaper long-term path is to
**generate** `skills-catalog.md` and `deliverables-glossary.md` (both languages)
directly from `module-help.csv`, leaving only tutorials/explanations hand-written.
That eliminates the drift class entirely at the cost of building a bilingual
generator. Revisit this when the manual sync becomes painful.

## 6. Verification status

What HAS been verified:

- The Divio file set is structurally symmetric across `vi/` and `en/`.
- All relative links and `#anchors` pass `check_doc_links.py`; Mermaid blocks pass
  `check_mermaid.mjs`.

What has NOT been fully verified — do this before relying on the docs in anger:

- **CSV ↔ model reconciliation.** `module-help.csv` may still carry v1 mechanics
  (flat `planning_artifacts`/`implementation_artifacts` output locations; no `PI`/`IR`/
  `SYNC` rows). Reconcile the CSV toward the contract (§2), then re-cross-check the
  reference docs against it.
- **No full end-to-end run.** Command sequences are correct *on paper* but have not been
  executed start-to-finish against a live install. Run the Quickstart + Walkthrough once
  on a clean project — including Phase 0 (`PI`) and an `IR` readiness check — and
  reconcile any drift.
- **Illustrative outputs are not captured from real runs.** The `bmad-help` and `BA`
  greeting blocks in `quickstart.md`, and the example ERD/API output, are explicitly
  labelled *illustrative*. Replace them with real captured output during the end-to-end
  run.

## 7. Known intentional deviations

- **Version:** the docs target HBC on BMad Method v6.x (this project runs v6.8.0; the
  README requirement floor is v6.3.0+). Update the README note if the floor moves.
- **Divio purity is relaxed on purpose:** `workflow-map.md` is reference-like but filed
  under Tutorials (labelled "best read after your first run"); `quickstart.md` embeds a
  small troubleshooting branch (normally How-to). This trades strict Divio separation for
  a smoother first-run path — keep it unless it causes confusion.
- **`bmad-help` is a BMad *core* skill, not part of HBC.** Docs lean on it as the
  catch-all "what next" helper but always provide a fallback (`BA`) so a missing/renamed
  `bmad-help` never blocks a new user — keep those reminders.
</content>
</invoke>
