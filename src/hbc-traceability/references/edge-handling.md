# Impact — Edge / Boundary Handling

Boundary rules for the **Impact** capability. Each row = a boundary → the required behavior. Invariant: **never silently drop anything, never silently drift.** Kept in sync with `_bmad-output/specs/spec-traceability-impact/edge-handling.md`.

## DECLARE (Stage 1)

| Boundary | Behavior |
|---|---|
| Matrix not yet initialized | Stop, suggest `traceability init`, do not analyze. |
| Reverse-map yields no REQ for a change | Flag "change not yet traced", ask the user — do not skip. |
| User declares a REQ id absent from the matrix | Report the wrong id, do not analyze. |
| Changed-set empty (git clean + nothing declared) | Report no-op "already in sync", stop. |
| `--since <ref>` wrong/nonexistent | Report the error, do NOT silently fall back to HEAD. |

## IMPACT (Stage 2)

| Boundary | Behavior |
|---|---|
| A REQ is DELETED (req_id disappears) | Warn about the conflict: orphaned downstream, suggest cleanup — do not treat as "no impact". |
| Shared artifact exceeds the N-REQ threshold | Group/summarize the verify list + warn about scale. |
| A REQ row with empty refs (early phase) | Distinguish "no downstream yet" vs "matrix incomplete"; state it clearly. |
| Coarse `design_ref` granularity (entity level) | Accept over-flagging (safe) over dropping. |

## FREEZE-CHECK (Stage 2b)

| Boundary | Behavior |
|---|---|
| The 3 sources disagree | Prioritize **task status > phase-gate > matrix `gate_status`**. |
| Missing `task-breakdown.md` (before Phase 3) | Fall back to gate + matrix; do not assume updatable by default. |

## SUGGEST (Stage 3)

| Boundary | Behavior |
|---|---|
| `design_ref` does not match `ref_skill_map` | Flag for manual handling, do NOT silently drop the artifact. |

## APPLY (Stage 4)

| Boundary | Behavior |
|---|---|
| Owning-skill has no update contract | Interactive: flag for manual update. Headless: `blocked` reason `skill_no_update_contract`. |
| Owning-skill fails at runtime mid-way | Branch-stop, preserve state, report clearly what is/isn't done, continue independent branches. |
| User applies a subset | Support the subset; preserve order; warn that the left-out part may drift. |

## RECONCILE (Stage 5)

| Boundary | Behavior |
|---|---|
| No validator for the artifact type | Rely on LLM semantic review + note "no validator"; do not pass by default. |
| Reconcile fails repeatedly | Limit re-suggest (default 2) → block + notify a human. |

## ADVISORY non-REQ (CAP-7)

| Boundary | Behavior |
|---|---|
| A glossary term is a common word | Filter by word boundary/context, lower the confidence. |
| Coding-standard changed but no code task yet | State clearly "no code task to flag yet", do not stay silent. |

## Cross-cutting

| Boundary | Behavior |
|---|---|
| Two impact runs touch the same artifact | Serialize/lock per artifact, no concurrent overwrite. |
