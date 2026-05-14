# Customization Surface Analysis (Round 3) — hbc-create-business-flow-diagram

Scanner: L3 (customization-surface economist). Target: `src/hbc-create-business-flow-diagram/`. Advisory only.
Round 3 — post-refactor re-scan of `customize.toml` and the enlarged `SKILL.md` (~260 lines, Headless Mode section + Stage 1 sub-stages added).

## Customization Posture

Opted in. Surface shape (workflow-specific scalars beyond the BMad baseline):

- `business_flow_template` (path)
- `diagram_type` (hint scalar)
- `business_flow_output_path` (single workspace path — collapsed from round-1 pair)
- `on_complete` (hook scalar)

Plus the always-present BMad fields: `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` (canonical default present). Total workflow-specific scalars: **4** (down from 5 in round 1). No arrays-of-tables, no boolean toggles, no hooks beyond `on_complete`, no identity/persona/communication-style fields. SKILL.md reads every declared scalar as `{workflow.X}` — no silent-no-op hardcodes against declared knobs.

Posture is **still appropriate, now cleaner than round 1**. The refactor moved the surface from "leaning slightly loud" to "about right."

## Resolved Round-1 Findings

### R-1 — A-1 (split output scalars) resolved cleanly

Round 1 flagged `output_dir` + `output_folder_name` as a medium-abuse permutation surface. The new file collapses both to:

```toml
business_flow_output_path = "{planning_artifacts}/business-flows/D-06-{project_name}-{date}/"
```

SKILL.md Stage 1a now binds directly: `{doc_workspace} = {workflow.business_flow_output_path}` and the comment block calls out the "no two-scalar combination" intent. The comment also documents the resume-friendly override pattern (drop `{date}` to make re-runs land in the same workspace) — that's the right level of teaching for a knob whose default embeds a date stamp. **Closed cleanly, no residue.**

### R-2 — A-2 (`diagram_type` as half-arguing knob) addressed via comment

Round 1 flagged that `diagram_type`'s comment half-argued against itself. The new comment is tighter: "Hint for the starting Mermaid diagram type surfaced at Stage 1. The workflow may override per-flow when a different type fits better — this is a default, not a contract." That makes the team-override rationale explicit (org-wide default for the starting choice) and labels the knob honestly as a hint. **Closed.** Severity-low recommendation from round 1 satisfied.

### R-3 — Anti-temptations from round 1 still correctly absent

Confirmed by direct read of `customize.toml`:

- No `project_mode` / `migration` / `as_is_to_be_enabled` toggle. Mode is decided at Stage 1 (interactive) or via `--mode` flag (headless) — per-run state, not team config. (Principles: boolean toggles in `[workflow]` are textbook abuse.)
- No per-skill `document_output_language` override. Project-wide policy stays in `_bmad/config.yaml` `core`, where round 1 placed it. The two new headless flags (`--mode`, `--diagram-type`) reinforce the same shape: runtime intent goes through CLI flags or interactive prompts, **not** through customize.toml.

Both anti-temptations remain resisted. Good.

## New Opportunity Findings (from the ~200 SKILL.md additions)

### O-1 — Hardcoded `.scan/*.json` artifact paths under `{doc_workspace}` (low-opportunity)

Three new hardcoded paths appear in Stage 1b and Stage 4:

- `{doc_workspace}/.scan/artifacts.json`
- `{doc_workspace}/.scan/mermaid.json`
- `{doc_workspace}/.scan/fr.json`

These are internal scratch artifacts the scripts emit and the LLM consumes within the same run. They're not user-facing outputs and not template-loaded resources, so they don't meet the `<purpose>_template` / `<purpose>_output_path` bar. **Recommendation: leave them hardcoded.** Lifting them would be exactly the "permutation forest" the principles file warns against — no team has a legitimate reason to relocate transient script-to-LLM JSON. Flagging only to confirm the call was considered.

If anything ever changed: collapse the three paths into a single `{doc_workspace}/.scan/` convention by stating "scripts write JSON returns to `{doc_workspace}/.scan/<scriptname>.json`" in the Conventions block — but that's a style nit, not a customization knob.

### O-2 — D-06 primary filename is hardcoded (low-opportunity, leave alone)

`{doc_workspace}/D-06-business-flow-diagram.md` appears verbatim in Stages 1a, 4, 5, and in the JSON return contract. In principle this could be a `business_flow_filename` scalar, but the filename is locked to the HBLab D-* document-family convention (the same convention that makes `business_flow_template` shareable across D-* skills). A team that renames it breaks the cross-document anchoring. **Recommendation: leave hardcoded.** This is institutional knowledge, not a knob.

### O-3 — No `on_validate` or `on_stage_complete` hook lifted from the new flush/menu blocks (correctly absent)

The Stage 2 compaction-flush, Stage 3/4 parallel-lens menus, and Stage 5 distillator offer are all the kinds of seams where an author *could* be tempted to add hook scalars (`on_stage_2_complete`, `on_validation_pass`, `on_distillate_offer`). Per principles, 4+ `on_<event>` hooks signal workflow internals leaking into the override surface. The current file has exactly **one** hook (`on_complete`) and that's the right ceiling. **No action needed — confirming the temptation was correctly resisted.**

## New Abuse Findings (from the ~200 SKILL.md additions)

### A-1 — Stage 1a resume menu (R/U/V/N/X) is runtime intent, NOT customization (correctly absent — anti-finding)

