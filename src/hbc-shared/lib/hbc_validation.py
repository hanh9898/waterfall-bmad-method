#!/usr/bin/env python3
"""Shared validation primitives for HBC validators (Wave 0 / C-1).

Single source of truth for table parsing, column extraction, language-aware
section detection (English canonical + configured document language — NO
hardcoded Japanese), and the honest verdict object (S-3).

Validators import this via a sys.path bootstrap computed relative to skill-root:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
    from hbc_validation import parse_table, extract_column, find_section, verdict

Design boundary: this module only describes STRUCTURE. Semantic / completeness
judgement is out of scope here — that is the LLM review layer (Wave 2). The
`verdict` helper makes that boundary explicit in the output shape.
"""
from __future__ import annotations

import re

# Semantic-review states for the honest verdict (S-3).
SEMANTIC_NA = "n/a"          # structural-only validator, no semantic gate here
SEMANTIC_PENDING = "pending"  # semantic review owed but not yet done → not passed
SEMANTIC_PASSED = "passed"    # LLM/human semantic review completed


def find_section(content: str, *labels: str) -> re.Match | None:
    """Return the first level-1/level-2 markdown heading matching ANY of ``labels``.

    Labels are tried in order; matching is case-insensitive substring within a
    top-level (``#`` or ``##``) heading line — deeper subsections (``###`` …) are
    intentionally NOT matched, so a label that also appears in a subsection title
    (e.g. "Phạm vi" inside "### 1.1 Phạm vi và mục tiêu") does not shadow the real
    section. Pass the English canonical label plus the configured-language label,
    e.g. ``find_section(text, "Scope", "Phạm vi")``. No language is hardcoded.
    Empty/None labels are skipped. Returns ``None`` if no label matches.
    """
    for label in labels:
        if not label:
            continue
        m = re.compile(
            rf"^#{{1,2}}\s.*{re.escape(label)}.*$", re.IGNORECASE | re.MULTILINE
        ).search(content)
        if m:
            return m
    return None


def _heading_level(heading_line: str) -> int:
    """Number of leading '#' characters in a heading line."""
    stripped = heading_line.lstrip()
    return len(stripped) - len(stripped.lstrip("#"))


def section_body(content: str, match: re.Match) -> str:
    """Return the text from the end of heading ``match`` up to the next heading of
    equal-or-higher level (or end of document).

    Cutting at equal-or-higher level (not a fixed ``##``) means a section's own
    deeper subsections stay inside its body, while the next sibling/parent heading
    correctly terminates it.
    """
    level = _heading_level(match.group(0)) or 2
    start = match.end()
    nxt = re.search(rf"\n#{{1,{level}}}\s", content[start:])
    return content[start:start + nxt.start()] if nxt else content[start:]


# --- Test-case (TC) block parsing — shared by D-27 readiness + facet engines ---
_FENCE_LINE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_TC_HEADING_RE = re.compile(r"^#{3,6}[ \t]+TC-", re.MULTILINE | re.IGNORECASE)


def strip_code_fences(text: str) -> str:
    """Remove fenced code blocks so markup inside them (e.g. an example ``### TC-``
    heading) is never read as real document structure.

    A line-state scan (not a regex) so it pairs fences correctly regardless of
    info-string, indentation, or fence char (``` or ~~~). An UNCLOSED fence drops
    to end-of-input — fail-safe: fenced/garbled example content never leaks out to
    be miscounted as a real TC.
    """
    out: list[str] = []
    fence: str | None = None  # the opening fence char (` or ~) while inside a block
    for line in text.splitlines(keepends=True):
        m = _FENCE_LINE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0]
            else:
                out.append(line)
        elif m and m.group(1)[0] == fence:
            fence = None  # matching close — drop the closing line too
    return "".join(out)


def iter_tc_blocks(text: str) -> list[str]:
    """Each test-case detail block body, split on a ``### … TC-`` heading at levels
    3–6 (so ``#### TC-`` is not silently missed; case-insensitive), with fenced
    code stripped first. Returns the bodies AFTER each TC heading; text before the
    first heading is dropped.
    """
    return _TC_HEADING_RE.split(strip_code_fences(text))[1:]


