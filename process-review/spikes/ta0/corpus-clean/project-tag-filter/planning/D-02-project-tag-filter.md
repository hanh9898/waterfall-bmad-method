---
document_id: D-02
title: "Project Tag Filter — Requirements"
version: "1.0"
status: approved
---

# Project Tag Filter — Requirements

> A genuine second mini-feature (not a mirror of the case): adds a colored tag
> taxonomy to projects and a saved-filter on the project list. Small but
> internally consistent across D-02 / D-19 / code / matrix / task-breakdown / gate.

## Requirements

| req_id | category | requirement | priority |
|--------|----------|-------------|----------|
| REQ-PROJECT-TAG-FILTER-001 | Model | A `project.tag` entity with name + color. | High |
| REQ-PROJECT-TAG-FILTER-002 | Model | Many2many between `project.project` and `project.tag`. | High |
| REQ-PROJECT-TAG-FILTER-003 | UI | Saved filter on the project list to filter by one or more tags. | Medium |
