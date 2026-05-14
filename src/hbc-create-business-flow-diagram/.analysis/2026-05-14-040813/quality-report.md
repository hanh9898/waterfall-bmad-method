# BMad Quality Analysis: hbc-create-business-flow-diagram

**Analyzed:** 2026-05-14T04:08:13Z | **Path:** C:/Users/HanhNT2/stc-erp-bmad-custom/src/hbc-create-business-flow-diagram
**Interactive report:** quality-report.html
**Round:** 7 (post round-6 polish)

## Assessment

**Excellent** — Round 6 closed all 13 round-5 findings end-to-end and added one over-delivery (a third `fresh_reason` value, `stale_artifact`) without introducing any structural regression; the seven residual findings are uniformly polish-grade and none blocks execution, violates a stated promise, or affects any of the six audited user archetypes.

All four scanners (L1 architecture, L2 determinism, L3 customization, L4 enhancement) independently return Excellent. The remaining ceiling-grade nuance: two medium findings (a `fresh_reason` closed-set documentation gap and an unspecified equality rule for `--scope-of-change=auto`) sit cleanly inside the Excellent bar per the principles-file rubric ("no high+ issues, few medium"). The skill is now in the same shape-quality bracket as `bmad-product-brief` — every named "Patterns BMad has seen pay off" is present and operational, every closed-set value has tests, every state transition has an audit signal.

## What's Broken

None. No critical or high-severity issues.

## Opportunities

### 1. Closed-set `fresh_reason` not mirrored to the headless contract (medium — 2 observations)

The discover script emits three `fresh_reason` values (`no_workspace`, `crashed_no_progress`, `stale_artifact`) but the headless contract documents only the first two and SKILL.md prose names only the first two. The third value is emitted by `discover-planning-artifacts.py:194` and would land in `.decision-log.md` (and in JSON output if extended) without ever appearing in the contract file — the exact closed-set drift the `reason` mirror was designed to prevent. Same author, same skill, two different levels of contract hygiene for two structurally identical closed sets.

**Fix:** Add a `## fresh_reason values` table to `references/headless-contract.md` mirroring the existing blocker-reasons table, naming all three values and when each fires. Optionally add a third bullet at `SKILL.md:97-100` for the `stale_artifact` case (or collapse it into `crashed_no_progress` at the script layer if the runtime behaviour is identical).

**Observations:**
- `fresh_reason` closed-set not declared in headless contract; `stale_artifact` undocumented — `references/headless-contract.md` (L3)
- `fresh_reason: stale_artifact` not surfaced in SKILL.md prose — `SKILL.md:97-100` (L1, L2)

### 2. `--scope-of-change=auto` equality rule unspecified (medium — 1 observation)

Both `SKILL.md:206-208` and `references/headless-contract.md:16` say the auto-detect mode compares arrays — identical means polish, differs means semantic — but neither file defines what equality means. Set vs ordered? Case-sensitive? Whitespace-stripped? Two runs against the same Update payload could produce different polish/semantic classifications depending on how the LLM happens to compare the arrays — exactly the cross-run nondeterminism the headless contract exists to prevent.

**Fix:** Add one sentence to both files pinning the comparison rule (recommended: unordered set-membership on stripped, lowercased strings — reordering and whitespace do not count as semantic). Do NOT lift into a script: both inputs are already in conversation context (L2 intelligence-placement). Address F3 in the same edit by adding the safe default: "if no prior flush block is parseable, treat as semantic" (a missing baseline is not evidence of no-change).

**Observations:**
- Equality semantics for Stage-3 auto-diff not defined — `SKILL.md:206`, `references/headless-contract.md:16` (L2, L4)

### 3. Polish-grade ergonomics and documentation nits (low — 5 observations)

Four scanner-surfaced low-severity observations that don't block any user archetype and don't violate any stated promise. Each is a one-edit fix; none individually warrants a theme.

**Fix:** Apply each in a single polish commit; none gates anything else.

