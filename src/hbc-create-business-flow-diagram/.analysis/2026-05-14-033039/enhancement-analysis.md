# Enhancement Analysis — hbc-create-business-flow-diagram (Round 5, post-round-4 polish)

## Skill understanding

D-06 Business Flow Diagram generator (Mermaid sequence/flowchart/state) sitting between PRD and Architecture in the HBLab planning phase. Round 4 reorganised Stage 1 into 1a-resume → 1b-open-floor (with embedded wrong-skill off-ramp and 1e short-circuit) → 1c-consume → 1d-no-PRD-halt → 1e-defaults, lifted the parallel-lens menu to top-level once with cost/shape disambiguation, carved the headless contract to `references/headless-contract.md`, and tightened Stage 4 auto-fix to validator-emitted flags only. The scripts gained Japanese-PRD globs, sharded-PRD walking, repeated `--prd` arguments, per-issue `auto_fixable` flags, and a `--workspace` resume-state mode on the discover script.

## Round-3 findings — round-4 disposition (each finding, with evidence)

### High items (round 3) — disposition

**H1. `[A][P][C]` menu doesn't disambiguate "one deep lens" vs "three parallel lenses".** → **Resolved.** `SKILL.md:61-73` defines the menu once at top level under `## Parallel-lens menu`; `[A]` is labelled "single deep lens via bmad-advanced-elicitation. Cost: ~5 minutes. Current draft is preserved on cancel"; `[P]` is "three parallel lenses (analyst + architect + UX) via bmad-party-mode. Cost: ~15 minutes." Stages 3 and 4 cite back to the menu with stage-specific lens-targets (`SKILL.md:192,218`). Cost, shape, draft-preservation, and target all explicit. This is the cleanest fix in the round.

**H2. Resume-vs-Update branching unsafe with partial frontmatter.** → **Resolved.** `discover-planning-artifacts.py:170-181` now computes `recommended_intent` server-side using the testable cases: `not primary_exists` → Fresh; `steps == []` → Fresh ("crashed before any step write" — explicit code comment); `"stage-5" in steps` → Update; `"stage-1" in steps` → Resume; else Fresh. `SKILL.md:89-94` mirrors the rule in prose ("primary exists but `stepsCompleted` is empty (treat as crash-recovered scratch). Initialize from template"). Headless takes the same value (`SKILL.md:109` + `headless-contract.md` defaults row). The round-3 crash-recovery footgun is closed.

### Medium items (round 3) — disposition

**M1. `validate-mermaid.py` regex misses quoted aliases, `Note over`, activation prefixes.** → **Resolved.** `validate-mermaid.py:48-78` adds `DECL_RE` with `"(?P<quoted>[^"]+)"|(?P<bare>\w+)` quoted-or-bare alternation, a dedicated `NOTE_RE` whose targets count as "used" (`scripts/validate-mermaid.py:117-122`), and an `ACTIVATION_RE` that recognises `activate A` / `deactivate A`. Arrow regex supports `+`/`-` activation prefixes on both sides (`ARROW_RE` lines 57-64). Each issue carries `auto_fixable: bool` with the rule documented in the docstring (line 21). Stage 4 now consumes this flag explicitly (`SKILL.md:212-214`). Round-3 false-positive risk on legitimate Mermaid is closed.

**M2. `discover-planning-artifacts.py` English-only globs and symlink behaviour unspecified.** → **Resolved.** PRD globs (`discover-planning-artifacts.py:30`) now include `*要件定義書*.md`, `*要件*.md`, `*企画書*.md`; UX globs include `*画面*.md`; use-case includes `*ユースケース*.md`. Symlinks are no longer silently followed: `_unique_paths` (lines 46-57) deduplicates by `p.absolute()` not `p.resolve()`, the docstring spells out "do not resolve() — that follows symlinks silently", and each entry carries `is_symlink: bool` in the JSON (`_make_entry`, line 42). Tests verify the Japanese path (`test_discover-planning-artifacts.py:68-76`).

