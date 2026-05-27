# Determinism & Distribution Analysis — hbc-agent-ba

**Scan date:** 2026-05-27  
**Skill type:** Agent (no scripts/ directory)  
**Prepass status:** execution-deps-prepass → pass (0 stages, 0 issues); scripts-temp → no scripts/ directory

---

## Existing Scripts Inventory

None. This skill has no `scripts/` directory. The only script reference is an external shared utility:

- `{project-root}/_bmad/scripts/resolve_customization.py` — invoked in Step 1 for agent-block resolution. This is a project-level script, not skill-owned. Not a duplicate candidate.

---

## Assessment

Intelligence placement is largely correct: the LLM handles persona embodiment, contextual greeter logic, and menu dispatch — all genuinely judgment-dependent operations. The activation sequence is well-structured with a script-first fallback for config resolution (Step 1), which is the right pattern for a fragile TOML merge.

Two operations in the activation sequence are deterministic and would benefit from script pre-passes: the Phase 1 state scan (Step 6) and the config key extraction (Step 5). Both currently ask the LLM to do file I/O and structured-data parsing that has exactly one correct output for any given filesystem state — the definition of script work. The token cost is low-to-moderate per activation, but it compounds on every session start.

---

## Script Findings

### SF-1 — Phase 1 Artifact State Scan (Medium)

**File:line:** `SKILL.md:57-65`  
**LLM tax band:** Medium (150–300 tokens per activation — filesystem glob, 4 pattern checks, status table construction)

**Current pattern:**  
The LLM is told to "Check existing Phase 1 artifacts at the configured output location" for four glob patterns (`D-02*`, `D-03*`, `D-06*`, `phase-1-gate*`) and "build a compact status summary (exists/missing for each)." This is a pure filesystem existence check with deterministic output: given the same directory, the result is always the same table.

**What a script would do:**  
Accept the output path as an argument, glob for each pattern, and emit compact JSON:
```json
{
  "D-02": {"exists": true, "file": "D-02-requirements.md"},
  "D-03": {"exists": false, "file": null},
  "D-06": {"exists": true, "file": "D-06-business-flow.md"},
  "phase-1-gate": {"exists": false, "file": null}
}
```
The LLM receives the JSON pre-pass and formats the status summary from it — zero filesystem reads in the prompt, deterministic input.

**Estimated token savings:** 150–250 tokens per activation (eliminates glob reasoning and directory-read content from context).  
**Language:** Python (stdlib `pathlib`, `glob`, `json`)  
**Pre-pass potential:** High — this is exactly the pre-pass pattern ("hand the LLM compact JSON instead of raw files"). The LLM scanner reads the JSON, not the directory.

**Severity:** Medium. Functionality is correct; this is an efficiency opportunity, not a correctness risk.

---

### SF-2 — Config Key Extraction (Low)

**File:line:** `SKILL.md:49-55`  
**LLM tax band:** Low-to-medium (100–200 tokens — read two YAML files, extract 3–4 scalar keys)

**Current pattern:**  
Step 5 asks the LLM to load `config.yaml` and `config.user.yaml`, then extract `user_name`, `communication_language`, `document_output_language`, and the `hbc` module output location. These are structured lookups with a defined merge order (base → user override). The output is deterministic.

**What a script would do:**  
The shared `resolve_customization.py` in `_bmad/scripts/` already handles TOML merging — a sibling script (or an extension of the same script) accepting `--key config` or similar could emit the relevant YAML keys as a flat JSON dict. Alternatively, a short inline script invocation with `python3 -c "import yaml; ..."` passed the merged config would work.

**Consideration:** The `resolve_customization.py` script already runs in Step 1. If it were extended to emit config keys as part of its output (or as a separate `--key config` mode), Step 5 could consume those values from the same pre-pass without a second file read.

**Estimated token savings:** 100–150 tokens per activation.  
**Language:** Python (stdlib `yaml` or `tomllib`)  
**Pre-pass potential:** Medium — low complexity, but the savings are modest because these files are small.

**Severity:** Low. Correct as-is; script would improve consistency and reduce token overhead at scale.

---

## Distribution Findings

