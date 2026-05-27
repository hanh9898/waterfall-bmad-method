# Customization Surface Analysis — hbc-agent-ba

**Scan date:** 2026-05-27  
**Skill type:** Agent  
**Scanner:** L3 Customization Surface

---

## Customization Posture

The skill is fully opted in. `customize.toml` declares the canonical `[agent]` block with all required always-present arrays (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`) and the standard agent-shape scalars (`icon`, `role`, `identity`, `communication_style`, `principles`). The menu uses `[[agent.menu]]` tables keyed by `code`, which is correct for key-merge semantics.

Surface size: **medium-lean**. 5 menu items, 3 principles, 1 persistent fact, no hook scalars, no template scalars. Compared to the `bmad-agent-analyst` reference, the structure is nearly identical in shape — a healthy sign.

---

## Opportunity Findings

### LOW-OPPORTUNITY — No `on_complete` hook scalar

The agent does not expose an `on_complete` hook. The Phase 1 gate (`[PG]`) is the natural terminal event, but there is no way for a team to append a post-gate action (e.g. notify a CI pipeline, write a summary to a project log) without forking. This is low-priority because hooks are most valuable when the workflow produces a single terminal artifact; agents typically cycle through menus rather than terminate cleanly. Flag as a future consideration if HBC's CI tooling ever integrates with the Phase 1 gate.

**Proposed scalar (optional, not urgent):**
```toml
on_phase1_gate_complete = ""   # shell command or empty
```

### LOW-OPPORTUNITY — `persistent_facts` single entry, no doc comment on extending

The single entry `"file:{project-root}/**/project-context.md"` is correct and follows BMad convention. However, the `bmad-agent-analyst` reference includes a multi-line comment explaining the two forms (literal sentence vs. `file:` glob). This skill's comment is shorter and omits the literal-sentence form. Teams looking to add, say, an org-standards document as a persistent fact have no in-file hint. Not a correctness issue, but a discoverability gap.

**Fix:** Add a one-line comment example alongside the existing entry:
```toml
# Literal example: "Our org is AWS-only -- do not propose GCP or Azure."
persistent_facts = [
  "file:{project-root}/**/project-context.md",
]
```

---

## Abuse Findings

### MEDIUM-ABUSE — `name` scalar present but hardcoded empty; no guidance on the non-configurable contract

`name = ""` is listed in the `[agent]` block with the comment "non-configurable skill frontmatter, create a custom agent if you need a new name/title". This matches the reference pattern. However, the comment says "DO NOT EDIT" at the file top, while the block-level comment implies `name` exists but is intentionally empty. A reader could be confused about whether leaving `name = ""` is an error or intentional.

The `bmad-agent-analyst` reference uses `name="Mary"` (non-empty), making clear the name is set at build time. In `hbc-agent-ba` the name is genuinely empty, which is fine for an HBC module agent that derives its display title from `title = "Business Analyst"`. The risk is that an override author might write `name = "HBC-BA"` thinking it applies — it won't, and the resolver won't warn them.

**Fix:** Strengthen the non-configurable comment slightly:
```toml
# Non-configurable. Name is intentionally blank for this module agent;
# the title field is the display identity. Fork the skill to change it.
name = ""
```

### LOW-ABUSE — No comment on scalar override behavior for `icon`, `role`, `identity`, `communication_style`

The block-level merge-rules comment covers arrays correctly. It does not state that `icon`, `role`, `identity`, and `communication_style` are **scalars** (override wins — the full value is replaced, not appended). A team overriding `communication_style` to add one sentence would accidentally drop the entire default. The `bmad-agent-analyst` reference has the same gap.

**Fix:** One sentence after the merge-rules comment block:
```toml
# icon, role, identity, communication_style: scalar -- override replaces entirely.
```

---

## Structural Correctness

| Check | Result |
|---|---|
| Always-present arrays present | Pass — all three declared |
| Menu tables keyed by `code` | Pass — all 5 items have `code` |
| Mixed `code`/`id` keying | Pass — consistent `code` only |
| Boolean toggles | Pass — none present |
| Identity/persona in `[workflow]` instead of `[agent]` | N/A — this is an agent skill; persona is correctly in `[agent]` |
| Scalars without override comments | Minor — see LOW-ABUSE above |
| `customize.toml` scalar vs. SKILL.md hardcode mismatch | Pass — SKILL.md reads `{agent.*}` throughout, no hardcoded duplicates |
| `on_<event>` hook count (abuse threshold: 4+) | Pass — zero hooks |

---

## Overall Assessment

**About right.** The surface is clean, minimal, and correctly structured. The agent shape maps precisely to the BMad agent customization contract. No permutation-forest risk, no identity-in-workflow confusion, no broken key-merge cases.

The two medium/low abuse findings are documentation gaps, not structural defects. The single opportunity (no `on_complete` hook) is genuinely optional for an agent skill.

---

## Top 3 Insights

1. **Key-merge is correctly wired.** All `[[agent.menu]]` items carry `code` keys. Teams can replace a specific menu item (e.g. swap the `[BF]` skill for a custom diagram builder) without touching the others. This is the most consequential correctness property of the surface, and it is right.

2. **The override contract for scalars is underdocumented.** `communication_style` is the highest-risk scalar: a team that appends a sentence will lose the entire default voice. One in-file comment prevents a silent, confusing override. The `bmad-agent-analyst` reference has the same gap — this is a cross-agent pattern to address.

3. **`persistent_facts` is well-seeded but not extensible by example.** The BMad default glob is present. Adding the literal-sentence comment example costs two lines and pays off every time a team wants to inject org-standards as persistent context without reading the schema docs.
