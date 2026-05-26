# Enhancement Analysis -- hbc-traceability

**Scanner:** enhancement-opportunities
**Date:** 2026-05-26
**Skill path:** src/hbc-traceability

---

## Skill Understanding

Living traceability matrix manager for HBC waterfall lifecycle projects. Four capabilities (Init, Update, Report, Audit) maintain a seven-column markdown table mapping requirements through design, implementation, and testing. Primary users: BA initializing the matrix, architects/developers/testers populating columns after each phase, PMs/QA auditing coverage gaps. Key assumption: project follows HBC phased delivery with D-02 requirements, D-19 design, D-27 test specs, and phase gate reports at known paths.

---

## User Journeys

### The First-Timer (BA after Phase 1 gate)

**Narrative:** BA invokes traceability for the first time. They have D-02 requirements but have never used this skill.

**Friction points:**
- No guidance on what D-02 should look like for successful extraction. If requirements use a non-standard ID format (e.g. `RQ-01` instead of `REQ-001`), `extract-trace-ids.py` silently returns zero matches. The `NO_MATCHES` status is returned to the LLM, but there is no proactive suggestion to check the regex pattern or show the user what patterns were tried.
- If D-02 does not exist at the expected glob path (`_hbc_output/plan/D-02-*`), the script returns `NO_FILES`. The SKILL.md does not tell the LLM to help the user locate the file or suggest an alternative path.

**Bright spots:**
- Capability inference from agent context is smart -- a BA post-Phase 1 gets `init` suggested without needing to know the command.
- Confirmation before acting on inferred capability is respectful of user autonomy.

### The Expert (Dev mid-Phase 3)

**Narrative:** Developer runs `traceability update` expecting Phase 3 code_ref population. They know exactly what they want.

**Friction points:**
- Phase 3 update asks for source code root path interactively if `source_code_path` is empty. An expert who invokes this repeatedly across sprints gets asked the same question every time. There is no "remember this for the session" or suggestion to configure `customize.toml`.
- No quick-run path. The expert must walk through the full activation steps (resolve customization, prepend, persistent facts, config, append) every time. For a report or audit that just reads the matrix, this overhead is noticeable.

**Bright spots:**
- Phase detection from column fill state is genuinely clever -- no need to specify which phase.
- Explicit script invocations mean deterministic extraction; the expert can trust the numbers.

### The Confused User (invoked by accident)

**Narrative:** User says "trace this bug" and the skill triggers on "trace."

**Friction points:**
- The description triggers on "truy vet" (Vietnamese for traceability) which is good, but the word "traceability" is broad enough to catch unrelated conversations about code tracing, distributed tracing, etc. The skill does not verify intent before executing activation steps.
- Once activated, if no matrix exists and no D-02 is found, the user hits a dead end with no graceful escape. The skill should detect "this project has no HBC artifacts" early and bail with a clear message.

**Bright spots:**
- The `[TR]` agent menu code is unambiguous for intentional invocation.

### The Edge-Case User (non-standard project)

**Narrative:** Project has requirements in a spreadsheet export, uses custom IDs like `FR-001` instead of `REQ-xxx`, or has D-19 and D-27 in non-standard locations.

**Friction points:**
- The regex patterns are hardcoded in SKILL.md for each phase update command. There is no customize.toml scalar for `req_id_pattern`, `design_entity_pattern`, or `test_case_pattern`. A team with `FR-xxx` IDs must fork the entire skill.
- D-19 and D-27 glob paths are hardcoded (`_hbc_output/design/D-19-*`). If the team's directory structure differs, there is no override.

### The Hostile Environment

**Narrative:** Context compaction drops SKILL.md mid-Update.

**Friction points:**
- The Update capability has 5 sub-steps (read matrix, detect phase, run phase-specific extraction, write, report). If compaction drops SKILL.md between reading the matrix and writing the update, the LLM loses the phase-specific regex commands and the column-mapping logic. The matrix file itself has no frontmatter recording "last update was Phase 2" to help recovery.
- If `extract-trace-ids.py` fails (Python not available, permission error), there is no fallback guidance. The skill assumes Python 3.10+ is available without stating this prerequisite.

### The Automator (headless pipeline invocation)

**Narrative:** Phase gate skill calls `traceability report --headless` after a gate passes, to include coverage stats in the gate report.

