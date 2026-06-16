# Skill Integration Contract — hbc-sync triggers

This document specifies how the existing document-creating skills integrate with
hbc-sync to support the three trigger modes (REQ-005) without infinite loops
(BR-13). The change to each skill is **additive and safe** — default behavior is
unchanged.

## 1. Config flag (customize.toml)

Each document-creating skill gains one `[workflow]` key:

```toml
# When true, after a successful `update`, automatically invoke hbc-sync to
# cascade the change downstream (auto-chained trigger, REQ-005). Default false.
auto_sync_after_update = false
```

Default `false` means no behavior change unless a team opts in via override.

## 2. Handoff suggestion (hybrid trigger — SKILL.md)

At the skill's Save/Handoff stage, when running in `update` mode AND NOT invoked
by sync, add a one-line suggestion:

> _"Tài liệu đã cập nhật. Chạy `hbc-sync` để đồng bộ các tài liệu/test/code phụ thuộc?"_

This realizes the **hybrid** trigger: the user is reminded but stays in control.

## 3. Suppression guard (auto-chained safety — BR-13)

The skill MUST detect the `--invoked-by-sync` flag (or `invoked_by_sync=true` in
headless context). When present:

- Do NOT run the handoff suggestion (step 2).
- Do NOT auto-trigger sync (step 1), even if `auto_sync_after_update = true`.

This is the teeth that prevents the loop: `update → sync → update → sync → …`.
hbc-sync ALWAYS passes `--invoked-by-sync` when it invokes a skill, so any skill
reached through a cascade will not start a new cascade.

## 4. Decision table

| Invocation | `auto_sync_after_update` | `--invoked-by-sync` | Action after update |
|------------|--------------------------|---------------------|---------------------|
| User runs skill directly | false | absent | Suggest sync (hybrid) |
| User runs skill directly | true  | absent | Auto-invoke hbc-sync (auto-chained) |
| Invoked BY hbc-sync | any | present | Do nothing (suppressed, BR-13) |

## 5. Skills in scope (10)

hbc-create-requirements, hbc-create-glossary, hbc-create-business-flow-diagram,
hbc-create-er-diagram, hbc-create-coding-standards, hbc-create-api-spec,
hbc-create-test-plan, hbc-create-test-spec, hbc-task-breakdown, hbc-implement.

> The `matrix` (hbc-traceability) is a cascade target, not a trigger source — it
> does not need the auto_sync flag (it is always terminal, BR-09).
