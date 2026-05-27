# Determinism & Distribution Analysis — hbc-agent-ba

**Scan date:** 2026-05-27T160500
**Skill type:** Agent (scripts/ directory added since last analysis)
**Prepass status:** execution-deps-prepass → pass (0 stages, 0 issues); scripts-temp → warning (4 findings); prompt-metrics → info (0 waste patterns, 0 back-references)

---

## Existing Scripts Inventory

One skill-owned script now present:

| Script | Language | Purpose | Status |
|--------|----------|---------|--------|
| `scripts/scan-phase1-state.py` | Python (stdlib only) | Glob for D-02, D-03, D-06, phase-1-gate artifacts; emit JSON with exists/file/updated per artifact, status, next_recommended, reason | Functional — no PEP 723 block, no unit tests, no sys.exit() codes |

One external shared utility (not skill-owned, not a duplicate candidate):

- `{project-root}/_bmad/scripts/resolve_customization.py` — invoked in Step 1 for agent-block resolution.

---

## Assessment

The primary script opportunity identified in the prior analysis (T143000 SF-1 — Phase 1 state scan) has been resolved: `scripts/scan-phase1-state.py` is now in place and SKILL.md at line 65 correctly invokes it via `python3 {skill-root}/scripts/scan-phase1-state.py {agent.output_path}`. Intelligence placement is now sound — filesystem existence checks, frontmatter date extraction, and status derivation all live in the script; the LLM receives compact JSON and handles persona, greeting, and menu dispatch. One low-priority script opportunity (config key extraction, SF-2 from prior analysis) remains unaddressed but is still low severity. The script itself has three quality gaps flagged by the scripts scanner (no PEP 723 block, no unit tests, no exit codes) that reduce operational reliability without affecting correctness of the current implementation.

---

## Script Findings

### SF-1 — Phase 1 Artifact State Scan [RESOLVED]

**Prior finding:** SKILL.md:57-65 — LLM performing filesystem glob and status derivation with medium token tax (150-250 tokens per activation).

**Current state:** `scripts/scan-phase1-state.py` added. SKILL.md line 65 now reads: `Run: python3 {skill-root}/scripts/scan-phase1-state.py {agent.output_path}`. The script correctly implements all four glob patterns, frontmatter date extraction, core-artifact completeness check, next_recommended derivation, and a safe fallback for missing output directory. Script-first, LLM-fallback pattern preserved at line 69-70 (matches the Step 1 pattern for the resolver).

**Residual script quality issues** (from scripts-temp.json):

#### SF-1a — Missing PEP 723 Inline Dependency Block (Medium)

**File:line:** `scripts/scan-phase1-state.py:1`
**Current state:** Script uses only stdlib (`argparse`, `glob`, `json`, `os`, `re`) — no third-party deps. However, the PEP 723 block is absent, which means `uv run` and other PEP 723-aware runners cannot introspect or manage the script.
**What to add:**
```python
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
```
**Impact:** No runtime failure today (stdlib only), but makes the script unrunnable via `uv run scripts/scan-phase1-state.py` without the block. Medium — correctness risk when the project adopts uv-based script execution.

#### SF-1b — No sys.exit() Exit Codes (Low)

**File:line:** `scripts/scan-phase1-state.py:1`
**Current state:** `main()` returns normally in all cases, exiting with code 0 regardless of whether the output directory exists or the scan finds missing artifacts. Callers (including the SKILL.md fallback logic) cannot distinguish "scan ran, directory missing" from "scan ran, all artifacts found" via exit code alone.
**What to add:** `sys.exit(0)` on success, `sys.exit(1)` when status is `blocked`, `sys.exit(2)` on unexpected error. The JSON payload already carries the semantic result — exit codes add a machine-readable signal layer for shell callers and CI.
**Impact:** Low — SKILL.md reads the JSON output, not the exit code. Does not cause current failures. Reduces future shell-integration utility.

#### SF-1c — No Unit Tests (High)

**File:line:** `scripts/scan-phase1-state.py` — `scripts/tests/` directory does not exist.
**Current state:** `scan-phase1-state.py` has three logic paths with testable branches: (a) output directory missing, (b) some artifacts missing (blocked), (c) all core artifacts present (complete). The frontmatter date regex has its own correctness surface. None are covered.
**What to add:** `scripts/tests/test-scan-phase1-state.py` with `pytest` cases using `tmp_path` fixtures for each branch. At minimum: missing-directory path, all-missing path, partial-missing path (checks `next_recommended` ordering), all-present path (checks `status == "complete"` and `next_recommended == "PG"`), and frontmatter date extraction (valid/invalid/missing cases).
**Impact:** High — the script is invoked on every agent activation. A regression in glob pattern matching or status derivation logic would silently degrade every greeting without a test catching it first.

