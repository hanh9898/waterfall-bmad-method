# Gate Semantics — correctness, adversarial QUALITY, sign-off, waivers, autonomy

Loaded by `hbc-phase-gate` SKILL.md. The cardinal sin of a gate is a **false PASS**
(the RCA case passed a Phase-2 gate whose evaluator had crashed and whose matrix was
missing REQ-040/041/042). Never go green on un-computed, ambiguous, or unadjudicated
evidence.

## Verdicts

- **PASSED** — every `required=yes` item is PASS or `NA` (and, for Phase 1/2, the B6-5 sign-off is recorded).
- **FAILED** — any `required=yes` item FAILs.
- **CONTESTED** — no FAIL, but a required item the evaluator can't resolve (ambiguous metric, unresolvable matrix source) or two QUALITY lenses disagree. Blocks; a human adjudicates. Never an auto-pass.
- **WARNING** — lenient mode downgrade of a FAILED gate, **non-correctness items only**.
- **BLOCKED** — evaluator crashed / un-runnable. Never a PASS.

`gate_mode` `lenient` downgrades FAILED→WARNING **except**: entry-gate items
(`summary.entry_gate_failed > 0`), all other correctness items
(`summary.correctness_failed > 0`), and CONTESTED items — these block in either mode.
Lenient relaxes thoroughness, never factual correctness.

## Correctness items (B6-3 extend · T2.7)

A **correctness item** is one whose FAIL means the artifacts are factually wrong /
inconsistent, not merely thin. The script classifies them (`_is_correctness_item`):
- **entry-gate** — a required CONTENT check that a PRIOR phase gate PASSED;
- **`[MATRIX]`** — every required matrix-completeness check;
- any required item the author tags **`[correctness]`** in its description or criteria cell (e.g. a MODEL_DRIFT-clean QUALITY item).

Correctness FAILs are never downgraded by lenient mode and never silenced by a waiver.

## A9 matrix-completeness — `[MATRIX]`, script-computed (B6-2 · T1.5)

`[MATRIX]` items reuse the shared `missing_from_matrix` / `matrix_coverage_gaps`
primitives. The `artifact_pattern` is the per-feature matrix; the criteria cell names
the D-02 source and optional columns:

```
d02={output_folder}/features/{feature}/planning-artifacts/D-02-* cols=design_ref,code_ref,test_ref
```

