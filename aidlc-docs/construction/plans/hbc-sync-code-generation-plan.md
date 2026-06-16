# Code Generation Plan — hbc-sync

## Unit Context
- **Unit**: hbc-sync (cascade document synchronization orchestrator skill)
- **Project type**: Brownfield — BMad skill module
- **Code location**: `src/hbc-sync/` (workspace root, theo convention module — KHÔNG vào aidlc-docs/)
- **Documentation**: `aidlc-docs/construction/hbc-sync/code/` (markdown summaries only)
- **Requirements covered**: REQ-001 → REQ-009
- **Business rules**: BR-01 → BR-15
- **PBT properties**: P-1 → P-7 (Partial mode: PBT-02, 03, 07, 08, 09)

## Reference: Existing Skill Pattern (từ Reverse Engineering)
- SKILL.md: frontmatter (name + description với trigger phrases) + Overview + Conventions + Headless + On Activation + workflow stages
- customize.toml: `[workflow]` block với 3-layer override header
- scripts/: Python 3.10+, argparse CLI, JSON output (`ensure_ascii=False`)
- references/headless-contract.md: input args + JSON return schema + closed-set blocked reasons

## Generation Steps

### Step 1: Skill Core — SKILL.md
- [x] Create `src/hbc-sync/SKILL.md`
- [ ] Frontmatter: name=hbc-sync, description với trigger phrases ("sync", "đồng bộ", "cascade", "lan truyền thay đổi", menu [SYNC])
- [ ] Overview: orchestrator pattern, single responsibility, DAG cascade
- [ ] Conventions (skill-root, project-root, skill-name resolution)
- [ ] On Activation: resolve customization, load graph
- [ ] Workflow stages: Detect → Analyze → Select → Cascade → (Traceability)
- [ ] Headless Mode section
- **Covers**: REQ-001..009, BR-01..15

### Step 2: Configuration — customize.toml
- [x] Create `src/hbc-sync/customize.toml`
- [ ] `[workflow]` block: graph_path, manifest_path, state_path, skill_mappings, trigger defaults, source_code_path
- [ ] 3-layer override header comment
- **Covers**: REQ-001 (configurable graph), REQ-005 (trigger config), NFR-003

### Step 3: Dependency Graph — assets/dependency-graph.yaml
- [x] Create `src/hbc-sync/assets/dependency-graph.yaml`
- [ ] DAG nodes D-02..code + matrix theo functional design (business-logic-model.md §1)
- [ ] depends_on edges, skill mappings, terminal/strategy flags
- **Covers**: REQ-001 (DAG with shared nodes)

### Step 4: Script — load-graph.py
- [x] Create `src/hbc-sync/scripts/load-graph.py`
- [ ] Parse YAML, build graph, validate DAG (no cycle — BR-11)
- [ ] CLI: `--graph <path> --project-root <path> [-o out.json]`
- [ ] JSON output: nodes, topological order, validation result
- **Covers**: REQ-001, BR-11, P-1

### Step 5: Script — analyze-impact.py
- [x] Create `src/hbc-sync/scripts/analyze-impact.py`
- [ ] ChangeDetector: so hash vs `.sync-manifest.json` (BR-06)
- [ ] ImpactAnalyzer: descendants traversal + dedupe shared nodes + topological order
- [ ] Selection gap resolution helper (BR-14)
- [ ] CLI: `--graph --manifest --changed <docs> --project-root [-o]`
- [ ] JSON: affected[], order[], gaps[]
- **Covers**: REQ-002, BR-02, BR-03, BR-06, BR-14, P-2, P-3, P-6, P-7

### Step 6: Script — sync-state.py
- [x] Create `src/hbc-sync/scripts/sync-state.py`
- [ ] State save/load/clear (`.sync-state.json`) + manifest update (`.sync-manifest.json`)
- [ ] body-hash helper (sha256, strip frontmatter)
- [ ] CLI: `--action save|load|clear|hash|update-manifest ...`
- **Covers**: REQ-006, BR-10, BR-06, NFR-002, P-4, P-5

### Step 7: Headless Contract — references/headless-contract.md
- [x] Create `src/hbc-sync/references/headless-contract.md`
- [ ] Input args table (`--headless`, `--changed`, `--select-all`, `--invoked-by-sync`)
- [ ] JSON return schema (status, cascade_result, affected, blocked, skipped)
- [ ] Closed-set blocked reasons (graph_has_cycle, semantic_change_needs_human, downstream_conflict, ...)
- **Covers**: REQ-006, BR-05, BR-13, BR-15

### Step 8: PBT Tests — scripts/tests/
- [x] Create `src/hbc-sync/scripts/tests/test_properties.py`
- [ ] Hypothesis strategies: dag_strategy, graph_with_cycle, sync_state, sync_manifest, changed_nodes, selection_with_gap
- [ ] Properties P-1..P-7 (DAG validity, downstream closure, topological order, state round-trip, idempotence, shared-node single-visit, gap closure)
- [ ] Example-based tests cho critical paths (PBT-10 complement)
- **Covers**: PBT-02, 03, 07, 08, 09, 10; P-1..P-7

### Step 9: Modify Existing Skills — auto-sync trigger + guard
- [x] Thêm config `auto_sync_after_update = false` vào 10 create skill customize.toml
- [x] Tạo references/skill-integration.md (contract đầy đủ + decision table)
- [x] Chèn "Sync Handoff" section vào 10 SKILL.md (hybrid suggest + BR-13 guard)
- **Covers**: REQ-004, REQ-005, BR-13

### Step 10: Module Registration — module.yaml + customize.toml menus
- [x] Note hbc-sync trong post-install-notes của module.yaml ([SYNC] cross-cutting)
- [x] Thêm menu code [SYNC] vào 5 agents (BA/ARCH/QA/DEV/TST)
- **Covers**: REQ-005 (manual trigger qua menu)

### Step 11: Documentation Summaries
- [x] Create `aidlc-docs/construction/hbc-sync/code/implementation-summary.md`
- [ ] Liệt kê files created/modified, mapping tới REQ/BR
- **Covers**: traceability of implementation

## Story/Requirement Traceability
| Step | REQ | BR | PBT |
|------|-----|----|----|
| 1 | all | all | - |
| 2 | 001,005 | - | - |
| 3 | 001 | 11 | P-1 |
| 4 | 001 | 11 | P-1 |
| 5 | 002 | 02,03,06,14 | P-2,3,6,7 |
| 6 | 006 | 06,10 | P-4,5 |
| 7 | 006 | 05,13,15 | - |
| 8 | all | - | P-1..7 |
| 9 | 004,005 | 13 | - |
| 10 | 005 | - | - |
| 11 | - | - | - |

## Scope Summary
- **Total steps**: 11
- **New files**: ~8 (SKILL.md, customize.toml, dependency-graph.yaml, 3 scripts, headless-contract.md, test file)
- **Modified files**: up to 10 existing skill SKILL.md (handoff section) + module.yaml
- **Doc summaries**: 1
