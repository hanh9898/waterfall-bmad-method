# Determinism & Distribution Analysis — hbc-create-business-flow-diagram

**Scanner:** L2 (determinism)
**Target:** `C:/Users/HanhNT2/stc-erp-bmad-custom/src/hbc-create-business-flow-diagram`
**Date:** 2026-05-14
**Pre-pass:** `execution-deps-prepass.json` (0 issues, single stage `.decision-log` — no useful dep graph extracted)

---

## Existing scripts inventory

- **No `scripts/` directory in the skill.** All deterministic plumbing currently lives in the prompt.
- Skill reuses two shared BMad scripts only:
  - `{project-root}/_bmad/scripts/resolve_customization.py` (SKILL.md:23, 110) — workflow block resolution and `on_complete` hook.
- No skill-local scripts; no pre-passes; no post-processing validators.

---

## Assessment

The skill is a small, well-shaped workflow (~113 lines) where most stages legitimately require interpretation — actor identification, AS-IS/TO-BE delta reasoning, and Mermaid layout choices are judgment calls. **However, Stage 1 (artifact discovery) and Stage 4 (validation) contain three clearly deterministic operations that currently cost the LLM significant tokens per run with zero quality benefit:** PRD/UX/research file discovery via glob patterns, Mermaid syntax validation, and FR-traceability cross-referencing. These are textbook script candidates. Distribution-wise the workflow is linear-by-design (each stage feeds the next), but the Stage 1 source-doc scan is the one place where parent-bloat / implicit-read risk is real.

---

## Script findings

### S1. PRD/UX/research discovery scan — HIGH severity, HIGH pre-pass potential

- **Location:** SKILL.md:52-58 (Stage 1)
- **Current LLM behavior:** LLM glob-walks `{planning_artifacts}` looking for `*prd*.md`, `*prd*/index.md`, `*ux*.md`, `*use-case*.md`, `D-04*.md`, `D-05*.md`, `research/*.md`. For a typical planning_artifacts tree this means listing the directory, applying multiple shell-glob patterns, deduping, and detecting sharded vs. single-doc layout — all deterministic file-system work.
- **Determinism leak (violates "Intelligence placement"):** glob matching and path existence checks have no judgment component. Same input → same output, trivially unit-testable.
- **Script alternative:** `scripts/discover-planning-artifacts.py {planning_artifacts}` walks the directory once and emits a compact JSON pre-pass:
  ```json
  {
    "prd": {"path": "...", "form": "sharded|single", "size": 12345},
    "ux": [...],
    "use_cases": [...],
    "research": [...],
    "missing": ["prd"]
  }
  ```
  The LLM receives the compact JSON and decides only the things that need judgment (which files are *relevant*, which to include/exclude). This is the **pre-pass pattern** — highest-value, most-missed opportunity per the scanner reference.
- **LLM tax saved per invocation:** Heavy. A real PRD directory listing + ambiguous matching often runs 800-1500 tokens of tool output and reasoning; the JSON pre-pass is ~200 tokens.
- **Estimated savings:** ~600-1300 tokens/run.
- **Language:** Python (stdlib `pathlib` + `glob`).

### S2. Mermaid syntax validation — HIGH severity, HIGH script fit

