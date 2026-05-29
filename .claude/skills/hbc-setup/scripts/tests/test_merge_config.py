"""Unit tests for merge-config.py functions."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the module from a filename that contains a hyphen
# ---------------------------------------------------------------------------
_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "merge-config.py"

try:
    import yaml as _yaml  # noqa: F401 — just verify availability
except ImportError:
    pytest.skip("pyyaml is required for these tests", allow_module_level=True)

_spec = importlib.util.spec_from_file_location("merge_config", _SCRIPT_PATH)
assert _spec and _spec.loader
merge_config_mod = importlib.util.module_from_spec(_spec)

# Prevent the module-level `parse_args()` / `sys.exit()` from interfering.
# The module only calls them inside `if __name__ == "__main__"`, so plain
# exec_module is safe here.
_spec.loader.exec_module(merge_config_mod)

# Convenience aliases
load_yaml_file = merge_config_mod.load_yaml_file
merge_config = merge_config_mod.merge_config
extract_user_settings = merge_config_mod.extract_user_settings
apply_legacy_defaults = merge_config_mod.apply_legacy_defaults
apply_result_templates = merge_config_mod.apply_result_templates
extract_module_metadata = merge_config_mod.extract_module_metadata
cleanup_legacy_configs = merge_config_mod.cleanup_legacy_configs


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture()
def minimal_module_yaml():
    """A minimal module.yaml dict."""
    return {
        "code": "test-mod",
        "name": "Test Module",
        "description": "A test module",
        "module_version": "1.0.0",
        "output_folder": {
            "prompt": "Where?",
            "default": "output",
        },
        "secret_key": {
            "prompt": "Secret?",
            "user_setting": True,
        },
    }


@pytest.fixture()
def minimal_answers():
    """Minimal answers dict with core + module sections."""
    return {
        "core": {
            "user_name": "Alice",
            "communication_language": "en",
            "output_folder": "my-output",
        },
        "module": {
            "output_folder": "docs",
            "secret_key": "s3cret",
        },
    }


# ===================================================================
# load_yaml_file
# ===================================================================

class TestLoadYamlFile:
    def test_nonexistent_file_returns_empty_dict(self, tmp_path: Path):
        result = load_yaml_file(str(tmp_path / "nope.yaml"))
        assert result == {}

    def test_valid_yaml_returns_dict(self, tmp_path: Path):
        p = tmp_path / "cfg.yaml"
        p.write_text("foo: bar\ncount: 42\n", encoding="utf-8")
        result = load_yaml_file(str(p))
        assert result == {"foo": "bar", "count": 42}

    def test_empty_yaml_returns_empty_dict(self, tmp_path: Path):
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        result = load_yaml_file(str(p))
        assert result == {}

    def test_yaml_with_only_comments_returns_empty_dict(self, tmp_path: Path):
        p = tmp_path / "comments.yaml"
        p.write_text("# just a comment\n", encoding="utf-8")
        result = load_yaml_file(str(p))
        assert result == {}


# ===================================================================
# merge_config — core values, module section, anti-zombie, user-key stripping
# ===================================================================

class TestMergeConfig:
    def test_core_values_at_root(self, minimal_module_yaml, minimal_answers):
        """Core answers (except user-only keys) appear at root level."""
        result = merge_config({}, minimal_module_yaml, minimal_answers)
        # output_folder is a core key that is NOT user-only, so it lives at root
        assert result.get("output_folder") == "my-output"

    def test_module_section_created(self, minimal_module_yaml, minimal_answers):
        """Module answers appear under a section keyed by module code."""
        result = merge_config({}, minimal_module_yaml, minimal_answers)
        assert "test-mod" in result
        assert result["test-mod"]["output_folder"] == "docs"

    def test_anti_zombie_removes_old_module_section(
        self, minimal_module_yaml, minimal_answers
    ):
        """Existing module section is replaced, not merged."""
        existing = {"test-mod": {"stale_key": "old_value"}}
        result = merge_config(existing, minimal_module_yaml, minimal_answers)
        assert "stale_key" not in result["test-mod"]

    def test_core_user_keys_stripped_from_config(
        self, minimal_module_yaml, minimal_answers
    ):
        """user_name and communication_language must NOT appear in config.yaml."""
        existing = {"user_name": "OldUser", "communication_language": "de"}
        result = merge_config(existing, minimal_module_yaml, minimal_answers)
        assert "user_name" not in result
        assert "communication_language" not in result

    def test_other_module_sections_preserved(
        self, minimal_module_yaml, minimal_answers
    ):
        """Merging one module must not remove sections from other modules."""
        existing = {"other-mod": {"key": "val"}}
        result = merge_config(existing, minimal_module_yaml, minimal_answers)
        assert result["other-mod"] == {"key": "val"}

    def test_module_code_required(self):
        """Missing 'code' in module_yaml causes sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            merge_config({}, {"name": "No Code"}, {"core": {}, "module": {}})
        assert exc_info.value.code == 1

    def test_legacy_core_section_migrated(self, minimal_module_yaml, minimal_answers):
        """A legacy 'core' dict in existing config is migrated to root."""
        existing = {"core": {"output_folder": "legacy-out"}}
        result = merge_config(existing, minimal_module_yaml, minimal_answers)
        # The core section should be gone; output_folder from answers overwrites
        assert "core" not in result or not isinstance(result.get("core"), dict)


