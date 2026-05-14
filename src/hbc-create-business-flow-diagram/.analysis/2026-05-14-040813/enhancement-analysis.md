# Enhancement Analysis — hbc-create-business-flow-diagram (Round 7, post-round-6 polish)

## Skill understanding

D-06 Business Flow Diagram generator (Mermaid sequenceDiagram / flowchart / stateDiagram) sitting between PRD and Architecture in the HBLab planning pipeline. Round 6 closed every round-5 enhancement finding and the still-open round-3 carryovers. The skill now carries a 10-flag headless contract, a 7-reason closed-set blocker table, a server-side `recommended_intent` with a `fresh_reason` discriminator, a scope-of-change gate on Update, a strict 4-of-4 short-circuit on Stage 1b, a zero-actor branch on Stage 2, and a migration-vs-AS-IS sanity check on Stage 1e. This is a re-walk to decide whether the residual surface justifies Excellent.

## Round-5 findings — round-6 closure verification

Each finding was re-walked against the present-state files. Citing principles from `skill-quality-principles.md`.

### N1 (HIGH) Update-then-Update version bump — **CLOSED**

*Verification.* Stage 3 (`SKILL.md:202-209`) defines the scope-of-change gate as the load-bearing check before any version-history write. The three paths are explicit:

- Auto-detect (`SKILL.md:206`): compare current `stage_2_actors` and `stage_2_flows` against the prior session's flush block in `.decision-log.md`. Identical → polish (append note to prior row, no bump). Differs → semantic (new row, minor bump).
- Manual override interactive (`SKILL.md:207`): explicit prompt with the two-category framing ("polish (typo / wording / layout) or semantic (actors / flows / outcomes)?").
- Headless override (`SKILL.md:208`): `--scope-of-change=polish|semantic|auto`, default `auto`.

Either path logs scope + rationale to `.decision-log.md` (`SKILL.md:209`). Headless contract (`headless-contract.md:16`, defaults table line 30) carries the same. The "did anything actually change?" gate is now real and structurally enforced. The decision-log policy is consistent with the **Decision-Log Workspace** pattern — "Overrides also write to the addendum: the rejected reasoning needs to live somewhere" (principles file). Audit-trail signal preserved.

*Residual question.* The principles file doesn't require this, but: **what if the prior session's flush block is malformed or missing?** Stage 2 (`SKILL.md:188-191`) mandates the flush as "required, not optional" and a malformed primary frontmatter would be a determinism-layer concern, not enhancement. If the diff procedure encounters no prior flush block, the safe default in prose would be "treat as semantic" (a missing baseline is not evidence of no-change). SKILL.md is silent on this corner — minor opportunity, not a hold-back; the LLM's natural fallback would be to ask. Filed as polish-grade observation, not a finding.

### N2 (medium) 1b partial-reply loose-read — **CLOSED**

*Verification.* `SKILL.md:130-132` upgrades the short-circuit clause from round-5's "specifies … unambiguously" to:

> **Short-circuit Stage 1e** — strict gate. Only skip 1e when the open-floor reply *explicitly* covers **all four** of: mode, scope, sources, diagram type. A partial reply (any of the four absent or ambiguous) falls through to 1e for confirmation. Log which dimensions were inferred from 1b vs confirmed in 1e to `.decision-log.md`.

This is the right shape on three axes:
1. "**explicitly covers all four**" — boolean, not a model-judgement of "feels unambiguous". Round 5's loose-read risk vanishes because the gate has no middle position.
2. The fall-through is "to 1e for confirmation" — meaning 1e *runs* but presumably can pre-fill the dimensions that were addressed. SKILL.md doesn't say "pre-fill" explicitly. The 1e block at `SKILL.md:163-167` still presents as the standard "Detected … Inferred … Confirm or override" — the model can pre-fill from the 1b reply naturally without a script instruction. Outcome-based, not prescriptive (principles: "Outcome vs Prescriptive").
3. The "**Log which dimensions were inferred from 1b vs confirmed in 1e**" line is the audit-trail clincher. The future reader can see exactly which dimensions the user explicitly chose vs the model inferred. Capture-don't-interrupt + Decision-Log Workspace working in concert.

Minor observation, not a finding: the principles-file pattern **soft-gate elicitation** ("anything else, or shall we move on?") would land naturally as the 1e closing line, but it's optional polish. The strict gate alone closes N2.