def tc_ids(text: str) -> set[str]:
    """TC ids DECLARED as ``### … TC-NNN`` headings (levels 3-6, fence-stripped) —
    the authoritative test-case set of a D-27, mirroring iter_tc_blocks detection.
    Use to reconcile specified TCs against what a downstream report actually ran."""
    return {
        f"TC-{m}"
        for m in re.findall(r"^#{3,6}[ \t]+TC-(\d{3,})", strip_code_fences(text),
                            re.MULTILINE | re.IGNORECASE)
    }


def tc_field(block: str, label: str) -> str | None:
    """Value of a ``**Label:**`` field inside a TC block, captured up to the next
    ``**…:**`` field, blank line, or end — so a value wrapped onto the next line is
    still read. ``None`` if the field is absent, ``""`` if present but empty.

    The gap after the label is matched with ``[ \\t]*`` (NOT ``\\s*``): a bare
    ``**Label:**`` at end of line must NOT consume the newline and swallow the next
    field's line (which would, e.g., let an empty REQ ID field absorb a later
    ``**Trace:** REQ-555`` and falsely bind it). HTML comments stripped first.
    """
    cleaned = re.sub(r"<!--.*?-->", "", block, flags=re.DOTALL)
    m = re.search(
        rf"\*\*{re.escape(label)}:\*\*[ \t]*(.*?)(?=\n\s*\*\*|\n\s*\n|\Z)",
        cleaned, re.DOTALL,
    )
    return m.group(1).strip() if m else None


_TC_HEADING_CAP_RE = re.compile(r"^#{3,6}[ \t]+(TC-\d{3,})", re.MULTILINE | re.IGNORECASE)
_REQ_ID_ANY_RE = re.compile(r"REQ-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-)?\d{3,}")


def tc_req_map(text: str) -> dict[str, set[str]]:
    """REQ id -> set of TC ids bound to it, from a D-27's ``### TC-NNN`` detail
    blocks (each block's ``**REQ ID:**`` field; a block may name several REQs).
    Fence-stripped, levels 3-6 — mirrors iter_tc_blocks detection. This is the
    AUTHORITATIVE D-27 TC↔REQ binding used to detect matrix `test_ref` drift."""
    clean = strip_code_fences(text)
    parts = _TC_HEADING_CAP_RE.split(clean)  # [pre, tc1, body1, tc2, body2, ...]
    out: dict[str, set[str]] = {}
    it = iter(parts[1:])
    for tc_id, body in zip(it, it):
        req_field = tc_field(body, "REQ ID") or ""
        for req in _REQ_ID_ANY_RE.findall(req_field):
            out.setdefault(req, set()).add(tc_id.upper())
    return out


_TC_IN_CELL_RE = re.compile(r"TC-\d{3,}", re.IGNORECASE)


def matrix_req_tc_map(matrix_text: str) -> dict[str, set[str]]:
    """REQ id -> set of TC ids found in that REQ's ``test_ref`` cell, parsed from a
    traceability-matrix markdown table. Header-aware: the ``req_id`` and ``test_ref``
    columns are located BY NAME from the header row (a fixed positional map would
    misread a legacy 7-column matrix that has no leading ``feature`` column). A REQ
    with an empty ``test_ref`` maps to an empty set — present, but untraced."""
    out: dict[str, set[str]] = {}
    col_order: list[str] | None = None
    in_table = False
    for line in matrix_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            in_table = True  # separator → data rows follow
            continue
        low = [c.lower() for c in cells]
        if "req_id" in low and "test_ref" in low:
            col_order = low  # header — map columns by name, not position
            in_table = True
            continue
        if not in_table or col_order is None:
            continue
        ri, ti = col_order.index("req_id"), col_order.index("test_ref")
        if ri >= len(cells):
            continue
        m = _REQ_ID_ANY_RE.match(cells[ri])
        if not m:
            continue
        test_ref = cells[ti] if ti < len(cells) else ""
        tcs = {t.upper() for t in _TC_IN_CELL_RE.findall(test_ref)}
        out.setdefault(m.group(0), set()).update(tcs)
    return out


