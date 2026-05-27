# Customization Surface Analysis — hbc-agent-ba

**Scan date:** 2026-05-27
**Skill type:** Agent
**Scanner:** L3 Customization Surface

---

## Customization Posture

The skill is fully opted in. `customize.toml` declares a canonical `[agent]` block with all required always-present arrays (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`) and the full complement of agent-shape scalars (`icon`, `role`, `identity`, `communication_style`, `principles`). The menu uses `[[agent.menu]]` tables keyed by `code`, satisfying the key-merge requirement. SKILL.md consumes every agent-block field via `{agent.*}` references — no hardcoded values shadow declared scalars.

Surface size: **medium-lean**. 5 menu items, 3 principles, 1 persistent-facts entry, no template scalars, no `on_<event>` hook scalars. Shape is nearly identical to the `bmad-agent-analyst` reference pattern — a healthy signal.

---

## Opportunity Findings

### LOW-OPPORTUNITY — No `on_phase1_gate_complete` hook scalar

The Phase 1 gate (`[PG]`) is the natural terminal event for the agent's lifecycle. Teams integrating with CI or a project dashboard have no way to append a post-gate action (e.g., notify a pipeline, write a summary to a project log) without forking the skill. This is genuinely low-priority for an agent skill — agents cycle through menus rather than terminate cleanly — but worth naming if HBC's tooling ever adds gate-completion hooks.

**Proposed scalar (optional, not urgent):**
```toml
on_phase1_gate_complete = ""   # shell command or empty string; runs when [PG] reports complete
```

### LOW-OPPORTUNITY — `persistent_facts` has no literal-sentence example comment

The single entry `"file:{project-root}/**/project-context.md"` is correct and follows BMad convention. However, teams who want to inject an org-standards statement (e.g., "Our org requires JIRA traceability for all requirements") must read the schema docs to learn the literal-sentence form. A one-line comment costs nothing.

**Fix:** Add alongside the existing entry:
```toml
# Literal example: "Our org requires JIRA traceability for all requirements."
persistent_facts = [
  "file:{project-root}/**/project-context.md",
]
```

### LOW-OPPORTUNITY — No `output_path` scalar paired with `{agent.output_path}` consumption

`customize.toml` already declares `output_path = "{project-root}/_hbc_output/plan"` and SKILL.md correctly reads it as `{agent.output_path}`. This pairing is correct. However, the scalar carries no inline comment explaining when a team would override it (e.g., a project with a different artifact root). Without the comment, the scalar is present but opaque.

**Fix:** Add a one-line comment:
```toml
output_path = "{project-root}/_hbc_output/plan"   # Override if your project uses a different Phase 1 artifact root.
```

---

## Abuse Findings

### MEDIUM-ABUSE — `name` scalar present but intentionally empty; contract ambiguity for override authors

`name = ""` appears in the `[agent]` block with a comment marking it "Non-configurable." The intent (HBC module agents derive display identity from `title`, not `name`) is correct, but the comment leaves open a path for a confused override author to write `name = "HBC-BA"` — an override that will resolve silently and produce no visible effect (the resolver accepts it, but no consumer reads it for display). The current comment in customize.toml reads:

> Non-configurable. Name is intentionally blank for this module agent; the title field is the display identity. Fork the skill to change it.

This is already the strengthened version recommended in the previous analysis run. No further change needed — this finding is **resolved** since the prior scan.

### LOW-ABUSE — Scalar override behavior underdocumented for agent-shape fields

The merge-rules block comment correctly covers arrays (`activation_steps_*`, `persistent_facts`, `principles`): it states overrides append. It does not state that `icon`, `role`, `identity`, and `communication_style` are scalars whose override **replaces entirely**. A team adding one sentence to `communication_style` would silently drop the entire default voice.

The existing comment reads:
```toml
#   scalars (icon, role, identity, communication_style): override replaces entirely
```

This is already present in the current file. **Finding is resolved** — the scalar behavior is documented.

> **Net abuse status:** Both abuse findings from the previous analysis run are already addressed in the current `customize.toml`. The surface has no active abuse conditions.

---

## Structural Correctness

| Check | Result | Notes |
|---|---|---|
| Always-present arrays present | Pass | `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` all declared |
| Menu tables keyed by `code` | Pass | All 5 items carry `code`; resolver can replace individual items |
| Mixed `code`/`id` keying | Pass | Consistent `code` only throughout |
| Boolean toggles | Pass | None present |
| Identity/persona in `[workflow]` instead of `[agent]` | N/A | This is an agent skill; persona correctly lives in `[agent]` |
| `customize.toml` scalar vs. SKILL.md hardcode mismatch | Pass | SKILL.md reads `{agent.*}` throughout; no hardcoded duplicates found |
| `on_<event>` hook count (abuse threshold: 4+) | Pass | Zero hooks declared |
| `output_path` scalar declared and consumed | Pass | Declared in `customize.toml`, consumed as `{agent.output_path}` in SKILL.md |
| Scalars with no override comment | Minor | `output_path` scalar has no "when to override" comment |

---

## Path Standards Note (from prepass)

The path-standards prepass flagged 3 HIGH findings, but all 3 are in `.analysis/` output files and `references/.decision-log.md` — not in SKILL.md or customize.toml. These are scanner artifacts and decision-log prose (mentions of `_bmad/scripts/` without `{project-root}` prefix), not actionable path errors in the skill's operational files. SKILL.md itself is clean: all `_bmad` references carry the `{project-root}` prefix.

---

## Overall Assessment

**About right — with two minor documentation gaps that are worth closing.**

The surface is correctly structured and genuinely minimal. The agent shape maps precisely to the BMad agent customization contract. Key-merge semantics are correct on all 5 menu items. The `output_path` scalar is properly wired end-to-end. No permutation-forest risk, no identity-in-workflow confusion, no broken key-merge cases.

The two issues from the previous scan (`name` comment clarity, scalar override documentation) appear to have been addressed in the current file. What remains is documentation-level only: the `persistent_facts` literal-sentence example and an `output_path` "when to override" comment.

---

## Top 3 Insights

1. **Key-merge is correctly wired and stable.** All `[[agent.menu]]` items carry `code` keys. Teams can replace a specific menu item (e.g., swap `[BF]` for a custom diagram builder) without touching the others. This is the highest-consequence correctness property of the surface, and it is right.

2. **The `output_path` scalar is the most valuable override point the skill exposes, but it has no "when to override" guidance.** Projects with non-standard artifact roots will need this override, but the scalar is currently undocumented. One inline comment prevents confusion and removes the need to read SKILL.md to understand the field.

3. **`persistent_facts` is well-seeded but not extensible by example.** The BMad default glob is present and correct. Adding the literal-sentence comment example costs two lines and pays off every time a team wants to inject org-standards as persistent context (JIRA requirements, compliance policies, naming conventions) without reading the schema specification.
