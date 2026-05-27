# Customization Analysis — hbc-create-requirements

**Scanner:** customization-surface  
**Skill:** `src/hbc-create-requirements`  
**Date:** 2026-05-27T10:30:00

---

## Customization Posture

**Opted in:** Yes. `customize.toml` is present and well-structured.

**Surface size:** 6 fields total under `[workflow]`:
- 3 standard arrays: `activation_steps_prepend`, `activation_steps_append`, `persistent_facts`
- 3 workflow-specific scalars: `template_path`, `output_path`, `vague_terms`

**Shape:** Lean and focused. Every scalar maps to a clear behavioral dimension. No boolean toggles, no identity fields, no hook overload.

---

## Opportunity Findings

### 1. Missing `on_complete` hook scalar — low-opportunity

**Location:** `customize.toml` (absent)  
**Observation:** Stage 5 (Save and Handoff) suggests hardcoded next-step recommendations ("create D-03 Glossary, then D-06 Business Flow"). Organizations with different document pipelines or different downstream skills would benefit from an `on_complete` hook that lets them inject a custom handoff message or trigger.  
**Proposed scalar:** `on_complete = ""` (string; empty = use default suggestion; non-empty = execute as post-save step)  
**Severity:** Low-opportunity. The current next-step suggestion is guidance, not a contractual trigger. Most teams will not override this.

### 2. Validation script invocation uses bare `scripts/` path — medium-opportunity

**Location:** SKILL.md Stage 4, line 74  
**Observation:** The validation command is:
```
python3 scripts/validate-requirements.py {output_file} --project-root {project-root}
```
The script path `scripts/validate-requirements.py` is hardcoded relative to the skill root. This is correct per conventions (bare paths resolve from skill root), but the script path is not lifted to `customize.toml`. If an organization wants to swap in a stricter validator (e.g., one that checks against a corporate requirements taxonomy), they currently cannot override the script path without forking.  
**Proposed scalar:** `validation_script = "scripts/validate-requirements.py"` with a comment: "Override to use a custom validation script. Must accept the same CLI interface."  
**Severity:** Medium-opportunity. The validation script is a core differentiator of this skill; making it swappable gives teams real configurability without forking. However, the script interface contract would need documenting.

### 3. Next-step skill suggestions are hardcoded in SKILL.md — low-opportunity

**Location:** SKILL.md Stage 5, line 93  
**Observation:** The handoff names specific skills (`hbc-create-glossary`, `hbc-create-business-flow-diagram`, `hbc-phase-gate`). If the module prefix or skill names change, this text becomes stale. This is not a customization issue per se (it is guidance, not a parameter), but it is a maintenance fragility.  
**Proposed fix:** Not a scalar candidate. Acknowledge as a documentation coupling. If the skill set stabilizes, no action needed; if it is volatile, consider a `next_steps_hint` scalar.  
**Severity:** Low-opportunity.

### 4. `persistent_facts` ships the BMad default glob — no action needed

**Location:** `customize.toml` line 16-18  
**Observation:** `persistent_facts = ["file:{project-root}/**/project-context.md"]` is present. This is the recommended BMad convention. No issue.

---

## Abuse Findings

### 1. `vague_terms` is a comma-separated string, not an array — medium-abuse

**Location:** `customize.toml` line 28  
**Observation:** The field is declared as:
```toml
vague_terms = "fast,easy,user-friendly,simple,good,nice,efficient,appropriate,adequate,reasonable"
```
TOML natively supports arrays. A comma-separated string forces both the script and any override author to parse/unparse a comma convention. The script (`validate-requirements.py` line 45) manually splits on commas. The `--vague-terms` CLI arg also takes a comma string, which is fine for CLI ergonomics, but the TOML source should be a proper array.  
**Fix:** Change to `vague_terms = ["fast", "easy", "user-friendly", ...]`. Update `load_vague_terms()` in the script to read a TOML array (or fall back to comma-split for the CLI arg). This aligns with TOML idiom and makes overrides less error-prone.  
**Severity:** Medium-abuse. The current encoding works but is fragile and non-idiomatic. Override authors may introduce whitespace or quoting errors in a comma string.