The context question asked whether `[R][U][V][N][X]` should be configuration. **Verified runtime.** Each option corresponds to a per-run decision about an existing workspace's state — Resume an incomplete run, Update with a new revision row, Validate-only re-check, start Fresh, or Exit. The headless defaults table already resolves these deterministically (`Resume if incomplete; Update if full; Fresh if no prior file`). A team-level "always Update" or "always Fresh" override would silently destroy in-progress work the user didn't realize was there. The right surface is the runtime menu (interactive) or the decision-log frontmatter inspection (headless). **Leave out of customize.toml.**

### A-2 — Stage 3 / Stage 4 `[A][P][C]` parallel-lens menus are runtime intent (correctly absent — anti-finding)

Same shape as A-1. `[A] Advanced Elicitation`, `[P] Party Mode`, `[C] Continue` are per-run choices about review depth — the user reads the consolidated findings and decides whether the current artifact justifies the extra lens. The headless default is `[C]` (logged as auto-decision). A team-level "always invoke Party Mode at Stage 3" override would either (a) double the runtime cost for every D-06 unconditionally or (b) suppress the legitimate human-loop break-point. **Leave out.** The principle here: parallel-lens invocation is a judgment call about *this* artifact's risk, not a team policy.

(If a future need ever surfaced "team X always wants the advanced-elicitation lens before save," the right answer is a thin sibling skill or an `activation_steps_append` entry that pre-loads the choice — not a new scalar.)

### A-3 — Headless input flags are CLI, not workflow config (correctly absent — anti-finding)

The new "Headless Mode > Input flags" table lists `-H`, `--prd-path`, `--mode`, `--scope`, `--diagram-type`, `--no-prd-ok`. **None of these belong in `[workflow]`.** They are per-invocation arguments — an automator picks them for *this* run. The only one that even brushes against config is `--diagram-type`, and SKILL.md correctly wires it to read `{workflow.diagram_type}` as the *default* when the flag is unset. That's the right factoring: CLI flag overrides the team default which overrides the BMad default. **Confirmed clean.**

### A-4 — Context question: should `[workflow]` expose disable-flag scalars for some teams? (anti-finding)

The brief asked whether `[workflow]` should have scalars to disable specific headless flags for some teams (e.g. forbid `--no-prd-ok` in regulated environments). **The answer is no.** Per principles, boolean toggles in `[workflow]` are flagged as the surface doing the work of a variant skill. Three reasons specifically:

1. CLI policy is a different concern from workflow shape. The right enforcement point is the automator's own config or a CI policy lint, not the skill's customize.toml.
2. A "disable `--no-prd-ok` for this team" toggle is unenforceable from the skill side — anyone with shell access can still pass the flag. The customize.toml override creates a false sense of policy.
3. The set would grow. Once `--no-prd-ok` is gated, someone wants `--mode` gated, then `--scope`, then the file is a permutation forest of flag-disablement booleans.

The right shape if a team genuinely needs guardrails: wrap the skill invocation in a project script that filters arguments. **Leave the surface clean.**

### A-5 — Defaults table heuristics are NOT customization (anti-finding)

The "Defaults table" lists heuristics like `unless PRD body contains "AS-IS", "current state", or 現状 → migration` and `unless discover-planning-artifacts.py reports >1 sub-process candidate → multi`. Tempting candidate scalars: `migration_keywords = [...]`, `multi_scope_threshold = 1`. **Reject both.** They're inside the LLM's judgment band (per principles' Outcome-vs-Prescriptive table — "Ensure the user's requirements are complete" beats "Step 1: ask about X"). Externalising a Japanese keyword list to TOML invites teams to edit it, get it wrong, and produce silently-mis-classified runs. The current shape — heuristic stated in SKILL.md, decision logged in `.decision-log.md` — is correct. **No action.**

## Overall Assessment

**About right.** The refactor moved the surface from round-1's "leaning slightly loud" to a clean four-scalar shape. The substantial SKILL.md growth (`~260` lines vs round 1's smaller form) added two big concept blocks — Headless Mode and Stage 1 sub-stages — *without* leaking either into the customization surface. That's a deliberate restraint the author should get credit for: every place where a new section *could* have justified a new scalar (resume-menu policy, parallel-lens policy, flag-allowlist, heuristic thresholds), the author kept the surface flat.

The one remaining structural call-out is round-1 O-4 (template lives in `{project-root}/templates/` rather than `assets/`). That's a path-conventions / architecture question more than a customization question, and not in scope for L3 to re-litigate.

## Top Insights

1. **Round-1 A-1 closed cleanly.** `business_flow_output_path` is the principles-aligned single-scalar shape, the comment teaches the resume-friendly override pattern, and SKILL.md binds directly to the resolved value. No residue.

2. **The ~200 new SKILL.md lines added zero new customize.toml scalars — and that's correct.** Every visible seam (resume menu, parallel-lens menu, headless flags, defaults heuristics) is runtime intent, not team policy. The author resisted four distinct surface-bloat temptations in one refactor; that's the harder discipline.

3. **Hook count remains at one (`on_complete`).** The Stage 2/3/4/5 flush/menu/save seams are all places where an author drifts into `on_<event>` hook proliferation. Holding at one hook keeps the surface auditable. The principles ceiling is "4+ hooks = leakage"; this skill sits well under it.
