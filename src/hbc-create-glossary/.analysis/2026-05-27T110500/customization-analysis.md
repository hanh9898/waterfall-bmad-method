# Customization Surface Analysis — hbc-create-glossary

**Scan date:** 2026-05-27  
**Scanner:** L3 Customization Surface  
**Skill path:** `src/hbc-create-glossary`

---

## Customization Posture

The skill has opted in to customization. `customize.toml` declares three workflow scalars plus the three always-present arrays:

| Field | Type | Value |
|---|---|---|
| `template_path` | scalar | `templates/D-03_用語集_template.md` |
| `output_dir` | scalar | `{project-root}/_hbc_output/plan` |
| `validation_script` | scalar | `scripts/validate-glossary.py` |
| `persistent_facts` | array | `["file:{project-root}/**/project-context.md"]` |
| `activation_steps_prepend` | array | `[]` |
| `activation_steps_append` | array | `[]` |

Surface size is lean — no booleans, no identity fields, no `on_<event>` hooks, no arrays-of-tables. The shape is appropriate for a focused document-generation skill.

---

## Abuse Findings

### [HIGH-ABUSE] `output_dir` declared but never read — override silently no-ops

**Location:** `customize.toml` line 24 / `SKILL.md` Stage 3 line 73  
**Detail:** `customize.toml` declares `output_dir` so teams can redirect where D-03 lands. However, SKILL.md never references `{workflow.output_dir}`. The validation command in Stage 3 uses a bare `{output_file}` variable:

```
python3 {workflow.validation_script} {output_file} --project-root {project-root}
```

`{output_file}` is an unbound runtime variable — not the resolved scalar. Stage 4 also saves the document without referencing `{workflow.output_dir}`. Any team override of `output_dir` is silently ignored, making the field cargo-weight in the contract.

**Fix:** Replace `{output_file}` with a derived expression using `{workflow.output_dir}`. The SKILL.md Stage 3 and Stage 4 must both read `{workflow.output_dir}` to construct the output path. One approach: define the resolved output path as `{workflow.output_dir}/D-03-{project_name}.md` and reference it consistently.

**Secondary:** The field name `output_dir` deviates from the BMad convention of `<purpose>_output_path`. Rename to `glossary_output_path` and point it at the full filename pattern (e.g., `{project-root}/_hbc_output/plan/D-03.md`) rather than a directory. This makes the override unambiguous and matches the principles file's naming pattern.

---

### [LOW-ABUSE] `output_dir` naming does not follow `*_output_path` convention

**Location:** `customize.toml` line 23  
**Detail:** BMad principles specify `<purpose>_output_path` for writable destinations. `output_dir` is opaque (is it the file path or the containing directory?) and breaks the established pattern. This is a secondary consequence of the issue above; fixing the wiring also fixes the name.

---

## Opportunity Findings

### [MEDIUM-OPPORTUNITY] Scanner script hardcoded — no customize.toml scalar

**Location:** `SKILL.md` Stage 1 line 36  
**Detail:** The validation script is correctly exposed as `{workflow.validation_script}` — a team can supply a custom validator with the same CLI interface. The source-scan script is not given the same treatment:

```
python3 scripts/scan-glossary-sources.py --project-root {project-root}
```

This path is hardcoded. A team with a different project layout or a richer term-extraction pipeline cannot swap the scanner without forking the skill. The pattern is already established by `validation_script`; adding `scan_script` follows the same logic.

**Proposed scalar:**
```toml
# Source scan script. Override to use a custom scanner with the same CLI interface.
scan_script = "scripts/scan-glossary-sources.py"
```

SKILL.md Stage 1 would then read:
```
python3 {workflow.scan_script} --project-root {project-root}
```

Severity is medium, not high, because the scanner is not expected to vary as often as the validator, and the fallback (no scanner) is handled implicitly. Still, consistency with `validation_script` is worth the one-line change.

---

### [LOW-OPPORTUNITY] No `on_complete` hook for downstream orchestration

**Location:** `SKILL.md` Stage 4 / `customize.toml`  
**Detail:** Stage 4 suggests next steps in prose ("Recommended: create D-06..."). For interactive use this is fine. For headless orchestrators driving a multi-skill pipeline, there is no hook scalar to inject a post-completion command.

The BMad convention `on_complete` would let a module-level orchestrator auto-chain to `hbc-phase-gate` or another skill without baking that coupling into `hbc-create-glossary`'s prose.

**Proposed scalar:**
```toml
# Shell command to run after D-03 is saved. Empty = no hook.
on_complete = ""
```

This is low priority — the headless contract already returns `output_path` and `decision_log`, which an orchestrator can use to chain. The hook would be additive convenience, not a blocking gap.

---

## What Is Working Well

- `template_path` and `validation_script` are correctly wired — SKILL.md reads `{workflow.template_path}` and `{workflow.validation_script}` at the points of use.
- `persistent_facts` ships the BMad default glob (`file:{project-root}/**/project-context.md`). For a skill that extracts terms from project context, this is exactly right.
- No boolean toggles. No identity or communication-style fields in `[workflow]`. No arrays-of-tables without keys. The surface respects its scope.
- Scalar comments in `customize.toml` are present and clear, explaining when and why each field would be overridden.
- The headless contract is documented in `references/headless-contract.md` and the return schema is specific. `status: blocked` includes a `reason` field and still returns `decision_log`, consistent with BMad headless discipline.

---

## Overall Assessment

**Verdict: Mostly right — one real wiring bug.**

The surface is appropriately lean for a single-document generation skill. The `output_dir` field is broken at the wiring level: it is declared and commented but SKILL.md never reads it, so no override can take effect. This is the only issue that requires a fix before the skill can be considered correct. The remaining findings are advisory improvements.

---

## Top 3 Insights

1. **`output_dir` override silently no-ops.** `customize.toml` promises teams can redirect the output directory, but SKILL.md uses an unbound `{output_file}` variable instead of `{workflow.output_dir}`. Fix the wiring and rename to `glossary_output_path` pointing at the full file path pattern, not a directory.

2. **Scanner script is the odd one out.** `validation_script` is customizable; `scan-glossary-sources.py` is not, despite being equally swappable. Adding `scan_script` to customize.toml costs one line and closes an inconsistency the principles file's pattern already anticipates.

3. **Surface discipline is otherwise sound.** Three scalars, no booleans, no identity fields, sensible comments, and the BMad default persistent-facts glob in place. The shape is right; the wiring on one field needs repair.