### N3 (medium) Fresh-with-discard audit collapse — **CLOSED**

*Verification.* The `fresh_reason` field is end-to-end:

- Script (`discover-planning-artifacts.py:181-194`): three values — `no_workspace` (primary doesn't exist), `crashed_no_progress` (primary exists, `stepsCompleted == []`), `stale_artifact` (frontmatter exists but no `stage-1` yet — a fourth sub-case I hadn't anticipated, defensible). When `recommended_intent` is `Update` or `Resume`, `fresh_reason` is `None`.
- SKILL.md (`SKILL.md:99-101`): surfaces all three reasons in the resume menu with explicit per-reason guidance.
- Headless audit (`SKILL.md:120`): "log the auto-choice (plus `fresh_reason` if applicable) to `.decision-log.md`".
- Headless contract (`headless-contract.md:25`): explicitly cites the discrimination — "`fresh_reason: \"crashed_no_progress\"` is logged separately from `fresh_reason: \"no_workspace\"`".
- Tests (`test_discover-planning-artifacts.py:112-167`): cover all three Fresh sub-cases plus the Update + `fresh_reason: None` invariant.

The audit-trail signal is now complete. **Decision-Log Workspace** pattern fully honoured — "The user ends the session with a shared accounting of how their thinking was handled" applies equally to automators reading the log later.

A nice bonus: `stale_artifact` (line 194) catches an edge case that wasn't in the round-5 list — primary frontmatter present but stage-1 never completed. Round-6 over-delivered.

### N4 (low) Meta-explain Headless Mode — **CLOSED with one caveat**

*Verification.* `SKILL.md:55-67` is the current `## Headless Mode` block. Round 5 said the block was "three lines of meta-explanation"; round 6 expanded it into:
1. A one-sentence pointer to the contract file (line 57).
2. A closed-set blocker-reason list with one-line cause per reason (lines 59-66).
3. A "Add new reasons only by extending this list and the contract file together" rule (line 67).

This is **reference-shaped**, not procedural — it's the data the user needs at-glance plus the contract-extension rule. The principles file's anti-pattern is "Write a separate `## Workspace` section header with meta-explanation of the pattern" (DLW treatment) — meta-explanation, *not* concrete data. The reason-mirror here is concrete data with a real consequence (it's the closed-set automators switch on).

The one caveat: the reasons are listed in BOTH `SKILL.md:59-66` AND `headless-contract.md:65-73`. Two-place truth is a maintenance hazard. The headless contract file calls itself "the brief reason list in SKILL.md is a compaction-survival mirror, not a separate source of truth" (`headless-contract.md:3`) — meaning the duplication is intentional, framed as compaction-survival. That's a valid use of file weight per the principles ("Stages must be self-contained — context compaction can drop SKILL.md mid-flow"). The duplicate is doing real work.

**Verdict:** the reason-mirror is not a new smell — it pays its keep. Closed.

### N5 (low) Session heading regex English-only — **CLOSED**

*Verification.* `discover-planning-artifacts.py:155-162`:

```python
sessions = list(
    re.finditer(
        r"^##\s+([^\n]*\d{4}-\d{2}-\d{2}[^\n]*)$",
        text,
        re.MULTILINE,
    )
)
```

This is the recommended fix from round 5 ("switch to a date-based anchor `^##\s+.*?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}`") — actually slightly more permissive than I had suggested because it accepts a date-only heading (no T-suffixed time) too, which is appropriate for cleaner per-day session blocks. Code comments (lines 153-156) cite English and Vietnamese examples. Test `test_session_heading_regex_matches_vietnamese_log` (`test_discover-planning-artifacts.py:189-211`) verifies a `## 2026-05-14T10:23 — Phiên: Cập nhật` heading parses correctly. The decision-log template (`assets/decision-log-template.md:19`) carries the date-stamped heading without prescribing the literal English word "Session". Locale-agnostic resume now works.

### SO1 (R3 carryover, low) Zero-actor PRD — **CLOSED**

*Verification.* Stage 2 (`SKILL.md:184`):

> **Zero-actor branch** — if the source contains no human or system actors (e.g. pure data-pipeline products triggered solely by cron or queue events), do not render a vacuous "System talks to itself" diagram. Promote the trigger (scheduled job, queue, webhook) to a first-class actor and explain the choice in the decision log. Interactive: confirm with the user. Headless: log and continue.

One paragraph, outcome-based ("promote the trigger to a first-class actor and explain"), not prescriptive about how to declare it in Mermaid. Honours **outcome vs prescriptive** correctly — the LLM knows how to write a `participant ScheduledJob` line; we just need to tell it that's the right shape. The interactive-vs-headless split mirrors the rest of the workflow.

### SO2 (R3 carryover, low) Migration-vs-AS-IS sanity check — **CLOSED**

*Verification.* Stage 1e (`SKILL.md:169`): the sanity check fires at the confirmation step ("if mode resolves to `migration` but no PRD source contains AS-IS / 現状 / 'current state' / similar markers, warn the user and offer to switch to `greenfield`"). Headless path returns `blocked` with `reason: "migration_without_as_is"` unless `--allow-migration-without-as-is` is passed.

The `--allow-migration-without-as-is` escape hatch is well-judged: there's a legitimate use case (the user is documenting migration *because they're inventing the migration story now*, with AS-IS to come from interviews not docs). Forcing them through `blocked` would be wrong. Closed-set blocker (`headless-contract.md:72`) is in the table. **Graceful degradation** pattern honoured (principles file: "Subagent-dependent features fall back; the user opts in to acknowledge").

