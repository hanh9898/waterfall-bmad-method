# Determinism & Distribution Analysis — Round 3 (post-refactor)

Target: `hbc-create-business-flow-diagram`
Scanner: L2 (intelligence placement, distribution)

## Existing scripts inventory

| Script | Stage | Role |
|---|---|---|
| `scripts/discover-planning-artifacts.py` | 1b pre-pass | Globs PRD/UX/use-case/research under `{planning_artifacts}`, classifies whole-doc vs sharded PRD, enumerates shard set from `index.md` markdown links (fallback: dir glob), checks `business_flow_template` existence. Emits compact JSON. |
| `scripts/validate-mermaid.py` | 4 | Extracts ```mermaid blocks; parses `participant`/`actor` declarations + arrow lines; reports `undeclared_participant`, `orphan_declaration`, `missing_expected_actor`, `no_mermaid_blocks`. |
| `scripts/check-fr-coverage.py` | 4 | Regex-extracts FR-/NFR-* IDs from one-or-more PRD inputs (file or directory; rglob if dir) and from the D-06 output, returns covered / uncovered / phantom set diff. |

No other prompt files at skill root; `references/` is empty (everything lives in SKILL.md — fine at ~260 lines).

## Assessment

Intelligence placement is sound. The three scripts stay strictly in the plumbing lane (glob, regex extract, set membership) and SKILL.md consumes their JSON outputs by name (`artifacts.json`, `.scan/mermaid.json`, `.scan/fr.json`). The round-1 finding "PRD/UX/research discovery done in-prompt" is resolved — SKILL.md §1b explicitly says "Trust its output instead of re-globbing" and the only remaining prompt-side glob language refers to `persistent_facts` (orthogonal). No prompt-side "for each shard, read…" loop survives. Stage 4 validation cleanly splits deterministic checks (script) from judgment checks (layout readability, AS-IS/TO-BE delta clarity, language consistency) — the principles file's script-vs-prompt boundary is respected line-for-line.

## Script-quality findings (the three new scripts)

### S1 — All three scripts missing PEP 723 metadata block (severity: medium)

**Files:** `scripts/discover-planning-artifacts.py:1`, `scripts/validate-mermaid.py:1`, `scripts/check-fr-coverage.py:1`

Per `script-standards.md` "PEP 723 Inline Metadata (Required)", every Python script — even stdlib-only — MUST include a `# /// script` block with `requires-python`. None of the three have it. They're all stdlib-only so the dependency list is empty, but the block must still be present (the standard is explicit: "still include the metadata block"). The L1 scripts scanner already flagged this with severity medium.

**Fix:** prepend after the shebang on each script:
```python
# /// script
# requires-python = ">=3.10"
# ///
```

### S2 — No `scripts/tests/` directory (severity: high per L1 scanner)

`script-standards.md` Interface Standards: "Tests in `scripts/tests/`." The directory doesn't exist; none of the three scripts have unit tests. For pure plumbing with regex-driven contracts (especially `validate-mermaid.py`'s arrow regex and `check-fr-coverage.py`'s FR regex), this is the highest-leverage place tests would catch regressions. Round 1 didn't flag this because the scripts didn't exist yet — it's a new gap introduced by the refactor.

### S3 — CLI inconsistency in `check-fr-coverage.py` (severity: medium)

Two of the three scripts follow the standard `-o`/`--output` flag for the JSON output path. `check-fr-coverage.py` instead uses `--output` for the D-06 input path (line 59) and a custom `-o`/`--out` for the JSON output (line 60). This collides with the documented Interface Standard ("`-o` flag for output file") and with the convention the other two scripts establish in the very same `scripts/` directory. The risk: an LLM following the pattern of the sibling scripts will invoke `check-fr-coverage.py -o foo.json` and silently get `foo.json` as the JSON path while no D-06 path is supplied — argparse will then halt, but the friction is real and the surface is asymmetric.

**Fix:** rename `--output` (D-06 path) to e.g. `--d06` or `--target`, and let `-o` map to `--output` as the JSON sink, matching the siblings.

The SKILL.md invocation at line 218 already deals with this implicitly:
```
python3 {skill-root}/scripts/check-fr-coverage.py --prd <each-prd-path-or-shard> --output {doc_workspace}/D-06-business-flow-diagram.md -o {doc_workspace}/.scan/fr.json
```
— but the call site has to know the non-standard binding.

### S4 — `discover-planning-artifacts.py` uses non-standard exit code (severity: low)