**Friction points:**
- Headless mode requires `capability` as input but the JSON return schema does not include `status: complete|blocked` as specified in BMad headless conventions. The current schema has no `status` field at all. A calling agent cannot distinguish "report succeeded with gaps" from "report failed because matrix does not exist."
- No `decision_log` path in headless return. BMad convention says headless returns should include the decision log path for audit trail. This skill has a `.decision-log.md` but it is a build-time artifact, not a runtime audit log. For a living matrix, runtime decisions (e.g., "inferred Phase 2, matched REQ-003 to Entity_User") are lost.
- `trace-report.py` exits with code 1 when gaps exist (line 129). This is semantically wrong for headless: gaps are expected data, not errors. A calling script checking exit codes would interpret a normal audit result as a failure.

---

## Headless Assessment

**Level: Easily Adaptable** -- needs a headless path on 2-3 interaction points.

**Interaction points that could auto-resolve:**
1. **Capability determination** (Step 5) -- already required in headless. Good.
2. **Phase 2/3 Update confirmation** -- "Inferred 'update' from Dev context. Proceed?" -- already skipped in headless. Good.
3. **Source code path prompt** (Phase 3 update) -- needs `source_code_path` pre-configured in customize.toml or passed as arg. Currently asks interactively if empty.
4. **Phase detection confirmation** -- Update auto-detects phase. In headless, should just proceed. Not explicitly addressed.

**What a headless invocation needs:**
- **Inputs:** `capability` (required), `phase` (optional, for Update to skip detection), `source_code_path` (required for Phase 3 Update)
- **Return format:** Should conform to BMad headless convention: `{ status: "complete"|"blocked", capability, matrix_path, ...coverage_data, decision_log?, reason? }`
- **Exit codes:** `trace-report.py` should exit 0 on successful parse regardless of gap count; exit 1 only for actual errors (file not found, parse failure).

---

## Facilitative Patterns Check

| Pattern | Present? | Assessment |
|---------|----------|------------|
| Open-floor opening | No | Not applicable -- this is a utility skill, not a discovery workflow. |
| Soft-gate elicitation | No | **Would be valuable at Phase 2 Update.** After LLM maps REQs to design entities, a "Does this mapping look right? Anything to adjust?" before writing would catch errors. Currently writes directly. |
| Intent-before-ingestion | Partial | Capability inference checks context before acting, but does not verify the user actually wants traceability work (vs. "trace" meaning something else). |
| Capture-don't-interrupt | No | Not applicable -- no discovery flow. |
| Dual-output | No | **Would be valuable.** The matrix is human-readable markdown, but downstream skills (phase gate, audit) need structured data. Currently, `trace-report.py` produces the structured form, but only on explicit Report/Audit invocation. An auto-generated `.matrix-summary.json` alongside the markdown would let other skills consume coverage without invoking the full Report capability. |
| Parallel review lenses | No | Not applicable for this utility. |
| Three-mode architecture | Partial | Has interactive + headless. No "yolo" mode. A yolo mode for Update would skip the mapping confirmation and auto-apply best-guess mappings. |
| Graceful degradation | No | **Missing.** If Python is unavailable, there is no fallback. If D-19/D-27 files do not exist, there is no guidance on partial update. |
| Decision-Log Workspace | Build-time only | The `.decision-log.md` is used for skill design decisions, not for runtime traceability decisions. **This is a gap** -- mapping decisions ("REQ-003 traces to Entity_User because...") are the most valuable audit content and they vanish with the conversation. |

---

## Findings

### HIGH-OPPORTUNITY: Runtime decision log for mapping decisions

**Location:** SKILL.md, Update capability (lines 93-121)

**Observation:** The most valuable traceability decisions -- "REQ-003 maps to Entity_User because both handle user registration" -- are made by LLM judgment during Phase 2 and Phase 3 updates. These rationales exist only in the conversation and vanish on session end or compaction. A future auditor seeing `design_ref: Entity_User` in the matrix has no way to know WHY that mapping was chosen, whether it was confirmed by the user, or whether it overrode a previous mapping.

**Suggestion:** Add a runtime `.trace-decisions.md` (or repurpose `.decision-log.md` with runtime session headings) that captures each non-obvious mapping rationale during Update. One line per mapping: `REQ-003 -> Entity_User: user registration flow described in D-02 section 3.2 maps to User table in D-19`. This transforms the matrix from "data" to "auditable evidence" -- a significant quality jump for waterfall lifecycle traceability where audit trails matter.

### HIGH-OPPORTUNITY: Headless return does not conform to BMad convention

**Location:** SKILL.md, Headless Mode (lines 23-46)

**Observation:** The headless JSON schema lacks `status` and `decision_log` fields. Exit code from `trace-report.py` treats "gaps found" as error (exit 1). A calling skill cannot reliably distinguish success-with-data from failure.