def test_ref_drift(d27_text: str, matrix_text: str) -> dict[str, dict[str, list[str]]]:
    """Detect matrix ``test_ref`` drift against the authoritative D-27 TC↔REQ binding.

    For each REQ that HAS a matrix row, compare its ``test_ref`` TC set against the
    TCs D-27 binds to that REQ (``tc_req_map``):
      - ``missing`` — TC bound in D-27 but absent from the matrix row (D-27 grew, the
        matrix was never back-filled — the DF-9 failure mode).
      - ``stale``   — TC in the matrix row but no longer bound in D-27 (renumbered or
        deleted upstream).
    Returns ``{req: {"missing": [...], "stale": [...]}}`` for drifted REQs only; an
    empty dict means the matrix ``test_ref`` is in sync with D-27. REQs absent from
    the matrix are intentionally ignored here — that gap is the matrix↔D-02 check's
    job (``missing_from_matrix``), not test_ref drift's.
    """
    d27_map = tc_req_map(d27_text)
    drift: dict[str, dict[str, list[str]]] = {}
    for req, mtx_tcs in matrix_req_tc_map(matrix_text).items():
        d27_tcs = d27_map.get(req, set())
        missing = sorted(d27_tcs - mtx_tcs)
        stale = sorted(mtx_tcs - d27_tcs)
        if missing or stale:
            drift[req] = {"missing": missing, "stale": stale}
    return drift


def parse_table(content: str, *labels: str) -> list[list[str]]:
    """Locate the section identified by ``labels`` and return its markdown
    table's DATA rows (header and separator excluded) as lists of cell strings.

    Returns ``[]`` when the section or a table is absent. Only rows after the
    ``|---|`` separator are treated as data — this is what lets callers trust
    table cells instead of scanning prose (S-4).
    """
    m = find_section(content, *labels)
    if not m:
        return []
    rows: list[list[str]] = []
    in_data = False  # True after a separator; reset by any non-pipe (prose/blank) line
    for line in section_body(content, m).splitlines():
        s = line.strip()
        if not s.startswith("|"):
            # A prose/blank line ends the current table block. The next pipe line
            # starts a fresh block, so its header row is skipped again — this lets
            # a section with MULTIPLE sub-tables (e.g. `### 4.1`/`### 4.2`, each with
            # its own table) contribute ALL their data rows without leaking any
            # sub-table's header row in as data.
            in_data = False
            continue
        # strip one bounding pipe each side so rows with or without a trailing
        # pipe both split correctly (GFM allows omitting the trailing pipe).
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            in_data = True  # separator → subsequent rows in this block are data
            continue
        if not in_data:
            # header row before the separator
            continue
        rows.append(cells)
    return rows


def extract_column(rows: list[list[str]], index: int) -> list[str]:
    """Return cell values at ``index`` across ``rows``, skipping rows too short."""
    return [r[index] for r in rows if index < len(r)]


def section_has_content(text: str) -> bool:
    """True if ``text`` has real content beyond scaffolding.

    Scaffolding = blank lines, table separators, and standalone table headers
    (a header row immediately followed by a separator, with no data rows) and
    HTML comment lines. Shared by every validator's section non-emptiness check.
    """
    non_blank = [ln.strip() for ln in text.splitlines() if ln.strip()]

    skip: set[int] = set()
    for i, line in enumerate(non_blank):
        if i + 1 < len(non_blank):
            nxt = non_blank[i + 1]
            is_separator = nxt.startswith("|") and set(nxt) <= {"|", "-", " ", ":"}
            is_header = line.startswith("|") and not set(line) <= {"|", "-", " ", ":"}
            if is_header and is_separator:
                skip.add(i)
                skip.add(i + 1)

    for i, line in enumerate(non_blank):
        if i in skip:
            continue
        if set(line) <= {"|", "-", " ", ":"}:
            continue
        if line.startswith("<!--") and line.endswith("-->"):
            continue
        return True

    return False


def check_required_sections(content: str, sections, empty_check: bool = True) -> list[dict]:
    """Standard SECTION_MISSING / SECTION_EMPTY issues for required sections.

    ``sections`` is an iterable of ``(canonical, *acceptable_labels)`` tuples —
    canonical is the English name reported in issues; any label (canonical or a
    configured-language alias) satisfies the presence check. No language is
    hardcoded. This is the shared replacement for each validator's bespoke
    ``check_sections`` (S-1 + C-1).

    ``empty_check`` — when False, only presence is checked (no SECTION_EMPTY),
    matching validators that historically did presence-only.
    """
    issues: list[dict] = []
    for entry in sections:
        canonical = entry[0]
        labels = entry[1:]
        match = find_section(content, canonical, *labels)
        if not match:
            alt = f" / {' / '.join(labels)}" if labels else ""
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{canonical}'{alt} not found",
                "section": canonical,
                "auto_fixable": False,
            })
            continue
        if not empty_check:
            continue
        body = section_body(content, match)
        stripped = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
        if not section_has_content(stripped):
            issues.append({
                "type": "SECTION_EMPTY",
                "message": f"Section '{canonical}' exists but has no content",
                "section": canonical,
                "auto_fixable": False,
            })
    return issues