`script-standards.md` Interface Standards: "Exit codes: 0=pass, 1=fail, 2=error". The script returns `0` on success and `2` on template_missing (line 143). Template missing is a "fail" state (script ran fine, found something wrong), not a script error. Exit code 1 is the right semantic. The SKILL.md only inspects the JSON body, so this is cosmetic, but it diverges from the contract the other two scripts honour (1 = issues found, 2 = file unreadable).

### S5 — `validate-mermaid.py` ARROW_RE may miss self-arrows and notes (severity: low / informational)

The regex `^\s*(\w+)\s*(?:->>?|-->>?|--?\)|--?x|--?X)\s*[+-]?(\w+)\s*:` captures the standard set, but Mermaid sequenceDiagram also supports:
- `Note over A,B: msg` (no arrow, but introduces A and B as participants)
- `loop`/`alt`/`opt`/`par`/`activate`/`deactivate` blocks that reference participants

The script will (correctly) treat these as orphans-or-undeclared depending on which side has the declaration, which may surface false positives once the LLM-generated D-06 starts using notes or activation blocks. This is not blocking — the SKILL.md (line 226) frames script findings as input to a fix loop, not as absolute pass/fail — but it's worth a comment in the script's `--help` so the LLM doesn't auto-"fix" a legitimate `Note over` line.

This is not an intelligence leak (the script reports facts, the LLM judges), but the regex coverage is an honest limitation.

### S6 — FR regex tolerates leading zeros but not lowercased forms (severity: low / informational)

`FR_RE = r"\b(N?FR-[0-9]+(?:\.[0-9]+)*)\b"` is case-sensitive. `fr-001` in a PRD body won't match. This is fine if the team convention is upper-case (it appears to be), but worth a `re.IGNORECASE` flip or an explicit decision in `--help`. Not a leak.

## Intelligence-placement findings (SKILL.md consuming scripts)

### P1 — Stage 4 consumes the script JSON correctly

`§4 Validation` (lines 213-219) invokes both scripts with explicit `-o` JSON sinks under `.scan/`. `§4` (lines 221-222) reads the JSON, presents consolidated findings, applies deterministic auto-fixes only in headless, and surfaces non-deterministic gaps (uncovered FRs) as `blocked` rather than silently inventing. This is exactly the intelligence-placement split the principles call for: script counts the set, LLM decides what to do about an uncovered FR.

### P2 — Stage 1b consumes `artifacts.json` correctly

`§1b` (lines 124-131) invokes `discover-planning-artifacts.py`, checks `template_missing` → HALT, `artifacts_dir_exists` → fall through to no-PRD menu. The script's classification (`is_sharded`, `shard_paths[]`) is used downstream in `§4` (line 221: "or each shard from `artifacts.json` for sharded PRDs"). No re-globbing in the prompt — confirmed by direct grep.

### P3 — Stage 2 elicitation is judgment, correctly kept in prompt (no finding)

`§2 Discovery` extracts actors/triggers/steps/decisions/outcomes from sources. This is interpretation — meaning, role classification, deciding what counts as a "trigger" — and rightly stays in the prompt. The compaction-flush mechanism (write actor list to frontmatter + decision log) is a state-preservation pattern, not a deterministic operation that could be scripted away.

### P4 — `--expected-actors` is passed by the LLM, not derived (no finding, design observation)

