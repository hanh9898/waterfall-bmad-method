# D-19 — Database Design (ER Diagram)

## 1. Overview
- **Overview**: (Describe the scope and purpose of this database design)

## 2. ER Diagram

> [!NOTE]
> Describe the relationships between tables with an ER diagram (using Mermaid).

```mermaid
erDiagram
    EntityA {
        int id PK
        string name
        timestamp created_at
    }

    EntityB {
        int id PK
        int a_id FK
        text description
    }

    EntityA ||--o{ EntityB : has
```

## 3. Table Definitions

---
### 3.1. Table Name
- **Logical name**:
- **Physical name**:
- **Overview**:

| Logical name | Physical name | Type | Constraints | Description |
|---|---|---|---|---|
| ID | id | INTEGER | PK, NOT NULL, AUTO_INCREMENT | |
| | | | | |

---

## 4. Index Definitions

| Table (physical) | Index name | Columns | UNIQUE |
|---|---|---|---|
| | | | |

---

**Revision History**

| Date | Version | Changes | Author |
|---|---|---|---|
| yyyy-mm-dd | 1.0 | Initial creation | |
