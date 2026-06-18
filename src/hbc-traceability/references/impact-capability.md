# Impact Capability — Cascade Document Sync

Operational detail for the **Impact** capability (the 5th, beside Initialize/Update/Report/Audit). SKILL.md holds the concise flow; this file holds the per-stage rules. Contract of record: `_bmad-output/specs/spec-traceability-impact/SPEC.md`.

**Core principle:** Impact only READS the existing sources of truth (matrix, task-breakdown status, phase-gate, git), infers the impact, and SUGGESTS — **it never edits content itself**. Every edit goes through the owning-skill in `update` mode. Humans decide, the system suggests.

Lifecycle: **DECLARE → IMPACT → FREEZE-CHECK → SUGGEST → (validate-plan) → APPLY → RECONCILE → ADVISORY (non-REQ)**.

Every `impact.py` command passes the `{workflow.*}` values configured in `customize.toml` (git baseline, flood-threshold, gate-reports-glob, task-breakdown, reconcile-max-retries) — nothing hardcoded.

## Stage 1 — DECLARE (CAP-1)

The user declares the REQ/artifact that just changed. Corroborate against git and normalize to REQ:

```
python3 scripts/impact.py detect --matrix {workflow.matrix_path} \
  --declared "<REQ-xxx,...>" --since {workflow.impact_git_baseline} --project-root {project-root}
```

- The git baseline defaults to `{workflow.impact_git_baseline}` (working tree vs HEAD); replace it with another ref when the user specifies one at runtime.
- Non-REQ changes (code/test/design) are reverse-mapped to REQ via the matrix (`code_ref`/`test_ref`/`design_ref` → `req_id`).
- Present the `changed-set` for the user to **confirm** before moving to IMPACT.
- Boundaries (matrix not initialized, untraced change, wrong REQ id, empty changed-set → no-op, bad `--since`): see `references/edge-handling.md`.

## Stage 2 — IMPACT (CAP-2)

Read the matrix across **all columns** to find every affected REQ/artifact:

```
python3 scripts/impact.py analyze --matrix {workflow.matrix_path} \
  --changed "<REQ-xxx,...>" --flood-threshold {workflow.impact_flood_threshold} --project-root {project-root}
```

The script returns two facets, deduped on shared artifacts:
- **VERTICAL spread (apply)** — the downstream of the REQ that just changed.
- **HORIZONTAL spread (verify)** — other REQs whose ref points at the same artifact (review only; they do not change on their own).

LLM judgment on the script's output: confirm the apply/verify labels, assign impact_level, filter noise. Boundaries (a deleted REQ → orphan conflict; shared-artifact flood; still-empty ref): see `references/edge-handling.md`.

## Stage 2b — FREEZE-CHECK (CAP-3)

Classify each affected **REQ** as updatable or frozen:

```
python3 scripts/impact.py freeze --matrix {workflow.matrix_path} \
  --reqs "<REQ-xxx,...>" --task-breakdown {workflow.task_breakdown_path} \
  --gate-reports-glob {workflow.gate_reports_glob} --project-root {project-root}
```

Combine the 3 sources; on disagreement, **prioritize: task status > phase-gate > matrix `gate_status`**. A frozen artifact (done/PASSED) → **do not edit in place**, route to a "create new task" suggestion. Missing task-breakdown → fall back to gate+matrix.

## Stage 3 — SUGGEST (CAP-4)

Present the impact to the user, use `{workflow.ref_skill_map}` to map each ref → owning-skill, ordered by the sequential phase order (design→test→code; apply before verify). Present a suggestion table, then stop — every application waits for the user to act (Stage APPLY). A ref with no mappable skill → flag for manual handling, do not silently drop it. The output is a suggestion table of "which skill to run, in what order" + a "create new task" list for the frozen part.

