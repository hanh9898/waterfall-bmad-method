# Business Logic Model — hbc-sync

## 1. Dependency Graph Schema (`assets/dependency-graph.yaml`)

```yaml
# Dependency graph: DAG with shared nodes
# Each node = a document/artifact. edges declare "depends_on" (parents).
version: 1
nodes:
  D-02:
    skill: hbc-create-requirements
    output_glob: "{planning_artifacts}/D-02-*"
    depends_on: []
  D-03:
    skill: hbc-create-glossary
    output_glob: "{planning_artifacts}/D-03-*"
    depends_on: [D-02]
  D-06:
    skill: hbc-create-business-flow-diagram
    output_glob: "{planning_artifacts}/D-06-*"
    depends_on: [D-02]
  D-19:
    skill: hbc-create-er-diagram
    output_glob: "{planning_artifacts}/D-19-*"
    depends_on: [D-02]
  D-12:
    skill: hbc-create-coding-standards
    output_glob: "{planning_artifacts}/D-12-*"
    depends_on: [D-19]
  D-21:
    skill: hbc-create-api-spec
    output_glob: "{planning_artifacts}/D-21-*"
    depends_on: [D-02, D-19]
  D-26:
    skill: hbc-create-test-plan
    output_glob: "{planning_artifacts}/D-26-*"
    depends_on: [D-02, D-06]
  D-27:
    skill: hbc-create-test-spec
    output_glob: "{planning_artifacts}/D-27-*"
    depends_on: [D-02, D-26]
  task-breakdown:
    skill: hbc-task-breakdown
    output_glob: "{implementation_artifacts}/task-breakdown.md"
    depends_on: [D-19, D-27]
  code:
    skill: hbc-implement
    output_glob: "{workflow.source_code_path}"
    depends_on: [D-12, D-27, task-breakdown]
    strategy: code_cascade   # special handling per C-07
  matrix:
    skill: hbc-traceability
    mode: update
    depends_on: [D-02, D-19, D-27, code]
    terminal: true           # always last, delegated fully
```

## 2. Cascade Algorithm (Topological Traversal on DAG)

```
function cascade(graph, changed_nodes, selection):
    # 1. Compute affected set = union of descendants of changed_nodes
    affected = {}
    for n in changed_nodes:
        affected += descendants(graph, n)

    # 2. Validate selection for gaps (BR-14)
    selection = resolve_selection_gaps(graph, affected, selection)
    # → auto-include or warn when an intermediate affected ancestor is deselected

    # 3. Filter by resolved selection
    affected = affected ∩ selection

    # 4. Topological sort (Kahn's algorithm) restricted to affected subgraph
    order = topological_sort(subgraph(graph, affected))
    # → guarantees: a node appears only after ALL its parents in affected set

    # 5. Process in order
    blocked_subtrees = {}
    for node in order:
        if node.id == "matrix":              # BR-04 exception, BR-09
            invoke_skill(node.skill, "update", partial_context, invoked_by_sync=true)
            continue
        if any(parent in blocked_subtrees for parent in node.parents):
            blocked_subtrees.add(node)        # Q2=C: inherit blocked branch
            continue
        save_state(node, "in_progress")        # resume point (BR-10)
        context = gather_context(node, results_of_parents)  # Q3=A: all parents
        decision = classify_change(node, context)            # Q1=C, may set conflict (BR-15)
        if decision in (SEMANTIC, CONFLICT) and not headless:
            ask_user(node, context)            # stop & ask
        elif decision in (SEMANTIC, CONFLICT) and headless:
            blocked_subtrees.add(node); save_state(node, "blocked", "semantic_change_needs_human"); continue
        # BR-13: always suppress downstream auto-sync to prevent infinite loop
        result = invoke_skill(node.skill, "update", context, invoked_by_sync=true)
        if result.status == "blocked":
            blocked_subtrees.add(node)         # Q2=C: branch-stop
            save_state(node, "blocked", result.reason)
        else:
            mark_done(node)
            update_manifest_hash(node)         # BR-06: baseline advances on success
    # 6. Finalize
    clear_state_if_complete()
    return CascadeResult(done, blocked_subtrees, skipped)
```

## 3. State Machine

```
   [IDLE]
     │ start cascade
     ▼
   [ANALYZING] ──> [AWAITING_SELECTION] ──> [CASCADING]
                                                 │
                  ┌──────────────────────────────┼─────────────────┐
                  ▼                ▼              ▼                 ▼
            [NODE_AUTO]     [NODE_ASKING]   [NODE_BLOCKED]   [NODE_DONE]
                  │                │              │                 │
                  └────────────────┴──────┬───────┴─────────────────┘
                                          ▼
                                  [all nodes processed?]
                                     │ no → next node
                                     │ yes
                                     ▼
                                 [TRACEABILITY] ──> [COMPLETE]

   Interrupt at any [NODE_*] → state persisted → resume to that node
```

## 4. Change Classification (Q1=C Hybrid)

**Change detection (BR-06)**: ChangeDetector tính sha256(body) mỗi doc, so với `.sync-manifest.json`. Hash khác → changed. `--changed <doc>` override luôn coi là changed.

**Script heuristic signals** (deterministic pre-pass, sau khi xác định doc đã đổi):
| Signal | Suggested class |
|--------|-----------------|
| Hash đổi nhưng chỉ thêm dòng mới (ID mới), không sửa/xóa dòng cũ | mechanical (likely) |
| Section bị xóa / số dòng giảm | semantic |
| Bảng có cell bị sửa nội dung (không phải thêm row) | semantic |
| REQ/TC ID bị xóa | semantic (high) |
| Downstream reference tới ID vừa bị xóa upstream | semantic + conflict (BR-15) |

**LLM final decision**: đọc heuristic + nội dung thực tế + change context → quyết định mechanical / semantic / conflict. LLM có thể override heuristic với rationale (ghi vào decision log).

## 5. Data Transformations
- Input: user change description (free-text) + auto-detected changed docs (timestamp/hash)
- → ChangeSet: `{changed: [{doc, change_type, sections}], context: "..."}`
- → ImpactReport: `{affected: [{doc, impact_level, reason, skill}], order: [...]}`
- → SelectionResult: `{selected: [doc...], dropped: [doc...]}`
- → CascadeResult: `{done: [...], blocked: [{doc, reason}], skipped: [...]}`
