"""Tests for merge-help-csv.py."""

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the module from its hyphenated filename via importlib
# ---------------------------------------------------------------------------
_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "merge-help-csv.py"
_spec = importlib.util.spec_from_file_location("merge_help_csv", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

read_csv_rows = _mod.read_csv_rows
extract_module_codes = _mod.extract_module_codes
filter_rows = _mod.filter_rows
write_csv = _mod.write_csv
cleanup_legacy_csvs = _mod.cleanup_legacy_csvs
HEADER = _mod.HEADER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv_file(path: Path, rows: list[list[str]]) -> None:
    """Write a list of rows (including header) to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def _read_csv_file(path: Path) -> list[list[str]]:
    """Read all rows from a CSV file."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


# ---------------------------------------------------------------------------
# read_csv_rows
# ---------------------------------------------------------------------------

class TestReadCsvRows:
    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        header, rows = read_csv_rows(str(tmp_path / "nope.csv"))
        assert header == []
        assert rows == []

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.csv"
        empty.write_text("", encoding="utf-8")
        header, rows = read_csv_rows(str(empty))
        assert header == []
        assert rows == []

    def test_header_only_returns_header_no_rows(self, tmp_path: Path) -> None:
        p = tmp_path / "header_only.csv"
        _write_csv_file(p, [["module", "skill", "display-name"]])
        header, rows = read_csv_rows(str(p))
        assert header == ["module", "skill", "display-name"]
        assert rows == []

    def test_valid_csv_returns_header_and_rows(self, tmp_path: Path) -> None:
        p = tmp_path / "data.csv"
        _write_csv_file(p, [
            ["module", "skill", "display-name"],
            ["mod-a", "sk1", "Skill One"],
            ["mod-b", "sk2", "Skill Two"],
        ])
        header, rows = read_csv_rows(str(p))
        assert header == ["module", "skill", "display-name"]
        assert len(rows) == 2
        assert rows[0] == ["mod-a", "sk1", "Skill One"]
        assert rows[1] == ["mod-b", "sk2", "Skill Two"]


# ---------------------------------------------------------------------------
# extract_module_codes
# ---------------------------------------------------------------------------

class TestExtractModuleCodes:
    def test_empty_rows(self) -> None:
        assert extract_module_codes([]) == set()

    def test_extracts_unique_codes(self) -> None:
        rows = [
            ["mod-a", "sk1", "x"],
            ["mod-b", "sk2", "y"],
            ["mod-a", "sk3", "z"],
        ]
        assert extract_module_codes(rows) == {"mod-a", "mod-b"}

    def test_strips_whitespace(self) -> None:
        rows = [["  mod-a  ", "sk1", "x"]]
        assert extract_module_codes(rows) == {"mod-a"}

    def test_skips_empty_first_column(self) -> None:
        rows = [
            ["", "sk1", "x"],
            ["   ", "sk2", "y"],
            ["mod-a", "sk3", "z"],
        ]
        assert extract_module_codes(rows) == {"mod-a"}

    def test_skips_empty_rows(self) -> None:
        rows = [[], ["mod-a", "sk1"]]
        assert extract_module_codes(rows) == {"mod-a"}


# ---------------------------------------------------------------------------
# filter_rows
# ---------------------------------------------------------------------------

class TestFilterRows:
    def test_removes_matching_rows(self) -> None:
        rows = [
            ["mod-a", "sk1", "x"],
            ["mod-b", "sk2", "y"],
            ["mod-a", "sk3", "z"],
        ]
        result = filter_rows(rows, "mod-a")
        assert len(result) == 1
        assert result[0][0] == "mod-b"

    def test_keeps_all_when_no_match(self) -> None:
        rows = [
            ["mod-b", "sk2", "y"],
            ["mod-c", "sk3", "z"],
        ]
        result = filter_rows(rows, "mod-a")
        assert len(result) == 2

    def test_empty_rows_returns_empty(self) -> None:
        assert filter_rows([], "mod-a") == []

    def test_preserves_empty_row_entries(self) -> None:
        rows = [[], ["mod-a", "sk1"], ["mod-b", "sk2"]]
        result = filter_rows(rows, "mod-a")
        assert len(result) == 2
        assert result[0] == []
        assert result[1][0] == "mod-b"

    def test_strips_whitespace_for_comparison(self) -> None:
        rows = [["  mod-a  ", "sk1"]]
        result = filter_rows(rows, "mod-a")
        assert result == []


# ---------------------------------------------------------------------------
# write_csv
# ---------------------------------------------------------------------------

class TestWriteCsv:
    def test_writes_header_and_rows(self, tmp_path: Path) -> None:
        p = tmp_path / "out.csv"
        write_csv(str(p), ["h1", "h2"], [["a", "b"], ["c", "d"]])
        all_rows = _read_csv_file(p)
        assert all_rows[0] == ["h1", "h2"]
        assert all_rows[1] == ["a", "b"]
        assert all_rows[2] == ["c", "d"]
        assert len(all_rows) == 3

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        p = tmp_path / "deep" / "nested" / "dir" / "out.csv"
        write_csv(str(p), ["h1"], [["v1"]])
        assert p.exists()
        all_rows = _read_csv_file(p)
        assert len(all_rows) == 2

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        p = tmp_path / "out.csv"
        _write_csv_file(p, [["old_h"], ["old_v"]])
        write_csv(str(p), ["new_h"], [["new_v"]])
        all_rows = _read_csv_file(p)
        assert all_rows[0] == ["new_h"]
        assert all_rows[1] == ["new_v"]
        assert len(all_rows) == 2

    def test_writes_header_only_when_no_data_rows(self, tmp_path: Path) -> None:
        p = tmp_path / "empty_data.csv"
        write_csv(str(p), ["h1", "h2"], [])
        all_rows = _read_csv_file(p)
        assert len(all_rows) == 1
        assert all_rows[0] == ["h1", "h2"]


# ---------------------------------------------------------------------------
# cleanup_legacy_csvs
# ---------------------------------------------------------------------------

class TestCleanupLegacyCsvs:
    def test_deletes_module_and_core_csvs(self, tmp_path: Path) -> None:
        legacy_dir = tmp_path / "_bmad"
        mod_csv = legacy_dir / "mod-a" / "module-help.csv"
        core_csv = legacy_dir / "core" / "module-help.csv"
        _write_csv_file(mod_csv, [["h"]])
        _write_csv_file(core_csv, [["h"]])

        deleted = cleanup_legacy_csvs(str(legacy_dir), "mod-a")
        assert len(deleted) == 2
        assert str(mod_csv) in deleted
        assert str(core_csv) in deleted
        assert not mod_csv.exists()
        assert not core_csv.exists()

    def test_handles_missing_files_gracefully(self, tmp_path: Path) -> None:
        legacy_dir = tmp_path / "_bmad"
        legacy_dir.mkdir(parents=True)
        deleted = cleanup_legacy_csvs(str(legacy_dir), "mod-a")
        assert deleted == []

    def test_deletes_only_module_csv_when_core_missing(self, tmp_path: Path) -> None:
        legacy_dir = tmp_path / "_bmad"
        mod_csv = legacy_dir / "mod-a" / "module-help.csv"
        _write_csv_file(mod_csv, [["h"]])

        deleted = cleanup_legacy_csvs(str(legacy_dir), "mod-a")
        assert len(deleted) == 1
        assert str(mod_csv) in deleted

    def test_returns_string_paths(self, tmp_path: Path) -> None:
        legacy_dir = tmp_path / "_bmad"
        mod_csv = legacy_dir / "mod-x" / "module-help.csv"
        _write_csv_file(mod_csv, [["h"]])

        deleted = cleanup_legacy_csvs(str(legacy_dir), "mod-x")
        assert all(isinstance(p, str) for p in deleted)


# ---------------------------------------------------------------------------
# CLI integration (subprocess)
# ---------------------------------------------------------------------------

class TestCliIntegration:
    def _run_script(self, *extra_args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_SCRIPT_PATH), *extra_args],
            capture_output=True,
            text=True,
        )

    def test_basic_merge_creates_target(self, tmp_path: Path) -> None:
        source = tmp_path / "source.csv"
        target = tmp_path / "target.csv"
        _write_csv_file(source, [
            ["module", "skill", "display-name"],
            ["mod-a", "sk1", "Skill One"],
        ])

        result = self._run_script("--target", str(target), "--source", str(source))
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout)
        assert output["status"] == "success"
        assert output["rows_added"] == 1
        assert output["total_rows"] == 1

        all_rows = _read_csv_file(target)
        assert all_rows[0] == ["module", "skill", "display-name"]
        assert all_rows[1] == ["mod-a", "sk1", "Skill One"]

    def test_anti_zombie_replaces_old_rows(self, tmp_path: Path) -> None:
        target = tmp_path / "target.csv"
        _write_csv_file(target, [
            ["module", "skill", "display-name"],
            ["mod-a", "old-sk", "Old Skill"],
            ["mod-b", "sk-b", "Skill B"],
        ])

        source = tmp_path / "source.csv"
        _write_csv_file(source, [
            ["module", "skill", "display-name"],
            ["mod-a", "new-sk", "New Skill"],
        ])

        result = self._run_script("--target", str(target), "--source", str(source))
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout)
        assert output["rows_removed"] == 1
        assert output["rows_added"] == 1
        assert output["total_rows"] == 2

        all_rows = _read_csv_file(target)
        # mod-b row kept, old mod-a removed, new mod-a appended
        data_rows = all_rows[1:]
        modules = [r[0] for r in data_rows]
        assert "mod-b" in modules
        assert modules.count("mod-a") == 1
        # The mod-a row should be the new one
        mod_a_row = [r for r in data_rows if r[0] == "mod-a"][0]
        assert mod_a_row[1] == "new-sk"

    def test_legacy_cleanup_via_cli(self, tmp_path: Path) -> None:
        source = tmp_path / "source.csv"
        target = tmp_path / "target.csv"
        legacy_dir = tmp_path / "_bmad"

        _write_csv_file(source, [
            ["module", "skill"],
            ["mod-a", "sk1"],
        ])

        # Create legacy files
        legacy_mod = legacy_dir / "mod-a" / "module-help.csv"
        legacy_core = legacy_dir / "core" / "module-help.csv"
        _write_csv_file(legacy_mod, [["h"]])
        _write_csv_file(legacy_core, [["h"]])

        result = self._run_script(
            "--target", str(target),
            "--source", str(source),
            "--legacy-dir", str(legacy_dir),
            "--module-code", "mod-a",
        )
        assert result.returncode == 0, result.stderr
        output = json.loads(result.stdout)
        assert len(output["legacy_csvs_deleted"]) == 2
        assert not legacy_mod.exists()
        assert not legacy_core.exists()

    def test_empty_source_exits_with_error(self, tmp_path: Path) -> None:
        source = tmp_path / "empty_source.csv"
        target = tmp_path / "target.csv"
        _write_csv_file(source, [["module", "skill"]])

        result = self._run_script("--target", str(target), "--source", str(source))
        assert result.returncode == 1
        assert "No data rows" in result.stderr

    def test_legacy_dir_without_module_code_exits_with_error(self, tmp_path: Path) -> None:
        source = tmp_path / "source.csv"
        target = tmp_path / "target.csv"
        _write_csv_file(source, [
            ["module", "skill"],
            ["mod-a", "sk1"],
        ])

        result = self._run_script(
            "--target", str(target),
            "--source", str(source),
            "--legacy-dir", str(tmp_path / "_bmad"),
        )
        assert result.returncode == 1
        assert "--module-code is required" in result.stderr
