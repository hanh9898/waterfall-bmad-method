# INVEST Story Generation

Generate stories for each approved epic following INVEST + 3C's principles. Process epics sequentially; within each epic, collaborate with the user to produce stories that pass all constraints below. All document content must be written in `{document_output_language}`.

## INVEST Criteria (every story must pass all six)

| Criterion | Test | Failure = |
|-----------|------|-----------|
| **Independent** | Can this story be implemented without waiting for other stories in the same epic? | Split or reorder |
| **Negotiable** | Does the story leave room for the dev to choose implementation approach? | Remove implementation prescriptions from AC |
| **Valuable** | Does a real user get something from this story? | Reframe user-centric or move to Technical Tasks |
| **Estimable** | Can a developer estimate this without deep investigation? | Add context in Conversation section or split |
| **Small** | Fits in 1-2 days? Points 1-5 on Fibonacci scale? | Split into smaller stories |
| **Testable** | Can each AC be verified by observing user-facing behavior? | Rewrite AC to describe observable outcomes |

## 3C's Structure

Each story has three parts:

**Card** — the user story statement:
```
As a [user role],
I want [capability],
So that [value/benefit].
```

Rules:
- `[user role]` must be a real user persona, never "System" or "Developer"
- Stories where the actor is genuinely the system → move to Technical Tasks section
- "As a Developer" is acceptable only for developer-facing tools (CLI, API, SDK)

**Conversation** — context and negotiation notes:
- What the user and team discussed about scope
- References to Architecture.md sections for implementation approach
- Edge cases surfaced during discussion
- Anything the dev needs to understand intent without prescribing HOW

**Confirmation** — acceptance criteria as checklist:
```
- [ ] **Given** [precondition] **When** [user action] **Then** [observable outcome]
```

AC rules:
- Describe what the **user observes**, not what the code does
- Zero code, syntax, file paths, class names, or database column names
- Reference Architecture.md for implementation details: `> See Architecture.md § [section]`
- Each AC independently testable by a QA person who cannot read code

## Story Points (Fibonacci)

| Points | Meaning | Duration |
|--------|---------|----------|
| 1 | Trivial — single clear change | < half day |
| 2 | Small — straightforward, no unknowns | half day |
| 3 | Medium — clear but multi-part | 1 day |
| 5 | Large — some complexity, at the limit | 1-2 days |
| 8 | Too large — **must split** before accepting | > 2 days |

If a story estimates at 8+, split it before proceeding. Present split options to the user.

## Enabler Work Handling

Stories that exist to "set up" something for other stories are not user stories:

| Pattern | Action |
|---------|--------|
| "Install module X" | Move to Technical Tasks or Definition of Done |
| "Create database schema" | Fold into the first story that needs the data |
| "Set up CI/CD pipeline" | Technical Task |
| "Configure environment" | Technical Task |
| "Create base components" | Fold into the first story that uses them |

The Technical Tasks section at the bottom of the document captures these. They are real work but not user stories.

## Parallel Implementation

Reduce linear dependencies within each epic:
- Stories that touch independent parts of the system can run in parallel
- Note parallel-eligible stories in the Conversation section
- Only enforce sequence where data or API contracts create a genuine dependency
- Prefer vertical slices (full stack per feature) over horizontal layers

## Per-Epic Process

For each epic in the approved list:

1. Present the epic goal and its FRs
2. Propose story breakdown following all constraints above
3. For each story: write Card, Conversation, Confirmation with Architecture.md references
4. Assign Fibonacci points — split any story at 8+
5. Identify enabler work → Technical Tasks
6. Note which stories can run in parallel
7. Present to user for review — iterate until approved
8. Append approved stories to `{planning_artifacts}/invest-stories.md`

After all epics are complete, present the menu:

**Select an option:** [A] Advanced Elicitation [P] Party Mode [C] Continue to validation

- A → invoke `bmad-advanced-elicitation`
- P → invoke `bmad-party-mode`
- C → update frontmatter, return to SKILL.md Stage 4 (Final Validation)

Wait for user input before proceeding.