# ===================================================================
# extract_user_settings
# ===================================================================

class TestExtractUserSettings:
    def test_picks_user_name_and_language(self, minimal_module_yaml, minimal_answers):
        result = extract_user_settings(minimal_module_yaml, minimal_answers)
        assert result["user_name"] == "Alice"
        assert result["communication_language"] == "en"

    def test_picks_user_setting_true_from_module(
        self, minimal_module_yaml, minimal_answers
    ):
        result = extract_user_settings(minimal_module_yaml, minimal_answers)
        assert result["secret_key"] == "s3cret"

    def test_ignores_module_vars_without_user_setting(
        self, minimal_module_yaml, minimal_answers
    ):
        result = extract_user_settings(minimal_module_yaml, minimal_answers)
        # output_folder does NOT have user_setting: true
        assert "output_folder" not in result

    def test_empty_answers_returns_empty(self, minimal_module_yaml):
        result = extract_user_settings(minimal_module_yaml, {"core": {}, "module": {}})
        assert result == {}


# ===================================================================
# apply_legacy_defaults
# ===================================================================

class TestApplyLegacyDefaults:
    def test_legacy_fills_missing_core_keys(self):
        answers = {"core": {"user_name": "Alice"}}
        legacy_core = {"user_name": "OldAlice", "output_folder": "legacy-out"}
        result = apply_legacy_defaults(answers, legacy_core, {})
        # Existing answer wins
        assert result["core"]["user_name"] == "Alice"
        # Legacy fills the gap
        assert result["core"]["output_folder"] == "legacy-out"

    def test_answers_override_legacy(self):
        answers = {"module": {"key1": "new"}}
        legacy_module = {"key1": "old", "key2": "only-legacy"}
        result = apply_legacy_defaults(answers, {}, legacy_module)
        assert result["module"]["key1"] == "new"
        assert result["module"]["key2"] == "only-legacy"

    def test_no_legacy_returns_unchanged(self):
        answers = {"core": {"user_name": "A"}}
        result = apply_legacy_defaults(answers, {}, {})
        assert result == answers

    def test_both_core_and_module_legacy(self):
        answers: dict = {}
        result = apply_legacy_defaults(
            answers,
            {"user_name": "Legacy"},
            {"var1": "val1"},
        )
        assert result["core"]["user_name"] == "Legacy"
        assert result["module"]["var1"] == "val1"