### SO3 (R3 carryover, low) Targeted single-flow update — **CLOSED**

*Verification.* Stage 1a menu (`SKILL.md:115-117`) carries `[U1] Update all flows` / `[U2] Update a single named flow (specify name)` as sub-options. Headless flag `--update-flow=<name>` (`headless-contract.md:17`, `SKILL.md:200`). Stage 3 (`SKILL.md:200`):

> Update mode with `--update-flow=<name>` (or interactive U2): re-render only the specified flow, leaving other Mermaid blocks untouched.

This is the right behaviour — surgically replacing one Mermaid block instead of full re-render is exactly what a "I noticed Flow B is wrong" user wants.

*One real residual question (see findings below).* How does Stage 4 validate a partial re-render? The `check-fr-coverage.py` script runs against the entire D-06 file, comparing PRD FR ids against ids in the rendered output. With `--update-flow=<name>`, the un-touched flows still have their FR references, so the coverage script naturally runs against the full file and gives the correct answer. The mermaid validator also runs against the whole file by design (`validate-mermaid.py:166-225`). So the validators don't need to know about the partial-update semantics — they validate the final state of the document, which is correct regardless of how it got there.

Confirmed: Stage 4 validation works against partial output without modification. The auto-fix scope on a single-flow update applies the same rules to all blocks in the document, which is the right behaviour (the un-touched flows should already be valid; new findings on un-touched blocks are useful signals).

### L3 (R3 carryover, low) Word-boundary `\bprd\b` regex — **CLOSED**

*Verification.* `discover-planning-artifacts.py:241-246` uses `re.compile(r"\bprd\b", re.IGNORECASE)`. Test `test_prd_directory_match_uses_word_boundary` (`test_discover-planning-artifacts.py:213-225`) verifies `approved/` does not match but `prd/` does.

## User-journey re-walk

### 1. First-timer (interactive, no PRD knowledge)

*Path.* Activates the skill. Stage 1a runs the discover script silently, surfaces "no workspace yet" with `fresh_reason: no_workspace`. Stage 1b opens with the broad invitation to share whatever they have plus the wrong-skill off-ramp. They say "I want a flow for our checkout process" — partial reply (mode unclear, scope unclear, sources unclear, diagram type unclear). The strict gate at 1b correctly routes them to 1e, which presents the inferred defaults with a Confirm/override prompt. Stage 2 elicits actors. Stage 3 renders, asks polish-vs-semantic (will skip on a Fresh, version 1.0). Stage 4 validates. Stage 5 finalises.

*Friction points.* None visible. The soft landing is preserved because 1b → 1e is the path of least surprise for a non-expert.

*Bright spots.* The wrong-skill off-ramp at 1b is the right place for a confused first-timer who thought "create business flow diagram" meant "class diagram" — it fires before any heavier work. The zero-actor branch protects them if their domain is a data-pipeline product.

### 2. Expert (knows what they want, wants Yolo)