**M3. `check-fr-coverage.py` directory rglob pulls archived markdown.** → **Resolved.** `EXCLUDE_DIRS` (`check-fr-coverage.py:40-42`) prunes `archive`, `archived`, `old`, `notes`, `scratch`, `drafts`, `.git`, `node_modules`, `__pycache__` from the walk. Docstring (lines 16-18) spells this out. Still uses `rglob` for files, but the exclude-list is a real fix for the round-3 footgun.

**M4. Open-floor invitation present but doesn't short-circuit Stage 1e.** → **Resolved.** `SKILL.md:121-122` adds the explicit short-circuit clause: "if the open-floor reply already specifies mode, scope, sources, and diagram type unambiguously, log the inference to `.decision-log.md` and proceed directly to Stage 2 — skip the 1e confirmation block." See also Stage 1e's "(interactive only, unless short-circuited by 1b)" annotation at `SKILL.md:148`. The open-floor is now load-bearing — see new gap N3 below for the partial-reply edge.

**M5. Dated workspace folder fights resume.** → **Resolved.** `customize.toml:36` now defaults `business_flow_output_path = "{planning_artifacts}/business-flows/D-06-{project_name}/"` — no `{date}` segment. The opt-in for dated snapshots is documented in the same comment block (lines 31-35). Stage 1a binds `{doc_workspace}` to the single resolved path (`SKILL.md:81`), so the round-3 next-day-creates-new-folder bug is gone by default.

**M6. Stage 1b scan precedes intent gate; wrong-skill off-ramp fires too late.** → **Resolved.** Stage 1 reordered: 1a runs the discover script (with `--workspace` resume-state) but the user-facing intent gate plus wrong-skill off-ramp live in 1b, which fires "Before consuming the source inventory from 1a" (`SKILL.md:115`). Stage 1c is the consume step. The wrong-skill detection example is explicit: "the description trigger `'tạo sơ đồ'` / `'vẽ sơ đồ'` can match class-diagram, sequence-diagram-for-a-single-feature, or system-architecture intent" (`SKILL.md:117-119`). The scripted scan still runs in 1a (cheap, deterministic — no LLM token spend), but the intent-before-ingestion principle is honoured because the model commits to no work before the user can redirect. Pragmatic resolution of the round-3 ordering complaint.

### Low items (round 3) — disposition

**L1. Headless silently picks `[C]` for parallel lenses.** → **Resolved.** `--review-lenses=skip|advanced|party` added (`headless-contract.md:15`, defaults table line 26). JSON return contract carries `review_lenses_run: []` (`headless-contract.md:38-46`). `SKILL.md:63` cites the flag at the menu definition; Stage 5 logs `Lenses run` to the decision log (`SKILL.md:226`). Audit signal works.

**L2. Field-naming drift: `last_touched` vs `updated` vs `stage_2_actors`.** → **Resolved.** Decision-log template (`assets/decision-log-template.md:1-11`) now uses `updated: yyyy-mm-dd` and the same `stepsCompleted` / `inputDocuments` / `lastStep` / `mode` / `scope` / `diagram_type` set as the primary's frontmatter. Stage 2 flush still writes `stage_2_actors` / `stage_2_flows` but those are content fields, not state fields — a defensible separation. "One term per concept" honoured (Writing principle).

**L3. PRD-dir heuristic `"prd" in d.name.lower()`.** → **Open (low-impact).** `discover-planning-artifacts.py:228` is unchanged. `apprd/` would still match. The probability is low enough that this stays acceptable polish-grade — not flagged as regression.

**L4. `--prd-path` repeatable but discover script can't honour it.** → **Partially resolved.** `headless-contract.md:10` documents `--prd-path` as a SKILL.md-level flag, not a script-level flag — Stage 4's validator (`check-fr-coverage.py`) does accept repeated `--prd` arguments now. But Stage 1a's `discover-planning-artifacts.py` invocation has no path for "skip the glob; use these paths". A headless run with `--prd-path=X` still triggers the full filesystem glob in Stage 1a. The model is supposed to override the result, but the contract is not enforced by the plumbing.

### Still-open items from round 3

