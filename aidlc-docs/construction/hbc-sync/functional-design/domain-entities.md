# Domain Entities — hbc-sync

## Entity: Graph
| Field | Type | Description |
|-------|------|-------------|
| version | int | Schema version |
| nodes | dict[str, Node] | Map node_id → Node |

Invariant: must be a DAG (BR-11).

## Entity: Node
| Field | Type | Description |
|-------|------|-------------|
| id | str | Document id (D-02, task-breakdown, code, matrix) |
| skill | str | Skill to invoke for update |
| output_glob | str | Path pattern to locate the document |
| depends_on | list[str] | Parent node ids |
| mode | str | Skill mode (default "update") |
| strategy | str? | "code_cascade" for special code handling |
| terminal | bool | True for matrix (always last) |

## Entity: ChangeSet
| Field | Type | Description |
|-------|------|-------------|
| changed | list[ChangedDoc] | Documents detected/declared as changed |
| context | str | User free-text change description |
| detected_at | timestamp | When detection ran |

## Entity: ChangedDoc
| Field | Type | Description |
|-------|------|-------------|
| doc | str | Node id |
| change_type | enum | mechanical \| semantic (initial heuristic) |
| sections | list[str] | Affected sections (best-effort) |
| has_conflict | bool | True nếu downstream mâu thuẫn (BR-15) |

## Entity: SyncManifest (`.sync-manifest.json`)
Baseline để phát hiện thay đổi (BR-06).
```json
{
  "version": 1,
  "last_sync": "2026-06-16T10:00:00Z",
  "doc_hashes": {
    "D-02": "sha256:abc123...",
    "D-19": "sha256:def456...",
    "D-27": "sha256:..."
  }
}
```
- `doc_hashes`: sha256 của body mỗi doc (loại trừ frontmatter) tại lần sync thành công cuối
- Cập nhật hash cho node chỉ khi node đó cascade thành công
- ChangeDetector so hash hiện tại vs manifest để xác định changed set

## Entity: ImpactReport
| Field | Type | Description |
|-------|------|-------------|
| affected | list[AffectedDoc] | All downstream affected docs |
| order | list[str] | Topological processing order |

## Entity: AffectedDoc
| Field | Type | Description |
|-------|------|-------------|
| doc | str | Node id |
| impact_level | enum | high \| medium \| low (BR-07) |
| reason | str | Rationale for impact |
| skill | str | Skill that will update it |
| parents_changed | list[str] | Which parents triggered this |

## Entity: SelectionResult
| Field | Type | Description |
|-------|------|-------------|
| selected | list[str] | Docs user chose to update |
| dropped | list[str] | Docs user excluded |
| gap_warnings | list[GapWarning] | Selection gaps detected (BR-14) |
| auto_included | list[str] | Intermediate nodes auto-added to close gaps |

## Entity: GapWarning
| Field | Type | Description |
|-------|------|-------------|
| selected_node | str | Node được chọn |
| missing_ancestor | str | Parent affected nhưng không được chọn |
| resolution | enum | auto_include \| accept_risk |

## Entity: SyncState (`.sync-state.json`)
```json
{
  "sync_in_progress": true,
  "started": "2026-06-16T10:00:00Z",
  "changeset": { "changed": [...], "context": "..." },
  "order": ["D-19", "D-27", "task-breakdown", "code", "matrix"],
  "node_status": {
    "D-19": "done",
    "D-27": "in_progress",
    "task-breakdown": "pending",
    "code": "pending",
    "matrix": "pending"
  },
  "blocked": [],
  "results": { "D-19": { "status": "complete", "output_path": "..." } }
}
```

Invariant (PBT-02 round-trip): `parse(serialize(state)) == state`.

## Entity: CascadeResult
| Field | Type | Description |
|-------|------|-------------|
| status | enum | complete \| partial \| blocked |
| done | list[str] | Successfully updated docs |
| blocked | list[BlockedNode] | Nodes that returned blocked |
| skipped | list[str] | Descendants skipped due to blocked parent |

## Entity: BlockedNode
| Field | Type | Description |
|-------|------|-------------|
| doc | str | Node id |
| reason | str | Blocked reason from skill |

## Entity: CodeStrategy
| Field | Type | Description |
|-------|------|-------------|
| scope | enum | small \| medium \| large (BR-08) |
| action | enum | flag_tasks \| new_task \| rebreakdown |
| affected_tasks | list[str] | Task IDs to flag/create |