### DF-1 — Steps 5 and 6 Are Sequential but Independent (Low)

**File:line:** `SKILL.md:49-65`  
**Current pattern:** Steps 5 (Load Config) and 6 (Scan Phase 1 State) are listed sequentially. Config loading extracts output path from `hbc` module config; state scanning depends on that path. This creates an apparent ordering constraint that is real but tight: Step 6 needs the output path resolved in Step 5.

**Assessment:** The dependency is valid — the output location for the glob comes from the config. Sequential ordering is correct here. No distribution opportunity exists without first resolving the path. This is not an issue.

**Severity:** None / noted for completeness.

---

### DF-2 — Menu Dispatch Return Pattern Is Efficient (Strength — see below)

The return-to-menu-with-updated-status pattern at `SKILL.md:81` correctly re-uses the activation-time state scan pattern rather than loading all artifacts. No distribution issue here.

---

### DF-3 — No Implicit-Read Trap Detected

Reviewing activation language: Step 4 ("load the referenced contents as facts"), Step 5 ("Load config from..."), and Step 6 ("Check existing...") — none of these precede a subagent delegation that would suffer from implicit pre-reading. This agent dispatches to child skills via menu, not subagents launched from within its own context. The implicit-read trap does not apply to menu dispatch. Clean.

---

### DF-4 — Merge Rules Re-explained in Fallback (Low)

**File:line:** `SKILL.md:27-33`  
**Current pattern:** The fallback block for Step 1 (when `resolve_customization.py` fails) re-states the TOML merge rules inline: "Scalars override, tables deep-merge, arrays of tables keyed by `code` or `id` replace matching entries and append new entries, and all other arrays append." This is ~40 tokens of merge-rule explanation that duplicates what `customize.toml` comments already document.

**Consideration:** The fallback is a safety net for a fragile operation (the resolver failing), and the merge rules qualify as BMad institutional knowledge the model genuinely needs for correct fallback behavior. The re-statement is therefore defensible — it is the fallback procedure, not padding. However, if the project-level resolver contract is documented elsewhere and trusted, this block could be trimmed to "apply BMad structural merge rules to base → team → user" without loss of correctness.

**Impact:** ~40 tokens. Marginal.  
**Severity:** Low. Not a script opportunity; a brevity opportunity.

---

## Aggregate Token Savings Estimate

| Finding | Per-activation savings | Frequency | Priority |
|---------|----------------------|-----------|----------|
| SF-1 Phase 1 state scan script | 150–250 tokens | Every activation | Medium |
| SF-2 Config key extraction | 100–150 tokens | Every activation | Low |
| DF-4 Merge rules trim | ~40 tokens | Every activation (fallback rare) | Low |
| **Total per activation** | **290–440 tokens** | | |

At 10 activations/day: ~3,000–4,400 tokens/day saved. Not significant at current scale, but the state-scan script (SF-1) has additional value beyond tokens: it makes the status display deterministic and testable, removing the possibility of the LLM misreading a glob result.

---

## Strengths

**Script-first fallback architecture (Step 1):** The pattern of "run the script; if it fails, do it yourself" for the TOML resolver is the right design for fragile operations. It keeps the happy path deterministic while preserving agent resilience. Worth replicating in SF-1 if a state-scan script is added.

**No stages, no dependency graph over-constraint:** The prepass confirms zero stages and zero dependency issues. The agent uses a flat linear activation (not a multi-stage workflow), which is appropriate for an interactive coordinator. No parallelism is being blocked.

**Menu dispatch is outcome-based:** "Accept a number, menu `code`, or fuzzy description match. Only clarify when two or more items are genuinely ambiguous." This is the correct form — it describes the outcome (dispatch) rather than prescribing how the LLM should parse input. No improvement needed.

**No subagent spawning:** This agent dispatches to skills, not subagents. The subagent-spawning-from-subagent failure mode and the implicit-read trap do not apply. The architecture correctly stays within the agent's lane.

**Compact status presentation:** Step 7 correctly instructs the agent to show the Phase 1 status summary before rendering the menu, not as a separate loading step. The intent-before-presentation flow is efficient.
