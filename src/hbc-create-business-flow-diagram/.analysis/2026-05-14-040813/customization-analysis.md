# Customization Analysis — Round 7

**Target:** `hbc-create-business-flow-diagram`
**Date:** 2026-05-14
**Scanner:** L3 Customization (post-round-6 polish)

`customize.toml` is unchanged since round 5. The new pressure points sit on the boundary between `customize.toml` and the now-substantially-grown `references/headless-contract.md` (three new flags, one new reason, two new defaults-table rows) plus the SKILL.md prose that mirrors them. The judgment for this round is therefore almost entirely about **what the new flags reveal about the customization surface** — what they imply should be lifted, and what they correctly resist lifting.

## Customization posture

Opted in. Surface:

- Always-present scalars: `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` (BMad default glob shipped).
- Workflow-specific scalars: `business_flow_template`, `diagram_type`, `business_flow_output_path`, `on_complete`.
- Four scalars total — well-shaped, well-named, every one carries a comment that explains when/why to override (principles file: "Scalars with no comment explaining when/why to override" is one of the listed anti-patterns; this file passes).

Each `{workflow.*}` reference in SKILL.md resolves through the resolver block on activation; no hardcoded path collisions with declared scalars. Naming follows the `<purpose>_template` / `<purpose>_output_path` / `on_<event>` patterns from the principles file.

## The R7-specific question: should the new headless flags become `[workflow]` scalars?

Three flags landed. Treating each independently:

### `--scope-of-change=polish|semantic|auto` — **do NOT lift**

The prompt flagged this as the strongest lift candidate ("team policy: always semantic for compliance projects"). It is not.

The `auto` default *already does the right thing for compliance projects*: it diffs the Stage 2 flush block and bumps semantically when actors or flows differ. The only thing a `[workflow]` scalar would buy is forcing `semantic` even when the diff says nothing changed — which is **lying in the revision history** to satisfy a meta-rule. That is exactly the kind of "the toggle solves a problem the workflow shouldn't have" that the principles file warns about under "Boolean toggles in customize.toml": *author didn't decide what the skill does; surface becomes a permutation forest. Fix: pick a default; users fork if they want the other shape.*

A team that genuinely needs "every edit bumps minor regardless of diff" wants a *different revision-history policy*, not a knob on this skill. Resisting this lift is correct. The headless flag is the right level of escape valve — per-run, audited via decision log, with the auto default protecting the common case.

### `--allow-migration-without-as-is` — **do NOT lift**

The prompt floated this as "always allow / never allow / require explicit acknowledgement". The current design *is* "require explicit acknowledgement" — and that is the only safe default for a skill whose AS-IS section is load-bearing for compliance audit.

A team policy of "always allow" would be a quiet contract erosion: every migration diagram silently produced without AS-IS, with no per-run signal that the author noticed. A team policy of "never allow" is already the behaviour without the flag. The middle ground — "the automator must pass the flag this run, and the decision log records that" — is the safety property. A `[workflow]` scalar would dissolve it.

This is the same pattern the principles file calls out: identity-style policy belongs to the agent-builder surface or to org-level guardrails, not to the workflow override surface.

### `--update-flow=<flow-name>` — **do NOT lift**

This is runtime intent (which flow to re-render this invocation), not configuration. There is no team policy that says "this team always updates flow X" — flow names are per-project artifacts. Correctly kept on the headless contract surface only.

## R7 verdict: the new flags hold a tight line

All three new flags belong exactly where they are. The prompt was right to call out that `--scope-of-change` is structurally similar to the resisted `migration-vs-greenfield` toggle and `per-skill language override` from earlier rounds — and the answer is the same. **Runtime mode selection is not configuration.** The customize.toml surface stays at four scalars; the headless contract grows. That asymmetry is the design working.

The author has now resisted three plausible-but-wrong lifts in a row (mode toggle, language override, scope-of-change). That is no longer accident; it is the right policy being applied consistently.

## Reason-values mirror — drift risk now real?

SKILL.md lists seven blocker `reason` values inline; the headless contract lists the same seven in its table. The line in SKILL.md says: *"Add new reasons only by extending this list and the contract file together."* The contract file says: *"Add new reasons only by extending this table — automators rely on the closed-set guarantee."*

This is a deliberate dual mirror, not multi-source-of-truth drift. The SKILL.md mirror exists for **compaction survival** — when the conversation drops mid-stage and SKILL.md is the only artifact still in context, the LLM needs the closed set inline to know what `blocked` reasons are legal. The contract file is the canonical extension point. The R7 state of the mirror was verified: all seven reasons match exactly between the two files, including the new `migration_without_as_is`.

**Verdict:** acceptable, with one nit. The current "add to both" instruction is in the SKILL.md prose but not in the contract file. Recommend adding to the contract file's last line: *"Add new reasons only by extending this table AND the brief mirror in SKILL.md — they are intentionally duplicated for compaction survival."* That makes the mirroring obligation visible from either side.

Not a customization-surface defect. Documentation-cohesion nit.

