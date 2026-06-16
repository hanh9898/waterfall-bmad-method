---
name: hbc-sync
description: "Cascade document synchronization for the HBC waterfall lifecycle. When a document changes, propagate the change to all downstream documents, plans, tests, and code by orchestrating each owning skill's update. Use when user says 'sync', 'đồng bộ tài liệu', 'cascade', 'lan truyền thay đổi', 'cập nhật liên quan', or agent menu [SYNC]."
---

# Sync (Cascade Document Synchronization)

## Overview

When any HBC document changes, its downstream documents, plans, tests, and code can fall out of sync. hbc-sync is the **orchestrator** that closes this gap: it analyzes the dependency graph (a DAG), determines which documents are impacted, lets you select what to update, then invokes each document's **owning skill** in `update` mode — in dependency order.

**Core principle — single responsibility (BR-01):** hbc-sync NEVER edits document content itself. Each downstream skill owns its own update. hbc-sync only detects, analyzes, orchestrates, and tracks.

Five-stage workflow: **Detect → Analyze → Select → Cascade → Reconcile**. Supports three trigger modes (manual, hybrid, auto-chained) and headless operation. Requires Python 3.10+ and PyYAML for the deterministic scripts.

**Args:** free-text change description (e.g. "added REQ-010 to D-02"); optional `--changed <docs>`, `--headless` / `-H`, `--invoked-by-sync`.

## Conventions

- Bare paths (e.g. `assets/dependency-graph.yaml`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.
- Communicate in `{communication_language}`; decision log in `{document_output_language}`.

## On Activation

Resolve the `{workflow.*}` block: run `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`. If missing, hand-merge `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml` (scalars override, arrays append).

Execute `{workflow.activation_steps_prepend}`. Load `{workflow.persistent_facts}` and config (`{output_folder}`, `{planning_artifacts}`, `{communication_language}`, `{document_output_language}`). Execute `{workflow.activation_steps_append}`.

**Resume check:** load cascade state first —
`python3 {skill-root}/{workflow.sync_state_script} --action load --state-path {workflow.state_path}`.
If `sync_in_progress: true`, surface the interrupted cascade and offer Resume (continue from first non-done node) or Restart. In headless mode, resume silently.

## Headless Mode

`--headless` / `-H` runs without prompts. Full contract — flags, return schema, closed-set blocked reasons — in [`references/headless-contract.md`](references/headless-contract.md). Key rules: auto-select all affected, auto-close selection gaps, mechanical changes auto-applied, semantic/conflict changes return `blocked`, every downstream skill invoked with `--invoked-by-sync` (BR-13).

## Workflow

### Stage 1 — Detect

Load + validate the dependency graph (BR-11):
```
python3 {skill-root}/{workflow.load_graph_script} --graph {skill-root}/{workflow.graph_path} --project-root {project-root}
```
If `validation.is_dag` is false → HALT (interactive) or return `blocked` reason `graph_has_cycle` (headless).

Determine the changed set (BR-06):
```
python3 {skill-root}/{workflow.analyze_impact_script} --graph {skill-root}/{workflow.graph_path} \
  --manifest {workflow.manifest_path} --project-root {project-root} [--changed <docs>]
```
The script compares each document's body hash (frontmatter stripped) against the baseline manifest; `--changed` forces specific nodes. Combine with the user's free-text description for semantic context. If `is_noop: true` (nothing changed), report "Đã đồng bộ — không có thay đổi" and stop (idempotence, BR-12).

### Stage 2 — Analyze

The analyze-impact output gives `affected` and topological `order`. For each affected document, apply **LLM judgment** to assign:
- **impact_level** (high/medium/low) — by change type (semantic vs mechanical) and how much the downstream depends on the changed part (BR-07). Qualitative, with a one-line rationale.
- **classification** — mechanical / semantic / conflict. Use the script heuristics (added-only lines → mechanical; deleted sections, edited table cells, removed REQ/TC ids → semantic; downstream references to a removed upstream id → conflict, BR-15) then decide.

### Stage 3 — Select

Present impact as a **tree view** (highlight affected nodes in the DAG) **and a table** (document · impact_level · classification · reason · owning skill). Let the user check/uncheck documents to update.

**Selection gap guard (BR-14):** if the selection keeps a node but drops an affected parent, warn and offer to auto-include the parent or accept the risk. Re-run analyze-impact with `--selected <ids> --auto-close-gaps` to compute the gap-free order. Headless: auto-close, log a warning.

### Stage 4 — Cascade

Process selected nodes in topological order (parents before children, BR-02; shared nodes once, BR-03). For each node:

1. Save resume state: `sync-state.py --action save --state-path {workflow.state_path} --payload '{"node":"<id>","status":"in_progress"}'` (BR-10).
2. Gather context from the original change + results of already-processed parents (structured JSON + human summary).
3. **Stop/ask (BR-05):** if classification is semantic/conflict and interactive → ask the user how to handle before proceeding; if headless → mark the node `blocked` (`semantic_change_needs_human` / `downstream_conflict`) and continue other branches.
4. **Invoke the owning skill in update mode, ALWAYS with the suppression flag (BR-13):**
   e.g. `hbc-create-test-spec update --invoked-by-sync` (headless adds `--headless`). The flag prevents the invoked skill from re-triggering sync (no infinite loop).
5. **`code` node (BR-08):** classify change scope and suggest a strategy — SMALL → flag affected tasks; MEDIUM → create new task(s) via `hbc-task-breakdown update` then `hbc-implement`; LARGE → recommend a full task-breakdown re-run. Confirm with user (interactive); headless auto-flags SMALL and blocks MEDIUM/LARGE.
6. On skill result: `complete` → mark done and advance the baseline (`sync-state.py --action update-manifest --node <id> --file <path>`); `blocked` → branch-stop (mark node + descendants skipped, BR-04), keep state for resume.

### Stage 5 — Reconcile

The `matrix` node runs last regardless of branch-stop (BR-04 exception, BR-09): invoke `hbc-traceability update --invoked-by-sync` (headless adds `-H`) so the matrix reflects the cascade — even partial. If the user deselected matrix, skip but warn "traceability có thể lệch".

Clear cascade state when complete: `sync-state.py --action clear --state-path {workflow.state_path}`. Append a session summary to `{workflow.decision_log}`: changed set, affected/selected, per-node outcome, blocked nodes + reasons, semantic decisions.

Report: documents updated, blocked (with reasons + fix guidance), skipped, and whether traceability was reconciled.

## Trigger Modes (REQ-005)

- **Manual** — user invokes `hbc-sync` / menu [SYNC] directly.
- **Hybrid** (default) — after an update skill finishes, it suggests running sync; user confirms.
- **Auto-chained** — an update skill with `auto_sync_after_update=true` invokes sync automatically. To avoid loops, sync ALWAYS invokes downstream skills with `--invoked-by-sync`, and those skills MUST suppress their own trigger when the flag is present (BR-13).

## On Complete

Read `{workflow.on_complete}` if set; otherwise return to the invoking agent menu.
