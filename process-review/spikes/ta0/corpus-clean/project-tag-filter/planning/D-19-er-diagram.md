---
document_id: D-19
title: "Project Tag Filter — Database Design"
version: "1.0"
status: approved
---

# D-19 — Database Design (Project Tag Filter)

## Tables

### project.tag
- **Tên vật lý (Physical name)**: `project.tag`
- `name` (Char), `color` (Integer), Many2many to `project.project`.