# ============================================================================
# Cross-document & code-reconciliation primitives (Wave 1 / U1 — Đợt-1 anti-false-green)
#
# Shared detection primitives behind the Đợt-1 checks: T1.1 MODEL_DRIFT,
# T1.2 spec-ref lint, T1.3 version-coherence, T1.5 matrix-coverage, plus
# T2.11 anti-churn and the T2.12 semantic-review status read. STRUCTURE-only
# (regex/parse), language-agnostic; *meaning* stays with the LLM review layer.
# Each is unit-tested and proven against the TD.0 regression fixture so the
# detectors agree with the F-6 metrics harness on what each known bug looks like.
# ============================================================================

# A requirement id, canonical (REQ-RESOURCE-PLAN-BILLABLE-040) or bare-numeric
# (REQ-040). Reuses the module's existing _REQ_ID_ANY_RE shape.
REQ_ID_RE = _REQ_ID_ANY_RE
# Any requirement/test/NFR id — the leak signature for the spec-ref lint (T1.2).
SPEC_REF_RE = re.compile(r"\b(?:REQ|TC|NFR)-[A-Za-z0-9-]+\b")
# A markdown doc id (D-02, D-19, ...) and a version token. The version token
# REQUIRES a `v` prefix (v2.3 / V2.3) so a section ref (§3.5), a bare decimal, or a
# date fragment is never misread as a cited version — version citations in the docs
# are written "v2.2" / "(v2.2)" / "**v2.2**", section refs are "§3.5".
_DOC_ID_RE = re.compile(r"\bD-\d{2}\b")
# Trade-off (documented): the mandatory `v` cuts section-ref/decimal noise at the
# cost of missing a bare-decimal citation "D-02 2.2" — cross-refs are v-prefixed by
# convention. The optional 3rd segment keeps a patch version (v2.2.1) whole.
_VER_TOKEN_RE = re.compile(r"\bv(\d+\.\d+(?:\.\d+)?)\b", re.IGNORECASE)
# A dated revision-history row in EITHER orientation — version-first
# ("| 1.0 | 2026-01-01 |", as D-02 writes it) or date-first
# ("| 2026-06-19 | 2.1 |", as D-19 writes it). Such a row narrates a past state,
# so any version it mentions is history, not a live cross-reference.
_REV_ROW_ANY_RE = re.compile(
    r"^\|\s*(?:\d+\.\d+\s*\|\s*\d{4}-\d{2}-\d{2}|\d{4}-\d{2}-\d{2}\s*\|\s*\d+\.\d+)",
    re.MULTILINE,
)
# Declared document version from a frontmatter `version:` line.
_VERSION_FM_RE = re.compile(r"^version:\s*[\"']?(\d+\.\d+)", re.MULTILINE)
# An Odoo model `_name = '...'` declaration in code. The optional `(` + `\s*`
# (\s spans newlines) also catches a name wrapped onto the next line:
#   _name = (\n    'resource.plan.request'\n)
_CODE_NAME_RE = re.compile(r"_name\s*=\s*\(?\s*[\"']([a-z][a-z0-9_.]+)[\"']")
# The SUBJECT model of a D-19 "Physical name (Tên vật lý): `model`" declaration —
# the first backtick token after the label's colon. The required ``:`` skips
# convention prose ("Tên vật lý theo `snake_case`...") that has no colon, and the
# lazy gap stops before a later "theo mẫu `other.model`" reference on the line.
_PHYS_LINE_RE = re.compile(
    r"(?:physical name|tên vật lý)[^\n`]*?:\s*`([a-z][a-z0-9_.]+)`", re.IGNORECASE
)
# Empty / placeholder reference-cell values (a matrix cell that traces nothing).
_EMPTY_REF = {"", "-", "—", "n/a", "none", "tbd", "x", "?"}


def _trailing_num(rid: str) -> int | None:
    m = re.search(r"\d+$", rid)
    return int(m.group()) if m else None


