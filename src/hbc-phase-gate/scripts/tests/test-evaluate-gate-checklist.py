#!/usr/bin/env python3
"""Tests for evaluate-gate-checklist.py."""

import os

from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "evaluate_gate_checklist",
    os.path.join(os.path.dirname(__file__), "..", "evaluate-gate-checklist.py"),
)
assert _spec is not None and _spec.loader is not None
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

parse_checklist = mod.parse_checklist
resolve_pattern = mod.resolve_pattern
evaluate_file = mod.evaluate_file
evaluate_content = mod.evaluate_content
evaluate_metric = mod.evaluate_metric


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


SAMPLE_CHECKLIST = """\
# Phase 1: Analysis — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P1-01 | Requirements doc exists | FILE | yes | _bmad-output/planning-artifacts/D-02* | | hbc-create-requirements |
| P1-02 | All REQs have IDs | CONTENT | yes | _bmad-output/planning-artifacts/D-02* | REQ-\\d{3} | |
| P1-03 | Coverage threshold met | METRIC | yes | _bmad-output/implementation-artifacts/coverage* | >= 80% | |
| P1-04 | Requirements quality | QUALITY | no | _bmad-output/planning-artifacts/D-02* | Check clarity | |
"""


class TestParseChecklist:
    def test_parses_all_rows(self, tmp_path):
        path = str(tmp_path / "checklist.md")
        _write(path, SAMPLE_CHECKLIST)
        items = parse_checklist(path)
        assert len(items) == 4

    def test_parses_item_fields(self, tmp_path):
        path = str(tmp_path / "checklist.md")
        _write(path, SAMPLE_CHECKLIST)
        items = parse_checklist(path)
        item = items[0]
        assert item["item_id"] == "P1-01"
        assert item["description"] == "Requirements doc exists"
        assert item["type"] == "FILE"
        assert item["required"] is True
        assert item["artifact_pattern"] == "_bmad-output/planning-artifacts/D-02*"
        assert item["skill_to_create"] == "hbc-create-requirements"

    def test_quality_item_parsed(self, tmp_path):
        path = str(tmp_path / "checklist.md")
        _write(path, SAMPLE_CHECKLIST)
        items = parse_checklist(path)
        quality = items[3]
        assert quality["type"] == "QUALITY"
        assert quality["required"] is False
        assert quality["criteria"] == "Check clarity"

    def test_empty_skill_to_create(self, tmp_path):
        path = str(tmp_path / "checklist.md")
        _write(path, SAMPLE_CHECKLIST)
        items = parse_checklist(path)
        assert items[1]["skill_to_create"] == ""

    def test_empty_file_returns_no_items(self, tmp_path):
        path = str(tmp_path / "empty.md")
        _write(path, "# No table here\nJust text.")
        items = parse_checklist(path)
        assert items == []


class TestResolvePattern:
    def test_substitutes_variables(self):
        result = resolve_pattern(
            "_bmad-output/{project_name}/D-02*",
            "/project",
            {"project_name": "acme"},
        )
        assert "acme" in result

    def test_prepends_project_root_for_relative(self):
        result = resolve_pattern("_bmad-output/planning-artifacts/D-02*", "/project", {})
        assert result.startswith("/project")

    def test_absolute_path_unchanged(self):
        result = resolve_pattern("/abs/path/D-02*", "/project", {})
        assert result == "/abs/path/D-02*"


class TestEvaluateFile:
    def test_pass_when_file_exists(self, tmp_path):
        _write(str(tmp_path / "D-02-requirements.md"))
        result = evaluate_file("D-02*", str(tmp_path), {})
        assert result["status"] == "PASS"
        assert "D-02-requirements.md" in result["evidence"]

    def test_fail_when_no_match(self, tmp_path):
        result = evaluate_file("D-02*", str(tmp_path), {})
        assert result["status"] == "FAIL"

    def test_matched_files_list(self, tmp_path):
        _write(str(tmp_path / "D-02-req.md"))
        _write(str(tmp_path / "D-02-req-v2.md"))
        result = evaluate_file("D-02*", str(tmp_path), {})
        assert len(result["matched_files"]) == 2


