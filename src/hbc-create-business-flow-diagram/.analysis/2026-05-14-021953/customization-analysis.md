# Customization Surface Analysis — hbc-create-business-flow-diagram

Scanner: L3 (customization-surface economist). Target: `src/hbc-create-business-flow-diagram/`. Advisory only.

## Customization Posture

Opted in. The skill ships a `customize.toml` with the full BMad always-present surface (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`) plus four workflow-specific scalars: `business_flow_template`, `diagram_type`, `output_dir`, `output_folder_name`, and the `on_complete` hook.

Surface size: 6 workflow-specific scalars (counting the output-path pair and `on_complete`). Shape: all scalars, no arrays-of-tables, no boolean toggles, no hooks beyond `on_complete`. SKILL.md correctly references the resolved values as `{workflow.business_flow_template}`, `{workflow.diagram_type}`, `{workflow.output_dir}`, `{workflow.output_folder_name}`, `{workflow.on_complete}`, `{workflow.persistent_facts}`, `{workflow.activation_steps_prepend}`, and `{workflow.activation_steps_append}` — no silent-no-op hardcodes that I could find.

`persistent_facts` ships with the canonical BMad default (`file:{project-root}/**/project-context.md`).

For context this is a single-artifact workflow that produces D-06 (one document plus a decision log) and sits in a standard place in the BMM pipeline. The current surface is roughly the BMad baseline + 3 domain knobs (template, diagram type, output location).

## Opportunity Findings (knobs that could exist but don't)

### O-1 — No persistent_facts entry for the wider HBLab D-* spec set (low-opportunity)

The skill is part of a 30+ document HBLab convention family (`templates/D-00…D-31`). Migration and greenfield mode, AS-IS/TO-BE conventions, revision-history format (`改訂履歴`), and the Japanese template all derive from house style. Today, none of that surfaces as a configurable fact — it lives implicitly in the template file.

The `persistent_facts` array is the right vehicle: if HBLab publishes a `D-*-conventions.md` or `business-flow-conventions.md` somewhere under `{project-root}`, declaring it as a `file:` entry would let team overrides extend the convention set without forking the skill. Currently each new house-style rule pushes the author toward editing `SKILL.md`. Severity is low because the project-context.md glob already covers the most likely landing spot; the suggestion is documentation, not a new scalar.

Proposed wording change only in the comment header above `persistent_facts`: name "HBLab D-* document conventions" as an example of the kind of file teams routinely add here.

### O-2 — Diagram-type allow-list isn't enforceable from the override surface (low-opportunity, deferral candidate)

`diagram_type` accepts `sequenceDiagram | flowchart | stateDiagram` (per SKILL.md context and Stage 3). The customize.toml comment lists the three values but cannot constrain them — a user override could write `"erDiagram"` and the workflow would either fail at Mermaid render time or silently generate the wrong artifact.

The right answer per principles is *not* a `diagram_type_allowed = [...]` array-of-strings (that's the surface doing validation work; "would an LLM do this correctly without being told?" — yes, given Stage 3's render guidance). The opportunity is purely descriptive: tighten the customize.toml comment so it reads as a hard contract ("Allowed values: …; other values fall back to sequenceDiagram with a decision-log note"). Severity low.

### O-3 — `--headless` JSON contract has no override surface (low-opportunity, but probably correct to leave alone)

Stage 5 hardcodes the headless return shape `{status, skill, primary, decision_log}`. In principle a downstream orchestrator might want to demand additional fields (`workspace`, `mode`, `flows_count`). The principles file explicitly calls out three-mode architecture but the headless contract is downstream-API-shaped, not user-shape — over-exposing it would create exactly the "permutation forest" warning. Flagging but recommending **no action**: keep the JSON contract closed.

### O-4 — `business_flow_template` value embeds path semantics in customize.toml that the principles file deprecates (low-opportunity)

The default `business_flow_template = "{project-root}/templates/D-06_業務フロー図_template.md"` reaches into project space rather than skill-asset space. Sibling `hbc-create-invest-epics-and-stories` ships `stories_template = "assets/invest-stories-template.md"` (skill-rooted). The principles file's path-conventions section says `assets/` is for "templates and other static content the workflow loads," so the BMad convention is skill-local defaults that overrides can redirect to project space — not the other way around.

This is structural, not a missing knob. Two paths to fix and only the second is in-scope for L3:
1. (Out-of-scope for this scan) Copy the D-06 template into `assets/` so the skill is self-contained.
2. If the design choice is genuinely "share the HBLab D-* template set across all D-* skills from one location," document that rationale in the customize.toml comment so future maintainers don't normalize it back to `assets/`.

Severity low — the path resolves and the override works.

## Abuse Findings (knobs that probably shouldn't exist or are over-engineered)

### A-1 — `output_dir` + `output_folder_name` split is a permutation surface (medium-abuse)

Two scalars combine on activation: `{doc_workspace} = {output_dir}/{output_folder_name}/`. The factoring lets a team pick the parent dir and the folder template independently — but in practice almost no one wants those independent. A team that moves planning artifacts wants one path. A team that wants flat dating (e.g. no `-{date}` suffix) wants one template.

Per principles, this is the workflow author "not deciding what the skill does" and pushing the decision to the surface. The cleaner shape is a single `<purpose>_output_path` scalar matching the principles file's pattern:

```toml
business_flow_output_path = "{planning_artifacts}/business-flows/D-06-{project_name}-{date}/"
```

…with one override point. Today, a team that wants to remove `{date}` from the folder template overrides `output_folder_name` and learns by reading SKILL.md that the workspace also depends on `output_dir`. Two-step mental model where one would do.

Severity medium because nothing breaks today — it just doubles the cognitive load of the surface and risks an override that touches one half but not the other (e.g. user overrides `output_folder_name` to drop `{project_name}`, doesn't realize `output_dir` is also configurable).

Recommended fix: collapse to one scalar `business_flow_output_path`; bind `{doc_workspace}` directly to the resolved value in Stage 1.

### A-2 — `diagram_type` as a global default duplicates judgment SKILL.md already makes (low-abuse, borderline)

Stage 1 explicitly says "Diagram type override if needed (default `{workflow.diagram_type}`)" and Stage 3 says "The workflow may override per-flow when a different type fits better" — i.e. the LLM picks per-flow at runtime, and the scalar is just the *starting* choice. That makes the knob a hint, not a contract.

The honest question: do teams actually want their business flows to default to `flowchart` org-wide rather than `sequenceDiagram`? If yes, keep it. If the answer is "the LLM will pick the right one for each flow anyway and the global default never matters," cut it. Per principles, a scalar with no comment explaining when/why to override is an abuse smell — and the existing comment ("override per-flow when a different type fits better") is half-arguing against the knob's own existence.

Severity low because the comment hedges enough that the user understands the limitation. Recommendation: keep but tighten the comment to "Starting suggestion the workflow surfaces in Stage 1; the LLM picks per-flow when justified. Override at the team level only if your org standardizes on `flowchart` over `sequenceDiagram` for business flows."

### A-3 — Context question: migration-vs-greenfield and AS-IS/TO-BE as toggles (anti-finding)

The context question raised whether `project_mode` (migration/greenfield) and AS-IS/TO-BE inclusion should be customizable. The answer is **no** — putting that on customize.toml would be textbook A-tier abuse:

- It's a boolean toggle (principles flag "3+ booleans = surface doing variant-skill's job"; even 1-2 boolean toggles for runtime branching is the wrong tool).
- The mode is per-*run*, not per-*team*. A greenfield project today is a migration project after v1 ships. Baking it into the team override file means every fresh project starts with stale state.
- The LLM already asks in Stage 1 ("Project mode — greenfield (TO-BE only) or migration (AS-IS + TO-BE)"). The runtime conversation is the right surface for runtime state.

**Recommendation: leave it out.** This isn't an opportunity, it's a temptation to avoid.

### A-4 — Context question: per-skill override of `document_output_language` (anti-finding)

The context question asked whether `document_output_language` should have a per-skill override here. The answer is **no**:

- It's already a `core` config value (verified in `_bmad/core/config.yaml`, `_bmad/bmm/config.yaml`). Project-wide policy.
- A per-skill override would mean a single project produces D-06 in Japanese while D-04 and D-08 are in English — that violates the HBLab D-* document family's purpose of being internally consistent.
- If a one-off run needs a different language, the user says so in the conversation. Stage 1 is the right surface, not customize.toml.

**Recommendation: leave it out.** Same temptation, same answer.

## Overall Assessment

**About right, leaning slightly loud.** The skill has done the hard work — opted in, lifted the genuinely team-variable knob (template path), kept identity/persona out of `[workflow]`, kept the override surface flat with no hooks beyond `on_complete`, and wired SKILL.md to read `{workflow.X}` everywhere. Surface size is in the healthy zone for a single-artifact workflow (~3 domain scalars + the BMad baseline).

The one real cost is the `output_dir`/`output_folder_name` split (A-1) — that's the only knob I'd actively collapse. The two anti-findings (A-3, A-4) confirm the author resisted the loudest available temptations.

## Top Insights

1. **Collapse `output_dir` + `output_folder_name` into a single `business_flow_output_path`.** Independent factoring buys nothing; one path scalar is the principles-aligned shape and removes the risk of a half-override.

2. **The two "should we add this?" questions from the context (migration mode, per-skill language) are both correctly answered "no."** Both are runtime per-conversation state, not team configuration. The right surfaces for them already exist (Stage 1 elicitation, core config).

3. **`diagram_type` is the weakest existing knob** but probably worth keeping because the comment honestly describes it as a hint, not a contract. The surface as a whole behaves — no boolean toggles, no agent-shape leakage, no hooks beyond `on_complete`, SKILL.md and customize.toml are in sync.
