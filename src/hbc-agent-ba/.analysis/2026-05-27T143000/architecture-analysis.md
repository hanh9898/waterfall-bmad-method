# Architecture Analysis — hbc-agent-ba

**Scan date:** 2026-05-27  
**Skill type:** Agent  
**SKILL.md:** 88 lines / ~1 136 tokens  
**Reference pattern:** bmad-agent-analyst

---

## Assessment

`hbc-agent-ba` is a faithful, well-contained adaptation of the BMad agent pattern. The activation flow is structurally sound, the persona is purposeful and domain-specific, and the menu is clearly scoped to Phase 1 artifacts. Two issues prevent a clean pass: a prescriptive numbered-step heading structure inside `## On Activation` that mirrors the reference pattern's form but surfaces as mechanical procedure rather than informed activation guidance, and a mismatch between Step 5 (Load Config) and Step 6 (Scan Phase 1 State) where config resolution and artifact scanning are hard-coded as sequential named steps rather than integrated into a single outcome-oriented activation block. Both are addressable without structural change to the skill.

---

## Findings

### HIGH — Prescriptive step numbering in `## On Activation` creates mechanical over-specification

**File:** `SKILL.md` lines 23–75 (`Step 1` through `Step 8`)

**What's wrong:** The eight numbered sub-steps are numbered headings (`### Step 1: …`, `### Step 2: …`, etc.). This is verbatim from the `bmad-agent-analyst` reference pattern. The principles file classifies numbered procedural steps for things the LLM does naturally as waste that "doesn't earn its keep." Steps 2, 3, 4, 7, and 8 in particular (`Execute Prepend Steps`, `Adopt Persona`, `Load Persistent Facts`, `Greet and Present`, `Execute Append Steps`) describe operations the LLM will do correctly from the outcome description alone; they don't need ordinal labels.

**Why it matters:** Numbered procedure framing biases the executing LLM toward mechanical compliance checking ("did I do step 4?") over informed judgment ("do I have what I need to greet the user well?"). It also makes the activation block brittle to any future re-sequencing — changing the logical order requires renumbering and creates false coupling between the numbers and the meaning.

**Exception — load-bearing steps that keep their numbers:** Step 1 (Resolve the Agent Block with exact script invocation) and Step 6 (Scan Phase 1 State with specific artifact paths) are fragile-operation invocations that the principles file explicitly protects. These two warrant procedural specificity. The others do not.

**Fix:** Collapse Steps 2–5 and Steps 7–8 into a single outcome-oriented `## On Activation` block ("Load and embody the resolved agent block, then load persistent facts and config. Greet the user by name, leading with `{agent.icon}`, and execute any append steps."). Keep Step 1 (script invocation) and Step 6 (artifact scan) as labelled sub-procedures because they specify exact paths and fragile operations.

---

### HIGH — Step 5 (`Load Config`) references a config path pattern divergent from the reference agent

**File:** `SKILL.md` lines 49–55

**What's wrong:** Step 5 instructs the agent to load `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml`, then resolve `{user_name}`, `{communication_language}`, `{document_output_language}`, and "Output location from the `hbc` module section". The `bmad-agent-analyst` reference uses `{project-root}/_bmad/bmm/config.yaml` and exposes `{planning_artifacts}` and `{project_knowledge}` as named variables. Neither path is wrong on its own, but `hbc-agent-ba` references a vague "hbc module section" rather than a declared config scalar. If the output location is important enough to scan in Step 6, it must be a named scalar in `customize.toml` referenced as `{workflow.<name>}`. It is not.

**Why it matters:** The principles file's "Hardcoded path in SKILL.md while customize.toml declares the scalar → Override silently no-ops" failure mode applies here in reverse: the skill is reading an undeclared path. There is no `output_path` or equivalent in `customize.toml`. The agent has to infer what "output location from the hbc module section" means — this is intelligence leaked into a path resolution step, and it will silently fail to scan any non-default layout.

**Fix:** Add an `output_path` scalar to `customize.toml` (e.g., `output_path = "{project-root}/docs/phase-1"` or equivalent HBC default). In Step 5 (or its collapsed equivalent), reference `{workflow.output_path}` explicitly. Step 6 then uses that resolved value for the artifact scan.

---

### MEDIUM — `references/.decision-log.md` placement diverges from the Decision-Log Workspace convention

**File:** `references/.decision-log.md`