def req_num_map(text: str) -> tuple[dict[int, str], set[str]]:
    """Map each requirement's trailing number → its longest-seen id, plus the set
    of distinct feature slugs encountered.

    For a single feature a requirement's identity *is* its trailing number — that
    is what lets the canonical id (REQ-FEAT-040) and the bare prose form (REQ-040)
    reconcile across documents. The slug set is returned so callers can detect a
    multi-feature input where trailing-number identity would collide and refuse to
    trust the count.
    """
    out: dict[int, str] = {}
    slugs: set[str] = set()
    for rid in REQ_ID_RE.findall(text or ""):
        num = _trailing_num(rid)
        if num is None:
            continue
        slug = rid[: rid.rfind("-")]
        if slug and slug != "REQ":
            slugs.add(slug)
        if num not in out or len(rid) > len(out[num]):
            out[num] = rid
    return out, slugs


def missing_from_matrix(d02_text: str, matrix_text: str) -> list[str]:
    """REQ ids defined in D-02 but with NO row in the traceability matrix (T1.5).

    Identity = trailing number (sound for a single feature; for multi-feature
    inputs check ``req_num_map(...)[1]`` for >1 slug and treat the count as
    unreliable). This is the "39/39 green but 040/041/042 never added" failure.
    """
    d02, _ = req_num_map(d02_text)
    matrix_nums = set(req_num_map(matrix_text)[0])
    return [d02[n] for n in sorted(d02) if n not in matrix_nums]


def parse_matrix(matrix_text: str) -> tuple[dict[str, int], list[list[str]]]:
    """``(header name→index, data rows)`` for a traceability-matrix markdown table.

    Header-name based (not positional) so both the 7-column legacy matrix and the
    8-column one (with a leading ``feature`` column) parse correctly. Only rows
    whose ``req_id`` cell is a real REQ id are returned as data.

    Header cells are normalized (lowercased, spaces→underscores) so a human/localized
    variant like ``req id`` / ``design ref`` is still recognized — otherwise an
    unrecognized header would yield zero rows and silently pass the coverage check.
    """
    header: dict[str, int] = {}
    rows: list[list[str]] = []
    for line in (matrix_text or "").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            continue  # separator
        low = [c.strip().lower().replace(" ", "_") for c in cells]
        if not header:
            if "req_id" in low:
                header = {name: i for i, name in enumerate(low)}
            continue
        i = header.get("req_id", 0)
        if i < len(cells) and REQ_ID_RE.match(cells[i]):
            rows.append(cells)
    return header, rows


def _blank_ref(cell: str) -> bool:
    return cell.strip().lower() in _EMPTY_REF


def matrix_coverage_gaps(
    matrix_text: str, columns: tuple[str, ...] = ("design_ref", "code_ref", "test_ref")
) -> dict[str, list[str]]:
    """Per-REQ list of which trace columns are EMPTY (T1.5).

    A REQ that has a matrix row but a blank ``design_ref``/``code_ref``/``test_ref``
    is still untraced for that axis. Returns ``{req_id: [empty_columns]}`` for
    rows with ≥1 gap (a missing column header counts as a gap for every row).
    """
    header, rows = parse_matrix(matrix_text)
    gaps: dict[str, list[str]] = {}
    for cells in rows:
        rid = cells[header["req_id"]].strip()
        empty = [
            c
            for c in columns
            if header.get(c, -1) < 0
            or header[c] >= len(cells)
            or _blank_ref(cells[header[c]])
        ]
        if empty:
            gaps[rid] = empty
    return gaps


def reqs_without_task(req_ids, tasks_text: str) -> list[str]:
    """REQ ids with no mention in the task-breakdown — every REQ needs ≥1 task (T1.5).

    Matched by trailing number so canonical and bare id styles reconcile.
    """
    task_nums = {n for n in (_trailing_num(r) for r in REQ_ID_RE.findall(tasks_text or "")) if n is not None}
    return sorted(
        r for r in req_ids if (_trailing_num(r) is not None and _trailing_num(r) not in task_nums)
    )


def revision_count(text: str) -> int:
    """Number of dated revision-history rows — the churn signal (T2.11). Counts
    BOTH orientations: version-first (``| N.N | YYYY-MM-DD |``, as D-02 writes it)
    and date-first (``| YYYY-MM-DD | N.N |``, as D-06/D-19 write it), so date-first
    docs are no longer silently un-counted. RCA case (D-02): 13; target ≤4."""
    return len(_REV_ROW_ANY_RE.findall(text or ""))