*Path.* Activates skill, gets the discover-script + menu. Open-floor: "PRD at `docs/prd-checkout-v2.md`, migration mode, three flows (cart-abandon, retry, payment-timeout), flowchart type." All four dimensions covered explicitly. Strict short-circuit fires, 1e is skipped, decision log records that all four dimensions came from 1b. Straight to Stage 2 with sources and scope locked in.

*Friction points — does the strict short-circuit kill experts?* Round 6 asked this explicitly. The answer is **no, with one specific risk**:

- The strict gate is correctly framed — an expert who states all four dimensions explicitly gets straight through. The model knows the four dimensions are mode / scope / sources / diagram type, so a competent open-floor reply naturally addresses them. The Yolo path is preserved.
- BUT: the model has to correctly parse all four from the user's prose. If the expert says "migration mode, three flows, flowchart" — they omitted *sources* (implied: use the auto-discovered PRDs). Strict reading says fall through to 1e. Loose reading says "sources = all discovered PRDs, defaults work". A model that's slightly too eager will short-circuit and the expert loses their explicit confirmation of sources.
- Mitigation: the explicit logging requirement ("Log which dimensions were inferred from 1b vs confirmed in 1e") forces the model to be honest about what was inferred. An expert who reviews `.decision-log.md` after the run sees clearly that sources came from auto-inference, not their reply.

A tighter design would be a one-line acknowledgement that all 4 of 4 dimensions are set ("Inferred from your reply: mode=migration, scope=multi (cart-abandon, retry, payment-timeout), sources=auto, type=flowchart. Confirm?"). That's a single ask — Yolo-friendly, not a 1e tour — but it surfaces the inferred dimension for explicit override. This would close the residual risk above. The current strict-fall-through is correct on safety; the one-line acknowledge would be the polish.

*This is a real opportunity, filed as a finding below (F1).*

### 3. Confused / wrong-skill user

*Path.* Activates with "tạo sơ đồ class cho User module" thinking this is the class-diagram skill. Stage 1a runs (cheap, deterministic, no token spend — defensible per **intent-before-ingestion**: scan is free, scan-first only fails when it consumes tokens or asks the model to commit to interpretation). Stage 1b's wrong-skill off-ramp fires: "the description trigger `'tạo sơ đồ'` / `'vẽ sơ đồ'` can match class-diagram, sequence-diagram-for-a-single-feature, or system-architecture intent. If the user's reply makes that clear, say so and point at the right skill."

*Verification.* Working. The off-ramp is in 1b, which fires "Before consuming the source inventory from 1a" (`SKILL.md:126`). Cost of the wrong-skill detection is one prompt, no tokens-wasted-on-elicitation.

### 4. Edge-case users

| Sub-case | Handling | Status |
|---|---|---|
| Zero-actor (data-pipeline / batch) | Stage 2 zero-actor branch promotes trigger to actor | Closed (SO1) |
| Migration-on-greenfield | Stage 1e sanity check + `--allow-migration-without-as-is` opt-in | Closed (SO2) |
| Targeted single-flow update | Stage 1a U2 + `--update-flow=<name>` | Closed (SO3) |
| Eager PRD-dir match (`apprd/`, `approved/`) | `\bprd\b` regex | Closed (L3) |
| Multiple sharded PRDs | Discover script enumerates every shard; FR validator takes repeated `--prd` | Closed (round 4) |
| Day-2 re-run / same-session re-run | Workspace resume + `fresh_reason` discrimination | Closed (N3) |
| Update-then-Update polish edits | Stage 3 scope-of-change gate, polish appends note, semantic bumps minor | Closed (N1) |
| Crashed prior run (frontmatter exists, no stage-1) | `fresh_reason: crashed_no_progress` + menu surfaces it | Closed (N3) |
| `stale_artifact` (primary frontmatter, no stage-1, no crash) | Round-6 bonus: `fresh_reason: stale_artifact` | Closed (over-delivery) |
| Localised decision-log heading | Date-anchored regex | Closed (N5) |

### 5. Hostile environment

