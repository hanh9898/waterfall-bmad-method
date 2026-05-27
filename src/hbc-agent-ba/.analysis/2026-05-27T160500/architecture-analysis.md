# Architecture Analysis — hbc-agent-ba

**Scan date:** 2026-05-27  
**Skill path:** `src/hbc-agent-ba`  
**Scanner:** quality-scan-architecture v1

---

## Assessment

`hbc-agent-ba` is a well-structured module agent that faithfully follows the BMad agent activation pattern — resolver → persona → context → state scan → menu. The skill is lean (96 lines, ~1 600 tokens), all workflow content is inline, and the customization surface in `customize.toml` is appropriately shaped. The two P1 prepass "critical" findings (`02-requirements.md`, `06-business-flow.md`) are confirmed false positives: the regex matched artifact code strings in prose (D-02, D-06), not stage file references — this is an agent skill with no carved-out stage files. One genuine structural gap exists — the `{agent.output_path}` scalar is consumed in activation but not declared with a companion reference in SKILL.md — and a handful of medium/low prose and script hygiene items round out the findings.

---

## Findings

### HIGH

#### H-01 · `SKILL.md:65` · Hardcoded path invocation vs declared scalar gap

**What:** `Scan Phase 1 State` invokes `python3 {skill-root}/scripts/scan-phase1-state.py {agent.output_path}`. The `output_path` scalar is declared in `customize.toml` (`output_path = "{project-root}/_hbc_output/plan"`), but SKILL.md references `{agent.output_path}` without confirming where the resolved value comes from, and the fallback instructions (`check {agent.output_path} manually`) repeat the same unresolved reference.

**Why it matters:** If the resolver script fails and the fallback path runs, the agent has no concrete path to fall back to — `{agent.output_path}` is still a template token at that point. The principles file requires: "Hardcoded paths next to a declared scalar = override silently no-ops." The inverse applies: relying on a template token in a fallback instruction where the resolver has already failed means the fallback is inoperative.

**Fix:** In the `### Scan Phase 1 State` fallback block, replace the bare `{agent.output_path}` reference with a concrete instruction: "Use the `output_path` value from the resolved agent block (Step 1 result). If Step 1 also failed, look for `_hbc_output/plan` under `{project-root}` as the default." The default comes from `customize.toml` and should be surfaced here so the fallback is actually executable.

---

#### H-02 · `scripts/scan-phase1-state.py` · No unit tests — scripts/tests/ directory absent

**What:** The scripts prepass confirms `scripts/tests/` does not exist. `scan-phase1-state.py` is the only script in this skill and has no tests.

**Why it matters:** The script is a fragile operation invoked on every activation. Regressions in glob pattern matching, frontmatter parsing, or the `next_recommended` logic will silently produce wrong status summaries without tests catching them.

**Fix:** Create `scripts/tests/test-scan-phase1-state.py` with cases for: directory not found, all artifacts missing, partial artifacts, all artifacts present, frontmatter date extraction, and the `next_recommended` ordering.

---

### MEDIUM

#### M-01 · `SKILL.md:45-55` · Activation Step 1 is prescriptive where outcome suffices

**What:** `### Step 1: Resolve the Agent Block` spells out the three-file merge sequence (base → team → user) with explicit file paths and merge rules. This is a procedural description of BMad structural merge — standard institutional knowledge — but the level of detail (listing all three file paths, restating the merge rules verbatim) exceeds what's needed.

**Why it matters:** Per the principles file, exact steps are warranted for fragile operations with one right way. The resolver script handles this deterministically; the fallback only needs to say "apply BMad structural merge rules" — the rules are institutional knowledge the agent already carries. Restating them adds weight without preventing a failure the LLM would otherwise make.

**Fix:** Trim the fallback to: "Read `customize.toml`, `{project-root}/_bmad/custom/{skill-name}.toml`, and `{project-root}/_bmad/custom/{skill-name}.user.toml` in order (skip missing files). Apply BMad structural merge rules." Remove the inline re-statement of merge rule specifics — the agent knows them.

---

#### M-02 · `scripts/scan-phase1-state.py:1` · Missing PEP 723 inline dependency block

**What:** The script uses only stdlib (`argparse`, `glob`, `json`, `os`, `re`) but has no PEP 723 `# /// script` block declaring `requires-python`.

**Why it matters:** Without a declared Python version constraint, runners (e.g., `uv run`) cannot guarantee the right interpreter. The `str | None` union syntax (line 24) requires Python 3.10+; silently running on 3.9 produces a `SyntaxError` with no diagnostic.

