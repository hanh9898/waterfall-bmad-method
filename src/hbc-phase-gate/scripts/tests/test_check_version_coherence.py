#!/usr/bin/env python3
"""Tests for check-version-coherence.py (T1.3)."""

import os
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "check_version_coherence",
    os.path.join(os.path.dirname(__file__), "..", "check-version-coherence.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)
check = mod.check


def _doc(doc_id, ver, body=""):
    return f'---\ndocument_id: {doc_id}\nversion: "{ver}"\n---\n{body}'


def test_stale_citation_flagged():
    docs = {
        "D-02.md": _doc("D-02", "2.3"),
        "D-26.md": _doc("D-26", "2.3", "Test plan derived per D-02 (v2.2)."),
    }
    r = check(docs)
    assert r["valid"] is False
    assert r["authority_versions"]["D-02"] == "2.3"
    msgs = [i["message"] for i in r["issues"]]
    assert any("D-02 v2.2" in m for m in msgs)


def test_coherent_when_aligned():
    docs = {
        "D-02.md": _doc("D-02", "2.3"),
        "D-26.md": _doc("D-26", "2.3", "Per D-02 v2.3 the scope is fixed."),
    }
    r = check(docs)
    assert r["valid"] is True and r["total_issues"] == 0


def test_revision_row_citation_not_flagged():
    # a date-first revision row narrating an old sync must not count as a live citation
    body = (
        "| Date | Version | Notes |\n|---|---|---|\n"
        "| 2026-06-19 | 1.1 | synced to D-02 v1.6 |\n"
    )
    docs = {"D-02.md": _doc("D-02", "2.3"), "D-19.md": _doc("D-19", "2.3", body)}
    r = check(docs)
    assert r["total_issues"] == 0


def test_section_ref_not_misread_as_version():
    docs = {
        "D-02.md": _doc("D-02", "2.3"),
        "D-19.md": _doc("D-19", "2.3", "See D-02 §3.5 and §2.1 for the rules."),
    }
    r = check(docs)
    assert r["total_issues"] == 0  # §3.5 / §2.1 are sections, not versions


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