---

### SF-2 — Config Key Extraction (Low) [UNCHANGED from T143000]

**File:line:** `SKILL.md:61` (`Embody Persona and Load Context` section)
**LLM tax band:** Low-to-medium (100–200 tokens — read two YAML files, extract 3 scalar keys)
**Current pattern:** The LLM is instructed to `Load config from {project-root}/_bmad/config.yaml and {project-root}/_bmad/config.user.yaml — resolve {user_name}, {communication_language}, and {document_output_language}`. This is a structured lookup with defined merge order (base → user override) and deterministic output.
**What a script would do:** Extend `resolve_customization.py --key config` or add a sibling utility that emits the three scalars as flat JSON. The LLM receives `{"user_name": "Alice", "communication_language": "en", "document_output_language": "vi"}` and uses it without loading YAML files directly.
**Estimated token savings:** 100–150 tokens per activation.
**Pre-pass potential:** Medium — low complexity, modest savings.
**Severity:** Low. Correct as-is; script would improve consistency and reduce activation token overhead.

---

## Distribution Findings

### DF-1 — Steps Are Correctly Sequenced, No Parallelism Blocked [CONFIRMED CLEAN]

The execution-deps-prepass confirms 0 stages, 0 dependency issues. The activation sequence (resolver → persona → state scan → greet) is correctly ordered. State scan depends on `{agent.output_path}` resolved from config; config loading precedes state scan. No false sequencing constraint exists.

### DF-2 — No Implicit-Read Trap [CONFIRMED CLEAN]

Activation language at lines 45-79 uses no "review", "acknowledge", or "summarize what you have" phrasing before a subagent delegation. This agent dispatches to child skills via menu dispatch, not subagents. The implicit-read trap does not apply. Clean.

### DF-3 — Merge Rules in Fallback Block [LOW — UNCHANGED]

**File:line:** `SKILL.md:49-55`
The fallback block for Step 1 re-states TOML merge rules inline (~40 tokens). These qualify as BMad institutional knowledge needed for correct fallback behavior. The T143000 analysis noted this as a brevity opportunity, not a correctness issue. The current SKILL.md tightens the fallback to a single sentence ("apply BMad structural merge rules to base → team → user order") — this is already the trimmed form. Finding is resolved.

### DF-4 — Workflow Integrity Prepass False Positives [INFORMATIONAL]

The workflow-integrity-prepass reports two "critical" missing stage files: `02-requirements.md` and `06-business-flow.md`. These are artifact filename examples in the headless JSON block (lines 30-33), not `references/` stage file references. The scanner is pattern-matching on filename fragments inside a fenced code block. These findings do not reflect real stage-file issues. No action needed on the skill; the scanner needs a fenced-block exclusion rule.

---

## Aggregate Token Savings Estimate

| Finding | Per-activation savings | Priority | Status |
|---------|----------------------|----------|--------|
| SF-1 Phase 1 state scan (script added) | 150–250 tokens | Medium | **RESOLVED** |
| SF-2 Config key extraction | 100–150 tokens | Low | Open |
| DF-3 Merge rules trim | ~0 tokens (already trimmed) | Low | **RESOLVED** |
| **Open savings** | **100–150 tokens/activation** | | |

SF-1 resolution eliminates the largest per-activation cost identified at T143000. Remaining open opportunity (SF-2) is low priority. At 10 activations/day, SF-2 represents ~1,000–1,500 tokens/day — not significant at current scale.

---

## Strengths

**SF-1 fully implemented with correct fallback pattern.** `scan-phase1-state.py` implements the pre-pass pattern correctly: emits compact JSON, handles the missing-directory edge case gracefully, and SKILL.md preserves the "run script; if it fails, do it manually" fallback at line 69-70. This mirrors the Step 1 resolver pattern and makes activation deterministic and testable. The `updated` field (frontmatter date extraction) extends the prior JSON spec from T143000, giving the LLM timestamped artifact state for the resume protocol.

**Script output extends the headless JSON spec.** The headless mode JSON schema in SKILL.md (lines 29-39) now maps cleanly to the script's output fields (`status`, `phase1_state`, `next_recommended`, `reason`). Headless invocations and interactive activations consume the same data structure.

**Menu dispatch remains outcome-based.** "Accept a number, menu `code`, or fuzzy description match. Only clarify when two or more items are genuinely ambiguous." No prescriptive step enumeration. Correct form.

**No subagent spawning, no context-bloating reads.** Architecture correctly dispatches to child skills via menu, not subagents. The implicit-read trap and subagent-spawning-from-subagent failure modes do not apply.

**Zero waste patterns, zero back-references** (prompt-metrics-prepass). SKILL.md stages are self-contained and carry no cross-file forward references that would break on compaction.
