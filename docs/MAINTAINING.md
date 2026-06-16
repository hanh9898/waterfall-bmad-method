# Maintaining the HBC docs

This is a meta-document for **doc maintainers**, not end users. It records the
conventions that keep the bilingual documentation correct and in sync.

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

## 2. Single source of truth for skills & deliverables

The authoritative data for skill codes, menu args, deliverable IDs, required
flags, and output locations is:

```
_bmad/hbc/module-help.csv
```

Several docs **copy** this data by hand (a deliberate trade-off — see below):

- `docs/{vi,en}/reference/skills-catalog.md`
- `docs/{vi,en}/reference/deliverables-glossary.md`
- `docs/{vi,en}/tutorials/workflow-map.md`
- tutorials that show commands (`getting-started-hbc.md`, `quickstart.md`, `how-to/*`)

### When `module-help.csv` changes

1. Identify the changed skill code(s) / deliverable(s) / args.
2. Grep the docs tree for each affected token and update **every** hit, in **both** languages:

   ```bash
   grep -rn "IM\b\|task TASK-xxx\|D-19" docs/
   ```

3. Pay special attention to the **"Required" columns** — the `required` field is a
   property of a *skill*. Skills like `PG` and `TRI/TRU/TRR/TRA` are
   `required = false` and must **not** be marked ✅ as deliverables.
4. Re-run the doc checks (below) and re-read the changed pages.

## 3. Doc checks (links + Mermaid)

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

## 4. The trade-off we chose (and the exit)

We keep the bilingual mirror and the hand-copied reference data **manually**,
backed by the convention above + the CI link check. This is the "boring, cheap
now" option; it is correct only as long as maintainers follow §2.

If HBC's skill set starts changing often, the cheaper long-term path is to
**generate** `skills-catalog.md` and `deliverables-glossary.md` (both languages)
directly from `module-help.csv`, leaving only tutorials/explanations hand-written.
That eliminates the drift class entirely at the cost of building a bilingual
generator. Revisit this when the manual sync becomes painful.

## 5. Verification status

What HAS been verified:

- All skill codes, args, deliverable IDs, `required` flags, and output locations
  are cross-checked against `module-help.csv`.
- All relative links and `#anchors` pass `check_doc_links.py`.

What has NOT been verified — do this before relying on the docs in anger:

- **No full end-to-end run.** The command sequences are correct *on paper* but
  have not been executed start-to-finish against a live install. Run the
  Quickstart + Walkthrough once on a clean project and reconcile any drift.
- **Illustrative outputs are not captured from real runs.** The `bmad-help` and
  `BA` greeting blocks in `quickstart.md`, and the "Change Password" ERD/API
  examples, are explicitly labelled *illustrative*. Replace them with real captured
  output when you do the end-to-end run.

## 6. Known intentional deviations

- **Version:** the docs target HBC on BMad Method v6.x (this project runs v6.8.0;
  the README requirement floor is v6.3.0+). Update the README note if the floor moves.
- **Divio purity is relaxed on purpose:** `workflow-map.md` is reference-like but
  filed under Tutorials (labelled "best read after your first run"); `quickstart.md`
  embeds a small troubleshooting branch (normally How-to). This trades strict Divio
  separation for a smoother first-run path — keep it unless it causes confusion.
- **`bmad-help` is a BMad *core* skill, not part of HBC.** Docs lean on it as the
  catch-all helper but always provide a fallback (`BA`) so a missing/renamed
  `bmad-help` never blocks a new user.