**SO1. Zero-actor PRD (data-pipeline / batch-only).** → **Still open.** Stage 2 (`SKILL.md:163-167`) lists "user roles, external systems, scheduled processes" — the scheduled-process hint is there, but no guidance on promoting a cron / event source to a first-class `actor` declaration. `validate-mermaid.py` still treats a `participant System` flow with only `System ->> System` arrows as syntactically fine, so the validator gives a vacuous pass on a shapeless diagram.

**SO2. Mistaken `--mode=migration` on greenfield PRD.** → **Still open.** Stage 2's "run discovery twice — once for AS-IS, once for TO-BE" (`SKILL.md:169`) will fabricate an AS-IS section if forced; nothing in headless checks "did the AS-IS half come back empty?" Reverse heuristic still absent.

**SO3. Update-then-update / targeted single-flow update.** → **Still open and worse on review (see new gap N1 below).** Round 4's `recommended_intent: Update` behaviour for "primary completed (`stage-5` in `stepsCompleted`)" doesn't disambiguate "small typo fix in Flow B" from "comprehensive re-run". Stage 3's "increment minor (`1.2` → `1.3`)" rule (`SKILL.md:188`) is correct for a single bump but breaks down on consecutive Update sessions started in the same calendar day (see N1).

## New gaps the round-4 polish introduced

### N1. High — Update-then-Update revision-history version bumping is undefined for back-to-back sessions

*Location.* Stage 3 (`SKILL.md:186-188`), `discover-planning-artifacts.py:170-181` (`recommended_intent` calculation), `headless-contract.md` defaults table.

*What I noticed.* `recommended_intent = "Update"` fires whenever `stage-5 in stepsCompleted`. The Stage-3 rule "read the latest version from the existing table, increment minor (`1.2` → `1.3`)" is correct in isolation. But consider:

1. Day-1 session: Fresh → version `1.0` written, Stage 5 completes, `stepsCompleted = [stage-1..5]`.
2. Day-1 second session (same day): user re-invokes to fix a typo. `recommended_intent = Update`. Stage 3 reads version `1.0` and writes `1.1`. Fine.
3. Day-1 third session (still same day): another typo. `recommended_intent = Update` again. Stage 3 reads `1.1` and writes `1.2`. Three revision-history rows for one calendar day, with three near-identical "Update" entries.

Real-world re-runs of fix-typo style are extremely common (the BA notices a Mermaid label is wrong; the architect during downstream Architecture work flags a missing actor). The skill produces a noisy revision history because there's no "scope-of-change" check. Worse: nothing prevents the user from running Update twice from a wrong intent — Stage 1a presents `[R] Resume / [U] Update / [V] Validate-only` and the recommended_intent is `Update`, so they take it. The result is `1.2` against an artifact that may not have changed meaningfully.

Round 3 flagged this loosely as "Update-then-update". Round 4 made it more concrete by hard-wiring `Update` as the recommendation for any completed primary, without a "did anything actually change?" gate. The version bump rule is now load-bearing on a model judgement that isn't called out anywhere.

*Suggestion.* In Stage 3 Update path, prompt the user (or headless: check `--prd-path` set vs unchanged source content) for "is this a semantic update (new flow / changed step) or a polish (typo / wording)?" Polish stays on the prior version row with an appended note; semantic changes bump. OR: only bump version when the discovery output (`stage_2_actors` / `stage_2_flows`) differs from the prior session's flush.

### N2. Medium — Stage 1b open-floor reply with partial coverage will be misread as "covers everything"

*Location.* `SKILL.md:121-122` (the short-circuit clause).

*What I noticed.* The clause reads "if the open-floor reply already specifies mode, scope, sources, and diagram type **unambiguously**, log the inference to `.decision-log.md` and proceed directly to Stage 2 — skip the 1e confirmation block."

The four-element "unambiguous" test sounds testable. In practice the model will pattern-match on something looser. Consider an expert reply like:

> "Use the PRD at `docs/prd-checkout-v2.md`, migration mode, three named flows: cart abandon, checkout retry, payment timeout."

