---
skill: {skill-name}
project_name: {project_name}
updated: yyyy-mm-dd
stepsCompleted: []
inputDocuments: []
lastStep: ""
scope: ""
level: ""
---

# Decision Log — {skill-name}

The decision log is canonical memory across sessions. Every meaningful runtime decision and its alternatives are recorded here; auto-fixes applied in headless mode are also logged here so they can be audited later.

This file is a peer of the primary document inside `{doc_workspace}`. The skill appends a new session block on every activation; it never overwrites prior sessions.

## yyyy-mm-ddThh:mm — Session: {intent: Create | Update | Validate}

### Sources
- List of documents loaded for this session (PRD path, Architecture path, D-20 path, research files). Mirror `inputDocuments` in frontmatter.

### Scope and level decisions
- **Scope:** single-domain | multi-domain ({domain areas}) — reasoning
- **Level:** conceptual | logical | physical — reasoning

### Discovery snapshot (Stage 2 flush)
- **Entities:** list with physical names, mirrored from primary document so compaction can't drop it
- **Relationships:** list with cardinality notation
- **Key attributes:** summary per entity

### Validation findings
- Mermaid ER syntax: pass | issues — details
- Entity coverage: pass | gaps — list
- Entity mapping: pass | uncovered entity ids — list
- Auto-fixes applied (headless only): list with rationale

### Handoff target
- Which downstream skill should consume this output (`hbc-create-coding-standards`, `hbc-create-api-spec`, `hbc-task-breakdown`).