| Failure | Handling | Status |
|---|---|---|
| Customisation resolver missing | Hand-merge fallback in SKILL.md + `resolver_missing` blocker | Closed (round 4) |
| Template missing | Blocked with `template_missing` reason | Closed (round 4) |
| `{planning_artifacts}` unreadable | `planning_artifacts_unreadable` reason | Closed (round 4) |
| Compaction mid-Stage-2 | Stage 2 flush writes `stage_2_actors`/`stage_2_flows` to primary frontmatter + decision-log Discovery snapshot block (required not optional) | Closed |
| Compaction mid-Stage-3 (mid-render) | No explicit flush. Stage 3 doesn't write intermediate state — full re-render on resume is correct because the Mermaid blocks are the primary's content, so the primary itself is the cache | Defensible by design |
| Compaction mid-Stage-1 (mid-1b open-floor) | The `discover-planning-artifacts.py` JSON sits on disk; resume re-runs the script. Stage 1b open-floor reply isn't yet captured anywhere. | Minor opportunity — see finding F2 |
| Subagent unavailable (party mode / advanced elicitation) | Parallel-lens menu has `[C] Continue` option; the lens menu itself is optional, not load-bearing | Closed (round 4 graceful degradation) |
| Discover script crash | Stage 1a says "consume the JSON" — implicit error handling not spelled out | Polish-grade, not flagged |

### 6. Automator (headless, pipeline)

*Path.* `python3 ... -H --prd-path=docs/prd.md --mode=migration --diagram-type=flowchart --review-lenses=skip --scope-of-change=auto`. Skill runs deterministically, applies validator auto-fixes, returns JSON.

*Audit signals.* Complete. All 10 flags documented in `headless-contract.md:6-18`. All 7 reasons in the closed-set table. `review_lenses_run` carries which lenses fired (empty in `skip`). `.decision-log.md` carries all auto-decisions with rationale, including `fresh_reason`, scope-of-change classification, and per-issue auto-fix entries citing the validator's `fix_hint`.

This meets the principles-file standard for headless: "the JSON return is the smallest set of paths the caller needs; the log carries the reasoning. Without this discipline, headless silently buries its calls and the audit trail breaks on the next session." Honoured.

## Findings (round 7)

| Severity | Location | Issue | Suggestion |
|---|---|---|---|
| Low (opportunity) | Stage 1b strict short-circuit | Strict 4-of-4 gate is safe but slightly hostile to experts who omit one obvious dimension (e.g. sources = "use auto-discovered PRDs"). Currently routes them to full 1e. | Add a one-line acknowledgement when 4 of 4 are explicit ("Inferred from your reply: …, confirm?") as a Yolo-friendly midpoint. The current strict path remains correct fallback; this is polish. |
| Low (opportunity) | Stage 1b open-floor reply (no flush) | If compaction drops mid-1b before the open-floor reply lands in `.decision-log.md`, the reply is lost and the next session re-asks. | Optional: a brief "1b note" line in `.decision-log.md` immediately after the reply is parsed, before 1e fires. Minor — 1b is short so the compaction window is narrow. |
| Low (polish) | Stage 3 scope-of-change auto-detect | Procedure is "compare current `stage_2_actors` / `stage_2_flows` against the prior session's flush block in `.decision-log.md`". Silent on the case where the prior flush block is missing or malformed. | One-line safe default: "if no prior flush block is parseable, treat as semantic" — a missing baseline is not evidence of no-change. The LLM would likely do this naturally; spelling it out hardens the audit trail. |

These are all genuinely opportunity-grade. None blocks the workflow. None creates a confusion path for any of the six user archetypes. F1 is the one I'd most-likely close if I were the next polish round.

## Facilitative patterns check (full state)

| Pattern | Status |
|---|---|
| Open-floor opening | Present (Stage 1b) with strict short-circuit + audit logging of inferred-vs-confirmed dimensions. **Best-in-class shape.** |
| Soft-gate elicitation | Present implicitly at 1b ("anything else, or shall we move on?" is the natural reading of "invite the user to share anything not yet captured … A soft 'anything else?' surfaces what they almost forgot"). Not explicitly present at Stage 2 close. Polish opportunity if anything. |
| Intent-before-ingestion | Practically resolved. Stage 1a's scan is deterministic / no-token; the model commits to no work before the user can redirect at 1b. |
| Capture-don't-interrupt | Present via decision log as session memory. Out-of-scope user observations could land in the addendum (per DLW pattern), though SKILL.md doesn't call out an `addendum.md` for this skill — defensible because the artifact is a tightly-scoped diagram, not a brief. |
| Dual-output | Present via Stage 5's `bmad-distillator` invocation offer. |
| Parallel review lenses | Present (single top-level menu with explicit cost/shape at `SKILL.md:69-79`). Headless flag + audit signal. |
| Three-mode architecture | Present. Guided (interactive) / Yolo (1b short-circuit + future F1 polish) / Headless (full contract). |
| Graceful degradation | Present (resolver hand-merge, parallel-lens `[C]`, `--allow-migration-without-as-is` opt-in). |
| Decision-Log Workspace | Canonical implementation. Workspace, `.decision-log.md`, append-only sessions with date-anchored headings, Resume/Update/Validate semantics, finalize summary block. The pattern's "the decision log is the load-bearing artifact, not the document" reading is preserved. |