This specifies sources (one path), mode (migration), and scope (multi — three named flows). It does *not* specify diagram type. A strict reading says "fall through to 1e to ask diagram type." A loose reading says "diagram type defaults to `{workflow.diagram_type}` = `sequenceDiagram`, ship it." Round 4's prose doesn't pick. If the model picks loose, an expert who genuinely wanted `flowchart` (because they're documenting decision branches in the checkout retry flow) is silently committed to `sequenceDiagram` and only finds out at Stage 3 when the rendered output is wrong-shaped.

The 1e confirmation block exists precisely to surface defaults the user might want to override. Short-circuiting it requires *all four* dimensions confirmed by the user, not three-out-of-four with a silent default for the missing one.

*Suggestion.* Tighten the short-circuit clause: "skip 1e *only when the open-floor reply explicitly addresses all four dimensions*. If any dimension is silent, present the 1e confirmation block but pre-fill the dimensions that were addressed and ask only about the remaining." This is a one-line clarification with material safety value.

### N3. Medium — `headless-contract.md` defaults table contradicts SKILL.md on `recommended_intent` semantics for Fresh

*Location.* `headless-contract.md:22` (defaults table row "Resume vs Update vs Fresh") vs `discover-planning-artifacts.py:170-181`.

*What I noticed.* The defaults-table row reads: "from `recommended_intent` in the discover script's `resume_state` output (Resume only when `stage-1` is in `stepsCompleted`; **Fresh when `stepsCompleted` is empty even if primary exists**)". The clause in bold is correct per the script and per `SKILL.md:91`. But the script treats `not primary_exists` and `steps == []` as two distinct conditions that both produce `Fresh` — there's no flag in the JSON saying "primary was found but discarded". In headless, the auto-decision log line will read `"recommended_intent: Fresh"` for both "no prior workspace" and "prior workspace existed but crashed before stage-1", which are very different recovery scenarios for an automator trying to audit.

The decision log doesn't distinguish either: `SKILL.md:111` says "log the auto-choice to `.decision-log.md`" but gives no hint that a partial workspace was just blown away as scratch.

*Suggestion.* Either (a) have the script emit `resume_state.discarded_partial: true` when primary existed but `stepsCompleted == []`, and require Stage 1a's headless log line to cite it; or (b) split `Fresh` into two reasons in `headless-contract.md` (`Fresh` vs `Fresh_after_crash_recovery`). The smaller fix is (a) — one new field, one log-line requirement.

### N4. Low — `headless-contract.md` mostly stays reference-shaped but the SKILL.md leak is minimal-but-real

*Location.* `SKILL.md:14` ("Stage 1 honours an input contract so automators can drive it deterministically — see [`references/headless-contract.md`](references/headless-contract.md) for the full flag set, defaults table, and JSON return contract") vs `SKILL.md:57-59` (`## Headless Mode` section).

*What I noticed.* `references/headless-contract.md` is correctly bounded: it's a table of flags + defaults + JSON shape + closed-set reasons. No procedural instructions ("first read X, then call Y"). That's reference-shaped, per the principles file's "carve to references/ when the section is a contract or reference table, not a procedure".

But the SKILL.md leak goes the other way: `## Headless Mode` (lines 57-59) repeats "`-H` / `--headless` runs without user prompts. The full contract … lives in [...]. Stages below cite that contract where each interactive decision has a headless default; the contract itself is the single source of truth." This is a three-line meta-explanation of a carve-out, which is the exact "meta-explanation of pattern" anti-pattern the principles file calls out under DLW treatment ("Do NOT: Write a separate `## Workspace` section header with meta-explanation of the pattern").

The principle generalises: don't write a `## Headless Mode` section that only explains a reference file exists. Either drop the section (the overview paragraph at `SKILL.md:14` already does the routing) or use it to actually express runtime behaviour ("headless mode is signalled by `-H`; every interactive prompt has a corresponding flag" — currently the section says nothing the contract file doesn't).

*Suggestion.* Delete `SKILL.md:57-59` entirely. The cross-reference at line 14 is sufficient; stages cite the contract where they need to.

### N5. Low — Decision-log template's `last_session_summary` extraction is fragile

*Location.* `discover-planning-artifacts.py:151-167` (the `## Session …` heading parser) vs `assets/decision-log-template.md:19` (the heading template).

