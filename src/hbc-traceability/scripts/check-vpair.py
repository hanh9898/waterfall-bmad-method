#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""v_pair-edge enforcement for hbc-traceability (TA.6 — V-Model design<->test).

WHAT THIS IS
============
The deliverable catalog declares, for each design deliverable, the V-Model TEST
LEVEL it must be paired with (``v_pair``): D-02/D-06 -> acceptance, D-09/D-19/D-21
-> integration-test, D-16/D-27 -> unit-test, D-14 -> e2e-test. A design deliverable
that EXISTS for a feature must carry that v_pair edge in the traceability matrix:
the requirements it contributes to must actually be traced to a test (a non-empty
``test_ref`` edge). A missing v_pair edge is a real V-Model design<->test coverage
gap (e.g. a model was designed in D-19 but no integration test edge was ever added).

This builds ON the TA.1 build-graph kernel (``hbc_buildgraph``): the matrix is a
VIEW computed from the graph (REQs from the upstream D-02 node, rows from the matrix
node), and ``missing_edges`` already flags REQs defined in D-02 with no matrix row.
TA.6 adds the catalog-driven v_pair LAYER on top: which design deliverables are
PRESENT, what test level each one requires, and whether that edge exists.

THE MODEL (catalog-driven, severity)
====================================
For each design deliverable D-xx that is PRESENT on disk AND declares ``v_pair: L``:
  * status MISSING / severity ``high``  -> the entire pairing is absent: the matrix
    node is missing, or NO matrix row carries a test edge (blank ``test_ref``
    everywhere). The design level has no test level at all.
  * status MISSING / severity ``medium`` -> the pairing is PARTIAL: some requirements
    have no test edge — a REQ defined in D-02 with no matrix row (``missing_edges``)
    or a matrix row with a blank ``test_ref``. Those requirements are designed but
    not test-traced at level L.
  * status present -> every requirement carries a test edge.

Absent / N-A deliverables are NOT flagged (no false MISSING for a deliverable a
feature legitimately does not have). Deliverables with ``v_pair: null`` (D-03, D-12,
D-26, constitution, ...) are skipped — they declare no V-Model test pairing.

WHAT IS THE MACHINE FLOOR vs DEFERRED
=====================================
This is the machine FLOOR: does a test EDGE exist for each requirement of a present,
v_pair-bearing design deliverable. Whether the traced test is actually AT level L
(an integration test, not a unit test masquerading) needs the per-row test-level
LABEL, which lives in D-26/D-27's level sections (often absent at matrix time). When
that label source is absent the level-MATCH is an honest ``pending`` note, forward-
referenced to T3.12 (V-Model surface) — NOT decided here. T3.12 is not built by this
task; this relies only on the catalog ``v_pair`` data, which is present today.

Output JSON (stdout):
  {
    "feature": "<dir name>",
    "present_design_deliverables": ["D-02", "D-06", "D-19", ...],
    "vpair_gaps": [ {deliverable, expected_test_level, status, severity, detail,
                     uncovered_reqs?} ],
    "level_match": "pending|n/a",          # test-LEVEL confirmation (T3.12 forward-ref)
    "summary": {"checked": N, "missing": M, "high": H, "medium": Mm}
  }

Run with `python` (Windows dev) or `python3` (Linux/Mac CI):
    python3 {skill-root}/scripts/check-vpair.py --feature-dir <dir>

Exit: 0 no v_pair gap · 1 >=1 v_pair gap · 2 io error (feature dir / D-02 missing).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- shared lib bootstrap (parents[2] -> hbc-shared/lib) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_buildgraph import load_corpus, BuildGraph  # noqa: E402
    from hbc_validation import parse_matrix, _blank_ref, req_num_map  # noqa: E402
except Exception as exc:  # pragma: no cover - import wiring
    print(json.dumps({"error": f"cannot import shared lib: {exc}"}), file=sys.stderr)
    raise SystemExit(2)