**Suggestion:** Add `"status": "complete"` (or `"blocked"` with `"reason"`) to the headless return. Add `"decision_log"` path if runtime decisions were logged. Change `trace-report.py` to exit 0 when parse succeeds, exit 1 only on actual errors. Add a `--strict` flag if callers want non-zero on gaps.

### MEDIUM-OPPORTUNITY: No recoverability after compaction during Update

**Location:** SKILL.md, Update capability

**Observation:** A Phase 2 Update involves: read matrix, extract from D-19, extract from D-27, LLM-judge mappings, write matrix. If compaction drops SKILL.md between steps 2 and 4, the LLM loses the column-mapping instructions and the phase-specific regex commands. The matrix file has no state marker indicating "Phase 2 update in progress, design_ref being populated."

**Suggestion:** Before starting an Update, write a brief status line to the matrix's YAML frontmatter (or a sibling `.trace-state.json`): `{ "update_in_progress": "design_ref", "started": "2026-05-26T17:00:00" }`. Clear it on completion. On re-activation, if this marker exists, surface it: "A Phase 2 update was interrupted. Resume or restart?" This is cheap insurance for the longest operation in the skill.

### MEDIUM-OPPORTUNITY: Hardcoded regex patterns and artifact paths limit team customization

**Location:** SKILL.md lines 84, 105-106; customize.toml

**Observation:** The requirement ID pattern (`REQ-\d{3,}`), design entity pattern, test case ID pattern, and artifact glob paths (D-02, D-19, D-27 locations) are all hardcoded in SKILL.md. Teams using `FR-xxx` IDs or storing artifacts in different directories cannot customize without forking.

**Suggestion:** Add customize.toml scalars: `req_id_pattern`, `test_case_pattern`, `design_entity_pattern`, and path scalars `requirements_path`, `design_path`, `test_spec_path`. SKILL.md references these as `{workflow.req_id_pattern}` etc. Sensible defaults in base customize.toml preserve zero-config behavior.

### MEDIUM-OPPORTUNITY: Soft-gate missing on mapping confirmation

**Location:** SKILL.md, Update Phase 2 (lines 103-107)

**Observation:** The Phase 2 update uses LLM judgment to map REQs to design entities and test cases. This is the highest-stakes decision in the entire skill -- a wrong mapping means a requirement appears traced when it is not. Yet there is no explicit instruction to confirm mappings with the user before writing. The LLM might do this naturally, but given the stakes, the instruction should be explicit.

**Suggestion:** After the mapping step, add: "Present the proposed REQ-to-design and REQ-to-test mappings as a table. Confirm with user before writing to the matrix. In headless mode, write directly and log confidence levels in the decision record."

### LOW-OPPORTUNITY: No "what changed" diff on Update

**Location:** SKILL.md, Update capability, step 7 (line 120)

**Observation:** After an Update, the skill reports aggregate coverage ("X/Y requirements now have design_ref populated"). It does not show what specifically changed -- which REQs got new mappings, which mappings were updated. For a user who just sat through a Phase 2 update, seeing "Updated design_ref. Coverage: 20/23" is less useful than seeing the actual 20 mappings that were written.

**Suggestion:** After writing the updated matrix, show a brief diff: new mappings added this session, any mappings that changed (if Update is re-run). This costs almost nothing and dramatically improves the user's confidence that the right things happened.

### LOW-OPPORTUNITY: Missing prerequisite check for Python 3.10+

**Location:** Scripts (`extract-trace-ids.py`, `trace-report.py`)

**Observation:** Both scripts require Python 3.10+ (declared in PEP 723 metadata). If the user's system has only Python 3.9 or no Python at all, script invocations fail with no helpful message from the skill. The SKILL.md does not mention this prerequisite.

**Suggestion:** Either add a brief note in Overview ("Requires Python 3.10+ for deterministic extraction scripts") or, better, have the On Activation flow check `python3 --version` before first script use and surface a clear message if unavailable.

---

## Top Insights

1. **The mapping rationale is the real traceability.** The matrix records WHAT traces to what, but not WHY. In a waterfall lifecycle where traceability is often an audit requirement, the reasoning behind each mapping is as important as the mapping itself. A lightweight runtime decision record would transform this skill from "coverage tracker" to "auditable evidence generator" -- a qualitative leap for its target audience.

2. **Headless convention compliance is table stakes for cross-skill orchestration.** The phase gate skill is an obvious consumer. Without `status` field and correct exit codes, the integration will be fragile. This is the fastest high-value fix.

3. **Soft-gate on mapping confirmation prevents the costliest error.** A wrong REQ-to-design mapping is invisible until late-phase audit, by which point the damage is done. An explicit confirmation step (interactive) or confidence logging (headless) is the single highest-leverage addition for correctness.