**Observations:**
- Strict 4-of-4 short-circuit mildly hostile to experts omitting one obvious dimension (F1) — `SKILL.md:130` (L4)
- No 1b-reply flush before 1e — narrow compaction window (F2) — `SKILL.md:130` (L4)
- SKILL.md is ~3% over the multi-branch soft target (259 lines / 4,690 tokens vs ~250-line soft guidance; no action required) — `SKILL.md` (L1)
- `\bprd\b` underscore boundary and date-anchored Session regex lack intent-comments — `scripts/discover-planning-artifacts.py:154, :241` (L2)
- `reason` dual-write obligation stated only on the SKILL.md side — `references/headless-contract.md` (L3)

## Strengths

- **Round-6 closed all 13 round-5 findings end-to-end.** L1 audit confirms each of N1/N2/N3, M-1/M-2, N-1/N-3/N-4, N-2, N5, SO1/SO2/SO3, L3 (14 items counting both prior-round nomenclature schemes) is resolved with specific file:line evidence. L4 independently re-walked the same closures from the user-journey lens.
- **Customization surface has converged across three rounds of new headless flags.** `--scope-of-change`, `--update-flow`, and `--allow-migration-without-as-is` all correctly landed on the headless contract surface, NOT in `[workflow]`. `customize.toml` stays at four well-shaped, fully-commented scalars while the headless contract grows — the right asymmetry.
- **All eight "Patterns BMad has seen pay off" are present and operational.** Open-floor opening, soft-gate elicitation, intent-before-ingestion, capture-don't-interrupt, dual-output, parallel review lenses, three-mode architecture, graceful degradation, plus canonical Decision-Log Workspace. Same shape-quality bracket as `bmad-product-brief`.
- **Closed-set discipline on blocker `reason` values with compaction-survival mirror.** Seven reasons declared in both `SKILL.md:55-67` and `headless-contract.md:65-73`, with the dual-write requirement stated in prose. The duplication is acknowledged as compaction-survival, not multi-source drift.
- **Intelligence placement on three new round-6 regex/classifier additions.** `fresh_reason` is a closed-set enum classifier driven by structural inputs; the date-anchored Session regex generalizes from English to ISO 8601 structure (Vietnamese parses); `\bprd\b` replaces a sloppy substring that would have matched `approved/` or `notes-on-the-prd/`. Each change paired with a focused new test.
- **Headless audit trail is automator-grade.** 10-flag input contract, 7-reason closed-set blocker table, JSON return carries `review_lenses_run`, per-decision logging requirement, validator auto-fix gated on per-issue `auto_fixable: true` from the script.
- **25 tests covering CLI contract, edge cases, and three new round-6 regressions.** `python scripts/tests/run-tests.py` returns `Ran 25 tests, OK (skipped=1)`. Subprocess invocation against the CLI, JSON parse, structural assertion — no mocking.

## Detailed Analysis

### Architecture

**Excellent.** All 13 round-5 findings closed with specific file:line evidence; the 22-line SKILL.md growth (237 → 258, now 259 with one trailing line counted) is fully load-bearing — every new sentence anchors a real architectural surface (gate / discriminator / branch / sanity check / closed-set mirror), not procedural padding. No structural regressions, no introduced contradictions.

Two low-severity observations: SKILL.md is ~3% over the multi-branch soft target (259 vs ~250 lines; no action required, well under the ~500-line hard ceiling), and `fresh_reason: stale_artifact` is implemented in the script but not enumerated in SKILL.md prose.

### Determinism & Distribution

**Excellent.** Round 6 hit three real seams (audit-trail discrimination, language-coupled regex, sloppy substring match) with focused fixes and matching tests. Intelligence placement, contract clarity, regex hygiene, and test coverage are all where they should be.

