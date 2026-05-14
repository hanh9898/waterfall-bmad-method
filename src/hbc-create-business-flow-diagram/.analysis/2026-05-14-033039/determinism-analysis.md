# Determinism & Distribution Analysis — Round 5 (post-round-4 polish)

Target: `hbc-create-business-flow-diagram`
Scanner: L2 (intelligence placement, distribution)
Pre-pass: `execution-deps-prepass.json` — zero issues, zero sequential patterns.

## Existing scripts inventory

| Script | Stage | Role |
|---|---|---|
| `scripts/discover-planning-artifacts.py` | 1a pre-pass | Globs PRD/UX/use-case/research (EN + JP), classifies whole-doc vs sharded PRD, enumerates shards from `index.md` links (dir-glob fallback), verifies `business_flow_template`, optionally emits `resume_state` (primary frontmatter + last session block from `.decision-log.md`) with `recommended_intent`. Each entry carries `is_symlink: bool`. |
| `scripts/validate-mermaid.py` | 4 | Extracts mermaid blocks; parses `participant`/`actor` declarations (bare + quoted alias); finds `undeclared_participant`, `orphan_declaration`, `missing_expected_actor`, `no_mermaid_blocks`. Recognises activation prefixes (`+A`/`-A`) and `Note over`/`left of`/`right of` participants as used. Per-issue `auto_fixable: bool` + `fix_hint`. |
| `scripts/check-fr-coverage.py` | 4 | Regex-extracts FR/NFR ids from `--prd` (file or dir, repeatable) and `--d06`; rglob skips `EXCLUDE_DIRS`; returns covered / uncovered / phantom. |
| `scripts/tests/run-tests.py` + 3 test files | dev | importlib-based test runner; 22 tests (1 skipped on Windows for symlink). |

`references/headless-contract.md` is the single non-empty reference; SKILL.md ~237 lines.

## Assessment

Intelligence placement is now **Excellent**. The script-vs-prompt boundary is honoured both ways: the scripts contain no meaning-judgments (they regex, set-diff, glob, count), and SKILL.md contains no deterministic operations the scripts already own. Round-3's nine sub-findings under "Script hygiene and long-tail input coverage" are addressed end-to-end, with one residual edge case in the `resume_state` regex worth a low-severity flag. The `auto_fixable` contract introduced in round 4 cleanly eliminates the M-7 prose-leak: the script emits a structured boolean per issue, and SKILL.md `§4` consumes it without re-deciding ("apply only … `auto_fixable: true` in `mermaid.json`. The validator decides what counts"). The runner hack for hyphenated test names is a documented, contained workaround, not a smell. Aggregate token saving against an in-prompt implementation remains in the same ~2.6k–5.2k band as round 3 — additionally, the `resume_state` shortcut saves another ~200–500 tokens per Resume/Update activation that would otherwise have the LLM read both the primary frontmatter and the last decision-log session.

## Round-3 / round-4 resolutions verified

