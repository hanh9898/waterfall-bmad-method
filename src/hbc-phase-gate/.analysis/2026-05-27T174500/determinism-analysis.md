# Determinism & Distribution Analysis — hbc-phase-gate

**Scan date:** 2026-05-27  
**Skill:** `src/hbc-phase-gate`  
**Pre-pass status:** execution-deps-prepass → pass (0 issues)

---

## Existing Scripts Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/evaluate-gate-checklist.py` | 270 | Parses phase gate checklist markdown; evaluates `[FILE]`, `[CONTENT]`, `[METRIC]` items deterministically via glob + regex; returns structured JSON; passes `[QUALITY]` items through as `PENDING_LLM`. |
| `scripts/tests/` | — | Directory exists but is empty (no test files present). |

No duplicate script proposals needed for the existing evaluator. All deterministic item types are already offloaded.

---

## Assessment

Intelligence placement is fundamentally sound: the skill correctly partitions deterministic work (FILE/CONTENT/METRIC checks) into `evaluate-gate-checklist.py` and reserves the LLM exclusively for `[QUALITY]` judgment items. The two remaining LLM-tax opportunities are narrow — a `find` shell command invoked inline by the LLM rather than bundled into the script, and the delta-table construction (prior results vs. current results) which is pure data manipulation. Distribution shape is simple single-pass with no multi-stage fan-out needed; the pre-pass confirms no dependency-graph issues. The skill is well within its complexity budget at 117 lines.

---

## Script Findings

### SF-01 — `find` near-match discovery is LLM-executed shell (medium)

**Severity:** Medium (LLM tax: light, ~50–80 tokens per missing FILE item, but repeated per failure)  
**Location:** `SKILL.md:92`  
**Current pattern:**
> "For each `FAIL` on a `[FILE]` item: run `find {project-root} -name "*{artifact_keyword}*"` to discover near-matches…"

The LLM is instructed to execute a `find` command and interpret results inline, after the evaluator script has already finished. This is deterministic work — given the artifact keyword, the near-match search always produces the same result set.

**What a script would do:** Extend `evaluate-gate-checklist.py` (or a thin wrapper) to, on any `FILE` FAIL, run `glob.glob` / `os.walk` with fuzzy keyword matching and include near-match candidates in the JSON `evidence` field alongside the FAIL status. The LLM then reads compact evidence from the JSON rather than running a shell command.

**Token savings:** ~50–80 tokens per missing FILE item × number of gate failures per run. Eliminates a shell tool call from the LLM turn.  
**Language:** Python (extend existing script)  
**Pre-pass potential:** Yes — near-match candidates fold directly into the existing JSON output schema under an `evidence` or `near_matches` field.

---

### SF-02 — Delta table construction is deterministic data manipulation (low)

**Severity:** Low (LLM tax: light, ~80–120 tokens)  
**Location:** `SKILL.md:99–107`  
**Current pattern:**
> "Append a session entry to `phase-{N}-gate-log.md`… Populate from `prior_results` map. Mark changes: `FAIL→PASS` (fixed), `PASS→FAIL` (regression), `NEW` (first evaluation), or `—` (unchanged). End with a one-line delta summary."

The delta computation (join prior_results map against current results, classify each item as fixed/regressed/new/unchanged, count each class) is a pure data join with no ambiguity. Given identical inputs it always produces identical output.

**What a script would do:** A `generate-gate-log-entry.py` script accepts `--prior-results` (JSON) and `--current-results` (JSON from the evaluator) and emits a ready-to-append markdown block with the filled delta table and summary line. The LLM appends the block verbatim.

**Token savings:** ~80–120 tokens per gate run saved on computing the delta; eliminates risk of miscounting or mis-classifying status transitions.  
**Language:** Python  
**Pre-pass potential:** Yes — the evaluator already reads the prior gate report for `prior_results`. The delta computation can be integrated into the same evaluator invocation or a lightweight post-step script.

---

## Distribution Findings

No distribution issues found.

The pre-pass dependency graph shows no stages (this is a single-pass evaluation workflow, not a multi-stage interactive flow), zero hard or soft dependencies, no cycles, and no parallel groups. This is correct — the skill has one linear evaluation path from checklist load → script evaluation → LLM quality judgment → write outputs. There is no fan-out opportunity being missed, and no sequential-vs-parallel misalignment.

The skill correctly avoids the implicit-read trap: it does not use "review", "acknowledge", or "summarize" language that would cause the parent to pre-read artifacts before delegating to the evaluator script.

---

## Aggregate Token Savings

| Finding | Per-run savings (est.) |
|---------|----------------------|
| SF-01: Near-match discovery in script | 50–80 tokens × failing FILE items |
| SF-02: Delta table from script | 80–120 tokens |
| **Total (typical run with 2–3 FILE failures)** | **~200–360 tokens** |

Low-to-moderate aggregate. The skill is already well-optimized by having the main evaluator script handle all deterministic checks — the marginal gains above are worth capturing but are not blocking.

---

## Strengths

- **Ideal intelligence placement.** The evaluator script handles all deterministic item types (`FILE`, `CONTENT`, `METRIC`) and surfaces `QUALITY` items as `PENDING_LLM` — the LLM never touches deterministic checks. This is the pattern working exactly as intended.
- **Compact JSON handoff.** The script returns per-item `status` + `evidence` fields, so the LLM reads a structured summary rather than raw artifact files. Token cost for the judgment phase is minimized to only the QUALITY items that need it.
- **Variable substitution in script.** `{coverage_threshold}` and `{project_name}` are passed via `--var` flags and substituted inside the script before glob expansion — the LLM does not do string interpolation itself.
- **Skill-to-create hints in JSON.** When a FILE item fails, the `skill_to_create` field in the JSON output directly feeds the LLM's fix guidance, avoiding re-read of the checklist to find the creator skill.
- **Single, focused evaluation path.** No spurious multi-stage complexity. The workflow is appropriately linear for a gate-check operation.
- **Headless mode is clean.** The JSON return contract is fully specified with exact field names and types. No ambiguity for callers.