The script computes `traced/total`, `missing_from_matrix`, and `coverage_gaps` — these
are the numbers the gate reports (**never an LLM-claimed count**). FAIL when any REQ is
missing a row or has a blank ref. If no D-02 source resolves, the item is CONTESTED
(can't establish the REQ universe) — never a silent pass.

## Robustness (B6-6 · T1.6)

- **Crash → BLOCKED.** The evaluator wraps `main()` in a last-resort catch that emits `{"status":"BLOCKED","reason":"evaluator_crashed"}` and exits non-zero. A crashed gate never yields exit 0. If you can't run the script at all, the gate is BLOCKED — do not hand-wave a pass.
- **Ambiguous → CONTESTED.** A required `[METRIC]` whose number can't be extracted returns CONTESTED, not a silent SKIP/PASS.
- **Manual fallback** is only for a *recoverable* failure you can fully reproduce by hand. A manual PASS over a crashed correctness check is the RCA false-pass — never do it.

## B6-1 adversarial QUALITY

For every `required=yes` QUALITY item, evaluate with two lenses, each backed by
quantitative evidence (counts/IDs, not adjectives):
- **skeptic** — hunts for gaps, missing facets, unmet NFRs;
- **acceptance** — does the artifact meet its stated intent?

PASS only when both agree. **Disagreement → CONTESTED** (carry both summaries) — never
silently resolve to PASS. Interactive: surface to the user. Headless: include both in
the JSON. `{workflow.quality_parallel_review}` only toggles whether this is also logged
as a parallel pass; the two-lens discipline applies to required QUALITY items regardless.

## B6-5 design-phase sign-off (T2.6)

A Phase 1 or Phase 2 PASS additionally requires explicit **USER sign-off** — the design
is a human commitment, not just structurally complete. Present the evidence, ask the
user to confirm, record the sign-off in the report decision section.
- Headless `--assumptions-allowed`: a clean-but-unsigned design gate returns `PASSED_PENDING_SIGNOFF` (not a clean PASS), never blocking the first turn.
- Headless `--strict`: blocks for the sign-off.
- De-ceremony counterweight (RM.3): when D-02 frontmatter `maturity: exploratory`, this sign-off relaxes to a lightweight acknowledgement.

## Waiver (B6-4 · T2.7)

`--na D-NN` may skip an **inapplicable** deliverable (only the applicable-if D-19/D-21),
and the D-02 frontmatter must carry a one-line rationale per waiver. A waiver may
**never** silence a correctness item — the script reports `waiver_rejected` and still
evaluates it. A waiver with no deliverable+rationale, or aimed at a correctness item, is
invalid.

## Autonomy (A5 · T2.1)

Separate **mechanical** from **domain** decisions. Mechanical — path resolution, running
the evaluator, formatting, counting — decide and proceed. **The verdict is mechanical and
non-negotiable: a failed/CONTESTED correctness item BLOCKS, full stop.** Never soft-pedal
a real gap into a pass.

The one genuine **domain** decision is **whether a surfaced gap is a deliberate,
acceptable deferral** vs a real omission, plus the B6-5 sign-off call. **ASK; never
fabricate that a gap is "fine" to make the gate green.** A confirmed deferral becomes an
explicit rationale-bearing waiver (and may not touch a correctness item).

Headless (the CI default must NEVER fabricate a PASS):
- `--strict` — stop at the first possible-deferral / sign-off and return `blocked` with the question.
- `--assumptions-allowed` (CI default) — treat every surfaced gap as real (safe non-green default), log that no deferral/sign-off was confirmed, return the honest verdict (`FAILED`/`CONTESTED`, or `PASSED_PENDING_SIGNOFF` for a clean-but-unsigned design gate) rather than blocking. CI never gets a false green.

## Forward-refs (advisory touchpoints — engines not built here)

Wired as advisory notes the gate surfaces; the enforcing engines land in later units.
- **A2/A8 STALE + auto-revalidate** — stale upstream-version citations are already flagged (`check-version-coherence.py`). Advisory; the live dirty-set + auto-revalidate is interim (T2.4) and **spike TA.1 will replace** it.
- **A4 ADR-gate** — open `ADR`/`TBD`/`[NEEDS CLARIFICATION]` markers should block "complete"; note them. Full ADR engine is **T2.5**.
- **Maturity-gating** — read the catalog maturity modifier (`hbc-shared/references/deliverable-catalog.yaml`): `exploratory` may downgrade non-core required→optional and relax B6-5 sign-off, but the **correctness floor (matrix/model/entry-gate) is INVARIANT**. Apply only the sign-off relaxation here as advisory; full ceremony-gating is **T3.16**.

## Trục-A outcome: two-stage gate + RECYCLE (TA.3 — built)

Spike TA.0 passed (GO), so the RECYCLE outcome is now built in `scripts/gate-outcome.py`:

- **Stage 1** = the checklist evaluator (this file's rules) — "are this phase's own artifacts OK?"
- **Stage 2** = the TA.1 build-graph `dirty_set` over the feature — "is any artifact this phase depends on stale?"
- **Outcome state-machine:** `BLOCKED` (stage-1 crash, OR recycle loop-cap hit) → `RECYCLE→phase-(n−k)` (an earlier phase owns the earliest dirty upstream — hand control back there, not a flat FAIL) → `FAIL` (local failure, no dirty upstream) → `PASS` (stage-1 PASS and no dirty upstream). A crash is never a PASS; `--recycle-cap` bounds the loop (exceed → BLOCKED/escalate).
- Recycle target = the **lowest** owning-phase number among dirty nodes strictly upstream of phase N (earliest = root cause).

## Trục-A: 2-tier verdict (TA.4 — built)

Checklist items split into two **tiers**, computed by `scripts/gate-tier.py` over the
evaluator JSON (the evaluator itself is untouched):

- **MUST (knockout)** — every correctness item (entry-gate · `[MATRIX]` · `[correctness]`-tagged) **and** every `required` item. ANY must-FAIL is a **knockout → gate FAILED**, full stop; a must-CONTESTED → CONTESTED; a must-BLOCKED → BLOCKED. This is the existing knockout behaviour, now made explicit per tier — the knockout set never shrinks vs U16, so a SHOULD-fail can never demote a MUST.
- **SHOULD (scorecard)** — non-required, non-correctness items. **Scored** `passed/total` over only the items actually evaluated to PASS/FAIL (PENDING_LLM / NA / SKIP / CONTESTED excluded from the denominator — an un-judged or waived should is not a failure). A low scorecard **does NOT hard-block**: in `lenient` mode a ratio below the floor (default 0.8) surfaces a **WARNING**; in `strict` a clean knockout is simply PASSED regardless of the scorecard.

`gate-tier.py` emits `{tier_verdict, knockout, scorecard}`. Verdict precedence honors U16:
**BLOCKED**(must) > **FAILED**(must knockout) > **CONTESTED**(must) > **WARNING**(should below floor, lenient only) > **PASSED**. The `knockout.status` (`PASSED`/`FAILED`) is the authoritative **stage-1 status** fed to `gate-outcome.py`; the full tier dict rides in the outcome `tier` field for the report. Run: `python3 scripts/gate-tier.py <eval-results.json> [--gate-mode lenient] [--should-floor 0.8]`.

## Trục-A: circuit-breaker on blown appetite (TA.8 — built)

When the recycle **loop-cap is hit** (`gate-outcome.py` reason `recycle_cap_exceeded`) the feature has **blown its appetite** — it keeps recycling to the same earlier phase yet the upstream stays dirty. Instead of a silent dead-end BLOCKED, the outcome now carries a **`circuit_breaker`** decision surface with three options:

- **re-slice** — break the feature into smaller, independently-convergent slices (the stuck upstream likely spans too much scope);
- **defer** — park the feature out of the active loop so it stops burning recycles;
- **kill** — stop work; repeated failure says the cost exceeded the appetite.

It is a **RECOMMENDATION, not an action** (`decision: "user"`): the gate offers the options + a non-binding default leaning (broad dirty upstream → re-slice; single stuck node → defer) and the **user decides**. It triggers ONLY on a genuine cap-hit with dirty upstream — never on a normal RECYCLE (below cap), a local FAIL (no dirty upstream), or a stage-1 crash (which BLOCKS first as a crash, not a blown appetite). Deterministic; the outcome stays BLOCKED so CI never reads it as green.