The Stage-3 scope-of-change auto-diff is correctly kept in the prompt — both inputs are already in conversation context, the operation is one-shot per Update invocation, and lifting it to a script would add a round-trip for a comparison the LLM can do in one step. The equality rule wants pinning (S1, medium). Three very-low documentation polish items follow (S2 closed-set tabulation, S3 underscore-boundary comment, S4 ISO-8601 contract comment).

**Token savings:** ~4000-8000 per typical invocation vs a no-scripts variant (1500-3000 from discover, 1000-2000 per Mermaid block from validate-mermaid, 500-1500 per PRD shard from check-fr-coverage). Round 6 added no new scripts.

### Customization Surface

**Excellent.** `customize.toml` is unchanged since round 5 and remains right-sized — four well-shaped, fully-commented scalars (`business_flow_template`, `diagram_type`, `business_flow_output_path`, `on_complete`) with no boolean toggles. Posture: opted-in.

The three new round-6 headless flags were all correctly kept off the customization surface; the author has now resisted three plausible-but-wrong lifts in a row (mode toggle, language override, scope-of-change). The principle internalised: configuration is per-project policy, not per-run intent.

One concrete fix worth landing: the `fresh_reason` closed-set is enforced in the script but undeclared in the contract (medium-abuse). One low doc nit: the `reason` dual-write obligation is stated only on the SKILL.md side.

### User Experience

**Excellent.** All six user archetypes pass. First-timer gets the soft-landing 1b → 1e path with wrong-skill off-ramp protection. Expert wants Yolo and gets it when all four dimensions are explicit (one polish opportunity, F1, when one dimension is implicit). Confused user hits the wrong-skill off-ramp before any token-heavy elicitation. Edge cases all have named branches with closed-set audit signals (including the round-6 over-delivery of `stale_artifact` as a fourth Fresh sub-case). Hostile environment survives all named compaction windows except the narrow mid-1b window (F2). Automator gets the full 10-flag headless contract with audit-trail completeness.

All eight named facilitative patterns operational. Headless level: headless-ready.

## Trajectory

Seven rounds from initial scan to current state:

- **R1:** Good (2 broken + 12 opportunities)
- **R2-R3:** Convergence; R3 was Good with 0 broken + 9 themes
- **R4:** Closed all 9 R3 themes
- **R5:** Good ceiling — 0 broken + 1 high + 4 medium + 4 low + 4 carryover (13 items total)
- **R6:** Closed all 13 R5 findings; added one over-delivery (`fresh_reason: stale_artifact`)
- **R7:** **Excellent** — 0 broken + 0 high + 2 medium + 5 low, all polish-grade

The arc has the canonical shape of a skill that's been written by someone who internalised the principles file rather than treated it as a checklist. The pattern in the last three rounds — closed-set discipline on blocker reasons, three plausible-but-wrong customization lifts correctly resisted, intelligence placement on every new classifier, four-surface consistency on the U1/U2/`--update-flow` feature — is not accident. R7 finds no structural reason to hold below Excellent.

## Recommendations

1. **Add a `fresh_reason values` closed-set table to `references/headless-contract.md`** mirroring the existing blocker-`reason` table, naming all three values (`no_workspace`, `crashed_no_progress`, `stale_artifact`) and when each fires. Optionally add a third bullet at `SKILL.md:97-100`. Resolves 2 observations. Effort: low.

2. **Pin the `--scope-of-change=auto` equality rule** in both `SKILL.md:206` and `references/headless-contract.md:16` (recommended: unordered set-membership on stripped, lowercased strings). Add the F3 safe-default sentence: "if no prior flush block is parseable, treat as semantic." Resolves 1 observation. Effort: low.

3. **Polish commit covering the four remaining low/very-low items:** F1 one-line Yolo acknowledgement at `SKILL.md:130`, F2 brief 1b-reply flush, intent-comments on `\bprd\b` and the date-anchored regex in `discover-planning-artifacts.py`, and the symmetric dual-write note in `references/headless-contract.md`. Resolves 5 observations. Effort: low.