# ===================================================================
# apply_result_templates
# ===================================================================

class TestApplyResultTemplates:
    def test_template_applied(self):
        module_yaml = {
            "my_path": {
                "prompt": "Path?",
                "result": "{project-root}/{value}",
            },
        }
        result = apply_result_templates(module_yaml, {"my_path": "docs"})
        assert result["my_path"] == "{project-root}/docs"

    def test_no_double_prefix(self):
        """If the value already contains {project-root}, skip the template."""
        module_yaml = {
            "my_path": {
                "prompt": "Path?",
                "result": "{project-root}/{value}",
            },
        }
        result = apply_result_templates(
            module_yaml, {"my_path": "{project-root}/already"}
        )
        assert result["my_path"] == "{project-root}/already"

    def test_no_template_passthrough(self):
        module_yaml = {
            "plain": {"prompt": "Name?"},
        }
        result = apply_result_templates(module_yaml, {"plain": "hello"})
        assert result["plain"] == "hello"

    def test_unknown_key_passthrough(self):
        result = apply_result_templates({}, {"unknown": "val"})
        assert result["unknown"] == "val"


# ===================================================================
# extract_module_metadata
# ===================================================================

class TestExtractModuleMetadata:
    def test_picks_name_description_version(self):
        mod = {
            "code": "abc",
            "name": "ABC Module",
            "description": "Does stuff",
            "module_version": "2.0.0",
        }
        meta = extract_module_metadata(mod)
        assert meta["name"] == "ABC Module"
        assert meta["description"] == "Does stuff"
        assert meta["version"] == "2.0.0"

    def test_missing_version_gives_none(self):
        meta = extract_module_metadata({"code": "x", "name": "X"})
        assert meta["version"] is None

    def test_default_selected_included_when_present(self):
        meta = extract_module_metadata(
            {"code": "x", "name": "X", "default_selected": True}
        )
        assert meta["default_selected"] is True

    def test_default_selected_absent_when_not_in_yaml(self):
        meta = extract_module_metadata({"code": "x", "name": "X"})
        assert "default_selected" not in meta


# ===================================================================
# cleanup_legacy_configs
# ===================================================================

class TestCleanupLegacyConfigs:
    def test_deletes_correct_files(self, tmp_path: Path):
        mod_dir = tmp_path / "my-mod"
        mod_dir.mkdir()
        mod_cfg = mod_dir / "config.yaml"
        mod_cfg.write_text("key: val\n")

        core_dir = tmp_path / "core"
        core_dir.mkdir()
        core_cfg = core_dir / "config.yaml"
        core_cfg.write_text("user_name: Bob\n")

        deleted = cleanup_legacy_configs(str(tmp_path), "my-mod")
        assert str(mod_cfg) in deleted
        assert str(core_cfg) in deleted
        assert not mod_cfg.exists()
        assert not core_cfg.exists()

    def test_returns_empty_when_no_files(self, tmp_path: Path):
        deleted = cleanup_legacy_configs(str(tmp_path), "my-mod")
        assert deleted == []

    def test_other_module_dirs_untouched(self, tmp_path: Path):
        other_dir = tmp_path / "other-mod"
        other_dir.mkdir()
        other_cfg = other_dir / "config.yaml"
        other_cfg.write_text("keep: me\n")

        cleanup_legacy_configs(str(tmp_path), "my-mod")
        assert other_cfg.exists()


# ===================================================================
# CLI integration (subprocess)
# ===================================================================