| Round-3 sub-finding | Status | Evidence |
|---|---|---|
| PEP 723 missing on all scripts | **Resolved** | `discover-planning-artifacts.py:1-5`, `validate-mermaid.py:1-5`, `check-fr-coverage.py:1-5`, three test files, and `run-tests.py:1-5` all carry `# /// script` with `requires-python = ">=3.10"`. Empty `dependencies = []` declared explicitly — matches the stdlib-only convention in `script-standards.md`. |
| No `scripts/tests/` directory | **Resolved** | 22 tests in three files; full pass (`Ran 22 tests in 3.057s. OK (skipped=1)`). |
| `check-fr-coverage.py` CLI inconsistency | **Resolved** | Now `--prd` + `--d06` + `-o/--output` JSON sink. Matches sibling pattern. SKILL.md line 201 invokes with the new shape. |
| Exit code 2 for `template_missing` | **Resolved** | `discover-planning-artifacts.py:241` returns `1 if fatal else 0`. Exit 2 reserved for argparse / filesystem errors. |
| Mermaid regex misses `Note over`, activation prefixes, quoted aliases | **Resolved** | `DECL_RE` (lines 48-53) handles quoted aliases via named-group alternation. `ARROW_RE` (lines 57-64) accepts optional `+`/`-` activation prefix. `NOTE_RE` (lines 67-71) and `ACTIVATION_RE` (lines 74-78) feed `_block_uses`. Tests at `test_validate-mermaid.py:65-117` exercise each. |
| Japanese filename globs | **Resolved** | `PRD_GLOBS`, `UX_GLOBS`, `USE_CASE_GLOBS` (lines 30-38) include `*要件定義書*.md`, `*企画書*.md`, `*ユースケース*.md`, `*画面*.md`. Test at `test_discover-planning-artifacts.py:68-76`. |
| Symlink invisibility | **Resolved** | `_make_entry` (line 42) emits `is_symlink: bool`; `_unique_paths` deliberately uses `absolute()` not `resolve()` (line 53 comment). Test at `test_discover-planning-artifacts.py:99-110` (skipped on Windows but covers POSIX). |
| `check-fr-coverage.py` walks stale folders | **Resolved** | `EXCLUDE_DIRS` (lines 40-42) + `_walk_md` (lines 53-61). Test at `test_check-fr-coverage.py:89-107` confirms `FR-999` in `archive/` and `FR-888` in `notes/` are skipped. |
| FR regex case sensitivity | **Still open (informational)** | `FR_RE` (line 37) remains case-sensitive. Not flagged this round — the team convention is uppercase; making it case-insensitive would risk matching `fr-001` inside narrative prose like "fr-001 is a typo" or template scaffolding. Left as-is is defensible. |
| M-7 prose-leak (per-issue `auto_fixable`) | **Resolved** | `validate-mermaid.py:139` computes the boolean from regex evidence; `fix_hint` is added when true. SKILL.md `§4` reads it directly instead of restating "deterministic enough that..." prose. |
| M-8 `resume_state` (skill stops parsing two files in-line) | **Resolved** | `--workspace` flag (line 196) + `_extract_resume_state` (lines 118-182) emit `recommended_intent` from primary frontmatter + last `## Session …` block. SKILL.md `§1a` line 89 reads `resume_state.recommended_intent` directly. |

## New findings (round 5)

### L1 — `_extract_resume_state` regex requires inline-list frontmatter (severity: low)

**File:** `scripts/discover-planning-artifacts.py:140`

The `stepsCompleted` parser uses `^stepsCompleted:\s*\[(.*?)\]\s*$` with `re.MULTILINE`, which matches only the inline form `stepsCompleted: [stage-1, stage-2]`. Block-style YAML (the more idiomatic form an LLM writing to frontmatter mid-flow may emit) is silently treated as empty:

```yaml
stepsCompleted:
  - stage-1
  - stage-2
```

Consequence: a partially-completed primary written with block-style frontmatter would surface `recommended_intent: "Fresh"` instead of `Resume`, which is exactly the round-3 user-visible failure mode this script was built to prevent. The unit test at `test_discover-planning-artifacts.py:127-144` only exercises the inline form, so the regression is not caught.

Two paths to fix, in order of cost:

1. **Cheap, no dependency change.** Extend the regex with a second pattern that captures block-style:
   ```python
   block_match = re.search(r"^stepsCompleted:\s*\n((?:\s+-\s+\S+\s*\n)+)", fm, re.MULTILINE)
   ```
   then split on `- ` and strip. Add a test for the block form.

2. **Robust.** Pull in `pyyaml` via PEP 723 (`dependencies = ["pyyaml>=6.0"]`) and parse the frontmatter with `yaml.safe_load`. This also handles quoted scalars (`updated: "2026-05-14"`) and multi-line strings that the current regex `[\"']?(.*?)[\"']?\s*$` mishandles when the value is empty (`lastStep: ''` produces `primary_last_step: "''"` — quotes left in).