### 2. `output_path` points to a directory, not a file — low-abuse (naming clarity)

**Location:** `customize.toml` line 24  
**Observation:** `output_path = "{project-root}/_hbc_output/plan"` is a directory path. SKILL.md Stage 1 checks for "existing D-02" at this path, but the actual filename presumably gets constructed at runtime (e.g., `D-02-{project_name}.md`). The scalar name `output_path` is slightly ambiguous — it could mean a file path or a directory path.  
**Fix:** Either rename to `output_dir` for clarity, or document in the comment that this is a directory and the filename is derived. Minor naming hygiene.  
**Severity:** Low-abuse.

### 3. No abuse from boolean toggles — clean

**Observation:** Zero boolean toggles in `customize.toml`. The skill made clear design decisions (5-stage workflow, deterministic validation, headless mode via CLI flag) rather than exposing shape-changing booleans. This is correct.

### 4. No identity/persona fields in `[workflow]` — clean

**Observation:** No communication-style, principles, or identity fields. The skill correctly delegates language to `{communication_language}` and `{document_output_language}` which are resolved from the broader BMad config, not declared here.

### 5. No hook overload — clean

**Observation:** Zero `on_<event>` hooks. The workflow internals stay internal. If the `on_complete` opportunity (Finding 1) is adopted, it would be the only hook — well within the 3-hook safe zone.

---

## SKILL.md Wiring Check

| customize.toml scalar | SKILL.md reference | Wired correctly? |
|---|---|---|
| `template_path` | `{workflow.template_path}` (Stage 3, line 57) | Yes |
| `output_path` | `{workflow.output_path}` (Stage 1, line 33) | Yes |
| `vague_terms` | Not referenced via `{workflow.vague_terms}` in SKILL.md; instead passed to script via `load_vague_terms()` which reads the override TOML directly | Partial — see note |

**Note on `vague_terms` wiring:** The script reads the override TOML file directly (`_bmad/custom/hbc-create-requirements.toml`) at line 37-48 of `validate-requirements.py`. This bypasses the BMad resolver's merge chain. If a user sets `vague_terms` in `.user.toml` (personal override), the script will not pick it up because it only checks the team-level override. The CLI `--vague-terms` arg exists as a workaround, but the three-layer merge (base -> team -> user) does not flow through to the script.

**Severity:** Medium. The script should either (a) accept the resolved value from SKILL.md via `{workflow.vague_terms}` passed as a CLI argument, or (b) replicate the full merge chain. Option (a) is simpler and more correct.

---

## Overall Assessment

**Verdict: About right, with two medium-severity items to address.**

The customization surface is well-shaped: three meaningful scalars (`template_path`, `output_path`, `vague_terms`) that cover the primary variance dimensions (what template, where to write, what counts as vague). No bloat, no identity fields, no toggle forest.

Two items need attention:
1. `vague_terms` should be a TOML array, not a comma-separated string.
2. `vague_terms` merge chain is incomplete — the validation script reads the team override directly instead of receiving the BMad-resolved value, which means personal (`.user.toml`) overrides silently fail for this field.

Everything else is clean.

---

## Top 3 Insights

1. **The `vague_terms` merge chain is broken for personal overrides.** The validation script bypasses the BMad resolver by reading `_bmad/custom/hbc-create-requirements.toml` directly. Personal `.user.toml` overrides are silently ignored. Fix: pass the resolved value from SKILL.md as a `--vague-terms` CLI argument to the script, making the resolver the single source of truth.

2. **`vague_terms` should be a native TOML array.** Comma-separated strings in TOML are a code smell. TOML has arrays; use them. This also makes the append-merge semantics clearer when overrides add domain-specific terms.

3. **The surface is appropriately lean for a Phase 1 skill.** Three workflow-specific scalars covering template, output, and validation vocabulary is the right level of configurability. Resist the urge to add hooks or toggles unless real user demand surfaces.