**Validate-plan (before APPLY):** before mutating anything, re-confirm the plan against the sources of truth — each ref still resolves to an owning-skill, the frozen part routes to a new-task (no in-place edit), the apply/verify labels are consistent. Present the validated plan to the user; only proceed to APPLY when the user agrees (headless: continue once validated). This is the final checkpoint before an irreversible operation.

## Stage 4 — APPLY (CAP-5)

Only when the user acts. For each selected item (a **subset** is supported), call the owning-skill in `update` mode **always with `--invoked-by-sync`** (anti-loop):

```
<owning-skill> update --invoked-by-sync [--headless]
```

- No update contract → interactive flag for manual handling; headless `blocked` reason `skill_no_update_contract`.
- Owning-skill runtime error → branch-stop that branch, preserve state, continue independent branches.
- `code` node: follow `hbc-implement`'s strategy (task-level), do not blindly regenerate.
- **Resume state:** before each node, write the cascade progress to `{output_folder}/traceability/.cascade-state.json` — a **separate file, DISTINCT from Update's `.trace-state.json`** (avoid schema collision). Contents `{cascade_in_progress, applied:[], pending:[], dispositions:{node→reconciled|deferred|frozen_task|blocked}, started}`; clear on completion. When activation sees leftover state → offer **Resume** (continue from the first `pending`) or **Restart**; headless resumes silently.

## Stage 5 — RECONCILE (CAP-6)

Verify "the change propagated correctly" — **2 main pillars + 1 auxiliary**:
1. **Deterministic validator** pass (e.g. `hbc-implement/scripts/validate-implementation.py`, D-27 facet coverage). No validator for the artifact type → rely on pillar 2, note "no validator".
2. **LLM semantic review** (rubric: `src/hbc-shared/references/semantic-review-rubric.md`) — read the original change + the updated artifact, judge that the specific change is present; also handle the horizontal verify spread.
3. (auxiliary) the fresh matrix cell — corroboration only, it does not prove the content changed.

Not-propagated-correctly → push back to SUGGEST (no clear, no rollback). The re-suggest loop is capped at `{workflow.impact_reconcile_max_retries}` → block + notify a human. Finally run `hbc-traceability update` for the related REQ so the matrix reflects the cascade.

> **When the cascade touched D-27 (added/renumbered TCs), re-pull `test_ref` (DF-9).** A cascade that grows D-27 is the exact source of matrix `test_ref` drift — the Update Phase 2 re-run above re-extracts TC↔REQ from the current D-27. Confirm it landed with `trace-report.py --matrix … --d27 …`: `d27_sync.in_sync` must be true (no `test_ref_drift`) before the cascade is considered reconciled. This is corroboration for pillar 3, not a substitute for the semantic review.

**Completeness check (close the cascade):** run
```
python3 scripts/impact.py complete --state {output_folder}/traceability/.cascade-state.json --changed "<REQ-xxx,...>"
```
The script returns `missing` = nodes in the changed-set with no terminal disposition in `dispositions` (reconciled / deferred-by-user (subset) / frozen→task / branch-stopped-blocked). Any `missing` → report it clearly rather than ending silently.

## Stage 6 — ADVISORY non-REQ (CAP-7)

When the changed-set contains a **non-REQ-bound** artifact (glossary D-03, coding-standard D-12) — a rare case, always **advisory, never auto-applied**:
- **glossary** — reverse-scan non-frozen artifacts for references to the changed term; present a "should review" list with confidence. Filter by word boundary/context to avoid a flood when the term is common (see `references/edge-handling.md`).
- **coding-standard** — flag every non-frozen code task to re-check against the new standard; if there is no code task yet, state clearly "none to flag yet", do not stay silent.

## Trigger modes

- **Manual** — the user calls `hbc-traceability impact` / menu [SYNC].
- **Hybrid** (default) — a create-* skill after `update` suggests running impact; the user confirms.
- **Auto-chained** — a skill with `auto_sync_after_update=true` calls impact directly; the cascade still calls the owning-skill with `--invoked-by-sync` as in APPLY, so it does not loop.
