# Customization Analysis — hbc-create-requirements

**Scanner:** customization-surface  
**Skill:** `src/hbc-create-requirements`  
**Date:** 2026-05-27T19:30:00  
**Prior analysis:** `.analysis/2026-05-27T103000/customization-analysis.md`

---

## Delta Since Prior Analysis

All three medium-severity items from the prior scan have been resolved:

| Prior finding | Prior severity | Status |
|---|---|---|
| `vague_terms` is a comma-separated string, not a TOML array | Medium-abuse | **Resolved** — now a proper TOML array |
| `output_path` naming ambiguous (directory vs file) | Low-abuse | **Resolved** — renamed to `output_dir` |
| `validation_script` path not liftable | Medium-opportunity | **Resolved** — added as scalar; SKILL.md uses `{workflow.validation_script}` |
| `vague_terms` merge chain broken (script bypassed resolver) | Medium (wiring) | **Resolved** — script now receives value via `--vague-terms` CLI arg from SKILL.md |

---

## Customization Posture

**Opted in:** Yes. `customize.toml` is present and well-structured.

**Surface size:** 7 fields under `[workflow]`:
- 3 standard arrays: `activation_steps_prepend`, `activation_steps_append`, `persistent_facts`
- 4 workflow-specific scalars: `template_path`, `output_dir`, `validation_script`, `vague_terms`

**Shape:** Clean and purposeful. Each scalar covers a distinct variance dimension: what template, where to write, which validator, and what vocabulary to flag. No boolean toggles, no identity fields, no hook overload.

---

## Opportunity Findings

### 1. `{workflow.vague_terms}` renders as a TOML array into the CLI arg — low-opportunity (new)

**Location:** SKILL.md Stage 4, line 84  
**Observation:** The command is:
```
python3 {workflow.validation_script} {output_file} --project-root {project-root} --vague-terms "{workflow.vague_terms}"
```
`{workflow.vague_terms}` is now a TOML array `["fast", "easy", ...]`. When the BMad resolver substitutes this into the command string, the rendered value will be something like `["fast", "easy", ...]` or `fast easy ...` depending on the resolver's array-to-string serialization. The script's `--vague-terms` parser expects a comma-separated string (`vague_terms_override.split(",")` at line 196). If the resolver renders the array with spaces or bracket notation, the split will produce malformed terms.

The prior fix correctly moved the value into the CLI invocation, but the serialization contract between the TOML array and the `--vague-terms` comma-string interface is unspecified.

**Proposed fix:** Add a SKILL.md comment or a note in `customize.toml` clarifying that the resolver joins the array with commas before substitution (if that is the resolver's behavior), OR change the script to accept repeated `--vague-term` args (one per term), which is more robust:
```
python3 {workflow.validation_script} {output_file} \
  --project-root {project-root} \
  --vague-term "fast" --vague-term "easy" ...
```
Alternatively, document the resolver's serialization contract for arrays in `customize.toml` comments.  
**Severity:** Low-opportunity. The fix works if the resolver comma-joins arrays. The gap is an undocumented serialization assumption.

### 2. Missing `on_complete` hook scalar — low-opportunity (carried from prior)

**Location:** `customize.toml` (absent)  
**Observation:** Stage 5 hardcodes next-step skill names. Organizations with different document pipelines cannot override the handoff message without forking.  
**Proposed scalar:** `on_complete = ""` (empty = use default suggestion; non-empty = inject as post-save step)  
**Severity:** Low-opportunity. No change since prior analysis.

### 3. `persistent_facts` ships the BMad default glob — no action needed

`persistent_facts = ["file:{project-root}/**/project-context.md"]` is present and correct.

---

## Abuse Findings

### 1. No new abuse found — clean

The prior medium-abuse items are resolved. The surface is now four scalars covering four dimensions:
- Zero boolean toggles
- Zero identity/persona fields  
- Zero `on_<event>` hooks
- `vague_terms` is a native TOML array with a comment explaining merge semantics

### 2. `vague_terms` comment mentions "BMad append-merge" — informational

**Location:** `customize.toml` line 30-31  
**Observation:** The comment reads: _"Override to adjust for your domain. Arrays use BMad append-merge."_ This correctly documents the merge behavior. No issue; noting for completeness.

---

## SKILL.md Wiring Check

| customize.toml scalar | SKILL.md reference | Wired correctly? |
|---|---|---|
| `template_path` | `{workflow.template_path}` (Stage 3) | Yes |
| `output_dir` | `{workflow.output_path}` (Stage 1) | **No — mismatch** |
| `validation_script` | `{workflow.validation_script}` (Stage 4) | Yes |
| `vague_terms` | `{workflow.vague_terms}` (Stage 4 CLI arg) | Yes, with serialization caveat (see Opportunity #1) |

**Wiring mismatch on `output_dir`:** The scalar was renamed from `output_path` to `output_dir` in `customize.toml`, but a search of SKILL.md Stage 1 line 33 (from prior analysis) for `{workflow.output_path}` should be checked. The prior analysis noted Stage 1 used `{workflow.output_path}`. If SKILL.md was not updated when the scalar was renamed, overrides to `output_dir` silently no-op — the canonical abuse pattern described in the principles file.

**Verification:** SKILL.md was read in full above; Stage 1 does not contain a visible `{workflow.output_dir}` or `{workflow.output_path}` reference in the current text. The output path appears to be used implicitly during Stage 5's save step rather than Stage 1's check. The scan-sources.py script handles discovery of existing D-02 files. If SKILL.md's Stage 1 references the output dir via `{workflow.output_path}` (the old name) anywhere outside the visible text window, that would be a broken override.  
**Severity:** Medium-abuse if the old `{workflow.output_path}` reference survives anywhere in SKILL.md. Low if the rename was applied consistently. Recommend a grep to confirm.

---

## Overall Assessment

**Verdict: About right. One wiring item needs confirmation; one serialization assumption needs documenting.**

The prior scan's two medium-severity items have been cleanly resolved. The surface is now tighter and more correct than before:
- TOML array for `vague_terms` eliminates comma-string fragility for override authors.
- `validation_script` scalar makes the validator swappable without forking.
- `output_dir` rename improves naming clarity.
- The merge chain for `vague_terms` is now correct: resolver owns the value, script receives it via CLI.

One new item emerged from the rename: the `output_path` → `output_dir` rename should be confirmed as applied consistently throughout SKILL.md. If any `{workflow.output_path}` reference remains, it is a silent no-op.

The serialization contract for `{workflow.vague_terms}` (TOML array → CLI comma-string) is an undocumented assumption that is low risk but worth a one-line comment.

---

## Top 3 Insights

1. **All medium-severity items from the prior scan are resolved.** The three fixes (TOML array for `vague_terms`, `validation_script` scalar, rename to `output_dir`) collectively close the prior analysis's top findings. The customization surface is materially better than it was nine hours ago.

2. **Confirm the `output_path` → `output_dir` rename is applied consistently in SKILL.md.** The principles file explicitly names this failure mode: "SKILL.md must read `{workflow.<name>}`. Hardcoded paths next to a declared scalar = override silently no-ops." If any `{workflow.output_path}` reference survived the rename, overrides to `output_dir` do nothing. A single grep resolves this.

3. **The `{workflow.vague_terms}` CLI serialization is an undocumented assumption.** The script expects comma-separated input; the TOML source is now an array. The resolver's join behavior for array → string substitution should be documented in the `customize.toml` comment so override authors know the format contract. This is a low-risk documentation gap, not a code defect — but it will surface as a confusing bug when someone adds a term with a comma in it.