class TestEvaluateContent:
    def test_pass_when_pattern_found(self, tmp_path):
        _write(str(tmp_path / "D-02-req.md"), "REQ-001: Login\nREQ-002: Logout")
        result = evaluate_content("D-02*", r"REQ-\d{3}", str(tmp_path), {})
        assert result["status"] == "PASS"
        assert result["match_count"] >= 2

    def test_fail_when_pattern_not_found(self, tmp_path):
        _write(str(tmp_path / "D-02-req.md"), "No requirements here")
        result = evaluate_content("D-02*", r"REQ-\d{3}", str(tmp_path), {})
        assert result["status"] == "FAIL"
        assert result["match_count"] == 0

    def test_fail_when_no_files(self, tmp_path):
        result = evaluate_content("D-02*", r"REQ-\d{3}", str(tmp_path), {})
        assert result["status"] == "FAIL"
        assert "No files found" in result["evidence"]

    def test_comma_separated_patterns(self, tmp_path):
        _write(str(tmp_path / "D-02-req.md"), "REQ-001")
        _write(str(tmp_path / "D-06-flow.md"), "REQ-002")
        pattern = f"{tmp_path}/D-02*,{tmp_path}/D-06*"
        result = evaluate_content(pattern, r"REQ-\d{3}", str(tmp_path), {})
        assert result["status"] == "PASS"
        assert result["match_count"] >= 2


class TestEvaluateMetric:
    def test_pass_when_above_threshold(self, tmp_path):
        _write(str(tmp_path / "coverage.txt"), "Overall coverage: 85%")
        result = evaluate_metric("coverage*", ">= 80%", str(tmp_path), {})
        assert result["status"] == "PASS"
        assert result["actual_value"] == 85.0

    def test_fail_when_below_threshold(self, tmp_path):
        _write(str(tmp_path / "coverage.txt"), "Overall coverage: 65%")
        result = evaluate_metric("coverage*", ">= 80%", str(tmp_path), {})
        assert result["status"] == "FAIL"
        assert result["actual_value"] == 65.0

    def test_fail_when_no_files(self, tmp_path):
        result = evaluate_metric("coverage*", ">= 80%", str(tmp_path), {})
        assert result["status"] == "FAIL"
        assert result["actual_value"] is None

    def test_skip_when_no_number_extractable(self, tmp_path):
        _write(str(tmp_path / "coverage.txt"), "No numbers here")
        result = evaluate_metric("coverage*", ">= 80%", str(tmp_path), {})
        assert result["status"] == "SKIP"

    def test_variable_substitution_in_criteria(self, tmp_path):
        _write(str(tmp_path / "coverage.txt"), "Coverage: 90%")
        result = evaluate_metric(
            "coverage*",
            ">= {coverage_threshold}%",
            str(tmp_path),
            {"coverage_threshold": "80"},
        )
        assert result["status"] == "PASS"
        assert result["threshold"] == 80.0


class TestEdgeCases:
    def test_type_case_insensitive(self, tmp_path):
        checklist = """\
# Test

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| T-01 | Test | file | yes | D-02* | | |
"""
        path = str(tmp_path / "checklist.md")
        _write(path, checklist)
        items = parse_checklist(path)
        assert items[0]["type"] == "FILE"

    def test_required_true_variants(self, tmp_path):
        checklist = """\
# Test

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| T-01 | A | FILE | yes | D* | | |
| T-02 | B | FILE | true | D* | | |
| T-03 | C | FILE | no | D* | | |
"""
        path = str(tmp_path / "checklist.md")
        _write(path, checklist)
        items = parse_checklist(path)
        assert items[0]["required"] is True
        assert items[1]["required"] is True
        assert items[2]["required"] is False


def test_dir_aware_glob_resolves_md_inside(tmp_path):
    # C-4: a D-06 workspace FOLDER matched by the glob resolves to the .md inside,
    # not the directory itself (fixes D-06 folder-vs-flat + "1 file(s)" confusion).
    ws = tmp_path / "planning-artifacts" / "D-06-business-flow"
    _write(str(ws / "D-06-business-flow-diagram.md"), "```mermaid\nsequenceDiagram\n  A->>B: hi\n```\n")
    res_file = evaluate_file("planning-artifacts/D-06-*", str(tmp_path), {})
    assert res_file["status"] == "PASS"
    assert any(m.endswith(".md") for m in res_file["matched_files"])
    res_content = evaluate_content("planning-artifacts/D-06-*", "mermaid", str(tmp_path), {})
    assert res_content["status"] == "PASS"
    assert res_content["match_count"] >= 1


def test_review_status_passed(tmp_path):
    # #5: REVIEW item passes only when semanticReview.status == passed
    doc = tmp_path / "planning-artifacts" / "D-27-test-spec.md"
    _write(str(doc), "---\nsemanticReview:\n  status: passed\n  reviewedBy: llm\n---\n\n# D-27\n")
    res = mod.evaluate_review("planning-artifacts/D-27*", str(tmp_path), {})
    assert res["status"] == "PASS", res


