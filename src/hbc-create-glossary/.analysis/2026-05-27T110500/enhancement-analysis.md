# Enhancement Analysis — hbc-create-glossary
**Scanner:** L4 Enhancement Opportunities
**Date:** 2026-05-27
**Skill:** `src/hbc-create-glossary`

---

## Skill Understanding

`hbc-create-glossary` generates D-03 用語集 (Glossary) — a bilingual reference of domain terms and abbreviations with project-specific definitions. Its primary user is a project analyst or documentation lead working within the hblab BMad workflow, typically after D-02 Requirements is in place. The skill assumes Python 3.10+ for both scripts, pre-existing D-02 / project-context.md artifacts as term sources, and a Japanese-primary template that produces a bilingual (JP/EN) markdown document.

---

## User Journeys

### First-Timer

**Narrative:** A new team member invokes the skill by typing "thuật ngữ" in the chat. They've just finished D-02. No prior glossary exists.

**Bright spots:**
- The scan script auto-detects source docs and returns term candidates immediately. The first-timer never manually lists files.
- The Stage 2 open invitation ("share domain-specific terms, abbreviations, jargon") is accessible and lowers the barrier.
- The next-step suggestion at Stage 4 handoff is clear and actionable.

**Friction points:**
- The first-timer sees `[A] Advanced / [P] Party Mode / [C] Continue` at Stage 3 with no inline description. They don't know what "Party Mode" means or how long either review will take. They'll likely mash `[C]` — discarding potentially valuable review they'd have wanted if it had been named clearly.
- The template filename `D-03_用語集_template.md` contains Japanese characters and spaces. On some operating systems or CI environments this causes path handling errors, but the SKILL.md gives no warning about this.
- The first-timer's definitions will likely be generic ("API: Application Programming Interface"). The LLM judgment check flags these, but the collaborative-fix loop in Stage 3 isn't described in enough detail: they won't know if they need to fix all flagged items before the glossary is saved.

---

### Expert User (knows exactly what they want)

**Narrative:** A senior analyst has a complete list of 40+ domain terms in a separate notes file. They want to feed the file, skip discovery Q&A, and get a reviewed glossary in one shot.

**Bright spots:**
- Headless mode with `--sources` covers this case entirely if they're comfortable with the CLI.
- The `update` arg lets them iterate on an existing D-03 without losing prior terms.

**Friction points:**
- There is no interactive "fast path" for experts who want to paste a pre-formatted term list. Stage 2 assumes an oral/chat-based collection process. An expert with a spreadsheet or CSV of terms has no way to signal "just ingest this list" — they'll be walked through the discovery Q&A anyway.
- The `--sources` arg in headless mode accepts file paths, but there is no guidance in SKILL.md (or headless-contract.md) about whether the expert can pass an arbitrary notes file (vs. only D-02 / project-context.md). The scan script only auto-extracts from `D-02*` and `D-01*` glob patterns — a notes file would be ignored silently.
- `update` mode is mentioned in the Args line but has no dedicated stage description. The expert who runs `update` on a 40-term glossary doesn't know how new terms merge with existing ones, whether duplicates are surfaced, or whether the revision history is auto-updated.

---

### Confused User (invoked by accident or wrong intent)

**Narrative:** A developer invokes `[GLO]` from the agent menu because they thought it would generate API documentation ("glossary" as in "API reference").

**Bright spots:**
- Stage 1b has an explicit intent gate: "If wrong skill, suggest the right one." This is good practice.

**Friction points:**
- The intent gate fires *after* the scan script runs, meaning the wrong-skill user has already waited for a potentially slow file-system scan before being redirected.
- The suggested alternatives at the intent gate aren't specified. "Suggest the right one" is outcome-based writing, which is correct per quality principles — but since API doc generation is a common confusion, a concrete redirection hint ("did you mean hbc-create-requirements?") baked into the SKILL.md would prevent a second wrong turn.
- The description trigger includes `'glossary'` as an English trigger, which is broad enough to activate on unrelated developer conversations ("let's add a glossary to our README", "check the API glossary"). The broader context guard is only as good as the LLM's interpretation of the description.

---

### Edge-Case User (technically valid but unexpected input)

**Scenario A — No source docs, rich oral knowledge:** A greenfield project where D-02 and project-context.md don't exist yet. The scan script returns `state: fresh`, `source_count: 0`, `candidate_count: 0`. The skill proceeds to Stage 2 but has no pre-populated candidates. The user is staring at a blank discovery stage with no anchoring terms. This is technically valid (the glossary can be built purely from oral input) but the transition from scan result to discovery isn't bridged: the SKILL.md doesn't say what to do when `candidate_count == 0`.