- **Location:** SKILL.md:94 (Stage 4, validation item 3)
- **Current LLM behavior:** "each code block parses; no orphan messages or undeclared participants." The LLM reads each generated Mermaid block, traces every `->>` and `-->>`, and cross-checks that every left/right side of the arrow appears in a `participant`/`actor` declaration.
- **Determinism leak (violates "Intelligence placement" — *prompt validating structure, comparing against schemas*):** This is pure parsing + set-membership checking. No judgment.
- **Script alternative:** `scripts/validate-mermaid.py {doc_workspace}/D-06-*.md` extracts ` ```mermaid` blocks, parses participant/actor declarations and message lines with a small regex grammar, and reports any message referencing an undeclared name. For full rigor, a PEP 723 dep on `mermaid-py` or a subprocess call to `mmdc --validate` (if available) gives a real parser.
- **Post-processing pattern:** This is the canonical post-processing validator from the script-opportunities reference (`Validate generated YAML parses correctly` equivalent).
- **LLM tax saved per invocation:** Heavy. Multi-flow documents with 3-5 Mermaid blocks easily eat 800+ tokens of careful reading; scripts return a pass/fail JSON with line numbers.
- **Estimated savings:** ~600-1000 tokens/run; also raises catch rate (LLM eyeballing misses orphans).
- **Language:** Python (`re` + small state machine; optional subprocess to `mmdc`).

### S3. FR → flow-step traceability — HIGH severity, MEDIUM-HIGH script fit

- **Location:** SKILL.md:93 (Stage 4, validation item 2)
- **Current LLM behavior:** "if PRD was used, every functional requirement traces to at least one flow step" — LLM scans the PRD for FR-* identifiers, then re-scans every Mermaid block looking for keyword/label coverage of each FR.
- **Determinism leak:** Extracting `FR-\d+` (or whatever the project's FR identifier pattern is) from the PRD and checking which ones are mentioned by id in the D-06 doc is deterministic. The *quality* judgment ("is this flow step really covering FR-12?") needs the LLM, but the **identifier-presence pre-pass** doesn't.
- **Script alternative:** `scripts/check-fr-coverage.py --prd {prd_path} --diagram {d06_path}` extracts FR identifiers from both files and returns:
  ```json
  {"covered": ["FR-1","FR-2"], "uncovered": ["FR-5"], "phantom": []}
  ```
  LLM then judges semantic coverage *only for the uncovered set* — a 90% reduction in scan surface.
- **LLM tax saved per invocation:** Medium-Heavy. PRD scans regularly run 1500-3000 tokens; the script makes the LLM only look at gaps.
- **Estimated savings:** ~1000-2500 tokens/run on PRD-backed flows.
- **Language:** Python (`re` for FR-pattern extraction; project's FR pattern is configurable via arg).

### S4. Actor-coverage cross-check — MEDIUM severity

- **Location:** SKILL.md:92 (Stage 4, validation item 1)
- **Current LLM behavior:** "every Stage-2 actor appears in at least one diagram" — LLM re-reads the actor list from Stage 2 and scans every Mermaid block for occurrence.
- **Determinism leak:** Set membership. Trivially deterministic. The hard part (deciding *what* counts as an actor) is judgment and stays in the prompt at Stage 2; the *check* is mechanical.
- **Script alternative:** Fold into S2's `validate-mermaid.py`. The script already extracts participant/actor declarations — accepting an `--expected-actors` arg (comma-separated, in `{document_output_language}`) lets it return missing-actor findings in the same JSON.
- **LLM tax saved per invocation:** Moderate. ~200-400 tokens on a typical 3-actor flow; more on 6+ actor multi-flow docs.
- **Estimated savings:** ~200-400 tokens/run.

### S5. Workspace bootstrap — LOW severity

- **Location:** SKILL.md:66 (Stage 1)
- **Current LLM behavior:** Computes `{doc_workspace}`, checks for existence, creates folder if absent, appends session heading to `.decision-log.md` if present, or seeds primary from `{workflow.business_flow_template}` if absent.
- **Determinism leak:** Borderline — small enough that staying in the prompt is fine, but a `scripts/bootstrap-workspace.py` would also enforce the date-stamped session-heading format consistently across sessions.
- **LLM tax saved per invocation:** Light. ~100-200 tokens.
- **Note:** Not recommended on its own; only worth bundling if S1 is implemented (same script could emit both discovery JSON and bootstrap result).

---

## Distribution findings

### D1. Stage 1 source-doc gather is the only real distribution opportunity — MEDIUM severity

- **Location:** SKILL.md:52-58
- **Current pattern:** Sequential "scan for PRD, then UX, then use-case docs, then research." Even with batched tool calls, the LLM still reads each candidate to decide relevance.
- **Implicit-read trap risk:** The Stage 1 language "Scan `{planning_artifacts}` for source documents... PRD (preferred input)" can pull the parent into reading PRD/UX content directly before Stage 2 needs it. There is no subagent delegation downstream that would *benefit* from the parent staying lean (single-agent workflow), so the trap is muted — but the trap is precisely what the script in S1 also prevents: the JSON pre-pass replaces "scan for" with "here is what exists," and the LLM only opens what Stage 2 actually requires.
- **Efficient alternative:** Combine with S1 (the script *is* the distribution fix here). No subagent fan-out warranted at this skill's scale.
- **Estimated impact:** Covered under S1's savings.

### D2. Stage 4 validation ordering is correct — no finding

- Validation checks (Stage 4) run **after** generation (Stage 3), which is the only sensible order — generation is the expensive step, but you cannot validate Mermaid until it exists. No fail-fast inversion to flag.

### D3. No subagent usage to critique — N/A

- Workflow is single-agent linear. The skill correctly does **not** invent subagent fan-out where there's no parallel work to do (Stage 2's AS-IS/TO-BE discovery is one place a future-extension might fan out two subagents in migration mode, but at current scope it's marginal and adds coordination overhead — not flagging).

### D4. Headless decision-log writes are sequential-by-necessity — no finding

- Decision-log entries happen at Stage 1 init, Stage 4 auto-fixes, and Stage 5 handoff. These are inherently temporal — no batching to gain.

---

## Aggregate token savings

| Finding | Tokens saved/run (typical) |
|---|---|
| S1 discovery pre-pass | 600-1300 |
| S2 Mermaid validation | 600-1000 |
| S3 FR coverage | 1000-2500 (PRD-backed runs) |
| S4 actor coverage | 200-400 |
| S5 workspace bootstrap | (skip standalone) |
| **Total** | **~2400-5200 tokens per run** |

Plus a quality win on S2/S3 (scripts catch orphans and uncovered FRs the LLM eyeballing will sometimes miss).

---

## Strengths worth preserving

- **No deterministic work currently hidden in scripts** — there are no scripts at all, so no risk of "intelligence leak into the script" from regex-based meaning extraction. This is a clean baseline; any added scripts should stay strictly in the plumbing lane.
- **Stage 2 discovery is correctly LLM-side** — actor identification, trigger interpretation, and AS-IS/TO-BE delta reasoning are judgment calls and belong in the prompt.
- **`on_complete` hook resolved via shared script** (SKILL.md:110) — uses the canonical resolver rather than reimplementing TOML merge logic.
- **Headless contract is minimal** (SKILL.md:106) — JSON shape is `{status, skill, primary, decision_log}`, no kitchen-sink output.
- **Mermaid keyword language rule is stated once** (SKILL.md:45-46) — not repeated in every stage, trusting the LLM to apply it.
- **No "Why It Matters" prose or defensive padding** in the validation steps — the four checks are stated, period.

---

## Recommendation summary

Add a single `scripts/` directory with three small Python scripts:
1. `discover-planning-artifacts.py` (S1) — highest ROI; the pre-pass pattern.
2. `validate-mermaid.py` (S2 + S4 combined) — quality + cost win.
3. `check-fr-coverage.py` (S3) — biggest token saver on PRD-backed runs.

All three should follow `references/script-opportunities-reference.md` output standard (JSON with `findings[]` and exit codes 0/1/2). Together they convert ~2400-5200 tokens per run of deterministic LLM work into ~600 tokens of compact JSON pre-pass and post-pass reads.