# Catalog lives in hbc-shared/references (read-only). parents[2] -> hbc-shared.
_CATALOG = Path(__file__).resolve().parents[2] / "hbc-shared" / "references" / "deliverable-catalog.yaml"

# A deliverable's v_pair is "the entire pairing absent" -> high; "partial" -> medium.
_SEV_HIGH, _SEV_MED = "high", "medium"


def load_vpair_map(catalog_path: Path) -> dict[str, str]:
    """``{D-xx: test-level}`` for every deliverable that declares a non-null v_pair.

    Catalog-driven and the SINGLE source of which design<->test pairing is required.
    Prefer PyYAML; fall back to a stdlib regex over each ``{ id: ... v_pair: ... }``
    entry so the script stays stdlib-only and never crashes when PyYAML is absent.
    Deliverables with ``v_pair: null`` are omitted (they declare no pairing).
    """
    text = ""
    if catalog_path.is_file():
        try:
            text = catalog_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    if not text:
        return {}
    out: dict[str, str] = {}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        for d in data.get("deliverables") or []:
            vp = d.get("v_pair")
            did = d.get("id")
            if did and vp:  # null/None/"" all falsy -> skipped
                out[str(did)] = str(vp)
        return out
    except Exception:
        # stdlib fallback: one entry per `{ ... }` line carrying id + v_pair.
        for m in re.finditer(r"\{[^{}]*\bid:\s*([\w-]+)[^{}]*\}", text):
            entry = m.group(0)
            did = m.group(1)
            vm = re.search(r"\bv_pair:\s*([^\s,}]+)", entry)
            if not vm:
                continue
            vp = vm.group(1).strip().strip('"').strip("'")
            if vp and vp.lower() not in ("null", "none", "~"):
                out[did] = vp
        return out


# Design-deliverable id pattern (D-02 ... D-27) — for locating present design files.
_DID_RE = re.compile(r"^D-\d{2}$")


def present_design_deliverables(root: Path, vpair_map: dict[str, str]) -> list[str]:
    """Which v_pair-bearing design deliverables EXIST under the feature dir.

    Presence = a ``D-xx*.md`` file anywhere beneath the feature (either supported
    layout). Only deliverables that carry a v_pair are considered — others have no
    pairing to enforce. Determined from the filesystem so an ABSENT deliverable is
    never flagged MISSING (it has nothing to pair). Sorted, deduped.
    """
    present: set[str] = set()
    for did in vpair_map:
        if not _DID_RE.match(did):
            continue
        if any(root.rglob(f"{did}*.md")):
            present.add(did)
    return sorted(present, key=lambda d: (int(d.split("-")[1]), d))


def matrix_test_edges(g: BuildGraph) -> tuple[bool, set[int], set[int]]:
    """From the graph's matrix node: ``(has_matrix, req_nums_with_test, req_nums_row)``.

    ``req_nums_with_test`` = trailing numbers of REQs whose matrix row carries a
    non-empty ``test_ref`` edge. ``req_nums_row`` = all REQ numbers that have a row.
    Reuses ``parse_matrix`` (header-name based, 7/8-col tolerant). None-safe: an
    absent matrix node yields ``(False, set(), set())``.
    """
    matrix = g.one_of_kind("matrix")
    if matrix is None:
        return False, set(), set()
    header, rows = parse_matrix(matrix.text)
    ri = header.get("req_id", 0)
    ti = header.get("test_ref", -1)
    with_test: set[int] = set()
    have_row: set[int] = set()
    for cells in rows:
        if ri >= len(cells):
            continue
        num = _trailing_num(cells[ri])
        if num is None:
            continue
        have_row.add(num)
        if ti >= 0 and ti < len(cells) and not _blank_ref(cells[ti]):
            with_test.add(num)
    return True, with_test, have_row


def _trailing_num(rid: str) -> int | None:
    m = re.search(r"\d+$", rid or "")
    return int(m.group()) if m else None


