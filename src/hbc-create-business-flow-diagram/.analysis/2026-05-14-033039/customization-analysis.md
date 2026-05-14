# Customization-Surface Scan — Round 5 (post-round-4 polish)

Target: `hbc-create-business-flow-diagram`
Files in scope: `customize.toml`, `SKILL.md`, `references/headless-contract.md`.

## Customization posture

Opted in. Surface is four workflow-specific scalars (`business_flow_template`, `business_flow_output_path`, `diagram_type`, `on_complete`) plus the three always-present arrays (`activation_steps_prepend`, `activation_steps_append`, `persistent_facts`). No arrays-of-tables, no boolean toggles, no identity / communication-style fields. Every scalar is referenced from SKILL.md as `{workflow.<name>}` (verified at lines 27, 39, 81, 86, 158, 236 of SKILL.md), so the "hardcoded-next-to-a-declared-scalar" silent-noop failure mode is closed. `persistent_facts` ships the BMad default glob. Shape matches the principles file exactly.

## Round-4 deltas — judgment

### `customize.toml` — `{date}` dropped from output-path default

Now exemplary. Round 3 already flagged the `{date}` baked into the default as a quiet abuse (it forced a new workspace on every re-run, defeating the resume protocol that the rest of SKILL.md spends real lines defending — Stage 1a's resume-state branching, the Decision-Log Workspace pattern, the frontmatter `stepsCompleted` cursor). The new default `{planning_artifacts}/business-flows/D-06-{project_name}/` aligns the customization surface with the workflow's own contract: stable per project, re-runs land in the same workspace, Stage 1a's `Resume` branch can actually fire. The comment block (lines 32-36) tells the operator exactly how to opt back into dated snapshots if they want them — a one-line policy change rather than a fork. This is the textbook shape for a `*_output_path` scalar under the principles file's customize.toml section. **Grade: Excellent.**

### `references/headless-contract.md` carve-out

Correct call. Per the principles file's carve-out rules, `references/` is for content that earns its own file. A contract — input flags table, defaults table, JSON return shape, closed-set reason enum — is reference material, not narrative, and three separate stages (1a / 1d / 4 / 5) cite it. SKILL.md now reads cleaner (header at line 14, full pointer at line 59) and the contract has one canonical home for automators. The carve-out itself is not a customization point, but it makes the customization story visible: line 25 of the contract shows `{workflow.diagram_type}` as the default for `--diagram-type`, which is the exact pattern that proves the scalar earns its keep (CLI flag overrides per invocation; toml scalar sets the org default; SKILL.md picks the resolved value).

### `--review-lenses` and `--no-prd-ok` — workflow-level configurability?

Verifying round 3's "no" against round 4: still no, and round 4 strengthens the case rather than weakens it. Three reasons:

1. `--review-lenses=skip|advanced|party` is a **per-invocation cost dial** (~5 min vs ~15 min vs 0), not a team policy. Teams that want "always run advanced" can set it in `activation_steps_append` ("invoke this skill with `--review-lenses=advanced`") — the existing surface already absorbs this case, and `activation_steps_append` is the principled merge point per the principles file. Adding `default_review_lenses` to `[workflow]` would be a boolean toggle in disguise (the principles file's customize-toml failure mode: "Boolean toggles … the surface is doing the job of a variant skill").
2. `--no-prd-ok` is similarly a per-run **automator stance**, not a team posture. The hypothetical "team policy: always require PRD" is already the headless default — round 4 made absent-PRD a `blocked` reason (`no_prd_and_no_interactive_in_headless`). To get the *opposite* policy ("never allow greenfield"), the team would forbid `--no-prd-ok` at their automator layer, not configure it in toml. Lifting this would create a permutation forest with no real second user.
3. Both flags would tempt the author into a per-team toggle matrix (`require_prd=true`, `auto_review=advanced`, `auto_fix_strict=true`...) — exactly the "permutation forest no one can reason about" the scanner instructions warn against.

**Round-4 design holds.** Do not lift.

### Closed-set `reason` values — customization point?

Verified: **no**, and the contract explicitly says so. Headless-contract line 69: *"Add new reasons only by extending this table — automators rely on the closed-set guarantee."* That is the right call. The closed-set IS the contract; making it customizable (`[workflow.reasons]` table) inverts the value — automators switching on `reason == "fr_coverage_gap"` would have to defend against arbitrary team-injected enum values, and the contract stops being a contract. Reason values are an extension point for the upstream skill author (PR to add a new row), not for downstream teams. This is the same logic that keeps subagent return schemas non-customizable.

If a team needs a new failure mode, the principled path is: PR the skill to add a new reason, with the trigger condition documented in the table. Toml-level customization here would be abuse.

### Round-3 anti-temptations — still absent?

Verified absent:

- **No migration-vs-greenfield toggle.** Mode is resolved per-invocation (heuristic + `--mode` flag in headless contract, line 12). The toml does not expose a `default_mode` scalar — correct, per the boolean-toggle failure mode.
- **No per-skill `communication_language` / `document_output_language` override.** Both still resolve from BMad config (`{project-root}/_bmad/config.yaml`) at On-Activation Step 4. Round 3 correctly identified these as project-level concerns; round 4 did not regress.
- **No identity / persona / tone fields in `[workflow]`.** Surface remains paths + behavior hooks, no agent-shape leakage.

## Opportunity findings

None of consequence. Two micro-observations, both low-opportunity (do not act unless asked):

- **Low-opportunity:** `assets/decision-log-template.md` is hardcoded at SKILL.md line 27 and line 111 (Stage 1a). Lifting to `decision_log_template` is possible but probably noise — the decision-log shape is a BMad-wide convention (DLW pattern in the principles file), not a per-team variant. Keeping it bare is the right call until a real second user appears.
- **Low-opportunity:** the discover/validate scripts (`scripts/discover-planning-artifacts.py`, `scripts/validate-mermaid.py`, `scripts/check-fr-coverage.py`) are not configurable. Per the principles file's intelligence-placement rule, scripts are plumbing; lifting their paths would only matter if a team wanted to substitute a different validator. No signal that exists.

## Abuse findings

None. Surface passes every check in the scanner instructions:

- No boolean toggles.
- No identity / communication-style fields.
- No `on_<event>` hook proliferation (one hook: `on_complete`).
- No arrays-of-tables (so no keying problems).
- No opaque scalar names — all four match the `<purpose>_template` / `<purpose>_output_path` / `on_<event>` patterns from the principles file.
- Every scalar carries a comment explaining when/why to override (output-path comment now also explains the round-4 `{date}` opt-in path, the strongest comment in the file).
- SKILL.md reads every declared scalar via `{workflow.<name>}` — no silent-noop overrides.

## Overall assessment

About right, and now exemplary. The round-4 dropping of `{date}` was the last real abuse on the surface; the carve-out of `headless-contract.md` makes the customization story (toml default → CLI flag override → resolved value in SKILL.md) visible in one place. Surface size (four scalars + three arrays) is small enough that a new operator can reason about every knob in under a minute, and large enough that the realistic axes of team variance (where the template lives, where outputs land, what default diagram type, what to do on complete) are absorbed without forking.

## Top insights

1. **Round-4 customize.toml is the canonical shape.** Four scalars, every one wired, every one commented, default-path stable for re-run resume. Future scanners can use this file as a reference exemplar for the `*_template` / `*_output_path` / `on_<event>` patterns from the principles file.
2. **Resist lifting per-invocation flags into team policy.** `--review-lenses` and `--no-prd-ok` are automator dials, not team postures; the existing `activation_steps_append` array already absorbs the "team always wants X" case without growing the scalar surface.
3. **The closed-set `reason` enum is the contract, not a customization point.** Round 4's explicit guarantee ("Add new reasons only by extending this table") is the correct boundary — toml-level extensibility here would invert the value proposition for every downstream automator.