**Fix:** Add at the top of the script:
```python
# /// script
# requires-python = ">=3.10"
# ///
```

---

#### M-03 · `SKILL.md:73` · `{communication_language}` present but `{document_output_language}` absent from greeting instruction

**What:** The `### Greet and Present` step says "speaking in `{communication_language}`" but the skill produces no document itself — it dispatches to sub-skills that produce D-02, D-03, D-06. This is correct. However, the `Embody Persona` step loads `{document_output_language}` from config but it is never referenced again, leaving it loaded but unused context.

**Why it matters:** Minor: unused config loading is not harmful, but it signals the config load block may be cargo-culted from a document-producing skill. If `{document_output_language}` is genuinely not needed, the load instruction should not reference it to avoid misleading sub-skill dispatch logic.

**Fix:** Remove `{document_output_language}` from the `Embody Persona` config load instruction. If sub-skills need it, they load it themselves.

---

### LOW

#### L-01 · `SKILL.md:75` · Suggested flow in parentheses is prescriptive framing

**What:** "suggested flow: REQ → GLO → BF → PG → TR" appears as a parenthetical in the Greet step.

**Why it matters:** The ordering logic is already encoded in the `next_recommended` output from the state scan script. Stating it again as a fixed sequence contradicts the adaptive recommendation the script produces (which may correctly suggest GLO first if REQ already exists). Mild tension between scripted recommendation and hardcoded prose suggestion.

**Fix:** Remove the parenthetical. The state scan result already drives the recommendation; trust it.

---

#### L-02 · `scripts/scan-phase1-state.py` · No meaningful exit codes

**What:** The scripts prepass flags that `scan-phase1-state.py` exits via normal `main()` return (exit code 0) regardless of `status: blocked`. The SKILL.md fallback checks for script failure, but "failure" here means Python exception, not `blocked` status.

**Why it matters:** Low impact for interactive use, but the principles file calls out exit code discipline for headless/agentic invocation. A `status: blocked` result exits 0, which is indistinguishable from a healthy `status: complete` to any shell-level caller.

**Fix:** Add `sys.exit(1)` when `status == "blocked"` and `sys.exit(2)` on caught exceptions in `main()`.

---

#### L-03 · `SKILL.md:14` · Waterfall cost-of-error rationale is valuable but slightly over-explained

**What:** The Overview's second paragraph ("In waterfall, the cost of a vague requirement compounds…") is domain framing that earns its place. However the final sentence re-states what the preceding sentence already established.

**Why it matters:** Low; the duplication is minor. The principles file flags "Why It Matters prose attached to obvious checks."

**Fix:** Collapse to one sentence: "In waterfall, a vague requirement compounds across phases — imprecision in D-03 produces ambiguity in D-02 and an untestable acceptance criterion at the gate."

---

## Strengths

**Inline workflow, right size.** All content stays in SKILL.md (96 lines, ~1 600 tokens). No spurious carve-outs to `references/`. The prepass zero waste-pattern count confirms clean prose.

**Conventions block properly stamped.** The canonical path-conventions block is present verbatim, correctly placed, and all paths in the skill use bare references from skill root.

**Headless mode is well-specified.** The `-H`/`--headless` section defines a precise JSON schema, a testable `status` contract (`complete` when all three core artifacts exist), and a `next_recommended` field — exactly what an orchestrator needs. The `reason` field makes the blocked state human-readable without requiring the caller to decode the `phase1_state` map.

**Script fallback is present and actionable.** Both the resolver script (Step 1) and the state scan script (Step 6) have explicit fallback instructions. Most agent skills omit one or both.

**Menu dispatch carries domain context forward.** The instruction to pass predecessor artifact paths when dispatching dependent workflows (e.g., D-02 path to [BF]) prevents the context-loss problem common in agent-to-skill handoffs. Proactive gate suggestion when all three artifacts are present is the right nudge.

**State scan script is clean.** `scan-phase1-state.py` is correctly scoped: glob + frontmatter parse + deterministic recommendation. No intelligence leak — the "next recommended" logic is a simple ordered-missing lookup, not LLM-grade judgment. The `-o` output flag for file-mode returns is a forward-compatible addition.

**`customize.toml` shape is correct.** Menu items key on `code`, enabling downstream team overrides to replace specific items without full re-declaration. `persistent_facts` uses the BMad-convention glob pattern. Boolean toggles are absent — the identity fields use scalars that replace cleanly on override.

**Decision log is present and meaningful.** `references/.decision-log.md` records the five key build decisions with rationale, not just outcomes. The previous quality analysis grade entry is a good practice for traceability.