def enforce_vpair(root: Path, g: BuildGraph, vpair_map: dict[str, str]) -> dict:
    """Catalog-driven v_pair-edge enforcement over the build-graph + matrix.

    The V-Model invariant: every present, v_pair-bearing design deliverable's
    requirements must carry a test EDGE in the matrix at the declared level. The
    requirement universe is the upstream D-02 node (matrix-as-view) so the matrix
    cannot silently omit a REQ. Severity: ``high`` = pairing entirely absent;
    ``medium`` = some requirements uncovered. Deterministic (sorted) and None-safe.
    """
    present = present_design_deliverables(root, vpair_map)
    d02 = g._d02_node()
    d02_nums = sorted(req_num_map(d02.text)[0]) if d02 is not None else []
    has_matrix, with_test, have_row = matrix_test_edges(g)

    # REQs with no test edge: defined in D-02 but no matrix row, OR a row whose
    # test_ref is blank. Identity = trailing number (single-feature sound).
    uncovered = sorted(n for n in d02_nums if n not in with_test)
    canon = {n: rid for n, rid in zip(d02_nums, (req_num_map(d02.text)[0][n] for n in d02_nums))} if d02 else {}

    gaps: list[dict] = []
    for did in present:
        level = vpair_map[did]
        if not has_matrix or not with_test:
            # No matrix at all, or matrix carries zero test edges -> the entire
            # design<->test pairing for this level is absent.
            gaps.append({
                "deliverable": did,
                "expected_test_level": level,
                "status": "MISSING",
                "severity": _SEV_HIGH,
                "detail": ("no matrix node" if not has_matrix
                           else "matrix carries no test edge for any requirement"),
            })
        elif uncovered:
            gaps.append({
                "deliverable": did,
                "expected_test_level": level,
                "status": "MISSING",
                "severity": _SEV_MED,
                "detail": f"{len(uncovered)} requirement(s) have no {level} test edge",
                "uncovered_reqs": [canon.get(n, f"REQ-...-{n:03d}") for n in uncovered],
            })
        else:
            gaps.append({
                "deliverable": did,
                "expected_test_level": level,
                "status": "present",
                "severity": None,
                "detail": "all requirements carry a test edge",
            })

    missing = [g for g in gaps if g["status"] == "MISSING"]
    return {
        "present_design_deliverables": present,
        "vpair_gaps": gaps,
        # The test-LEVEL label (is the edge actually an integration test, not just a
        # test) lives in D-26/D-27 level sections — a separate (T3.12) surface. We
        # confirm the EDGE here; the level MATCH is honestly pending.
        "level_match": "pending",
        "summary": {
            "checked": len(present),
            "missing": len(missing),
            "high": sum(1 for x in missing if x["severity"] == _SEV_HIGH),
            "medium": sum(1 for x in missing if x["severity"] == _SEV_MED),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Enforce V-Model v_pair design<->test edges (TA.6).")
    ap.add_argument("--feature-dir", required=True,
                    help="Feature directory containing the artifacts (planning/, traceability/, ...).")
    ap.add_argument("--catalog", default=None,
                    help="Override path to deliverable-catalog.yaml (default: hbc-shared).")
    args = ap.parse_args(argv)

    root = Path(args.feature_dir)
    if not root.is_dir():
        print(json.dumps({"error": f"feature dir not found: {root}"}), file=sys.stderr)
        return 2

    g = load_corpus(root)
    if g._d02_node() is None:
        print(json.dumps({"error": f"no D-02 (requirements) artifact found under {root}"}),
              file=sys.stderr)
        return 2

    catalog_path = Path(args.catalog) if args.catalog else _CATALOG
    vpair_map = load_vpair_map(catalog_path)
    if not vpair_map:
        print(json.dumps({"error": f"no v_pair data loaded from catalog: {catalog_path}"}),
              file=sys.stderr)
        return 2

    result = enforce_vpair(root, g, vpair_map)
    result = {"feature": root.name, **result}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["summary"]["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