Round-2 / round-3 had explicit script-standards guidance: "External dependencies must be confirmed with the user during the build process." For this skill's surface (one regex over frontmatter), option 1 is proportionate. Promote to medium if the team plans to emit block-style frontmatter by default.

### L2 — `lastStep: ''` parses with surviving quotes (severity: low)

**File:** `scripts/discover-planning-artifacts.py:144-149`

The `[\"']?(.*?)[\"']?\s*$` capture is non-greedy and the optional-quote on each side is greedy-optional, so empty-quoted values like `lastStep: ''` yield `primary_last_step: "''"`. Downstream consumers comparing `primary_last_step == "complete"` or branching on truthiness will see a truthy `"''"`. Not a current consumer (SKILL.md only uses `recommended_intent`), but the JSON field is documented and may grow consumers. The test at `test_discover-planning-artifacts.py:146-163` writes `lastStep: ''` and the script returns "Fresh" via the `not steps` path, so the bug doesn't surface — but it's latent in the JSON.

Fix: strip outer single OR double quote pair as a post-step, or switch to pyyaml (see L1).

### L3 — `auto_fixable` "not conflict" check is asymmetric (severity: low / informational)

**File:** `scripts/validate-mermaid.py:136-139`

The conflict check is:
```python
conflict = any(
    (info["display"] or "").strip() == name for info in decls.values()
)
```
This flags as conflicting only the case where the undeclared `name` collides with an existing **display label**. It does not check whether the same `name` collides with an existing declaration's `alias`. The asymmetry is defensible — if `name` matched an existing alias, it wouldn't be in `used - declared` in the first place — so the check is tight enough by construction. The remaining edge:

- If two arrows reference `User` and `user` (case-different), only one will be in `declared` after `participant User` is parsed. The other will show up as undeclared, and `auto_fixable=True` will tell the SKILL.md to add `participant user` — which then becomes a second participant, not a typo fix. The LLM caller can't know which is correct from the JSON alone.

The current test suite doesn't exercise this. Not blocking; the `auto_fixable=True` branch in headless still "adds a participant" — the worst that happens is a redundant lane in the rendered diagram, which Stage-4 LLM judgment will catch. Documenting this limit in the script's `--help` or in `fix_hint` (e.g., `"add \`participant {name}\` — verify it's not a typo of an existing participant"`) would buy the prompt one more guardrail without enlarging the contract.

### L4 — Test runner hack is acceptable; alternative is cleaner (severity: low / informational)

**File:** `scripts/tests/run-tests.py`

The importlib path-based loader exists because `python -m unittest discover` cannot import modules with hyphenated filenames. The fix is correct and isolated — 50 lines, documented purpose, single responsibility, runs cleanly. Verdict: **acceptable, not a smell.** The alternative paths and their costs:

| Option | Cost |
|---|---|
| Rename test files to `test_check_fr_coverage.py` (underscore) | Diverges from scan-scripts.py naming convention which expects `test_<script-name>.py` to mirror exactly. The convention itself is the constraint. |
| Rename scripts to underscored names (`check_fr_coverage.py`) | The `scripts/` directory's existing CLI invocations in SKILL.md become wrong; user-facing breakage on every install update. |
| Drop the convention and let test files have underscores even when scripts have hyphens | Loses the L1 lint that "test exists for this script" can do via filename match. |
| Keep `run-tests.py` (current) | 50 lines of stdlib-only code that the developer runs once per change. |

Current pick is the lowest-cost; the comment in the runner explains the trade. The only suggestion: surface this in `script-standards.md` ("Tests in `scripts/tests/` named `test_<script-name>.py`. Hyphenated names require a `run-tests.py` importlib loader — see `bmad-workflow-builder` ref impl") so other skill builders don't reinvent it.

## EXCLUDE_DIRS — completeness check

The current set is `{"archive", "archived", "old", "notes", "scratch", "drafts", ".git", "node_modules", "__pycache__"}`. Comparing against the HBC project layout (`templates/`, `_bmad/`, `src/`, `.analysis/`, `.claude/`) — looking specifically for folders that contain markdown an LLM might write to and would not be part of a PRD canon:

| Candidate | Verdict |
|---|---|
| `.analysis/` | **Add.** Quality-scan output (this file, in fact) sits under `.analysis/<timestamp>/` and would otherwise be walked into when the user points `--prd` at a project-root-ish path. Markdown inside `.analysis/` is process noise, not a PRD. |
| `.claude/` | **Add.** Skill installation directory; contains `skills/<skill>/SKILL.md` files which would match nothing FR-shaped but may slow rglob. |
| `.bmad/` / `_bmad/` | **Add `_bmad`.** Config + custom overrides + installed skills live here. Walking it is wasted time. (`.bmad` is unused in this layout but cheap to include as a sibling form.) |
| `templates/` | **Don't add.** Templates may carry placeholder FR ids worth surfacing as `phantom` so the LLM knows the template wasn't substituted — that's a genuine signal. |
| `dist/`, `build/`, `out/` | **Add.** Build output; if a markdown plan got into a build pipeline the source-of-truth would still be elsewhere. |
| `vendor/`, `.venv`, `.tox` | **Add for parity with `node_modules`.** Dependency directories, never PRDs. |
| `coverage/`, `.pytest_cache`, `.mypy_cache` | **Add the cache dirs.** Cheap parity with `__pycache__`. |
| `tmp/`, `temp/` | **Add.** Common scratch folders. |

Suggested expanded set (additive, no removals):

```python
EXCLUDE_DIRS: frozenset[str] = frozenset({
    "archive", "archived", "old", "notes", "scratch", "drafts", "tmp", "temp",
    ".git", "node_modules", "__pycache__",
    ".analysis", ".claude", "_bmad",
    "dist", "build", "out",
    "vendor", ".venv", ".tox",
    ".pytest_cache", ".mypy_cache", "coverage",
})
```

Severity of the current gap: **low**. The dominant cost when one of these isn't excluded is wall-clock rglob time and a noisy `prd_files_read` list — not a wrong pass/fail. (Phantom-FR risk only kicks in if the unexcluded folder genuinely contains FR-shaped ids that aren't in the canon, which is unlikely for `_bmad/`, `.claude/`, and the build dirs.) Promote to medium if any HBC repo has stale PRD copies under `.bmad/` or `.analysis/`.

### L5 — Subprocess tests rely on `sys.executable`, ignore PEP 723 (severity: low / informational)

**Files:** `scripts/tests/test_*.py` (each)

Every test invokes the script via `subprocess.run([sys.executable, str(SCRIPT), ...])`. This runs the script under the test interpreter, **not** under `uv run`. PEP 723's purpose is automatic dependency resolution; bypassing it means any future external dependency added to a script (e.g. `pyyaml` per L1) would fail the test suite under `python` even though it'd work fine in real use. The fix when that day comes: switch to `["uv", "run", "--script", str(SCRIPT), ...]` and assert `uv` is available, or keep `sys.executable` and ensure the test environment has the deps installed. Either is fine; document the chosen one. **Not a defect today** — the scripts are stdlib-only. Flagged for the future.

## Intelligence-placement findings (SKILL.md consuming scripts) — round 5 deltas

### P5 — Stage 1a now consumes a single JSON, no in-line frontmatter parsing (resolved M-8)

SKILL.md `§1a` (line 86) invokes the discover script with `--workspace {doc_workspace}` and reads `resume_state.recommended_intent`, `resume_state.last_session_summary`, `resume_state.primary_steps_completed` (lines 89-100). Round-3 had the prompt reading two files inline; round-4 lifts that into the script. The textbook pre-pass pattern.

### P6 — Stage 4 auto-fix branch is now data-driven (resolved M-7)

SKILL.md `§4` (line 214):
> "Apply only validator issues marked `auto_fixable: true` in `mermaid.json`. The validator decides what counts as safely-auto-applicable … Log every auto-fix to `.decision-log.md` citing the validator's `fix_hint`."

