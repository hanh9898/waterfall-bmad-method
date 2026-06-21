#!/usr/bin/env python3
"""U1 regression: the Đợt-1 primitives must catch the TD.0 known bugs.

This is the "bắt lỗi fixture" half of U1's DoD — it proves the shared detection
primitives (T1.1/T1.2/T1.3/T1.5 + T2.11) re-derive the same known-bug signals on
the frozen RCA fixture that the F-6 metrics harness measures, so the per-skill
checks built on these primitives are anchored to a fixed substrate.

If the fixture is absent (e.g. a slim checkout) the regression is skipped, not
failed — the unit tests in test_hbc_validation.py still prove the logic.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import hbc_validation as hv  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
FIX = REPO / "process-review" / "fixtures" / "resource-plan-billable"
ART = FIX / "artifacts"

pytestmark = pytest.mark.skipif(not FIX.is_dir(), reason="TD.0 fixture not present")


def _read(rel: str) -> str:
    return (ART / rel).read_text(encoding="utf-8", errors="replace")


def _code_text(subdir: str = "") -> str:
    base = FIX / "code" / subdir if subdir else FIX / "code"
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace") for p in base.rglob("*.py")
    )


@pytest.fixture(scope="module")
def docs():
    return {
        "d02": _read("planning-artifacts/D-02-resource-plan-billable.md"),
        "matrix": _read("traceability/matrix.md"),
        "d19": _read("planning-artifacts/D-19-opms/D-19-er-diagram.md"),
        "d26": _read("planning-artifacts/D-26-resource-plan-billable-test-plan.md"),
        "tasks": _read("implementation-artifacts/task-breakdown.md"),
    }


def test_t15_missing_matrix_rows_040_041_042(docs):
    missing = hv.missing_from_matrix(docs["d02"], docs["matrix"])
    nums = {m[-3:] for m in missing}
    assert {"040", "041", "042"} <= nums  # the three REQs never added to the matrix


def test_t15_stale_task_breakdown_leaves_reqs_untasked(docs):
    reqs = list(hv.req_num_map(docs["d02"])[0].values())
    untasked = hv.reqs_without_task(reqs, docs["tasks"])
    assert untasked, "stale v1.8 task-breakdown should leave v2.3 REQs without a task"


def test_t211_d02_churn_baseline_13(docs):
    assert hv.revision_count(docs["d02"]) == 13  # RCA "13 versions"
    assert hv.churn_assessment(docs["d02"])["high_churn"] is True


def test_t13_version_incoherence_d02_cited_stale(docs):
    authority = {"D-02": hv.doc_version(docs["d02"]), "D-19": hv.doc_version(docs["d19"])}
    assert authority["D-02"] == "2.3"
    issues = hv.version_coherence(authority, {"D-26": docs["d26"]})
    assert any(i["doc"] == "D-02" and i["cited"] == "2.2" for i in issues)
    # no historical revision-row citations should leak in as false incoherence
    assert all(i["cited"] not in {"1.6", "1.8"} for i in issues)


def test_t12_spec_ref_leak_baseline_44():
    prod = len(hv.spec_ref_leaks(_code_text("models"))) + len(
        hv.spec_ref_leaks(_code_text("wizard"))
    )
    test = len(hv.spec_ref_leaks(_code_text("tests")))
    assert prod + test == 44  # matches the harness baseline (29 prod + 15 test)


def test_t11_model_drift_request_snapshot_missing():
    drift = hv.model_drift(_read("planning-artifacts/D-19-opms/D-19-er-diagram.md"),
                           _code_text("models"))
    assert "resource.plan.request" in drift["design_only"]
    assert "resource.plan.request.line" in drift["design_only"]
    assert drift["code_only"] == []  # no rogue persistent models in code/models


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