## Closed-set `fresh_reason` — drift, AND it's already happened

The discover script (`scripts/discover-planning-artifacts.py`) emits three `fresh_reason` values:

1. `no_workspace`
2. `crashed_no_progress`
3. `stale_artifact` *(script line 194: "frontmatter exists but no stage-1 yet")*

SKILL.md names only the first two (Stage 1a). The headless contract names the first two (defaults table). **`stale_artifact` is emitted by the script but documented nowhere in the human-readable contract.**

This is exactly the closed-set drift the prompt warned about. The contract promises automators that they can switch on the values — but a `stale_artifact` value could land in `.decision-log.md` (and theoretically in JSON output if the contract were extended) without ever appearing in the contract file. Either:

- the script should not emit `stale_artifact` (collapse to `crashed_no_progress` or `no_workspace`), or
- the contract file should add a `fresh_reason` closed-set table parallel to the `reason` closed-set table, naming all three values and what they mean.

**Severity: medium-abuse** under the principles framing. The `reason` closed set is rigorously declared and mirrored; the `fresh_reason` closed set is not. The author has the discipline for one but not the other. Resolving this is single-edit work and lifts the contract from "closed-set in one place, drifty in another" to uniformly closed-set.

This is the strongest R7 finding.

## Update menu sub-options `[U1]`/`[U2]` — correctly NOT in `[workflow]`

Verified. The Stage 1a menu shows `[U1] Update all flows` / `[U2] Update a single named flow (specify name)` as runtime menu choices. Nothing in `customize.toml` references them; nothing in the headless contract treats them as defaults. The corresponding headless flag is `--update-flow=<name>` (presence/absence distinguishes U1 from U2). This is the right shape: menu sub-options are interaction surface, not configuration.

## Anti-temptations from earlier rounds — still resisted

- **No `migration_vs_greenfield` toggle.** Still inferred + flag-overridable, not a `[workflow]` scalar. Correct.
- **No `language` override per skill.** Language still resolved from project config (`{communication_language}`, `{document_output_language}`). Correct.
- **No `auto_fix_threshold` knob.** The validator's per-issue `auto_fixable` flag is the contract. Correct.
- **No proliferation of `on_<event>` hooks.** Still just `on_complete`. The principles file warns about 4+ hooks; this skill has one.
- **No boolean toggles.** Zero booleans on the surface. Strong signal.

## Findings summary

**Opportunity findings:** none. The four-scalar surface covers the legitimate variance (template, output destination, diagram-type default, completion hook). The remaining variance is per-run, not per-project.

**Abuse findings:**

| Severity | Finding | Fix |
|---|---|---|
| medium-abuse | `fresh_reason` closed-set is enforced in the script but not declared in `references/headless-contract.md` (and `stale_artifact` is emitted but undocumented). | Add a `fresh_reason` closed-set table to the contract file alongside the existing `reason` table; resolve whether `stale_artifact` is legitimate or should fold into `crashed_no_progress`. |
| low (doc nit) | The "add to both" obligation for the `reason` mirror is stated only on the SKILL.md side. | Add the symmetric note to the contract file. |

Neither is a `customize.toml` defect. Both are contract-file completeness issues; they belong to this scanner because they describe the **closed-set guarantees the headless layer makes to automators**, which is a customization-surface concern in the broad sense.

## Top insights

1. **The customization surface has converged.** Three rounds of new headless flags have arrived; none of them belonged in `[workflow]`. The author has internalized the principle that *configuration is per-project policy, not per-run intent*. The R7 state confirms this — `--scope-of-change`, `--update-flow`, and `--allow-migration-without-as-is` are all correctly on the headless surface, not the customization surface.

2. **The closed-set discipline is uneven.** The `reason` closed set is rigorously declared, mirrored, and the mirror obligation is annotated. The `fresh_reason` closed set lives inside the script with no contract-file counterpart, and one value (`stale_artifact`) has already drifted out of documentation. Same author, same skill — but two different levels of contract hygiene for two closed sets that play structurally identical roles for automators.

3. **Resisting plausible lifts is the load-bearing skill.** Each round's "should this become a scalar?" question has a plausible affirmative answer ("compliance teams want X always"). The pattern that keeps emerging: the right answer is to ship the smart default and let the headless flag carry per-run deviation. A `[workflow]` knob would solve the wrong problem (turning a runtime decision into a config decision) and introduce permutation-forest risk on a surface that has very deliberately stayed small.

## Overall assessment

**Excellent** — with one concrete fix worth landing.

The customization surface itself is right-sized, well-named, fully commented, and correctly aligned with `{workflow.*}` references in SKILL.md. No drift between declarations and usage. No anti-patterns from the principles file are present on the `[workflow]` surface. The headless contract surface has grown three flags this round, and **all three were correctly kept off the customization surface** — exactly the discrimination the principles file demands.

The one finding that brings the work below a "no changes" bar is the `fresh_reason` closed-set gap, which is a single edit to `references/headless-contract.md` and a small reconciliation against the script. Address that and there is nothing else to do here.