def churn_assessment(text: str, threshold: int = 4) -> dict:
    """``{revisions, threshold, high_churn}`` for a document's revision history (T2.11).

    ``high_churn`` (revisions > threshold) is the cue a create-skill surfaces to
    suggest the model isn't frozen yet (maturity=exploratory / run [DSC]) instead
    of bumping the version on every small edit.
    """
    n = revision_count(text)
    return {"revisions": n, "threshold": threshold, "high_churn": n > threshold}


def doc_version(text: str) -> str | None:
    """A document's declared version from its frontmatter ``version:`` line, or None."""
    m = _VERSION_FM_RE.search(text or "")
    return m.group(1) if m else None


def version_citations(text: str) -> list[tuple[str, str]]:
    """All ``(doc_id, version)`` version attributions in prose (T1.3).

    On each line, every version token is bound to the NEAREST preceding doc id on
    that line — so ``D-02 (v2.2), D-19 (v2.3)`` attributes 2.2→D-02 and 2.3→D-19
    rather than cross-wiring them. Lines that mention no doc id yield nothing (a
    bare frontmatter ``version:`` is handled by ``doc_version`` instead).
    """
    out: list[tuple[str, str]] = []
    for line in (text or "").splitlines():
        # A dated revision-history row (either orientation) describes a PAST state,
        # not a current cross-reference — never a coherence claim about the live
        # document, so it is skipped.
        if _REV_ROW_ANY_RE.match(line.strip()):
            continue
        tokens: list[tuple[int, str, str]] = []
        for m in _DOC_ID_RE.finditer(line):
            tokens.append((m.start(), "doc", m.group(0)))
        for m in _VER_TOKEN_RE.finditer(line):
            tokens.append((m.start(), "ver", m.group(1)))
        tokens.sort()
        cur: str | None = None
        for _pos, kind, val in tokens:
            if kind == "doc":
                cur = val
            elif cur is not None:
                out.append((cur, val))
    return out


def version_coherence(authority_versions: dict[str, str], citing_texts: dict[str, str]) -> list[dict]:
    """Flag citations whose cited version ≠ the authority doc's declared version (T1.3).

    ``authority_versions``: ``{doc_id: declared_version}`` (build with ``doc_version``).
    ``citing_texts``: ``{label: text}`` of the downstream docs to scan. This catches
    "D-26 cites D-02 v2.2 while D-02 is actually v2.3" — the cross-doc staleness the
    RCA case showed after the v2.0 U-turn. Returns one issue per stale citation.
    """
    issues: list[dict] = []
    for label, text in citing_texts.items():
        seen: set[tuple[str, str]] = set()
        for doc, cited in version_citations(text):
            declared = authority_versions.get(doc)
            if declared is not None and cited != declared and (doc, cited) not in seen:
                seen.add((doc, cited))
                issues.append({"source": label, "doc": doc, "cited": cited, "declared": declared})
    return issues


def spec_ref_leaks(text: str) -> list[str]:
    """Every REQ-/TC-/NFR- id embedded in a source/test file (T1.2).

    A spec id in code couples the implementation to the spec document — when the
    spec is renumbered the code silently rots. Returns the raw matches (with
    duplicates) so a caller can both count and list them.
    """
    return SPEC_REF_RE.findall(text or "")


def model_tokens_from_design(d19_text: str) -> set[str]:
    """Odoo model ``_name``s declared in D-19 "Physical name (Tên vật lý)" lines —
    the unambiguous model-level design tokens (e.g. ``resource.plan.request``).

    Restricted to physical-name lines (not the whole document) to stay high-signal:
    a model that the design declares as a real table but code never defines is the
    drift we care about, not an incidental dotted expression in prose.
    """
    out: set[str] = set()
    for line in (d19_text or "").splitlines():
        m = _PHYS_LINE_RE.search(line)
        if m:
            out.add(m.group(1))
    return out


