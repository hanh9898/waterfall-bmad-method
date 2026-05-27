# Enhancement Analysis — hbc-create-requirements

**Scanner:** enhancement-opportunities  
**Skill:** `src/hbc-create-requirements`  
**Date:** 2026-05-27  

---

## Skill Understanding

Generates a D-02 Requirements Specification document with unique REQ-xxx IDs, scope boundaries, user roles, functional and non-functional requirements. The primary user is a BA or PM running through Phase 1 Analysis of an HBC project. Key assumption: the user has source material (project briefs, interview notes, existing context) and wants structured, traceable requirements that feed downstream artifacts (glossary, business flows, traceability matrix).

---

## User Journeys

### The First-Timer

**Narrative:** User invokes the skill for the first time on a new project. They have a vague idea ("we need requirements for our order system") but no source documents ready. They don't know what REQ IDs are or why out-of-scope matters.

**Friction points:**
- **Stage 1b (Source inventory)** asks for documents but gives no guidance on what qualifies as a source. A first-timer with only a mental model gets no signal about whether "just tell me about it" is acceptable input. The open-floor opening pattern would help here — the skill should explicitly invite a brain-dump when no documents exist.
- **Stage 2 (Discovery)** lists six areas to elicit but doesn't signal which are most critical to get right first. A user might spend 20 minutes on stakeholder lists and run out of steam before reaching the scope boundary, which is arguably the most important section for preventing scope creep downstream.
- The **parallel-lens menu** at Stage 3 (`[A]`, `[P]`, `[C]`) is unexplained. A first-timer won't know what "Advanced Elicitation" or "Party Mode" means in this context. No tooltip, no short description.

**Bright spots:**
- Resume detection (Stage 1a) is genuinely helpful — a first-timer who gets overwhelmed can stop and come back.
- Handoff suggestions (Stage 5) connect to the broader pipeline, which teaches the workflow.

### The Expert

**Narrative:** Senior BA with 30 requirements already drafted in a spreadsheet. Wants to convert them into D-02 format with proper IDs and validation.

**Friction points:**
- **No "skip to build" entry point.** The expert must walk through Discovery even though their requirements are already complete. There's no mechanism to say "here's my requirements list, just format and validate it." The `create` arg implies fresh creation; `update` implies an existing D-02. Neither covers "import and convert."
- **Stage 2 conversation** will re-ask questions the expert has already answered in their spreadsheet. The skill doesn't detect that the source document already contains structured requirements and short-circuit Discovery.

**Bright spots:**
- Headless mode partially addresses this — an expert could pass source docs and skip interaction.
- The validation script is exactly what an expert wants: deterministic, fast, actionable.

### The Confused User (Wrong Skill)

**Narrative:** User says "requirements" but means "I need to set up my project" or "I need a PRD."

**Friction points:**
- **Stage 1c (Intent gate)** exists but is a single sentence. It says "If wrong skill, suggest the right one" but doesn't specify how to detect the mismatch or which skills to suggest. The LLM will improvise, which is usually fine, but this is a moment where naming specific sibling skills (hbc-create-prd, hbc-brainstorming) would prevent dead-ends.

**Bright spots:**
- The intent gate exists at all — many skills skip this.

### The Edge-Case User

**Narrative:** User has a project with 200+ requirements spread across multiple subsystems. Or: user has requirements in Vietnamese/Japanese and the template is bilingual Japanese/English.

**Friction points:**
- **REQ ID ceiling not addressed.** REQ-xxx pattern uses 3+ digits (regex `\d{3,}`), which handles up to REQ-999. But the template and script don't discuss what happens at REQ-1000+. The regex handles it (3+ digits), but the formatting convention (`{:03d}`) in the script pads to exactly 3. IDs >= 1000 would be `REQ-1000` (4 digits) and still match the regex, so this is fine technically — but the skill never says "IDs scale beyond 999."
- **Language mismatch.** The template uses Japanese section headers. If `{document_output_language}` is English, the validation script still checks for Japanese section names (`REQUIRED_SECTIONS` is hardcoded Japanese). The script will report sections as missing for any non-Japanese output. This is a real functional gap, though it belongs more to the determinism scanner — I flag it here because the user impact is confusion.

### The Hostile Environment

**Narrative:** Python 3.10+ not available. Or: the project has no `project-context.md`. Or: context compaction drops state mid-Discovery.

**Friction points:**
- **Python dependency is stated** ("Requires Python 3.10+") but there's no graceful fallback if validation can't run. The skill could note that validation is optional in degraded mode and the LLM judgment checks alone provide a baseline.
- **Compaction survival is partially addressed** — Stage 2 has a "compaction flush" to the decision log. But Stage 3 (Generation) and Stage 4 (Validation) don't mention compaction. If compaction fires between validation and save, the validation results (which exist only in conversation) are lost. The fix: write validation results to the decision log.
- **No `project-context.md`:** Stage 1b lists it as a source but doesn't say what to do when it's absent. Soft degradation ("proceed with available sources") would clarify.