def test_review_status_pending_fails(tmp_path):
    doc = tmp_path / "planning-artifacts" / "D-27-test-spec.md"
    _write(str(doc), "---\nsemanticReview:\n  status: pending\n---\n\n# D-27\n")
    res = mod.evaluate_review("planning-artifacts/D-27*", str(tmp_path), {})
    assert res["status"] == "FAIL", res


def test_review_status_missing_fails(tmp_path):
    doc = tmp_path / "planning-artifacts" / "D-27-test-spec.md"
    _write(str(doc), "---\ntitle: x\n---\n\n# D-27\n")
    res = mod.evaluate_review("planning-artifacts/D-27*", str(tmp_path), {})
    assert res["status"] == "FAIL", res


def test_review_inline_yaml(tmp_path):
    doc = tmp_path / "planning-artifacts" / "D-27-test-spec.md"
    _write(str(doc), "---\nsemanticReview: {status: passed}\n---\n\n# D-27\n")
    res = mod.evaluate_review("planning-artifacts/D-27*", str(tmp_path), {})
    assert res["status"] == "PASS", res


def test_review_status_no_trailing_newline(tmp_path):
    # F3: file whose final line is `status: passed` with no trailing newline still parses
    doc = tmp_path / "planning-artifacts" / "D-27-test-spec.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("---\nsemanticReview:\n  status: passed", encoding="utf-8")  # no \n at EOF
    res = mod.evaluate_review("planning-artifacts/D-27*", str(tmp_path), {})
    assert res["status"] == "PASS", res


def test_review_status_hyphenated_not_truncated(tmp_path):
    # F3: a hyphenated status is not truncated to before the hyphen
    doc = tmp_path / "planning-artifacts" / "D-27-test-spec.md"
    _write(str(doc), "---\nsemanticReview:\n  status: not-applicable\n---\n")
    # 'not-applicable' != 'passed' → FAIL, but must capture the FULL token (not 'not')
    res = mod.evaluate_review("planning-artifacts/D-27*", str(tmp_path), {})
    assert res["status"] == "FAIL"
    assert res["review_status"][doc.name] == "not-applicable"


# --- B2: entry-gate (prior gate PASSED) is non-negotiable even in lenient mode ---

def test_is_entry_gate_detects_prior_gate_check():
    entry = {"type": "CONTENT", "required": True,
             "artifact_pattern": "{output_folder}/gates/phase-1-gate*"}
    not_entry = {"type": "CONTENT", "required": True,
                 "artifact_pattern": "{output_folder}/planning-artifacts/D-02*"}
    optional = {"type": "CONTENT", "required": False,
                "artifact_pattern": "{output_folder}/gates/phase-1-gate*"}
    assert mod._is_entry_gate(entry) is True
    assert mod._is_entry_gate(not_entry) is False
    assert mod._is_entry_gate(optional) is False  # only required items block


_ENTRY_GATE_CHECKLIST = """\
# Phase 2 — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P2-00 | Phase 1 gate PASSED | CONTENT | yes | {output_folder}/gates/phase-1-gate* | Status:.*PASSED | |
"""


def _run_engine(checklist_path, project_root, *vars_):
    import json
    import subprocess
    import sys
    cmd = [sys.executable,
           os.path.join(os.path.dirname(__file__), "..", "evaluate-gate-checklist.py"),
           checklist_path, "--project-root", project_root]
    for v in vars_:
        cmd += ["--var", v]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def test_entry_gate_failure_not_downgraded_by_lenient(tmp_path):
    # No phase-1 gate report exists → entry-gate item FAILs. Even in lenient mode
    # the script must report overall FAILED + entry_gate_failed=1.
    path = str(tmp_path / "phase-2-gate-checklist.md")
    _write(path, _ENTRY_GATE_CHECKLIST)
    data, code = _run_engine(path, str(tmp_path),
                             f"output_folder={tmp_path}", "gate_mode=lenient")
    assert data["summary"]["entry_gate_failed"] == 1
    assert data["summary"]["overall_status"] == "FAILED"
    assert code == 1


def test_entry_gate_passes_when_prior_report_present(tmp_path):
    gates = tmp_path / "gates"
    gates.mkdir()
    _write(str(gates / "phase-1-gate.md"), "# Phase 1\n\n**Status:** PASSED\n")
    path = str(tmp_path / "phase-2-gate-checklist.md")
    _write(path, _ENTRY_GATE_CHECKLIST)
    data, code = _run_engine(path, str(tmp_path),
                             f"output_folder={tmp_path}", "gate_mode=lenient")
    assert data["summary"]["entry_gate_failed"] == 0
    assert data["summary"]["overall_status"] == "PASSED"
    assert code == 0