*What I noticed.* The script regex (`^##\s+Session\s+([^\n]+)$`) expects "Session" as a literal English word. The template at line 19 starts the heading with `## Session yyyy-mm-ddThh:mm — {intent: Create | Update | Validate}` — which is *not* translated to `{document_output_language}` per the Language Rules (because the heading word "Session" is a control word for the script, like "AS-IS" / "TO-BE"). The skill says (`SKILL.md:27-29`) "When rendering an output document or decision log, translate all prose (section headings, table headers …)". This contradicts the implicit contract that the script depends on the English word "Session".

If the model follows the Language Rules literally, a Japanese-language project gets `## セッション ...` headings in `.decision-log.md`, and the next session's `_extract_resume_state` returns `last_session_summary: None` because the regex doesn't match.

The decision-log template itself is currently not in the list of carve-outs preserving English (Mermaid keywords, AS-IS / TO-BE) at `SKILL.md:29`.

*Suggestion.* Either (a) add "Session" (or the full date-stamped heading pattern) to the Language Rules' preserved-form list, or (b) make the script tolerant of localised headings by switching to a date-based anchor (`^##\s+.*?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}`). Option (a) is the smaller diff.

### N6. Low — Deleted `references/.decision-log.md` is cleanly gone; nothing in SKILL.md implicitly references it

*Location.* whole skill.

*What I noticed.* The round-3 architecture finding was that the build-time decision log was mis-placed in `references/`. Round 4 deleted it (confirmed: `references/` contains only `headless-contract.md`, `Bash ls`). No SKILL.md prose, no script comment, no test references the deleted file. Round 4 got this clean. Mentioned here because the round-5 brief asked specifically about it.

## Headless assessment

**Level: Headless-ready.** All round-3 headless gaps are closed:

- `--review-lenses` flag + `review_lenses_run` return field — audit signal works.
- Stage 4 auto-fix scoped to validator-emitted `auto_fixable: true` — auditable per-issue rationale via `fix_hint`.
- `recommended_intent` server-side from `resume_state` — testable in code.
- `--no-prd-ok` opt-in for greenfield-without-PRD.

Remaining headless gaps are the four items above (N1 worst-affects audit clarity; N3 minor signal loss).

The JSON return contract (`headless-contract.md:35-46`) is the smallest set of paths the caller needs plus `review_lenses_run`. The closed-set `reason` table (lines 58-69) covers six named failures including `resolver_missing`. This meets the principles-file standard: "the JSON return is the smallest set of paths the caller needs; the log carries the reasoning."

## Facilitative patterns check (delta from round 3)

| Pattern | Round 3 | Round 5 |
| --- | --- | --- |
| Open-floor opening | Present, non-consuming | Present, with short-circuit clause. N2 is the partial-reply edge. |
| Soft-gate elicitation | Missing at Stage 2 | Still missing at Stage 2. No "anything else before we draw?" gate after actor list. |
| Intent-before-ingestion | Partial (scan-first) | Resolved as a practical matter — scan is deterministic / no-token; the model commits to no work before user can redirect via 1b. |
| Capture-don't-interrupt | Missing | Still missing. Decision log is session memory, not a side-channel capture for stray Stage-2 observations. |
| Dual-output | Present (opt-in) | Same. |
| Parallel review lenses | Conflated `[A]`/`[P]` | Resolved. Single top-level menu with explicit cost/shape. |
| Three-mode architecture | Present | Same. Guided / Yolo (1b short-circuit) / Headless all named. |
| Graceful degradation | Improved | Round-4 restored the resolver hand-merge fallback at `SKILL.md:37` — a quiet but important round-3 regression-fix. Template-missing still HALTs. |
| Decision-Log Workspace — Resume | Resolved | Resolved + tightened. `recommended_intent` is server-side. |

## Findings (round 5)