**Scenario B — Very large source docs with hundreds of candidates:** The scan script deduplicates but applies no scoring or ranking to candidates. A D-02 with 200 extracted candidates would be presented as a flat list. The user must triage 200 items manually. There is no mechanism to surface "high-confidence" vs. "speculative" candidates, making the pre-population feature a liability at scale.

**Scenario C — Mixed-language project:** A project with Vietnamese and English documentation. The `「」` Japanese quote patterns in `scan-glossary-sources.py` won't fire on Vietnamese text. `"CapitalizedPhrase"` double-quote pattern will catch some English terms, but Vietnamese terms (e.g. `"Hệ thống quản lý"`) use no standard markers. Candidate extraction would silently under-represent Vietnamese source material.

**Scenario D — Glossary with 0 abbreviations:** The template has a required 略語一覧 section. The validator checks for the section's presence but not whether it's populated. A project with zero abbreviations is technically valid but the validator won't flag an empty abbreviation table. The LLM may generate a placeholder row or leave the table empty — neither is caught automatically.

---

### Hostile Environment (deps fail, files missing, context limited)

**Bright spots:**
- SKILL.md Stage 3 explicitly states: "If the script is unavailable, fall back to LLM-only validation." This graceful degradation is good.
- Compaction flushes in Stages 2 and 3 write state to the decision log, allowing recovery.

**Friction points:**
- The scan script (`scan-glossary-sources.py`) has no explicit error return for permission errors — a `search_dir.glob()` call on a directory with restricted permissions will raise `PermissionError`, which bubbles as an unhandled exception and kills the script entirely. The LLM receives no JSON back and has no fallback path in SKILL.md for "scan script crashed" (distinct from "scan script unavailable").
- Context compaction mid-Stage 2 (during a long discovery conversation with many terms) is partially mitigated by the compaction flush. However, the flush only writes "term count and category summary" — it doesn't write the actual discovered terms. If compaction drops Stage 2 state before the flush fires, the full term list is lost and must be re-elicited.
- The `--project-root` argument is required for the scan script but SKILL.md always passes `{project-root}` — which is correct. However there is no check for what happens when `{project-root}` resolves to a non-existent path. The script will create an empty result (no source docs, no D-03 found) and return `state: fresh` silently, which could mask a misconfiguration.

---

### Automator (pipeline / another agent invoking headless)

**Bright spots:**
- Headless mode and a formal `headless-contract.md` exist — this is well-considered.
- `blocked` status with a one-line `reason` field and three explicit blocked-reason strings (`no_source_documents`, `validation_manual_fix`, `no_terms_extracted`) gives callers actionable routing logic.
- The return schema includes `validation.term_count` and `validation.total_entries`, which are useful for downstream quality gates.

**Friction points:**
- The headless contract's `--sources` arg accepts "comma-separated file paths" but the scan script's `--project-root` arg runs its own glob-based discovery. These two mechanisms are orthogonal: it is unclear whether passing `--sources` bypasses the scan script's auto-discovery or supplements it. An automator building a pipeline cannot reason about which documents will actually be scanned without reading the script source.
- The return schema has no `candidate_count_from_scan` field. A pipeline agent that invokes headless on a sparse source set cannot tell whether the glossary is thin because the domain has few terms or because candidate extraction failed.
- The headless contract doesn't document what happens when `--mode update` is used headlessly — does it require `--sources` to specify the existing D-03? Is the existing D-03 auto-detected from the output dir? This gap would cause a pipeline error in the update path.
- There is no `--dry-run` option documented for headless. A CI job that wants to validate an existing D-03 without mutating it (`--mode validate`) does exist, but it's underspecified in the contract (validate mode isn't mentioned in the return schema example or blocked-reason list).

---

## Headless Assessment

**Level: Easily adaptable** (currently functional but with gaps)

The headless foundation is solid. The contract exists, the return schema is defined, and the scan script provides the automated source discovery that makes headless viable. The main adaptations needed:

| Interaction point | Current state | Auto-resolution path |
|---|---|---|
| Stage 2 open invitation | Always interactive | Skip when `--headless`: treat scan candidates as full term list |
| Stage 2 soft-gate ("Any more?") | Interactive | Skip in headless: no more sources available |
| Stage 3 parallel-lens menu | Always interactive | Default to `[C] Continue` in headless; log choice to decision log |
| Stage 1b intent gate | Interactive | Skip in headless: assume intent is correct |
| Update mode term merging | Undocumented | Needs explicit headless path: auto-merge, flag conflicts as `blocked` |

**Minimum headless invocation for Create:**
```
hbc-create-glossary --headless --sources "path/D-02.md,path/project-context.md"
```

**Missing from contract:** `--mode validate` return schema, `--mode update` input requirements, behavior when `--sources` is omitted (auto-discovery only).