SKILL.md line 216: `--expected-actors "<comma-separated stage-2 actors>"`. The list comes from Stage 2's elicited actor inventory (stored in frontmatter `stage_2_actors`). This is the right boundary: deciding *what* the expected actors are is judgment (the prompt's job); checking *whether each one appears* in some Mermaid block is set membership (the script's job). The script does not try to infer actor names from PRD prose — it would have to interpret meaning to do so.

## Distribution findings

### D1 — Stage 4 validators run sequentially when they could batch (severity: low)

Lines 215-219 show two `python3 …` invocations one after the other. They're independent — `validate-mermaid.py` reads only the D-06 file; `check-fr-coverage.py` reads PRD + D-06. The Bash tool can run multiple commands in one message; the SKILL.md could explicitly invite batching ("invoke both in one tool call"). Token savings nil; wall-clock savings small. Not a strong finding — the LLM will likely batch them anyway given they're adjacent in the same fenced block. Flag as opportunity, not defect.

### D2 — Parallel-lens menus (Stage 3, Stage 4) already fan out via subagents

Lines 202-209 and 235-242 wire to `bmad-advanced-elicitation` / `bmad-party-mode` as subagents. Correct distribution pattern; no leak.

## Round-1 resolutions verified

| Round-1 finding | Resolution status |
|---|---|
| PRD/UX/research discovery scan done in-prompt | **Resolved.** `discover-planning-artifacts.py` owns the glob; SKILL.md §1b says "Trust its output instead of re-globbing." |
| Sharded-PRD shard enumeration done in-prompt | **Resolved.** Script enumerates shards from `index.md` links with directory glob fallback. |
| Mermaid syntactic validation done in-prompt (token-heavy regex work) | **Resolved.** `validate-mermaid.py` owns block extraction + declaration/arrow parsing. |
| FR coverage matrix done in-prompt | **Resolved.** `check-fr-coverage.py` returns the three set diffs. |
| Template existence check done in-prompt | **Resolved.** `template_exists` in `artifacts.json`. |

## Token savings — round-1 estimate validation

Round-1 estimate: 2400–5200 tokens saved.

Re-estimating against the realised scripts:

| Operation | LLM tax if done in-prompt | Realised script saving |
|---|---|---|
| Glob PRD/UX/use-case/research, classify sharded vs whole-doc, enumerate shards by parsing `index.md` markdown links | 800–1500 (heavy: depends on artifact-dir size; reading even a small `index.md` + listing matches is high tokens) | ~full savings; LLM reads ~50-line JSON instead |
| Extract Mermaid blocks from a multi-flow D-06 (could be 200+ lines of fenced content), parse declarations and arrows, set-diff | 1200–2500 (heavy: D-06 with N flows scales linearly) | ~full savings; LLM reads issue list only |
| FR ID extraction from PRD (potentially sharded — N files) and D-06, three-way set diff | 600–1200 (heavy on sharded PRDs: every shard read into context) | ~full savings; LLM reads three short ID lists |

Realised aggregate: **~2600–5200 tokens saved per Stage-1+Stage-4 run**, in line with the round-1 estimate. Sharded PRDs are where the win compounds most — every shard the LLM no longer has to slurp into context.

The scripts are not duplicating work the LLM still does. SKILL.md `§4` Judgment-checks list is genuinely non-deterministic (readability, delta clarity, language consistency, revision-history populated) — not overlap.

## Strengths to preserve

- **Pre-pass pattern at §1b.** Single script, single JSON output, downstream consumers read by key. Textbook intelligence placement.
- **Explicit `Trust its output instead of re-globbing` sentence** (line 131) — a clear anti-leak signal to future maintainers and to LLM consumers tempted to "double-check."
- **`§4` script-vs-judgment split is explicit.** Lines 213-228 separate "deterministic validators" from "Judgment checks (LLM, not script)" by sub-heading. This is a teachable example.
- **`--expected-actors` is LLM-provided, not script-inferred.** The script doesn't try to read PRD prose and decide which words look like actors — that would be intelligence leaking into the script.
- **Headless auto-fix is bounded.** Line 231: "apply only deterministic fixes (e.g. add a missing `participant` declaration where the alias is unambiguous from message lines). … For non-deterministic issues … do not silently invent — log them and return `blocked`." Exactly the right boundary for an automated fix loop.
- **No `references/` carve-out yet.** Skill is ~260 lines, under the multi-branch ceiling; inline beats over-decomposition.

## New deterministic gaps (introduced or remaining after refactor)

1. **PEP 723 absent on all three scripts** (S1) — medium, mechanical fix.
2. **No `scripts/tests/`** (S2) — high; regex contracts deserve tests.
3. **`check-fr-coverage.py` CLI diverges from sibling pattern** (S3) — medium, easy rename.
4. **Exit-code semantic mismatch on `discover-planning-artifacts.py`** (S4) — low, one-line fix.
5. **`validate-mermaid.py` regex doesn't cover `Note over` / `activate` / control blocks** (S5) — low; will cause false positives once D-06 outputs use those constructs.
6. **FR regex case-sensitive** (S6) — low / informational.

None are intelligence-placement leaks (no script makes meaning judgments); all are quality issues within the plumbing lane.

## Severity rollup

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 1 (S2: no tests) |
| Medium | 2 (S1: PEP 723; S3: CLI inconsistency) |
| Low | 3 (S4 exit code; S5 regex coverage; S6 case sensitivity; D1 batching opportunity) |

Aggregate verdict: refactor delivered. The three scripts are correctly scoped, the SKILL.md consumes them correctly, and round-1's token tax is realised. Remaining gaps are script-hygiene and minor regex completeness — none re-open the in-prompt-determinism wound.