**What's wrong:** The principles file specifies that for a folder-artifact (a built skill), "the workspace IS the artifact's folder; the log + addendum sit as peers of the primary file (e.g. `SKILL.md`)". The decision log here lives at `references/.decision-log.md`, not at `.decision-log.md` (peer of `SKILL.md`). It is nested one level deeper than the workspace convention calls for.

**Why it matters:** This is a housekeeping issue rather than an execution-breaking one, but it means the log is not where the BMad resume protocol would look for it. If a future skill were to check for a workspace, it would look for `.decision-log.md` adjacent to `SKILL.md` and miss this one.

**Fix:** Move `references/.decision-log.md` to `src/hbc-agent-ba/.decision-log.md` (peer of `SKILL.md` and `customize.toml`). Update the MEMORY.md note if it references this path.

---

### LOW — `## Overview` greets with role description rather than domain framing

**File:** `SKILL.md` lines 8–12

**What's wrong:** The Overview states "You are the Business Analyst coordinating Phase 1 …" and "Core outcome: user completes Phase 1 with D-02, D-03, and D-06." This is accurate but reads as task description rather than domain framing. The principles file notes that Overview's role is to establish "role, mission, and (where relevant) domain framing, theory-of-mind, design rationale" — context that enables judgment. The current Overview tells the LLM what it will do (coordinator, Phase 1), but doesn't give it the domain-specific theory of mind that makes the BA persona substantive: why precision in requirements matters in a waterfall context, what goes wrong when vague requirements pass the gate, etc.

**Note:** This is a LOW finding because the `customize.toml` `principles` array partially compensates ("No vague terms pass through — challenge 'fast', 'easy', 'user-friendly'", etc.). The Overview is not broken; it just misses an opportunity to pre-load judgment rather than rules.

**Fix (optional):** Add one or two sentences of domain framing, e.g., "In waterfall, the cost of a vague requirement compounds: a missed term in D-03 produces an ambiguous function in D-02 that produces an untestable acceptance criterion in the gate. Precision at Phase 1 gates prevents re-work downstream."

---

### LOW — Menu dispatch section lacks the "stop and wait" signal present in the reference

**File:** `SKILL.md` lines 77–87

**What's wrong:** The `bmad-agent-analyst` reference pattern ends its dispatch section with "**Stop and wait for input.**" This is load-bearing: without an explicit stop signal, agents in a long activation sequence sometimes continue processing instead of presenting the menu and pausing. The `hbc-agent-ba` menu section describes dispatch logic but does not include this stop instruction.

**Fix:** Add "Present the menu and stop. Wait for the user's selection." to the Menu Dispatch section after the numbered table description.

---

## Strengths

- **Activation flow structural integrity.** The six-step pattern (resolve → persona → facts → config → state scan → greet) correctly implements the BMad agent activation sequence and is properly wired. The script invocation at Step 1 includes the exact command with `--key agent`, matching the reference pattern.

- **Phase 1 state scan is a genuine addition.** Checking existing D-02/D-03/D-06/phase-1-gate artifacts before greeting is HBC-specific value that earns its place — the principles file would protect this as domain framing. The artifact codes are precise and the compact-summary instruction ("Build a compact status summary") avoids verbosity without under-specifying the output.

- **`customize.toml` is well-structured.** The `[agent]` block follows the reference pattern's shape exactly. The `principles` array is concrete and domain-appropriate (REQ-xxx ID tracing, challenging vague adjectives, cross-referencing artifacts). The `identity` and `communication_style` fields avoid the "You are an AI" anti-pattern.

- **Context-carry across workflows.** The instruction "Carry domain context forward — terms from GLO inform REQ review, requirements from REQ inform BF design" is outcome-based and gives the executing LLM real guidance without prescribing how to carry it.

- **Proactive gate suggestion is correctly wired.** "When all three core artifacts (D-02, D-03, D-06) exist, proactively suggest running the Phase 1 gate" is a testable condition that advances the workflow without requiring user initiative.

- **Decision log records genuine decisions.** The five entries all document real trade-offs (empty name field rationale, context-carry choice, proactive gate suggestion reasoning) rather than summarizing what was built. This matches the principles file's intent for the decision-log workspace pattern.

---

## Review Summary

| Severity | Count |
|----------|-------|
| HIGH     | 2     |
| MEDIUM   | 1     |
| LOW      | 2     |

**Verdict: WARNING** — Two HIGH findings should be resolved before the skill ships. The prescriptive step numbering is cosmetic but compounds over the agent's lifetime (every future reader incurs the cognitive tax of checking off steps); the missing `output_path` scalar is a functional gap that will cause silent scan failures on non-default HBC layouts.