This is the right contract shape: bool flag + human-readable hint, both produced by the script. No "if it's deterministic enough …" prose for the LLM to relitigate. Headless behaviour is now derivable from the JSON alone.

### P7 — Wrong-skill off-ramp is judgment, correctly kept in prompt (no finding)

`§1b` (line 117-119) catches `'tạo sơ đồ'` / `'vẽ sơ đồ'` reaching the wrong skill (class diagrams, system architecture, etc.) and redirects. This is intent-parsing — text classification under ambiguity — and stays in the LLM. No script would do this better.

## Distribution findings — round 5 deltas

### D1 (carried) — Stage 4 validators still run sequentially

SKILL.md lines 198-202 issue two `python3 ...` calls in adjacent fenced blocks. Independent, batchable. The prompt does not say "run in one tool call" but the formatting suggests it. Same status as round 3: opportunity, not defect. Token savings: nil. Wall-clock: small.

### D2 — No new distribution leaks introduced by round-4 changes

The `--workspace` flag added to the discover script consolidates two reads into one script call — that's a distribution win, not a loss. The lens menus already fan out via subagents (lines 65-71). No "review … acknowledge …" implicit-read traps in stages preceding subagent delegation.

## Strengths to preserve

- **Single-script pre-pass produces compact JSON consumed by name** (`§1a` lines 86-100 read by key). Canonical pattern.
- **`resume_state.recommended_intent` is computed by the script, not by the prompt.** This is the right placement: deciding which intent to default to based on `stepsCompleted` membership is set-membership, not judgment.
- **`auto_fixable: bool` is per-issue, not per-script.** This means `missing_expected_actor` (always false) and `undeclared_participant` (conditionally true) live in the same response — no separate response shape for "fix me" vs "block me".
- **`fix_hint` is only emitted when `auto_fixable=True`.** Asymmetric on purpose — there's nothing useful to say about an orphan declaration the LLM hasn't already seen.
- **Tests run scripts as subprocesses, not by importing internals.** Exercises the CLI contract, which is what callers depend on.
- **`_unique_paths` deliberately does not `resolve()` (line 53 comment).** Preserves symlink visibility — explicit design rationale captured in the code, exactly the "non-obvious choice" principles call for.
- **`EXCLUDE_DIRS` lowercases at compare time** (line 58), tolerating case-different folder names cross-platform. Good Windows defensiveness.

## Severity rollup

| Severity | Round 3 | Round 5 |
|---|---|---|
| Critical | 0 | 0 |
| High | 1 | 0 |
| Medium | 2 | 0 |
| Low | 4 | 5 (L1–L5) |

Round-3's three medium/high gaps closed. Round-5 surfaces five low-severity refinements, all within the plumbing lane.

## Aggregate verdict

**Excellent.** Round-4 changes hit every round-3 sub-finding with appropriate scope. The new findings are honest residuals — frontmatter parsing brittleness against block-style YAML (L1), latent quote-stripping bug (L2), `auto_fixable` typo-edge in `validate-mermaid.py` (L3), test-runner-hack-as-documented-pattern (L4 — accept), and a future-proofing note on subprocess-vs-`uv run` (L5). None are intelligence leaks; none reopen the "in-prompt determinism" wound. The pre-pass pattern at §1a is now textbook-quality and worth lifting into `script-opportunities-reference.md` as the reference example.

## What I would change before round 6

1. **L1 (block-style frontmatter)** — extend the regex or switch to pyyaml. One-line fix or a confirmed dependency add.
2. **L2 (empty-quoted values)** — sweep with the L1 fix, or post-strip outer quote pairs.
3. **L3 (typo-vs-add ambiguity in `fix_hint`)** — add `"verify not a typo of an existing participant"` to the hint string.
4. **EXCLUDE_DIRS expansion** — add `.analysis`, `.claude`, `_bmad`, build/cache/venv dirs.

Everything above is one-PR work; none of it changes the script contracts, only their robustness.
