# Architecture Analysis — hbc-create-glossary

**Scan date:** 2026-05-27
**Scanner:** L1 Architecture (unified: workflow-integrity + prompt-craft + cohesion)
**Prepass status:** workflow-integrity `pass` (0 issues), prompt-craft `info`

---

## Assessment

`hbc-create-glossary` is a well-structured, lean skill that fits the simple-utility category while supporting three non-trivial modes (create / update / validate) and headless invocation. The workflow is fully inline in SKILL.md, the file weight is justified, and the headless contract is explicit and correct. Two genuine issues exist: a mismatch between the `workflow_type` metadata claim and the actual four-stage structure, and a missing `output_file` variable in the Stage 3 validation script invocation that will cause a runtime failure. A handful of lower-severity findings follow. No security or data-loss risks are present.

---

## Findings

### [HIGH] Stage 3 validation script invocation references an undefined variable `{output_file}`

**File:** `SKILL.md:72`

```
python3 {workflow.validation_script} {output_file} --project-root {project-root}
```

`{output_file}` is not declared in `customize.toml` and is not a standard BMad config variable. `{workflow.template_path}`, `{workflow.output_dir}`, and `{project-root}` are all resolvable, but `{output_file}` is not. At runtime the LLM will either leave the token unexpanded (script receives the literal string `{output_file}`) or invent a path, both of which break deterministic validation. The principles file classifies exact script invocations as fragile-operation territory where precision is required.

**Fix:** Replace with a resolvable expression. The most straightforward fix, consistent with `customize.toml`, is:

```
python3 {workflow.validation_script} {workflow.output_dir}/{document_filename} --project-root {project-root}
```

Alternatively, declare `output_file` as a `customize.toml` scalar and reference it as `{workflow.output_file}`. Either path eliminates ambiguity.

---

### [MEDIUM] `workflow_type: simple-utility` contradicts a four-stage interactive workflow

**File:** `SKILL.md` frontmatter / prepass `metadata.workflow_type = "simple-utility"`

The prepass classifier tagged this skill as `simple-utility`. The principles file defines simple utilities as skills with no decisions to log — "the input/output IS the contract." This skill has four named stages, a decision log, resume/update/validate modes, a parallel-lens review menu, compaction-flush points, and a headless contract. That is a multi-stage workflow, not a simple utility. The mismatch will confuse any downstream tooling that uses `workflow_type` to select scanner profiles or generate marketplace metadata.

**Fix:** Declare `workflow_type: complex-workflow` (or `multi-stage-workflow` if that's the project's preferred term). The Decision-Log Workspace pattern is explicitly in use here — the frontmatter type should reflect it.

---

### [MEDIUM] `customize.toml` does not declare `output_file` or a resolvable filename convention, leaving the output path partially underspecified

**File:** `customize.toml:24–25`

`output_dir` is declared but the final filename is not. The skill produces a document like `D-03-<project-name>.md` but no variable carries that name. Stage 4 ("Finalize document") and the headless contract's `output_path` field both need a fully resolved path. Without a declared convention, the LLM will invent the filename, which breaks reproducibility and makes the headless contract's `output_path` non-deterministic across runs.

**Fix:** Add an `output_filename` scalar (e.g., `output_filename = "D-03_{project_name}_用語集.md"`) and reference it in Stage 3's script invocation and Stage 4's save step as `{workflow.output_dir}/{workflow.output_filename}`. This also resolves the HIGH finding above.

---

### [MEDIUM] `scan-glossary-sources.py` performs term-meaning classification with regex — intelligence leak into script

**File:** `scripts/scan-glossary-sources.py:18–30`

The script uses regex patterns to decide what content *means* — specifically, to classify whether a string is a domain term (Japanese quote pattern, capitalized phrase pattern) or an abbreviation. The principles file explicitly flags this: "Script using regex to decide what content MEANS = intelligence leak into the script." Regex can extract candidates reliably; classifying those candidates as domain-relevant terms vs. noise is a judgment call the LLM is better positioned to make.