### The Automator (Headless / Pipeline)

**Narrative:** Another agent or CI pipeline invokes `hbc-create-requirements --headless` with source documents to produce a D-02 without interaction.

**Friction points:**
- **Source document format unspecified.** Headless mode says "sources are required args" but doesn't define the arg format. Is it file paths? A JSON manifest? Comma-separated? The headless contract (`references/headless-contract.md`) describes the return schema but not the input schema.
- **No decision log in return.** The headless contract returns `output_path` and `validation` but not `decision_log` path. The quality principles explicitly state: "the JSON return is the smallest set of paths the caller needs (typically `skill` + `decision_log`)." The missing decision-log path means the automator can't audit what assumptions were made.
- **Partial success not represented.** If the validator finds 3 auto-fixable and 1 manual-fix issue, the skill auto-fixes the 3 and returns `blocked` for the 1. But the auto-fixes are not itemized in the return. The automator doesn't know what was silently changed.

---

## Headless Assessment

**Level: Easily Adaptable**

The skill declares headless support and has a return contract, but 2-3 interaction points need resolution:

| Interaction Point | Current | Headless Resolution |
|---|---|---|
| Stage 1a (Resume/Update) | Interactive choice | Default: create unless existing D-02 found, then update. Override with `--mode create\|update\|validate` arg. |
| Stage 1b (Source inventory) | Interactive collection | Require `--sources` arg with file paths. Block if none provided. |
| Stage 2 (Discovery) | Conversational elicitation | Extract from source documents. Block if sources yield insufficient content. |
| Stage 3 (Parallel-lens menu) | Interactive `[A]/[P]/[C]` | Skip — always continue. |
| Stage 4 (Fix loop) | Interactive fixes | Auto-fix what's auto-fixable, block on rest. Already specified. |

**Missing for headless:**
- Input schema (what args, what format)
- Decision-log path in return JSON
- Auto-fix changelog in return JSON

---

## Facilitative Patterns Check

| Pattern | Present? | Assessment |
|---|---|---|
| **Open-floor opening** | Absent | **High value to add.** Stage 2 jumps straight into structured elicitation. An open-floor invitation at the start of Discovery ("Share everything you have — documents, ideas, constraints, concerns — before we structure anything") would dramatically improve conversational feel and reduce redundant questioning. |
| **Soft-gate elicitation** | Absent | **High value to add.** Stage 2 covers six areas sequentially but never offers "Anything else on this area, or shall we move on?" The user who remembers one more constraint after moving past Scope has no natural re-entry point. |
| **Intent-before-ingestion** | Present | Stage 1c does this well — checks intent before scanning sources. |
| **Capture-don't-interrupt** | Absent | **Medium value.** During Discovery, if a user mentions something that belongs in the glossary or business flow, the skill should silently note it for handoff rather than redirecting. Stage 5's next-step suggestions partially address this but only at the end. |
| **Dual-output** | Absent | **Low value here.** The D-02 is already structured enough for LLM consumption. A distillate would add minimal value unless downstream skills specifically need a compressed format. |
| **Parallel review lenses** | Present | The `[A]/[P]/[C]` menu at Stages 3 and 4 implements this. |
| **Three-mode architecture** | Present | Guided (default), Headless (declared), but no Yolo/quick mode for experts. |
| **Graceful degradation** | Absent | **Medium value.** No fallback when Python validation fails, when subagents are unavailable for parallel lenses, or when source documents are unreadable. |
| **Decision-Log Workspace** | Present | Decision log exists, resume detection works, compaction flush at Stage 2. But incomplete — no compaction flush at Stages 3-4, no finalize audit. |

---

## Findings

### HIGH-OPPORTUNITY

**H1. No open-floor opening in Discovery**  
*Location:* SKILL.md, Stage 2  
*Noticed:* Discovery jumps into structured categories without first inviting the user to dump everything they know. This forces the skill into a Q&A interrogation pattern rather than a collaborative conversation.  
*Suggestion:* Add one sentence before the category list: "Begin Discovery with an open invitation for the user to share everything available — goals, documents, constraints, concerns, prior art — then identify which of the six areas below still need elicitation."

**H2. Headless input contract missing**  
*Location:* `references/headless-contract.md`  
*Noticed:* The contract defines the return schema but not the input schema. An automator cannot invoke headless mode without guessing what args to pass.  
*Suggestion:* Add an "Input Schema" section: required `--sources` (file paths), optional `--mode` (create/update/validate), optional `--vague-terms`. Include a minimal invocation example.

