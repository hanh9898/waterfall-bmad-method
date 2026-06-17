# Establish Active Feature (B)

Canonical procedure for resolving the **active feature** at the start of an HBC
agent session. HBC delivers incrementally **per feature** — establish the active
feature once at the start of the session, then keep it for the whole session.

## Resolve

1. **Source order:** arg `feature=<slug>` → session value (established earlier) →
   ask the user (kebab-case, e.g. `change-password`).
2. **Validate** slug against `^[a-z0-9][a-z0-9-]*$`. Reject and re-ask if invalid.
3. **Headless** (`-H` / `--headless` / `{agent.headless_default}`): feature is
   **required** — if no source provides it → return `status: blocked`,
   `reason: feature_required`. Interactive prompting is not allowed in headless mode.

## Carry forward

- **Pass `feature=<slug>`** to EVERY per-feature skill you dispatch
  (REQ/BFD/ERD/API/TP/TS/TB/IM/TE/AC/PG/TR…) — along with the same context capsule.
- Keep the active feature stable for the whole session; if context is lost
  (after compaction), restore it before dispatching further.

## Path layout

- Per-feature artifact: `{output_folder}/features/{feature}/…`
- **Shared** deliverables (D-12 Coding Standards, D-03 Glossary; baseline D-19/D-21):
  `{output_folder}/shared/…` — do NOT pass `feature` to shared skills
  (GLO, CS; ERD/API when writing the baseline).

## Phase 0 reminder

If `shared/coding-standards/D-12-*` or `shared/glossary/D-03-*` does not exist yet,
suggest running `hbc-project-init` ([PI]) to create the shared deliverables before
starting the first feature.