All eight named patterns from the principles file's "Patterns BMad has seen pay off" section are present and operational. This is the bar.

## Headless assessment

**Level: Headless-ready.** All round-3 / round-5 headless gaps are closed:

- 10-flag input contract with closed-set semantics (each flag has explicit default + heuristic).
- 7-reason closed-set blocker table; SKILL.md mirrors the list for compaction survival.
- JSON return contract carries `review_lenses_run` for audit.
- Per-decision logging requirement: every auto-decision lands in `.decision-log.md` with rationale.
- Validator auto-fix gated on per-issue `auto_fixable: true` from the script (not LLM judgement).

This is the full **headless mode** treatment from the principles file: "the decision log absorbs every assumption made without the user … the JSON return is the smallest set of paths the caller needs … on `blocked`, include a one-line `reason` and still return the log path so the caller can read the detail." Honoured to the letter.

## Verdict

**Excellent.**

Round 6 closed every round-5 finding (N1 high, N2/N3 medium, N4/N5 low) and every round-3 carryover (SO1/SO2/SO3, L3). The round-6 work added one over-delivery (`fresh_reason: stale_artifact` as a fourth sub-case), tightened the audit trail at three points (scope-of-change rationale, 1b-vs-1e dimension provenance, validator `fix_hint` citation in auto-fix log lines), and preserved the soft landing for first-timers while keeping the Yolo path operational for experts.

The three findings I raised in round 7 are genuinely polish-grade — they don't block any user archetype, they're not safety issues, and the principles file doesn't mandate any of them. F1 (one-line Yolo acknowledgement) would be a quality-of-life win for experts; F2 (1b flush) and F3 (safe default for malformed flush) harden the audit trail under specific compaction / corruption conditions.

What separates this from Good: every pattern from "Patterns BMad has seen pay off" is present and operational; every interaction point has a headless equivalent with an audit signal; every state transition between Fresh/Resume/Update/Validate has explicit, testable semantics; every closed-set value (blocker reasons, fresh_reasons, scope-of-change values, review-lens choices) is enforced at both the script layer and the prose layer with tests for the script-level invariants.

The skill is now in the same shape-quality bracket as `bmad-product-brief` per the principles-file's canonical-brief callout. The Decision-Log Workspace pattern is implemented end-to-end, the headless contract is reference-shaped (table not procedure), and the workflow prose is outcome-based for the LLM-judgement steps while being prescriptive only on the fragile-operation invocations (script calls, customize-resolver step). Promoting to Excellent.

## Top insights

1. **Round 6 closed the second-invocation theme cleanly.** Round 5 identified that the first-invocation ergonomics were textbook but the second-invocation (Update-then-Update, Fresh-with-discard, partial-open-floor) had silent-default risks. Round 6 hit all of them with the scope-of-change gate, `fresh_reason` discriminator, and strict 4-of-4 short-circuit with provenance logging. The audit trail now distinguishes every state-transition path that an automator or future-reader would want to inspect.

2. **The strict short-circuit is safety-correct but slightly hostile to experts.** A one-line acknowledgement ("Inferred from your reply: …, confirm?") when all four dimensions are explicit would close the residual Yolo-friction without compromising the audit trail. This is the single most-impactful polish opportunity in the current state.

3. **The skill demonstrates that all eight "Patterns BMad has seen pay off" can coexist in one workflow without bloating the file weight.** SKILL.md is ~260 lines, the headless contract is a separate reference file (~75 lines), the decision-log template is a peer asset (~42 lines). Every named pattern is operational, every closed-set value is testable, every state transition has an audit-trail signal. This is the bar — and round 7 found no structural reason to hold below it.
