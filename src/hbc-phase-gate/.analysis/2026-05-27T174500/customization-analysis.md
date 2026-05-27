# Customization Surface Analysis — hbc-phase-gate

**Scan date:** 2026-05-27  
**Skill:** `src/hbc-phase-gate`  
**Scanner:** quality-scan-customization

---

## Customization Posture

**Opted in.** `customize.toml` is present and actively wired. Surface includes:

- `phase_1_checklist` through `phase_4_checklist` — four `*_template`-equivalent scalars pointing to per-phase gate checklists in `assets/`.
- `gate_output_path` — a writable output destination.
- `on_complete` — a hook scalar (empty by default).
- `persistent_facts` — populated with the BMad default glob.
- `activation_steps_prepend` / `activation_steps_append` — always-present arrays (empty by default).

SKILL.md references every scalar correctly via `{workflow.phase_N_checklist}`, `{workflow.gate_output_path}`, and `{workflow.on_complete}`. No hardcoded path conflicts with a declared scalar.

**Surface size:** Moderate. Six meaningful exposed fields (four checklist paths + output path + hook). Well-proportioned for a validation workflow of this scope.

---

## Opportunity Findings

### O-1 · Medium-opportunity — `gate-report-template.md` is not a customizable scalar

**Location:** `assets/gate-report-template.md` is referenced by name in SKILL.md (`assets/gate-report-template.md`) but is not exposed as a scalar in `customize.toml`.

**Why it matters:** Teams that need branded or extended report structure (e.g., adding a risk column, a sign-off block, or conforming to a corporate template) currently have no override path short of forking the skill. The pattern is exactly what `*_template` scalars are designed for.

**Proposed scalar:**
```toml
# Report template for generated gate reports.
# Default ships with the skill. Override to customise layout or add org-specific sections.
gate_report_template = "assets/gate-report-template.md"
```

SKILL.md line 100 would change from the bare path to `{workflow.gate_report_template}`.

---

### O-2 · Low-opportunity — No `on_complete` documentation on *when* to set it

**Location:** `customize.toml` line `on_complete = ""`

The scalar exists and is correct, but there is no comment explaining what values are valid or what the expected invocation form is. SKILL.md does explain the semantics (line 117: "treat it as a skill invocation command, e.g. `"invoke hbc-traceability"`"), so the information exists — it is just not surfaced at the customization layer where a team author would look first.

**Proposed fix:** Add a comment above `on_complete`:
```toml
# Post-gate hook. Set to a skill invocation string (e.g. "invoke hbc-traceability")
# to trigger automatically after a gate completes. Leave empty to skip.
on_complete = ""
```

Low severity because the behavior is documented in SKILL.md and the field name is reasonably self-describing.

---

### O-3 · Low-opportunity — `persistent_facts` comment is absent

**Location:** `customize.toml` lines 17-19

The BMad default glob is present and correct, but there is no comment indicating what additional facts would be useful to append (e.g., `_hbc_output/traceability/matrix.md` or a project-level quality policy). Other scalars in the file have explanatory comments; `persistent_facts` has none. Users appending to this array in their team override file have no guidance.

**Proposed fix:**
```toml
# Foundational context loaded on activation. Append project-specific artifacts
# (e.g. "file:{project-root}/_hbc_output/traceability/matrix.md") in your team override.
persistent_facts = [
  "file:{project-root}/**/project-context.md",
]
```

---

## Abuse Findings

### A-1 · No abuse found — Boolean toggles

No boolean toggles present. `gate_mode` is correctly excluded from `customize.toml` with an explicit rationale comment (it is a project-level policy from `_bmad/config.yaml`). This is a model decision: the comment documents *why* the field was deliberately omitted rather than silently missing. No action needed.

---

### A-2 · No abuse found — Identity / communication-style in `[workflow]`

The `[workflow]` block contains only paths, a hook, and the always-present arrays. No persona, tone, or communication-style fields are present.

---

### A-3 · No abuse found — Hook count

One `on_complete` hook. Well below the four-hook threshold where internals start leaking into the override surface.

---

### A-4 · No abuse found — Array keying

No arrays-of-tables in `customize.toml`. The checklist entries are scalars (one per phase), not table arrays, so merge-by-key is not applicable and no keylessness problem exists.

---

### A-5 · No abuse found — Scalar/SKILL.md drift

All four `phase_N_checklist` scalars and `gate_output_path` are referenced via `{workflow.*}` in SKILL.md. The `gate_report_template` (O-1) is the only case where a path is hardcoded without a corresponding scalar — but since no scalar is declared, this is an opportunity (missing exposure), not a silent no-op conflict.

---

## Overall Assessment

**About right**, leaning slightly thin on one template path.

The surface is clean and principled. The decision to exclude `gate_mode` from `customize.toml` and route it through project-level config is well-reasoned and explicitly documented — rare discipline worth noting. The four per-phase checklist scalars are the highest-value exposure in the skill: they let teams substitute domain-specific quality criteria without forking. The `gate_output_path` scalar is useful for multi-project monorepos. The `on_complete` hook rounds out the automation story.

The only genuine gap is the `gate_report_template` (O-1): it is the one user-visible output artifact whose structure cannot be overridden without forking. Given the skill's role in formal phase-transition governance, report layout is a plausible customization target for enterprise or regulated environments.

---

## Top Insights

1. **The checklist-as-scalar pattern is the right call and should be preserved.** Four separate scalars (not a bundled array) let teams override individual phase checklists independently — exactly the granularity a mixed-maturity organization needs (e.g., tightening phase 2 without touching phases 1, 3, 4).

2. **`gate_report_template` is the only uncovered template path.** The skill loads one template file at runtime (`assets/gate-report-template.md`) that is not exposed in `customize.toml`. Lifting it as a scalar closes the last fork-forcing gap in the output pipeline.

3. **The `gate_mode` exclusion is a design-quality signal worth copying.** Documenting *why* a field was intentionally left out of the customization surface — as opposed to omitting it silently — is a pattern other HBC skills should adopt. It prevents future contributors from "helpfully" adding the field back without understanding the policy-vs-skill boundary.
