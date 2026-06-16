# Headless Contract — hbc-sync

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--headless` / `-H` | Yes | Run non-interactively |
| `--changed` | No | Comma/space-separated changed node ids (override hash detection). If omitted, auto-detect via manifest |
| `--select-all` | No | Auto-select ALL affected nodes (headless default) |
| `--context` | No | Free-text change description for semantic understanding |
| `--invoked-by-sync` | No | Internal guard — set when a skill is invoked BY sync, to suppress its own auto-sync trigger (BR-13) |

Example:
`hbc-sync --headless --changed D-02 --context "added REQ-010 for payment refund"`

## Behavior in Headless Mode

1. Change detection runs against `.sync-manifest.json` (BR-06); `--changed` overrides.
2. ALL affected nodes auto-selected; selection gaps auto-closed (BR-14).
3. **Mechanical** changes → auto-invoke downstream skills (each with `--invoked-by-sync`).
4. **Semantic** changes or **conflicts** → NOT auto-applied; node returns `blocked`.
5. `matrix` node always runs last on partial results (BR-04 exception, BR-09).
6. State persisted before each node (resume-safe); cleared on completion.

## Return Schema

```json
{
  "status": "complete | partial | blocked",
  "changed": ["D-02"],
  "affected": ["D-03", "D-06", "D-19", "D-21", "D-26", "D-27", "task-breakdown", "code", "matrix"],
  "order": ["D-03", "D-06", "D-19", "D-21", "D-26", "D-27", "task-breakdown", "code", "matrix"],
  "done": ["D-03", "D-06", "D-19"],
  "blocked": [
    { "doc": "D-27", "reason": "semantic_change_needs_human" }
  ],
  "skipped": ["task-breakdown", "code"],
  "auto_included": [],
  "is_noop": false,
  "state_path": "/path/to/.sync-state.json",
  "reason": "string (only when status=blocked at top level)"
}
```

## Status Values

- **complete** — all affected (selected) nodes updated successfully.
- **partial** — some nodes done, some blocked/skipped (branch-stop, BR-04).
- **blocked** — cascade could not start (e.g. invalid graph). `reason` set.

## Blocked Reasons (closed set)

- `graph_has_cycle` — dependency graph is not a DAG (BR-11). Extend with load-graph fix.
- `graph_not_found` — graph file missing.
- `pyyaml_unavailable` — cannot parse YAML graph.
- `semantic_change_needs_human` — node change is semantic; needs human judgment (BR-05).
- `downstream_conflict` — downstream contradicts the upstream change (BR-15).
- `skill_invocation_failed` — a delegated skill returned a non-recoverable error.
- `manifest_unreadable` — baseline manifest corrupted.

> When adding a reason, extend BOTH this list and the orchestration logic together.

## Circular-Trigger Safety (BR-13)

When hbc-sync invokes any downstream skill, it passes `--invoked-by-sync`. Skills
with `auto_sync_after_update` enabled MUST detect this flag and suppress their own
sync trigger — otherwise the update→sync→update loop never terminates.