---

## Facilitative Patterns Check

| Pattern | Present | Assessment |
|---|---|---|
| Open-floor opening | Partial | Stage 2 has the open invitation but it comes *after* a structured pre-population step. The invitation could more explicitly say "share everything you have before I ask structured questions." |
| Soft-gate elicitation | Yes | "Any more terms, or shall we finalize?" is correctly placed at each batch boundary. |
| Intent-before-ingestion | Partial | Stage 1b fires *after* the scan script runs. Intent should be confirmed before the system performs any work, not after a potentially 10-second scan. |
| Capture-don't-interrupt | Yes | Stage 2 explicitly calls out silent capture of requirements/business-flow insights. |
| Dual-output | No | The glossary is produced as a human document only. A distillate for downstream agents (e.g., a flat `term: definition` YAML or JSON) would materially help automators and subsequent document-generation skills that need to maintain terminology consistency. |
| Parallel review lenses | Partial | The `[A] Advanced / [P] Party Mode` menu exists but the labels are opaque. "Party Mode" is fun but unexplained; a first-timer won't know it means multi-reviewer perspective. |
| Three-mode architecture | Yes | Guided / (implicit Yolo via pre-populations) / Headless — well covered. |
| Graceful degradation | Partial | Script fallback is documented. Scan-script crash (vs. unavailable) is not handled. |

**Most valuable pattern to add:** Dual-output. The glossary is a foundational vocabulary document — every subsequent skill that generates D-04 through D-09 will benefit from a machine-readable `glossary-distillate.json` (term → definition map). Adding this as a Stage 4 step costs almost nothing and transforms the skill from a one-shot document generator into a living vocabulary service for the pipeline.

---

## Findings

### HIGH — Dual-output distillate missing

**Location:** Stage 4: Save and Handoff, `headless-contract.md`

The glossary is the canonical term reference for all downstream documents. Skills generating requirements specs, design docs, or test plans need to apply consistent terminology. Currently, each downstream skill re-reads the full D-03 markdown to extract terms, or ignores it entirely. A `glossary-distillate.json` (flat `{term: definition}` map) written alongside D-03 would:
- Give headless callers a machine-readable artifact.
- Let downstream skills load only the distillate (small) instead of the full document (large with formatting).
- Serve as the "dual-output" pattern at near-zero cost.

**Suggestion:** In Stage 4, after saving D-03, write `glossary-distillate.json` to the same output directory. Add the path to the headless return schema as `distillate_path`.

---

### HIGH — Intent gate fires after work is done

**Location:** Stage 1: Prerequisites, step 1b

The scan script runs before intent is confirmed. For a confused user, this means they've waited for file-system scanning before being told they're in the wrong skill. More importantly, for a pipeline caller, the scan creates side effects (reads files, evaluates state) before the caller's intent is verified.

**Suggestion:** Swap 1a and 1b: confirm intent first (one line of check — does the conversation context actually want a glossary?), then run the scan. This follows the "intent-before-ingestion" pattern and saves wasted work on wrong-skill invocations. In headless, skip the gate (intent is given by invocation).

---

### HIGH — Update mode is undocumented end-to-end

**Location:** SKILL.md Args line, `headless-contract.md`

`update` is listed as a valid arg but has no dedicated stage description. Key questions are unanswered:
- How are new terms merged with existing terms?
- Are duplicates between old and new terms surfaced or silently dropped?
- Is the revision history row in 改訂履歴 auto-updated?
- In headless, does `--mode update` require `--sources` for new terms, or does it re-scan the project?

An update user who adds 10 terms to a 40-term glossary has no guarantee the final document is correct, and a pipeline caller has no documented behavior to rely on.

**Suggestion:** Add an `## Update Mode` subsection to SKILL.md (3-4 sentences) covering: load existing D-03 as baseline, present diff of new candidates vs. existing terms, merge non-duplicates, append revision history row. Add `update` path to headless contract with its specific blocked reasons.

---

### MEDIUM — Parallel-lens menu labels are opaque

**Location:** Stage 3: Generation, final line

`[A] Advanced / [P] Party Mode / [C] Continue` — "Party Mode" is the BMad institutional name for multi-reviewer perspective, but a first-time user of this skill has no reason to know that. The expert who would benefit from `[A]` Challenge Mode also gets no description of what "Advanced" challenges (definitions? completeness? cross-artifact alignment?).

**Suggestion:** Add a one-line inline description at the menu point:
- `[A] Advanced — challenge definitions, find missing terms from D-02`
- `[P] Party Mode — multiple reviewer perspectives (terminology specialist, domain expert, end user)`
- `[C] Continue — proceed to save`

This is 2-3 lines added to SKILL.md and materially improves uptake of the review feature.

