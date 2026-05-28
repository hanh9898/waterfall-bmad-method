# Headless Contract

Communicate with the user in `{communication_language}`.

Authoritative reference for `--headless` / `-H` invocation of `hbc-create-business-flow-diagram`. Stages in `SKILL.md` cite this file for the closed-set of `reason` values and the defaults heuristics; the brief reason list in SKILL.md is a compaction-survival mirror, not a separate source of truth.

## Input flags

| Flag | Default | Effect |
|---|---|---|
| `-H` / `--headless` | off | Skip every interactive prompt; resolve decisions via the defaults table below; emit JSON return contract on completion or block. |
| `--prd-path=<path>` | unset | Use this exact PRD location, skip discovery glob. Repeatable for sharded PRDs or multiple sources. |
| `--mode=greenfield\|migration` | inferred | Force mode; skip mode confirmation. |
| `--scope=single\|multi` | inferred | Force scope; skip scope confirmation. |
| `--diagram-type=sequenceDiagram\|flowchart\|stateDiagram` | `{workflow.diagram_type}` | Force diagram type. |
| `--no-prd-ok` | off | In headless: treat absent PRD as "continue with greenfield elicitation". Without this flag, headless + no PRD → return `blocked`. |
| `--review-lenses=skip\|advanced\|party` | `skip` | Force the Stage-3 / Stage-4 parallel-lens menu. `skip` = no review. `advanced` = invoke `bmad-advanced-elicitation` at both stages. `party` = invoke `bmad-party-mode`. |
| `--scope-of-change=polish\|semantic\|auto` | `auto` | Update mode only. `polish` appends a note to the prior revision-history row without bumping. `semantic` appends a new row with a minor-version bump. `auto` (default) diffs `stage_2_actors` and `stage_2_flows` against the prior session's flush block — identical arrays → polish; any difference → semantic. |
| `--update-flow=<flow-name>` | unset | Update mode only. Re-render only the named flow, leaving other Mermaid blocks untouched. Without this flag, Update mode re-renders every in-scope flow. |
| `--allow-migration-without-as-is` | off | Acknowledge that `--mode=migration` was passed but no AS-IS / 現状 / "current state" markers exist in the PRD sources. Without this flag, the combination returns `blocked` with `reason: "migration_without_as_is"`. |

## Defaults table (when a flag is not provided)

| Decision | Headless default | Heuristic |
|---|---|---|
| Source selection | every match in `discover-planning-artifacts.py` output | scripted, deterministic |
| Resume vs Update vs Fresh | from `resume_state.recommended_intent` (Resume only when `stage-1` is in `stepsCompleted`; Fresh when `stepsCompleted` is empty even if primary exists — `fresh_reason: "crashed_no_progress"` is logged separately from `fresh_reason: "no_workspace"`) | from `.decision-log.md` + primary frontmatter |
| Mode | greenfield | unless PRD body contains "AS-IS", "current state", or `現状` → migration |
| Scope | single | unless `discover-planning-artifacts.py` reports >1 sub-process candidate → multi |
| Diagram type | `{workflow.diagram_type}` | configured default |
| Parallel-lens menu (Stage 3 + Stage 4) | `skip` (no review) | unless `--review-lenses` overrides |
| Stage-3 scope-of-change classification | `auto` (diff Stage 2 flush) | unless `--scope-of-change` overrides |
| Stage-3 update target | every in-scope flow | unless `--update-flow=<name>` narrows it |
| Stage-4 auto-fix | apply only validator findings with `auto_fixable: true` | from `validate-mermaid.py` per-issue flag |

Every auto-decision is appended to `{doc_workspace}/.decision-log.md`.

## JSON return contract

**Substitute every `{placeholder}` with its resolved value before emitting** — the contract below shows the template, not the literal output.

On success:
```json
{
  "status": "complete",
  "skill": "{skill-name}",
  "artifact": "{doc_workspace}/D-06-business-flow-diagram.md",
  "decision_log": "{doc_workspace}/.decision-log.md",
  "validation": {
    "mermaid": "{doc_workspace}/.scan/mermaid.json",
    "fr": "{doc_workspace}/.scan/fr.json"
  },
  "review_lenses_run": []
}
```

`review_lenses_run` is a list of `"advanced"` / `"party"` strings recording which review lenses fired during the run (empty when `--review-lenses=skip`).

On block:
```json
{
  "status": "blocked",
  "skill": "{skill-name}",
  "reason": "<one of the values below>",
  "decision_log": "{doc_workspace}/.decision-log.md",
  "review_lenses_run": []
}
```

Defined `reason` values (closed set — automators may switch on these):

| Reason | When it fires |
|---|---|
| `template_missing` | `{workflow.business_flow_template}` does not exist on disk. |
| `no_prd_and_no_interactive_in_headless` | Headless mode, zero PRDs found, and `--no-prd-ok` not set. |
| `planning_artifacts_unreadable` | `{planning_artifacts}` directory unreadable or absent. |
| `mermaid_validation_failed` | `validate-mermaid.py` returned issues that were not all `auto_fixable: true`. |
| `fr_coverage_gap` | `check-fr-coverage.py` reported `uncovered` or `phantom` FR ids. |
| `migration_without_as_is` | `--mode=migration` requested but no PRD source contains AS-IS / 現状 / "current state" markers, and `--allow-migration-without-as-is` was not passed. |
| `resolver_missing` | The customization resolver script failed AND the SKILL.md hand-merge fallback could not complete. |

Add new reasons only by extending this table — automators rely on the closed-set guarantee.
