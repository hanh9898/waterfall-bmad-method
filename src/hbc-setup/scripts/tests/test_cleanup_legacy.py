"""Tests for cleanup-legacy.py — legacy directory removal after config migration."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the module from a hyphenated filename via importlib
# ---------------------------------------------------------------------------
_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "cleanup-legacy.py"
_spec = importlib.util.spec_from_file_location("cleanup_legacy", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

find_skill_dirs = _mod.find_skill_dirs
count_files = _mod.count_files
verify_skills_installed = _mod.verify_skills_installed
cleanup_directories = _mod.cleanup_directories


# ===================================================================
# Helpers
# ===================================================================

def _make_skill(base: Path, dirname: str) -> Path:
    """Create a minimal skill directory with a SKILL.md file."""
    skill_dir = base / dirname
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Skill\n")
    return skill_dir


def _make_files(directory: Path, count: int) -> None:
    """Populate *directory* with *count* plain files."""
    directory.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (directory / f"file_{i}.txt").write_text(f"content {i}")


# ===================================================================
# find_skill_dirs
# ===================================================================


class TestFindSkillDirs:
    def test_finds_skill_dirs(self, tmp_path: Path) -> None:
        _make_skill(tmp_path / "module", "bmad-agent-builder")
        _make_skill(tmp_path / "module", "bmad-setup")

        result = find_skill_dirs(str(tmp_path / "module"))

        assert result == ["bmad-agent-builder", "bmad-setup"]

    def test_returns_empty_for_nonexistent_path(self, tmp_path: Path) -> None:
        result = find_skill_dirs(str(tmp_path / "does-not-exist"))

        assert result == []

    def test_returns_empty_when_no_skill_md(self, tmp_path: Path) -> None:
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "README.md").write_text("not a skill")

        result = find_skill_dirs(str(tmp_path))

        assert result == []

    def test_deduplicates_skill_names(self, tmp_path: Path) -> None:
        # Two SKILL.md files under directories with the same leaf name at
        # different nesting depths — should deduplicate.
        (tmp_path / "a" / "myskill").mkdir(parents=True)
        (tmp_path / "a" / "myskill" / "SKILL.md").write_text("")
        (tmp_path / "b" / "myskill").mkdir(parents=True)
        (tmp_path / "b" / "myskill" / "SKILL.md").write_text("")

        result = find_skill_dirs(str(tmp_path))

        assert result == ["myskill"]

    def test_nested_skill_dirs(self, tmp_path: Path) -> None:
        # SKILL.md nested two levels deep
        deep = tmp_path / "level1" / "level2" / "deep-skill"
        deep.mkdir(parents=True)
        (deep / "SKILL.md").write_text("")

        result = find_skill_dirs(str(tmp_path))

        assert result == ["deep-skill"]


# ===================================================================
# count_files
# ===================================================================


class TestCountFiles:
    def test_counts_files_recursively(self, tmp_path: Path) -> None:
        _make_files(tmp_path / "a", 3)
        _make_files(tmp_path / "a" / "b", 2)

        assert count_files(tmp_path) == 5

    def test_empty_directory(self, tmp_path: Path) -> None:
        assert count_files(tmp_path) == 0

    def test_ignores_subdirectories_in_count(self, tmp_path: Path) -> None:
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file.txt").write_text("hi")

        assert count_files(tmp_path) == 1


# ===================================================================
# verify_skills_installed
# ===================================================================


class TestVerifySkillsInstalled:
    def test_verified_skills_returned(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        skills_dir = tmp_path / "skills"

        # Legacy directory with two skills
        _make_skill(bmad / "mymodule", "skill-a")
        _make_skill(bmad / "mymodule", "skill-b")

        # Installed copies
        (skills_dir / "skill-a").mkdir(parents=True)
        (skills_dir / "skill-b").mkdir(parents=True)

        result = verify_skills_installed(
            str(bmad), ["mymodule"], str(skills_dir)
        )

        assert result == ["skill-a", "skill-b"]

    def test_missing_skill_causes_exit(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        skills_dir = tmp_path / "skills"

        _make_skill(bmad / "mod", "installed-skill")
        _make_skill(bmad / "mod", "missing-skill")

        # Only install one of them
        (skills_dir / "installed-skill").mkdir(parents=True)

        with pytest.raises(SystemExit) as exc_info:
            verify_skills_installed(
                str(bmad), ["mod"], str(skills_dir)
            )

        assert exc_info.value.code == 1

    def test_dir_without_skills_skipped(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        skills_dir = tmp_path / "skills"

        # _config has no SKILL.md
        config_dir = bmad / "_config"
        config_dir.mkdir(parents=True)
        (config_dir / "settings.json").write_text("{}")

        result = verify_skills_installed(
            str(bmad), ["_config"], str(skills_dir)
        )

        assert result == []

    def test_nonexistent_legacy_dir_skipped(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        bmad.mkdir()
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        result = verify_skills_installed(
            str(bmad), ["nonexistent"], str(skills_dir)
        )

        assert result == []


# ===================================================================
# cleanup_directories
# ===================================================================


class TestCleanupDirectories:
    def test_removes_directories_and_counts_files(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        _make_files(bmad / "mod", 4)

        removed, not_found, total_files = cleanup_directories(
            str(bmad), ["mod"]
        )

        assert removed == ["mod"]
        assert not_found == []
        assert total_files == 4
        assert not (bmad / "mod").exists()

    def test_nonexistent_dir_is_idempotent(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        bmad.mkdir()

        removed, not_found, total_files = cleanup_directories(
            str(bmad), ["does-not-exist"]
        )

        assert removed == []
        assert not_found == ["does-not-exist"]
        assert total_files == 0

    def test_file_instead_of_dir_skipped(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        bmad.mkdir()
        (bmad / "not-a-dir").write_text("I am a file")

        removed, not_found, total_files = cleanup_directories(
            str(bmad), ["not-a-dir"]
        )

        assert removed == []
        assert "not-a-dir" in not_found
        assert total_files == 0
        # The file should still exist — it was skipped, not deleted
        assert (bmad / "not-a-dir").is_file()

    def test_multiple_dirs_mixed(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        _make_files(bmad / "exists", 2)
        _make_files(bmad / "also-exists", 3)

        removed, not_found, total_files = cleanup_directories(
            str(bmad), ["exists", "ghost", "also-exists"]
        )

        assert removed == ["exists", "also-exists"]
        assert not_found == ["ghost"]
        assert total_files == 5


# ===================================================================
# CLI integration (subprocess)
# ===================================================================


class TestCLIIntegration:
    def _run_script(self, *extra_args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_SCRIPT_PATH), *extra_args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_basic_removal_json_output(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        _make_files(bmad / "mymod", 2)
        _make_files(bmad / "core", 1)

        proc = self._run_script(
            "--bmad-dir", str(bmad),
            "--module-code", "mymod",
        )

        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["status"] == "success"
        assert "mymod" in data["directories_removed"]
        assert "core" in data["directories_removed"]
        assert data["files_removed_count"] == 3
        assert not (bmad / "mymod").exists()
        assert not (bmad / "core").exists()

    def test_also_remove_adds_extra_dirs(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        _make_files(bmad / "mymod", 1)
        _make_files(bmad / "core", 1)
        _make_files(bmad / "_config", 2)

        proc = self._run_script(
            "--bmad-dir", str(bmad),
            "--module-code", "mymod",
            "--also-remove", "_config",
        )

        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert "_config" in data["directories_removed"]
        assert data["files_removed_count"] == 4
        assert not (bmad / "_config").exists()

    def test_skills_dir_verification_blocks_when_missing(
        self, tmp_path: Path
    ) -> None:
        bmad = tmp_path / "bmad"
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        _make_skill(bmad / "mymod", "some-skill")

        proc = self._run_script(
            "--bmad-dir", str(bmad),
            "--module-code", "mymod",
            "--skills-dir", str(skills_dir),
        )

        assert proc.returncode == 1
        data = json.loads(proc.stdout)
        assert data["status"] == "error"
        assert "some-skill" in data["missing_skills"]
        # Directory should NOT have been removed
        assert (bmad / "mymod").exists()

    def test_skills_dir_verification_passes(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        skills_dir = tmp_path / "skills"

        _make_skill(bmad / "mymod", "real-skill")
        (skills_dir / "real-skill").mkdir(parents=True)

        # core has no SKILL.md — should be removed without complaint
        _make_files(bmad / "core", 1)

        proc = self._run_script(
            "--bmad-dir", str(bmad),
            "--module-code", "mymod",
            "--skills-dir", str(skills_dir),
        )

        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["status"] == "success"
        assert data["safety_checks"]["skills_verified"] is True
        assert "real-skill" in data["safety_checks"]["verified_skills"]
        assert not (bmad / "mymod").exists()
        assert not (bmad / "core").exists()

    def test_nothing_to_remove(self, tmp_path: Path) -> None:
        bmad = tmp_path / "bmad"
        bmad.mkdir()

        proc = self._run_script(
            "--bmad-dir", str(bmad),
            "--module-code", "mymod",
        )

        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["status"] == "success"
        assert data["directories_removed"] == []
        assert data["files_removed_count"] == 0