def _model_present(name: str, text: str) -> bool:
    """Whole-identifier presence of an Odoo model name, tolerant of the dotted
    (``resource.plan.summary``) vs underscored-table (``resource_plan_summary``)
    spelling — present if ANY form appears as a whole token. Both directions of the
    conversion are tried so an underscore-spelled design name still matches a
    dotted ``_name`` in code and vice-versa.

    The boundary treats ``.`` AND word chars as identifier characters, so a shorter
    model name does NOT match inside a longer one (``resource.plan`` must not be
    'present' merely because ``resource.plan.request`` appears — that masking would
    hide real drift)."""
    forms = {name, name.replace(".", "_"), name.replace("_", ".")}
    for f in forms:
        if re.search(r"(?<![\w.])" + re.escape(f) + r"(?![\w.])", text):
            return True
    return False


def model_drift(design_text: str, code_text: str, *, extra_tokens=()) -> dict:
    """Bidirectional model-level drift between the D-19 design and the code (T1.1).

    ``design_only`` — a model declared in D-19 (physical-name ``_name``s, plus any
      ``extra_tokens`` a caller derives, e.g. field-level tokens) but absent from
      code: the RCA drift (design moved to Request+Snapshot, code stayed on the old
      model).
    ``code_only`` — an Odoo ``_name`` model in code that the design never mentions.
      Pass only persistent-model code (e.g. ``models/``, not transient wizards) to
      keep this signal meaningful.

    Presence is whole-identifier and dotted/underscored-tolerant (see
    ``_model_present``). ``drift`` is True when either list is non-empty.
    """
    code_text = code_text or ""
    design_text = design_text or ""
    design_tokens = model_tokens_from_design(design_text) | set(extra_tokens)
    code_names = set(_CODE_NAME_RE.findall(code_text))
    design_only = sorted(t for t in design_tokens if not _model_present(t, code_text))
    code_only = sorted(n for n in code_names if not _model_present(n, design_text))
    return {"design_only": design_only, "code_only": code_only, "drift": bool(design_only or code_only)}


# The semanticReview block = consecutive indented OR blank lines after the key,
# stopping at the next non-indented (dedented) line. Allowing blank lines inside
# means a block-form openFacets list separated by a blank line is NOT truncated
# (which would hide an open facet and read as a false pass).
_SR_BLOCK_RE = re.compile(r"semanticReview:[ \t]*\n((?:(?:[ \t]+\S.*)?\n)*)")


def semantic_review_status(text: str) -> dict:
    """Read the ``semanticReview`` frontmatter block (T2.12 / RM.2).

    Returns ``{status, open_facets_empty, passed}``. ``passed`` is true ONLY when
    ``status == 'passed'`` AND ``openFacets`` is present-and-empty — the exact
    condition the phase-gate REVIEW item enforces, kept here as the single
    structural read so every skill and the gate agree.

    Fail-safe defaults: a missing block, an unreadable status, or an ABSENT
    ``openFacets`` key all yield ``passed = False`` — you cannot earn a pass by
    simply omitting the facet list. ``status`` tolerates surrounding quotes.
    """
    m = _SR_BLOCK_RE.search(text or "")
    if not m:
        return {"status": None, "open_facets_empty": None, "passed": False}
    block = m.group(1)
    sm = re.search(r"status:\s*[\"']?([A-Za-z/]+)", block)
    status = sm.group(1).strip() if sm else None
    if "openFacets:" not in block:
        open_empty = None  # key absent → cannot assert emptiness → not a pass
    else:
        inline = re.search(r"openFacets:\s*\[(.*?)\]", block, re.DOTALL)
        if inline is not None:
            open_empty = not inline.group(1).strip()
        else:
            # block-list form: empty unless a "- item" exists (blank lines allowed)
            open_empty = not re.search(r"openFacets:[ \t]*\n(?:[ \t]*\n)*[ \t]*-\s+\S", block)
    return {
        "status": status,
        "open_facets_empty": open_empty,
        "passed": status == "passed" and open_empty is True,
    }


def verdict(
    structure_ok: bool,
    *,
    semantic_review: str = SEMANTIC_NA,
    checked: list[str] | None = None,
    not_checked: list[str] | None = None,
) -> dict:
    """Build the honest verdict object (S-3).

    A validator may only assert STRUCTURE. ``passed`` is true only when the
    structure is OK *and* the semantic review is not still ``pending`` — so a
    consumer can never read a green structural check as "document is correct".
    """
    return {
        "structure_ok": bool(structure_ok),
        "semantic_review": semantic_review,
        "checked": list(checked or []),
        "not_checked": list(not_checked or []),
        "passed": bool(structure_ok) and semantic_review != SEMANTIC_PENDING,
    }
