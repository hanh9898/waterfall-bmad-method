# Customization Surface Analysis — hbc-phase-gate

**Date:** 2026-05-26  
**Skill:** `hbc-phase-gate`  
**Classifier:** Simple workflow, opted in

---

## Customization Posture

The skill **has opted into `customize.toml`** with a focused, well-structured surface. Six scalars, one array for persistent facts, activation hooks. The surface is proportionate to the workflow's scope: a phase-gate evaluation engine with four phase checklists that need per-team overrides.

### Surface Shape

| Surface | Type | Count | Status |
|---------|------|-------|--------|
| Scalars | `*_checklist`, `*_output_path`, `on_complete` | 6 | healthy |
| Arrays | `persistent_facts`, `activation_steps_*` | 3 | healthy |
| Arrays-of-tables | — | 0 | N/A |
| Wired in SKILL.md | Yes, via `{workflow.*}` references | All | ✓ |

---

## Opportunity Findings

### 1. HIGH: `on_complete` hook is exposed but unused (comment suggests intent)

**Location:** `customize.toml` line 32; comment in line 72 of SKILL.md  
**Issue:** The hook is declared with a comment about gate reports, but the workflow doesn't execute the hook. The field is a placeholder.

**Finding:** If this hook is intended for post-gate actions (e.g., "trigger traceability update", "notify stakeholders", "post to project dashboard"), the wiring is incomplete. Either:
- Remove the field entirely (low-opportunity if no one overrides it)
- Wire the execution step in SKILL.md at the end (high-opportunity if teams want automation)

**Recommendation:** Clarify intent in decision log. If future use is likely, add execution in "On Complete" section and document the contract (what args/env are available to the hook script).

---

### 2. MEDIUM: `gate_mode` is read from config, not customizable in `customize.toml`

**Location:** SKILL.md line 43; no `customize.toml` scalar  
**Issue:** The gate-evaluation logic references `{gate_mode}` (strict vs lenient), but it's sourced from `_bmad/config.yaml` → hbc section. This prevents per-skill or per-team overrides of gate mode without rewriting config.

**Analysis:** The decision log justifies this as "a project-level decision, not per-gate choice" (Session 2026-05-26, decision 5). That's sound if `gate_mode` is truly org-wide. But if different phases or project streams want different strictness, the current design locks them.

**Recommendation:** Document in the `customize.toml` comment why `gate_mode` is NOT exposed here. If this constraint should loosen, add `gate_mode = "strict"` as a scalar override (wired in SKILL.md step 4). Low risk; adds flexibility.

---

### 3. MEDIUM: Four hardcoded phase checklist paths; naming could be tighter

**Location:** `customize.toml` lines 24–27  
**Issue:** The scalars `phase_1_checklist`, `phase_2_checklist`, etc. follow an obvious pattern but could benefit from a clarifying comment.

**Current state:**
```toml
phase_1_checklist = "assets/phase-1-gate-checklist.md"
phase_2_checklist = "assets/phase-2-gate-checklist.md"
phase_3_checklist = "assets/phase-3-gate-checklist.md"
phase_4_checklist = "assets/phase-4-gate-checklist.md"
```

**Recommendation:** Add a comment clarifying that these resolve relative to `{skill-root}` and that phase skills can override by declaring the same scalar in their own `{project-root}/_bmad/custom/hbc-phase-gate.toml`. Example:

```toml
# Gate checklists per phase. Phase skills override by setting these in
# {project-root}/_bmad/custom/hbc-phase-gate.toml (team or user level).
# Paths resolve relative to {skill-root} or {project-root} (use bare paths).
```

This is already documented in the SKILL.md comment (line 22–23) but the `customize.toml` comment is silent. Lowering the friction on override discovery is low-cost.

---

### 4. LOW: `persistent_facts` default glob is appropriate; no expansion needed

**Location:** `customize.toml` line 17–19  
**Status:** Healthy.

The skill ships the BMad default (`file:{project-root}/**/project-context.md`) which is low-risk, high-value. Phase gate evaluation will benefit from project context. No action needed.

---

### 5. LOW: `gate_output_path` is well-parameterized

**Location:** `customize.toml` line 30  
**Status:** Healthy.

The path is project-rooted and descriptive. Gate reports go to `_hbc_output/gates/phase-{N}-gate.md`, which is discoverable and follows HBC naming. Team overrides are straightforward. No action needed.

---

## Abuse Findings

### None detected.

- No boolean toggle permutation forest (gate_mode is intentionally centralized in config)
- No identity/communication-style fields in `[workflow]` (this is a tool, not an agent)
- No arrays-of-tables without key fields (no tables at all)
- No opaque scalar names
- No hardcoded paths next to customize.toml scalars — SKILL.md correctly uses `{workflow.phase_N_checklist}`, not bare paths
- Scalars have inline comments explaining their purpose
- No unused or shadowing declarations

---

## Overall Assessment

**Customization surface: ABOUT RIGHT**

The skill has a **small, focused surface** that exposes exactly what teams need to override (phase checklists, output location) and keeps org-level policy (gate mode) in the config layer. The surface isn't trying to do too much, and the wiring is sound.

### Strengths

1. **Clear field semantics** — Each scalar name directly signals its purpose (`phase_N_checklist`, `gate_output_path`, `on_complete`).
2. **Proper path resolution** — All scalars reference the right layer (`{skill-root}` for checklists, `{project-root}` for output).
3. **Merge-ready arrays** — `activation_steps_*` and `persistent_facts` follow the append pattern; teams can prepend/append custom steps without forking the entire workflow.
4. **No premature generality** — The surface doesn't expose every possible variation (e.g., report format, checker strictness per item); gate reports are templated once and apply to all phases. Lean is good here.

### Opportunities (not blockers)

1. **`on_complete` clarity** — Is this hook meant to fire? Wire it or document why it's deferred.
2. **`gate_mode` exposure** — Consider whether org-wide policy should allow project-level override.
3. **Checklist path comments** — Brief hint in `customize.toml` about how phase skills override would lower friction.

---

## Top 3 Insights

1. **`on_complete` hook is dangling.** It's declared but not wired in the workflow. If automation (traceability update, team notification) is part of the design, add the execution step and document the contract. If not, remove the field to reduce surface confusion.

2. **`gate_mode` as org-wide policy is reasonable but document the choice.** The decision log states gate mode is "project-level", but it's actually config-level. Teams can't override it per skill or per invocation. That's fine if strict evaluation is non-negotiable; add a line to the `customize.toml` comment explaining why this field is excluded.

3. **Phase skill override mechanism is underdiscoverable.** The decision log (line 16) mentions phase skills can override via `{project-root}/_bmad/custom/hbc-phase-gate.toml`, but this is only hinted at in SKILL.md comments. A one-sentence note in the `customize.toml` field comment would save teams hunting through docs. "Phase skills can override by setting the same scalar in their own `_bmad/custom/hbc-phase-gate.toml`."

---

## Recommendation Summary

| Finding | Action | Priority |
|---------|--------|----------|
| `on_complete` hook unused | Clarify intent in decision log; wire execution or remove | Medium |
| `gate_mode` not customizable | Document why; consider exposing if teams need flexibility | Low |
| Phase skill override underdiscoverable | Add clarifying comment in `customize.toml` field | Low |
| Persistent facts, output path, checklists | No changes needed | — |

**Overall:** The customization surface is lean, well-named, and correctly wired. Two low-friction documentation improvements would finish it. No refactoring needed.