**H3. Decision-log path absent from headless return**  
*Location:* `references/headless-contract.md`  
*Noticed:* Quality principles require headless returns to include the decision-log path for audit trail. Current schema omits it.  
*Suggestion:* Add `"decision_log": "/path/to/.decision-log.md"` to the return schema.

### MEDIUM-OPPORTUNITY

**M1. No soft-gate transitions in Discovery**  
*Location:* SKILL.md, Stage 2  
*Noticed:* Six discovery areas are listed but there's no guidance on transitioning between them gracefully. Users in flow get cut off; users who need more time on one area get pushed forward.  
*Suggestion:* Add: "At each area boundary, use soft-gate elicitation — 'Anything else on [area], or shall we move on to [next]?'"

**M2. Parallel-lens menu unexplained**  
*Location:* SKILL.md, Stages 3 and 4  
*Noticed:* `[A] Advanced Elicitation / [P] Party Mode / [C] Continue` appears without context. "Party Mode" is an HBC convention that new users won't know.  
*Suggestion:* Add a one-line parenthetical for each option, e.g., `[A] Advanced Elicitation (deeper probing on weak areas) / [P] Party Mode (creative lateral review) / [C] Continue`.

**M3. No compaction flush at Stages 3-4**  
*Location:* SKILL.md, Stages 3 and 4  
*Noticed:* Stage 2 has an explicit compaction flush to the decision log, but Stages 3 (generation complete) and 4 (validation results) don't. If compaction fires after validation but before save, validation findings are lost.  
*Suggestion:* Add compaction flush notes at end of Stage 3 ("write generated REQ count and scope summary to decision log") and end of Stage 4 ("write validation results summary to decision log").

**M4. No "import and convert" path for experts**  
*Location:* SKILL.md, Args  
*Noticed:* The three modes (create, update, validate) don't cover the expert who has pre-structured requirements and wants them formatted into D-02 without re-discovery. This is distinct from "update" (which assumes an existing D-02) and "create" (which assumes starting from scratch).  
*Suggestion:* Either add an `import` arg or document in Stage 2 that when source documents contain structured requirements, Discovery should detect this and skip to confirmation rather than re-eliciting.

**M5. Capture-don't-interrupt for cross-artifact insights**  
*Location:* SKILL.md, Stage 2  
*Noticed:* During requirements discovery, users frequently mention terms that should be in the glossary (D-03) or processes that should be in business flows (D-06). Currently nothing captures these for handoff.  
*Suggestion:* Add one line to Stage 2: "Silently capture any glossary-worthy terms or business-flow-worthy processes mentioned during Discovery — surface them in Stage 5 handoff alongside next-step suggestions."

### LOW-OPPORTUNITY

**L1. No graceful degradation when Python unavailable**  
*Location:* SKILL.md, Stage 4  
*Noticed:* The skill requires Python 3.10+ for validation but doesn't specify what happens if `python3` fails. LLM judgment checks alone would still provide value.  
*Suggestion:* Add: "If the validation script is unavailable (Python not installed or script error), fall back to LLM-only validation and note the limitation in the decision log."

**L2. Decision-log finalize audit missing**  
*Location:* SKILL.md, Stage 5  
*Noticed:* The decision-log workspace pattern calls for a finalize step that audits every meaningful decision-log entry against the primary artifact. Stage 5 says "Append closing session to decision log" but doesn't mention the audit pass.  
*Suggestion:* Add: "Before closing, audit decision log entries against the generated D-02 — confirm every logged decision is reflected in the document, the addendum, or explicitly set aside."

**L3. Smart defaults from project-context.md**  
*Location:* SKILL.md, Stage 1b  
*Noticed:* `project-context.md` is listed as a source but the skill doesn't say to pre-populate Discovery fields from it. If the context file already names stakeholders, timeline, and tech stack, the LLM should surface these as defaults rather than asking the user to restate them.  
*Suggestion:* Add to Stage 2 opening: "Pre-populate Discovery fields from project-context.md where available; present as defaults for confirmation rather than asking from scratch."

---

## Top Insights

1. **The open-floor opening is the single highest-impact addition.** Requirements discovery is fundamentally a conversation, and the skill currently skips the most natural part — letting the user talk first. One sentence in Stage 2 would transform the interactive experience from interrogation to collaboration.

2. **Headless mode is declared but under-specified on the input side.** The return contract is clean, but an automator cannot invoke the skill without guessing. Adding an input schema and the decision-log path to the return would make headless mode genuinely usable by pipelines.

3. **Compaction resilience is partially implemented but has a gap.** The Stage 2 flush is good design. Extending it to Stages 3 and 4 closes the window where validation results and generation state can be lost, which matters most for the long-running sessions this skill naturally produces.
