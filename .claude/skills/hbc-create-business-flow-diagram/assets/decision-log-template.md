---
skill: {skill-name}
project_name: {project_name}
updated: yyyy-mm-dd
---

# Decision Log — {skill-name}

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
- Which downstream skill should consume this output (`hbc-create-er-diagram`, `hbc-create-test-plan`).
