# Customization Analysis — hbc-traceability

**Scan date:** 2026-05-27
**Scanner:** customization-surface

---

## Customization Posture

**Opted in:** Yes. `customize.toml` is present, valid, and actively wired into SKILL.md.

**Surface size:** 6 fields — 3 standard (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`) + 3 workflow-specific (`matrix_path`, `matrix_template`, `source_code_path`). Lean and well-shaped.

**Wiring status:** SKILL.md reads `{workflow.matrix_path}` (Initialize step 2, Update sections), `{workflow.matrix_template}` (Initialize step 2), and `{workflow.source_code_path}` (Update Phase 3). All three declared scalars are consumed. No declared-but-ignored scalars detected.

**Resolver step:** Present in the On Activation section — "Resolve customization, load persistent facts and config per standard BMad activation." Correct invocation, though deliberately terse (intentional per BMad conventions).

**Delta from prior scan (2026-05-26):** OPP-1 from the prior run — `matrix_template` not exposed — has been resolved: `customize.toml` now declares `matrix_template` with a comment, and SKILL.md Initialize step 2 reads `{workflow.matrix_template}`. The `on_complete` hook field referenced in the prior scan's posture summary is not present in the current `customize.toml`; that appears to have been an inaccurate prior-scan artifact rather than a regression.

---

## Opportunity Findings

### OPP-1: `on_complete` hook absent — workflow produces artifacts and stops (low-opportunity)

**Location:** customize.toml — no `on_complete` field.

**Issue:** The Initialize and Update capabilities write artifacts to `{workflow.matrix_path}` and `.trace-decisions.md`, then stop. A team that wants to trigger a downstream skill (e.g. `hbc-phase-gate`, a notification hook, or a CI pipeline step) after a traceability update has no hook point without forking the skill.

**Proposed fix:**
```toml
# Optional: command or skill to invoke after a capability completes.
# Leave empty to take no post-run action.
on_complete = ""
```
Update SKILL.md Update and Initialize completion steps to check `{workflow.on_complete}` and invoke it if non-empty.

**Assessment:** Low-opportunity. The traceability matrix is a supporting artifact, not a gate; teams that need post-run hooks usually wire them at the phase-gate level. Flag but do not block on this.

---

### OPP-2: D-02 source glob pattern hardcoded in script invocation (low-opportunity)

**Location:** SKILL.md Initialize section, script invocation — `{project-root}/_hbc_output/plan/D-02-*` is baked in.

**Issue:** Teams with non-standard HBC output paths (e.g. renamed document codes or flat layouts) must fork the skill to change this pattern.

**Assessment:** Low-opportunity. The `_hbc_output/{phase}/{doc-code}-*` convention is shared across all HBC skills — it is module-level infrastructure, not skill-level configuration. Lifting this scalar here would create an orphaned knob that users could break without understanding cross-skill consequences. The correct resolution, if ever needed, is a module-wide path resolver.

---

### OPP-3: Regex ID patterns hardcoded in script invocations (low-opportunity)

**Location:** SKILL.md Initialize and Update Phase 2 script invocations — `REQ-\d{3,}`, `TC-\d{3,}` baked in.

**Issue:** Teams using alternative ID conventions (e.g. `FR-xxx`, `UC-xxx`) must modify script invocations directly.

**Assessment:** Low-opportunity. ID conventions are part of the HBC module design contract. Exposing per-skill regex scalars would fragment the convention surface. If ID formats need to vary, the right fix is a centralized HBC convention config referenced by all skills.

---

### OPP-4: Gate report glob hardcoded (low-opportunity)

**Location:** SKILL.md Update Phase 4 — `{project-root}/_hbc_output/gates/phase-*-gate.md` baked in.

**Assessment:** Same as OPP-2. Module-level convention, wrong level for per-skill scalar.

---

## Abuse Findings

### No abuse findings detected.

The surface is clean:

- **No boolean toggles.** Capability routing is handled by workflow logic, not toggle flags in customize.toml.
- **No identity or agent-shape fields.** The `[workflow]` section contains only path scalars and standard arrays — no communication style, principles, or persona content.
- **No excessive hooks.** Zero `on_<event>` fields currently. Minimal hook surface is appropriate for a utility skill.
- **No unkeyed arrays of tables.** No `[[workflow.X]]` table arrays exist; the resolver merge concern does not apply.
- **No opaque scalar names.** `matrix_path`, `matrix_template`, `source_code_path` — all follow the `<purpose>_path` / `<purpose>_template` conventions.
- **All scalars have comments.** Each field has a brief comment explaining when and why to override, including an illustrative example for `matrix_template` (column customization).
- **No declared-but-ignored scalars.** All three workflow-specific fields are consumed via `{workflow.X}` references in SKILL.md. Override silently no-ops are not possible for any declared field.

---

## Overall Assessment

**About right** — the surface is appropriately thin for a utility skill.

The three workflow-specific scalars cover the artifact destination (`matrix_path`), the schema template (`matrix_template`), and the one runtime-variable input (`source_code_path`). Together they cover every point where a team legitimately customizes the skill's behavior. The standard trio of prepend/append/persistent_facts is present.

All remaining hardcoded values (D-02 paths, regex patterns, gate paths) are HBC module conventions. Lifting them here would create configuration knobs that users can tweak without understanding the cross-skill ripple effects. The author correctly left them at the invocation level.

The one genuine missing piece is `on_complete` (OPP-1), but it is low-priority: the matrix is a supporting artifact consumed by gate checks, not a pipeline trigger.

---

## Top Insights

1. **OPP-1 from the prior scan was fixed correctly.** `matrix_template` is now declared in customize.toml with a clear comment and consumed in SKILL.md via `{workflow.matrix_template}`. The fix is complete — no stale hardcode remains.

2. **The absence of `on_complete` is a low-risk gap, not an oversight.** A traceability update naturally ends with "run `hbc-phase-gate` next" — a human-facing suggestion, not a machine hook. The current design is appropriate; adding `on_complete` is an optimization for advanced automation pipelines, not a day-one need.

3. **The surface correctly avoids the permutation forest.** By keeping all ID patterns, phase paths, and document codes as hardcoded invocation arguments (module conventions) rather than customize.toml scalars, the skill stays predictable. Every HBC skill that consumes D-02, D-27, or gate artifacts uses the same paths — a per-skill override surface would let one skill drift from the convention silently.
