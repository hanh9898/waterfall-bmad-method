# Architecture Analysis — hbc-create-business-flow-diagram

Scanner: L1 (architecture) · Date: 2026-05-14

## Assessment

A coherent, well-scoped Simple Workflow that lives entirely in `SKILL.md` plus `customize.toml` — the right shape for its complexity. Routing, customization surface, language discipline, and the Decision-Log Workspace pattern are all wired correctly; the skill reads cleanly end to end and the description matches what the stages actually do. Findings are mostly tidy-ups around the missing `## Overview` heading, a couple of structural mismatches between prose and frontmatter, and over-specification in the activation block that has crept in from the build template.

## Findings

### High

**H1 — `## Overview` heading absent; lead paragraphs serve as de facto overview**
`SKILL.md:6-10` — Principle: structure / `## Overview` and `## On Activation` present. The two paragraphs after the H1 title carry the role, mission, position in the BMM phase, and design rationale that an Overview is meant to carry, but they sit under no heading. The prepass reports it as missing; mechanical scanners (and any author opening the file to scan section headers) won't see it. Fix: insert `## Overview` above line 8 with no content change.

**H2 — `## On Activation` content reproduces the standard 5-step boilerplate instead of using the canonical short form**
`SKILL.md:19-46` — Principle: "What earns its keep" / outcome-vs-prescriptive. Steps 1-5 spell out the resolver invocation, the merge precedence, the persistent-fact loading semantics, the config-fallback chain, the greeting, and the append execution. This is exactly the on-activation procedure every BMad skill performs identically; the institutional pattern is to inline only the customization-resolver line plus a one-line greet/append, leaving the rest to the resolver script and the model. Roughly 25 lines of boilerplate can be replaced with the standard ~5-line block. Concrete duplications:
- Lines 23-25 re-teach the resolver's own merge rules (`scalars override, tables deep-merge, …`) — the resolver enforces them.
- Lines 31-33 re-teach what `file:`-prefixed persistent facts mean — that's a workflow-builder convention the model already follows.
- Line 37 enumerates five config files and three section names in order; this is exactly the kind of mechanical lookup the resolver / config loader handles.

Fix: replace Steps 1-5 with the canonical activation block (resolve workflow → run prepend → load persistent facts → load config → greet and run append, one line each).

**H3 — `workflow_type` claim mismatch between decision log and prepass**
`SKILL.md:48-106`, `.decision-log.md:16` — Principle: "Workflow type claim matches actual structure". The decision log classifies the skill as **Simple Workflow** and gives the justification ("multi-stage … fits inline in SKILL.md without `references/` carve-out"). The prepass infers `workflow_type: complex` from the presence of `### Stage N` headings. The skill is genuinely Simple by the principles file's lens (everything inline, ~113 lines, no carve-out), but the heading style `### Stage 1`, `### Stage 2`, … is the Complex-Workflow shape. Either:
- Rename `### Stage N: …` to neutral sectional headings (`### Prerequisites and Scope`, `### Discovery`, …) — preserves "Simple" claim, or
- Accept Complex classification and update the decision log.

The first is cheaper and matches what `bmad-create-invest-epics-and-stories` does.

### Medium

**M1 — Activation steps embed config-resolution prose that belongs in the resolver**
`SKILL.md:23-25` (the fallback paragraph) — Principle: "When procedure IS value" / fragile-operation invocations. The fallback paragraph that tells the LLM to manually read the three TOML files in base→team→user order and apply merge rules exists because the resolver script "might fail." If the resolver is missing the skill cannot function reliably regardless — the LLM hand-merging structural TOML is itself fragile. Either trust the resolver (drop the paragraph), or escalate failure ("if the resolver script is absent, halt and report"). The current middle path encodes a procedure the LLM will not execute reliably.

**M2 — Stage 1 mixes scope confirmation with workspace creation**
`SKILL.md:50-66` — Principle: "Workflow flows logically — earlier sections produce what later sections consume". Stage 1 does four distinct things: source-document scan, mode/scope confirmation, workspace binding/creation, and decision-log seeding. The workspace binding and decision-log creation depend on `{workflow.output_folder_name}` interpolation which uses `{project_name}` and `{date}` — both resolved during Step 4 of activation. The flow works, but the dense paragraph at lines 66 ("Bind `{doc_workspace}` … . Create the workspace folder if absent … . Initialize the primary … . The decision log is canonical memory across sessions … .") packs the workspace contract into a single sentence. The DLW guidance ("the decision log is canonical memory") is good and should stay where it is — but the workspace-binding mechanics could be one bullet, the decision-log seeding another, so the model doesn't have to disentangle them in one read.

**M3 — Stage 4 "Mermaid syntax" validation invites the LLM to do something it can't do robustly**
`SKILL.md:94` — Principle: "Intelligence placement / Prompts handle judgment, scripts handle plumbing". "Each code block parses; no orphan messages or undeclared participants" is a parse/lint job. The LLM will do this approximately by reading the block, but parses are a deterministic operation. This is a known pattern in BMad — flag where determinism leaks into the prompt. Acceptable in a Simple Workflow that doesn't want to ship a script, but worth noting: in headless mode the auto-fix promise on line 98 (`In headless mode, log every auto-fix to the decision log`) becomes a quality risk without a real parse step.

