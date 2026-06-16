# Unit Test Execution — hbc-sync

## Run Property-Based + Unit Tests

### 1. Execute All Tests (standalone runner)
```bash
python src/hbc-sync/scripts/tests/test_properties.py
```
Hoặc qua pytest (nếu cài):
```bash
pytest src/hbc-sync/scripts/tests/test_properties.py -v
```

### 2. Expected Results
- **10/10 properties pass** (no failures)
- Output kết thúc bằng: `All hbc-sync property tests passed.`

| Test | Property | PBT Rule |
|------|----------|----------|
| test_p1_valid_dag_has_no_cycle | P-1 DAG validity | PBT-03 |
| test_p1_cycle_is_detected | P-1 cycle rejection | PBT-03 |
| test_p2_downstream_closure | P-2 downstream closure | PBT-03 |
| test_p3_topological_order | P-3 topo order | PBT-03 |
| test_p4_state_round_trip | P-4 state round-trip | PBT-02 |
| test_p5_no_change_is_noop | P-5 idempotence | PBT-03 |
| test_p6_each_node_once | P-6 single-visit | PBT-03 |
| test_p7_gap_closure | P-7 gap closure | PBT-03 |
| test_body_hash_deterministic | hash determinism | PBT-02 support |
| test_body_hash_ignores_frontmatter | frontmatter-stripped hash | BR-06 |

### 3. Reproducibility (PBT-08)
- Hypothesis tự shrink khi fail (không disable)
- Khi fail, log seed để replay: chạy với `HYPOTHESIS_SEED` hoặc đọc seed trong output
- CI nên log seed mỗi run

### 4. Fix Failing Tests
1. Đọc shrunk minimal failing case trong output Hypothesis
2. Sửa logic trong `sync_common.py` / `load-graph.py` / `sync-state.py`
3. Thêm shrunk case làm example-based regression test (PBT-10)
4. Rerun đến khi pass