This doesn't block execution, but it does push semantic classification into a deterministic layer that will produce false positives and false negatives the LLM then has to silently correct.

**Fix:** Limit `scan-glossary-sources.py` to structural extraction (return all candidate strings matching surface patterns). Move the "is this a meaningful domain term?" judgment to the Stage 2 Discovery prompt, where the LLM can apply context. The script's return schema already uses `term_candidates` — just stop pre-filtering by meaning.

---

### [LOW] Stage 2 uses prescriptive enumeration where an outcome statement would do

**File:** `SKILL.md:51–55`

```
For each term, capture:
- **Term** — the word or abbreviation...
- **Definition** — meaning in this project's context...
- **Category** (optional) — domain grouping...
```

The three-field list is a schema, which earns its place. However, the surrounding prose is mildly prescriptive ("For each term, capture:") where the principles file prefers outcome framing. The schema itself is correct; the framing could be trimmed to "Capture term, project-specific definition, and optional category for each." This is a style note, not a blocking issue.

---

### [LOW] `headless-contract.md` carve-out may be premature for its size

**File:** `references/headless-contract.md` (40 lines, 276 tokens)

The headless contract is 40 lines. The principles file notes that `references/` is for content "carved out of SKILL.md only when SKILL.md was genuinely too big to scan." SKILL.md is currently 96 lines, well under the 130-line hard ceiling. The headless contract could be inlined as a `## Headless Contract` section, eliminating one file reference and keeping the skill self-contained. That said, the carve-out follows the principle that each carved file works standalone, and the file is referenced correctly with a bare path. This is a mild preference, not a rule violation.

---

## Strengths

- **Inline workflow:** All four stages live in SKILL.md. The skill is 96 lines — under the 130-line ceiling — and readable in one pass. The choice to keep everything inline rather than splitting into reference files is correct for this size and complexity.

- **Headless discipline:** The headless contract is precise — required args, optional args, return schema, all status values, all blocked reasons. The SKILL.md Headless Mode section is minimal and points to the contract without duplicating it. This is the right treatment.

- **Conventions block:** Stamped correctly per the principles file's path-conventions requirement. Bare paths, `{skill-root}`, `{project-root}`, `{skill-name}` — all four entries present.

- **Decision-log workspace pattern correctly applied:** Decision log is written at compaction-flush points in Stages 2 and 3, read on resume, and closed in Stage 4. The treatment is threaded through the workflow at the moments it matters, not front-loaded as ceremony.

- **Intelligence placement is mostly correct:** `validate-glossary.py` correctly handles structural checks (duplicate terms, empty definitions, section presence, minimum count) — deterministic checks in a deterministic layer. LLM judgment checks (ambiguity, contradictions, coverage against D-02) are correctly kept in the prompt.

- **Parallel-lens menu:** The `[A]` Advanced / `[P]` Party Mode / `[C]` Continue pattern at the end of Stage 3 is a lightweight, opt-in quality gate that adds value without bloating the happy path.

- **Soft-gate elicitation in Stage 2:** "Any more terms, or shall we finalize?" is textbook soft-gate application. Well placed.

- **customize.toml shape:** Correct always-present fields (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`), correct scalar naming convention (`template_path`, `output_dir`, `validation_script`), correct override-path comments. Clean.

---

## Summary Table

| Severity | Count | Items |
|----------|-------|-------|
| HIGH     | 1     | Undefined `{output_file}` in script invocation |
| MEDIUM   | 3     | workflow_type mismatch; undeclared output filename; intelligence leak in scan script |
| LOW      | 2     | Prescriptive Discovery framing; premature headless-contract carve-out |

**Verdict: WARN** — The HIGH finding (undefined `{output_file}` in the validation script call) will cause a runtime failure in Stage 3 on every interactive run. Fix it before shipping. The two MEDIUM findings around output path convention compound the same root cause and should be addressed together.