**M4 — Headless JSON contract specifies `primary` but the headless guidance in principles uses different naming**
`SKILL.md:106` — Principle: "Headless mode / JSON return is the smallest set of paths the caller needs". The contract `{"status", "skill", "primary", "decision_log"}` is reasonable, but the principles guidance suggests `report` for analysis flows and the canonical pair `skill` + `decision_log`. `primary` is non-standard; downstream callers won't know to look for it. Either rename to `artifact` / `document` to match a documented contract, or document this is a deliberate skill-specific extension in the decision log. Low-risk; flag for consistency.

**M5 — `## On Complete` repeats the activation pattern verbatim and could be a single instruction**
`SKILL.md:108-112` — Principle: "Multiple files that could be a single instruction" / outcome-vs-prescriptive. Three lines:
```
Run: python3 …/resolve_customization.py --skill … --key workflow.on_complete
If resolved {workflow.on_complete} is non-empty, follow it as the final instruction. Otherwise, invoke bmad-help.
```
This is exactly the standard hook pattern from peer skills (`hbc-create-invest-epics-and-stories` is identical). Keep — it's institutional. But the resolver invocation has *already been run once* at activation (Step 1). If `on_complete` was resolved as part of the `workflow` block then, a second resolver call here is wasted. Either:
- Note in Step 1 that the resolver call returns the full block including `on_complete`, then On Complete just reads `{workflow.on_complete}`, or
- Document that On Complete deliberately re-resolves because customization may have shifted (it shouldn't have, mid-run).

The current form is harmless but slightly wasteful.

### Low

**L1 — `output_folder_name` uses `{date}` without specifying format**
`customize.toml:35` — Principle: low-stakes ambiguity. `D-06-{project_name}-{date}` — is that `2026-05-14`, `20260514`, `2026-05-14T19:23`? The skill works either way, but two sessions on the same day will collide or accumulate depending on the choice. Specify the resolution (commonly `YYYY-MM-DD`) in the comment.

**L2 — Activation Step 5 has a triple-purpose mini-section**
`SKILL.md:39-46` — "Step 5: Greet and Execute Append Steps" plus a "Language rules for the entire workflow" subsection. The language rules are workflow-wide policy, not part of the greeting/append execution. Lifting them to a separate paragraph above `## Workflow` would make both sections single-purpose.

**L3 — Description trigger phrases miss the natural "vẽ"/"draw" verb in Vietnamese**
`SKILL.md:3` — Description format. Triggers `'create business flow diagram'`, `'create D-06'`, `'tạo sơ đồ luồng nghiệp vụ'`. Users will also say `'vẽ sơ đồ luồng nghiệp vụ'` (draw …) or `'vẽ D-06'`. Adding one Vietnamese variant covers a likely natural utterance with no cost to specificity.

### Not a real finding (prepass false positive)

**N1 — Prepass reports "Referenced stage file does not exist: 06-business-flow-diagram.md"**
`workflow-integrity-prepass.json:90-94, 112`. The prepass extracted `06-business-flow-diagram.md` from references such as `{doc_workspace}/D-06-business-flow-diagram.md` (the OUTPUT document filename) and `D-06-business-flow-diagram.md` in the headless contract. These are output paths, not stage references. There is no `references/` directory and the skill does not carve out stages. No fix needed — flag if the prepass regex can be tightened to ignore `D-06-…` filenames.

## Strengths

- **Right size, right shape.** ~113 lines, all inline, no `references/` carve-out, no scripts, no `assets/`. Matches "inline first, carve out only when needed."
- **Conventions block is stamped exactly per the principles file.**
- **Decision-Log Workspace treatment is canonical.** One sentence at Stage 1 ("the decision log is canonical memory across sessions") plus Stage 5 finalize entry, no ceremony, no tree diagram, no separate `## Workspace` section.
- **Description format is well-disciplined.** Quoted trigger phrases, summary plus triggers, includes a Vietnamese-language trigger that matches the configured `document_output_language`.
- **Language-rule handling is explicit and correct.** Distinguishes `{communication_language}` (user-facing) from `{document_output_language}` (artifact-facing) and explicitly carves out Mermaid keywords as English — this is exactly the kind of judgment context that earns its place.
- **Customization surface is clean.** Six scalars, one persistent-fact array, two activation arrays. No boolean toggles. `business_flow_template` and `output_dir` are correctly modeled as scalars, not buried in tables.
- **Downstream consumers named explicitly** (`bmad-create-architecture`, `bmad-create-ux-design`, `bmad-create-epics-and-stories`, `hbc-create-invest-epics-and-stories`) — the workflow knows where it sits in the BMM phase chain.
- **Headless mode is a first-class consideration** in Stage 1 (decision-log capture in headless) and Stage 5 (JSON contract).
- **Falls back to interactive elicitation when no PRD is present** and explicitly calls this out as "a normal mode, not a blocker" — good design rationale that prevents an LLM "optimizing" the elicitation branch away.
- **Distillator handoff is correctly gated** ("Skip with a note if distillator is unavailable; never inline a substitute") — graceful degradation per the principles file.
