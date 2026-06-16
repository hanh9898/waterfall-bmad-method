# Architecture Diagrams — capability "impact"

Companion của `SPEC.md`. Chứa sơ đồ; kernel chỉ giữ prose.

## Vòng đời 5 nhịp

```mermaid
flowchart LR
    A[DECLARE<br/>user khai changed-set<br/>git đối chiếu] --> B[IMPACT<br/>đọc matrix cả cột<br/>lan dọc / lan ngang<br/>freeze-check]
    B --> C[SUGGEST<br/>trình impact + thứ tự skill<br/>KHÔNG tự sửa]
    C --> D[APPLY<br/>user bấm → gọi owning-skill<br/>update mode + --invoked-by-sync]
    D --> E[RECONCILE<br/>validator + matrix tươi<br/>+ LLM semantic review]
    E -.->|chưa lan đúng| C
```

## Luồng dữ liệu — chỉ ĐỌC, không sở hữu state

```mermaid
flowchart TD
    subgraph SOT[Nguồn sự thật đã có - chỉ đọc]
        M[traceability matrix<br/>REQ↔artifact + gate_status]
        T[task-breakdown.md<br/>status TODO/IN_PROGRESS/DONE]
        G[hbc-phase-gate<br/>PASSED/FAILED]
        V[git diff<br/>baseline + drift]
    end
    IMPACT[capability impact] --> M & T & G & V
    IMPACT --> SUGGEST[suggest cho user]
    SUGGEST --> OWN[owning-skills update mode]
    OWN --> M
```

## Hai loại lan (CAP-2)

```mermaid
flowchart LR
    R10[REQ-010 đổi<br/>credit_limit → theo chi nhánh]
    R10 -->|lan DỌC = apply| DS[hạ nguồn REQ-010<br/>D-19 → D-27 → code<br/>theo thứ tự waterfall]
    R10 -->|đổi artifact dùng chung| CUS[(thực thể Customer)]
    CUS -->|lan NGANG = verify| R22[REQ-022 dùng chung Customer<br/>review order.py / TC-220]
    DS --> FZ{freeze-check}
    R22 --> FZ
    FZ -->|updatable| ED[đề xuất cập nhật]
    FZ -->|frozen/done| NT[đề xuất TẠO TASK MỚI]
```