| Severity | Location | Issue | Suggestion |
| --- | --- | --- | --- |
| High | Stage 3 Update path; `recommended_intent` for completed primaries | Back-to-back Update sessions bump `1.0` → `1.1` → `1.2` on cosmetic edits; no "did anything change?" gate (N1) | Add scope-of-change check (polish vs semantic) — polish stays on prior row; only semantic bumps version. Or auto-detect via Stage 2 flush comparison. |
| Medium | `SKILL.md:121-122` 1b short-circuit clause | Partial open-floor reply (three of four dimensions) will likely be read as "covers everything" with a silent default for the fourth (N2) | Tighten clause: skip 1e only when all four dimensions are explicit; otherwise pre-fill what was given and ask only the rest. |
| Medium | `headless-contract.md` defaults table vs script `recommended_intent` | `Fresh` collapses "no prior workspace" with "crashed workspace discarded" — audit-trail loses signal (N3) | Emit `resume_state.discarded_partial: true` and surface it in the headless decision-log line. |
| Low | `SKILL.md:57-59` `## Headless Mode` block | Three-line meta-explanation of the carve-out adds no runtime instruction; the principles file calls this anti-pattern out (N4) | Delete the block; the cross-reference at line 14 + per-stage citations are sufficient. |
| Low | `discover-planning-artifacts.py:154` Session heading regex vs Language Rules | Translated `## Session` heading in non-English projects breaks the resume-state extractor (N5) | Add "Session" to the preserved-English list at `SKILL.md:29` OR switch script to date-based anchor. |
| Low (still-open from R3) | Stage 2 + `validate-mermaid.py` | Zero-actor PRD produces shapeless diagram with vacuous validation (SO1) | One-line guidance: promote cron / event / batch trigger to first-class participant. |
| Low (still-open from R3) | Stage 2 migration path | `--mode=migration` on greenfield PRD fabricates AS-IS; no reverse heuristic (SO2) | If AS-IS half empty under forced migration mode, surface mismatch (interactive) or `blocked: mode_mismatch` (headless). |
| Low (still-open from R3) | Stage 1a Update mode | No targeted single-flow update path (SO3, distinct from N1) | Document or add `--update-flow=<name>` to scope Update. |
| Low (still-open from R3) | `discover-planning-artifacts.py:228` | `"prd" in d.name.lower()` matches `apprd/` etc. (L3) | Tighten to `\bprd\b`. |

## Excellent vs Good — verdict

**Good, very close to Excellent.** Round 4 closed five of the round-3 medium findings and both high findings. The remaining items are genuinely polish-grade: N1 is the only round-5 gap that could cause an audit-trail problem in production (cosmetic edits bump the version), but it doesn't block the workflow. N2-N5 are clarifications. SO1-SO3 are still-open edge cases inherited from round 3 with the same low impact as before.

What separates this from Excellent: the version-bump rule for Update-on-Update (N1) is now load-bearing on a model judgement the SKILL.md doesn't call out — that's the kind of silent default a future revision-history audit would expose. Closing N1 would push the skill to Excellent. N2 close-second.

## Top insights

1. **Round 4 did the hard work of cleaning up the round-3 ordering + silent-default theme.** Stage 1 reordering, short-circuit clause, `recommended_intent` server-side, dated-workspace default flipped, `--review-lenses` audit signal, parallel-lens menu disambiguation — these are all the round-3 calls. The remaining items cluster on a new theme: **state transitions on the second-and-later invocation**. Update-then-Update version bumps (N1), partial-open-floor reads (N2), crash-recovery vs no-prior collapse (N3), localised Session heading (N5). The first invocation is now textbook; the second-invocation ergonomics are where polish would land.

2. **The `references/headless-contract.md` carve-out is correctly bounded — it's a table, not a procedure.** No instructions leak into it, no "first do X" prose. The minor leak goes the other way: `SKILL.md:57-59` is three lines of meta-explanation about the carve-out's existence (N4). Deletable.

3. **The skill now has the canonical Decision-Log Workspace + headless contract + parallel-lens menu + open-floor short-circuit, all named and operational.** This is closer to `bmad-product-brief` shape than any of the round-1/2/3 iterations. The build pattern that worked: round 1 surfaced the framing gaps, round 3 surfaced the implementation gaps inside the framings, round 4 closed nearly all of them. The remaining round-5 list is what would normally be a `simplify` pass — minor language clarifications + one real risk on Update-then-Update version bumps.
