# Customization Analysis — hbc-traceability

**Scan date:** 2026-05-26
**Scanner:** customization-surface

---

## Customization Posture

**Opted in:** Yes. `customize.toml` is present and well-structured.

**Surface size:** 6 fields — 3 standard (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`) + 3 workflow-specific (`matrix_path`, `source_code_path`, `on_complete`). Lean and intentional.

**Wiring status:** SKILL.md reads `{workflow.matrix_path}`, `{workflow.source_code_path}`, and `{workflow.on_complete}` — all declared scalars are consumed. No hardcoded-value / declared-scalar collision detected.

**Resolver step:** Present at Step 1 of On Activation, with correct fallback chain and merge rules stated.

---

## Opportunity Findings

### OPP-1: `matrix_template` scalar not exposed (medium-opportunity)

**Location:** SKILL.md Initialize section, line 89 — `assets/matrix-template.md` is hardcoded.

**Issue:** The template path is baked into the Initialize instruction. A team that wants different matrix columns (e.g. adding `priority` or `module` columns) or different header formatting must fork the skill.

**Proposed fix:** Add to customize.toml:
```toml
# Path to the matrix template used during initialization.
# Override to add custom columns or change the header format.
matrix_template = "assets/matrix-template.md"
```
Update SKILL.md Initialize section to reference `{workflow.matrix_template}`.

---

### OPP-2: D-02 source pattern hardcoded (low-opportunity)

**Location:** SKILL.md Initialize section, line 84 — `{project-root}/_hbc_output/plan/D-02-*` is baked in.

**Issue:** The glob pattern for finding D-02 requirement documents is hardcoded. Most HBC projects follow this convention, so the override audience is small. However, teams with non-standard output structures would need to fork.

**Assessment:** Low-opportunity because the HBC output path convention is load-bearing for the entire module system. Lifting this scalar adds surface area for a rare use case. Flag but do not recommend action unless multiple teams request it.

---

### OPP-3: Regex patterns hardcoded in script invocations (low-opportunity)

**Location:** SKILL.md lines 84, 105-106 — regex patterns like `REQ-\d{3,}`, `TC-\d{3,}`, and the entity-name pattern are hardcoded in the script call arguments.

**Issue:** Teams using different ID conventions (e.g. `FR-xxx` instead of `REQ-xxx`) would need to modify every script invocation.

**Assessment:** Low-opportunity. The ID conventions are part of the HBC module design contract. Exposing them as scalars would create a permutation surface that complicates cross-skill interop. If ID formats ever vary, the right fix is a centralized convention config, not per-skill scalars.

---

### OPP-4: Gate report paths hardcoded (low-opportunity)

**Location:** SKILL.md line 114 — `{project-root}/_hbc_output/gates/phase-*-gate.md` is baked in.

**Assessment:** Same reasoning as OPP-2. HBC output path convention is shared infrastructure; lifting per-skill is the wrong level.

---

## Abuse Findings

### No abuse findings detected.

The surface is clean:

- **No boolean toggles.** The skill does not use toggle flags to change behavior — it uses capability routing instead.
- **No identity/agent-shape fields.** The `[workflow]` section contains only paths, arrays, and a hook — no communication style, principles, or persona fields.
- **No excessive hooks.** Single `on_complete` hook. Well within bounds.
- **No unkeyed arrays of tables.** No `[[workflow.X]]` sections exist.
- **No opaque scalar names.** All scalars follow the `<purpose>_path` / `<purpose>_template` / `on_<event>` conventions.
- **All scalars have comments.** Each field has an explanatory comment describing when and why to override.
- **No declared-but-ignored scalars.** Every customize.toml field is consumed by SKILL.md via `{workflow.X}` references.

---

## Overall Assessment

**About right** — leaning slightly thin.

The customization surface covers the primary artifact location (`matrix_path`), the one org-dependent input (`source_code_path`), and a completion hook (`on_complete`). The standard trio of prepend/append/persistent_facts is present. This is a well-shaped surface for a utility-style skill.

The one genuine lift candidate is the matrix template path (OPP-1). The remaining hardcoded values (D-02 paths, regex patterns, gate paths) are HBC module conventions that belong at the system level, not the skill customization level. Lifting them here would create orphaned knobs that users tweak without understanding the cross-skill consequences.

---

## Top Insights

1. **Template path is the one real lift.** `assets/matrix-template.md` defines the matrix schema (columns, header format). This is the most likely customization point — teams that add columns like `priority` or `module` to the matrix need a different template. Exposing it as `matrix_template` is low-risk and high-value.

2. **Hardcoded HBC paths are convention, not configuration.** The D-02, D-19, D-27, and gate paths follow the `_hbc_output/{phase}/{doc-code}-*` pattern shared across all HBC skills. These are not skill-level configuration — they are module-level infrastructure. If they ever need to change, the fix should be a module-wide path resolver, not per-skill scalars.

3. **The surface correctly avoids the permutation forest.** By keeping capability routing inside the skill logic (not as boolean toggles in customize.toml) and limiting the override surface to paths and a hook, the skill stays forkable without being fragile. The author made the right calls on what NOT to expose.