class TestCLIIntegration:
    def _write_module_yaml(self, path: Path) -> Path:
        import yaml

        data = {
            "code": "cli-mod",
            "name": "CLI Module",
            "description": "For CLI test",
            "module_version": "0.1.0",
            "some_var": {"prompt": "Value?", "default": "x"},
        }
        p = path / "module.yaml"
        p.write_text(yaml.dump(data), encoding="utf-8")
        return p

    def _write_answers(self, path: Path) -> Path:
        data = {
            "core": {
                "user_name": "TestUser",
                "communication_language": "ja",
                "output_folder": "out",
            },
            "module": {"some_var": "hello"},
        }
        p = path / "answers.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_cli_creates_config_files(self, tmp_path: Path):
        mod_yaml = self._write_module_yaml(tmp_path)
        answers = self._write_answers(tmp_path)
        config_path = tmp_path / "_bmad" / "config.yaml"
        user_config_path = tmp_path / "_bmad" / "config.user.yaml"

        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT_PATH),
                "--config-path",
                str(config_path),
                "--module-yaml",
                str(mod_yaml),
                "--answers",
                str(answers),
                "--user-config-path",
                str(user_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Verify JSON output
        output = json.loads(result.stdout)
        assert output["status"] == "success"
        assert output["module_code"] == "cli-mod"

        # Verify config.yaml was created
        assert config_path.exists()
        import yaml

        cfg = yaml.safe_load(config_path.read_text())
        assert "cli-mod" in cfg
        assert cfg["cli-mod"]["some_var"] == "hello"
        # output_folder should be at root
        assert cfg.get("output_folder") == "out"
        # user-only keys must NOT be in config.yaml
        assert "user_name" not in cfg
        assert "communication_language" not in cfg

        # Verify config.user.yaml was created
        assert user_config_path.exists()
        user_cfg = yaml.safe_load(user_config_path.read_text())
        assert user_cfg["user_name"] == "TestUser"
        assert user_cfg["communication_language"] == "ja"

    def test_cli_missing_module_yaml_fails(self, tmp_path: Path):
        answers = self._write_answers(tmp_path)
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT_PATH),
                "--config-path",
                str(tmp_path / "cfg.yaml"),
                "--module-yaml",
                str(tmp_path / "nonexistent.yaml"),
                "--answers",
                str(answers),
                "--user-config-path",
                str(tmp_path / "user.yaml"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1

    def test_cli_with_legacy_dir(self, tmp_path: Path):
        import yaml

        mod_yaml = self._write_module_yaml(tmp_path)
        answers_data = {
            "core": {"output_folder": "new-out"},
            "module": {},
        }
        answers_path = tmp_path / "answers.json"
        answers_path.write_text(json.dumps(answers_data), encoding="utf-8")

        # Create legacy files
        legacy_dir = tmp_path / "legacy"
        core_legacy = legacy_dir / "core"
        core_legacy.mkdir(parents=True)
        (core_legacy / "config.yaml").write_text(
            yaml.dump({"user_name": "LegacyUser", "communication_language": "de"})
        )
        mod_legacy = legacy_dir / "cli-mod"
        mod_legacy.mkdir(parents=True)
        (mod_legacy / "config.yaml").write_text(
            yaml.dump({"some_var": "legacy-val"})
        )

        config_path = tmp_path / "_bmad" / "config.yaml"
        user_config_path = tmp_path / "_bmad" / "config.user.yaml"

        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT_PATH),
                "--config-path",
                str(config_path),
                "--module-yaml",
                str(mod_yaml),
                "--answers",
                str(answers_path),
                "--user-config-path",
                str(user_config_path),
                "--legacy-dir",
                str(legacy_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        output = json.loads(result.stdout)
        assert output["status"] == "success"
        # Legacy files should have been deleted
        assert len(output["legacy_configs_deleted"]) == 2
        assert not (core_legacy / "config.yaml").exists()
        assert not (mod_legacy / "config.yaml").exists()

        # Legacy values serve as fallback
        cfg = yaml.safe_load(config_path.read_text())
        assert cfg["cli-mod"]["some_var"] == "legacy-val"

        user_cfg = yaml.safe_load(user_config_path.read_text())
        assert user_cfg["user_name"] == "LegacyUser"
        assert user_cfg["communication_language"] == "de"