---

### MEDIUM — Candidate extraction silently fails for non-Japanese, non-English sources

**Location:** `scripts/scan-glossary-sources.py`, `TERM_PATTERNS`

The `「」` Japanese quote patterns and `"CapitalizedPhrase"` English double-quote pattern are the only term extraction heuristics. Vietnamese, Korean, or custom-formatted source documents produce near-zero candidates. The first-timer working on a Vietnamese project sees 0 candidates and doesn't know why — they assume the skill is broken.

**Suggestion:** Two options (pick one):
1. Add a `--language` flag to the scan script and include a Vietnamese term pattern (e.g., italicized terms or bold-marked terms via `**term**` markdown markers, which are language-agnostic).
2. Add a fallback markdown-pattern extraction: any `**bold**` or `_italic_` term in source docs is a candidate, regardless of language. This is weaker signal but language-neutral.

Also add a note in Stage 2 when `candidate_count == 0` and `source_count > 0`: "No candidates extracted from sources — either terms aren't marked with standard patterns, or the documents are in a language the extractor doesn't cover. Please provide terms directly."

---

### MEDIUM — Compaction flush loses actual terms, only saves count

**Location:** Stage 2: Discovery, "Compaction flush" note

The flush writes "discovered term count and category summary to decision log." If context compaction fires mid-discovery before the flush, the actual terms are lost. Even after the flush fires, the decision log contains only count + categories — not the terms themselves. A resumed session after compaction cannot reconstruct what was already collected.

**Suggestion:** Change the compaction flush instruction to: "Write discovered terms (term + definition + category for each) and total count to decision log." The decision log is append-only and serves exactly this purpose. A full term dump at flush time costs a few hundred tokens but prevents total loss of discovery work.

---

### MEDIUM — No empty-abbreviation-table handling

**Location:** Template `D-03_用語集_template.md`, `scripts/validate-glossary.py`

The validator checks that 略語一覧 section *exists* but not that it's populated. A project with no abbreviations produces an empty table in the final document. This is visually confusing (a table with only headers), and the LLM has no instruction about what to do with an empty abbreviation section.

**Suggestion:** Add a Stage 3 LLM judgment check: "If no abbreviations were collected, either omit the 略語一覧 section or add a one-row placeholder noting 'No abbreviations defined.' Do not leave an empty table." Correspondingly, the validator's `REQUIRED_SECTIONS` check for 略語一覧 should be conditional on whether abbreviations exist.

---

### LOW — "Party Mode" label may not survive localization

**Location:** Stage 3: Generation

The label "Party Mode" is English slang that translates poorly into Japanese or Vietnamese. If `{communication_language}` is Japanese, the menu item will appear in an otherwise-Japanese conversation as an unexplained English phrase.

**Suggestion:** Use a language-neutral label at the menu point, e.g., `[P] Multi-lens review`, and let the LLM adapt the label to the communication language naturally.

---

### LOW — Revision history date is not auto-populated

**Location:** `templates/D-03_用語集_template.md`

The 改訂履歴 table's "Date" column is empty in the template (`| 1.0 | | | 初版作成 |`). Stage 4 says to update frontmatter but doesn't mention populating the revision history date. The LLM may or may not fill it — behavior is undefined.

**Suggestion:** Add to Stage 4: "Populate the 改訂履歴 row's date with today's date and the session's author (from config if available, otherwise leave author blank)."

---

### LOW — No adjacent-skill suggestions for the confused user at intent gate

**Location:** Stage 1b: Intent gate

"If wrong skill, suggest the right one" is outcome-based writing — correct per quality principles. But since the common confusion is known (API glossary → requirements, code glossary → technical spec), a brief parenthetical example would help: "(e.g., if user wants API reference, suggest hbc-create-requirements [REQ])."

---

## Top 3 Insights

**1. Add dual-output distillate — transforms the skill from document-generator to vocabulary service.**
The glossary is foundational to all downstream document quality. Without a machine-readable distillate, every subsequent skill either re-parses the full markdown or ignores the glossary entirely. A `glossary-distillate.json` written at Stage 4 costs ~3 lines of instruction and returns outsized value to the entire pipeline.

**2. Intent before ingestion — swap 1a and 1b.**
Confirming intent before running the scan script is a 1-line SKILL.md reorder that eliminates wasted work for confused users and ensures the scan's side effects are always intentional. This is the "intent-before-ingestion" pattern from the institutional library and it's missing here.

**3. Update mode needs a real specification.**
`update` is listed in Args but is effectively undocumented. For a skill that manages a living reference document, the update path is as important as the create path. A pipeline that calls `--mode update` headlessly has no reliable behavior contract. Three to four sentences in SKILL.md and two additions to the headless contract would close this gap completely.

