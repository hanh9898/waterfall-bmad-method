---
skill: {skill-name}
project_name: {project_name}
updated: yyyy-mm-dd
stepsCompleted: []
inputDocuments: []
lastStep: ""
mode: ""
scope: ""
diagram_type: ""
---

# Decision Log — {skill-name}

The decision log is canonical memory across sessions. Every meaningful runtime decision and its alternatives are recorded here; auto-fixes applied in headless mode are also logged here so they can be audited later.

This file is a peer of the primary document inside `{doc_workspace}`. The skill appends a new session block on every activation; it never overwrites prior sessions.

## yyyy-mm-ddThh:mm — Session: {intent: Create | Update | Validate}

### Sources
- List of documents loaded for this session (PRD path, UX path, use-case docs, research files). Mirror `inputDocuments` in frontmatter.

### Mode and scope decisions
- **Mode:** greenfield | migration — reasoning
- **Scope:** single overall flow | multiple named flows ({list}) — reasoning
- **Diagram type:** sequenceDiagram | flowchart | stateDiagram — reasoning (only note if overriding default)

### Discovery snapshot (Stage 2 flush)
- **Actors:** list, mirrored from primary document so compaction can't drop it
- **Triggers:** list
- **Flow inventory:** named flows with one-line summaries

### Validation findings
- Mermaid syntax: pass | issues — details
- Actor coverage: pass | gaps — list
- FR mapping: pass | uncovered FR ids — list
- Auto-fixes applied (headless only): list with rationale

### Handoff target
- Which downstream skill should consume this output (`bmad-create-architecture`, `bmad-create-ux-design`, `bmad-create-epics-and-stories`, `hbc-create-invest-epics-and-stories`).
