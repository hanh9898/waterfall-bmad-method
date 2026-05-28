#!/usr/bin/env python3
"""Tests for extract-entity-candidates.py."""

import json
import subprocess
import sys
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

SCRIPT = str(Path(__file__).resolve().parent.parent / "extract-entity-candidates.py")

_spec = spec_from_file_location(
    "extract_entity_candidates",
    SCRIPT,
)
assert _spec is not None and _spec.loader is not None
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

_extract_from_text = mod._extract_from_text
_is_valid = mod._is_valid
_walk_md = mod._walk_md


def _run(sources: list[str], output: str) -> dict:
    cmd = [sys.executable, SCRIPT] + sources + ["-o", output]
    subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(Path(output).read_text(encoding="utf-8"))


class TestIsValid:
    def test_short_names_accepted(self):
        assert _is_valid("a")
        assert _is_valid("ID")
        assert _is_valid("Users")

    def test_stop_word_short_accepted(self):
        assert _is_valid("data")

    def test_stop_word_long_rejected(self):
        assert not _is_valid("database")
        assert not _is_valid("application")

    def test_normal_name_accepted(self):
        assert _is_valid("OrderItem")
        assert _is_valid("Products")


class TestExtractFromText:
    def test_explicit_entity_marker(self):
        text = "Entity: Users\nEntity: Orders"
        entities, _, _ = _extract_from_text(text, "test.md")
        names = [e["entity_name"] for e in entities]
        assert "Users" in names
        assert "Orders" in names
        assert all(e["method"] == "explicit_marker" for e in entities)

    def test_japanese_entity_marker(self):
        text = "テーブル: Products"
        entities, _, _ = _extract_from_text(text, "test.md")
        assert any(e["entity_name"] == "Products" for e in entities)

    def test_data_object_reference(self):
        text = "The Customer entity stores user data."
        entities, _, _ = _extract_from_text(text, "test.md")
        assert any(e["entity_name"] == "Customer" for e in entities)

    def test_d20_table_header(self):
        text = "## テーブル: Employees\n\nColumn definitions..."
        entities, _, _ = _extract_from_text(text, "test.md")
        assert any(e["entity_name"] == "Employees" for e in entities)

    def test_orm_model(self):
        text = "class Product(Base):\n    pass"
        entities, _, _ = _extract_from_text(text, "test.md")
        assert any(e["entity_name"] == "Product" for e in entities)

    def test_attribute_extraction(self):
        text = "- `user_name`: string\n- `age`: integer"
        _, attrs, _ = _extract_from_text(text, "test.md")
        attr_names = [a["attribute_name"] for a in attrs]
        assert "user_name" in attr_names
        assert "age" in attr_names

    def test_relationship_extraction(self):
        text = "Users has many Orders"
        _, _, rels = _extract_from_text(text, "test.md")
        assert len(rels) >= 1
        assert rels[0]["from_entity"] == "Users"
        assert rels[0]["to_entity"] == "Orders"

    def test_arrow_relationship(self):
        text = "Customer → Invoice"
        _, _, rels = _extract_from_text(text, "test.md")
        assert any(r["from_entity"] == "Customer" and r["to_entity"] == "Invoice" for r in rels)

    def test_dedup_by_name(self):
        text = "Entity: Users\nThe Users entity stores data.\nTable: users"
        entities, _, _ = _extract_from_text(text, "test.md")
        user_entities = [e for e in entities if e["entity_name"].lower() == "users"]
        assert len(user_entities) == 1

    def test_line_numbers_tracked(self):
        text = "line1\nEntity: Orders\nline3"
        entities, _, _ = _extract_from_text(text, "test.md")
        order = next(e for e in entities if e["entity_name"] == "Orders")
        assert order["line"] == 2

    def test_stop_words_filtered(self):
        text = "The database entity handles requests."
        entities, _, _ = _extract_from_text(text, "test.md")
        names = [e["entity_name"].lower() for e in entities]
        assert "database" not in names

    def test_empty_text(self):
        entities, attrs, rels = _extract_from_text("", "test.md")
        assert entities == []
        assert attrs == []
        assert rels == []


class TestWalkMd:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "doc.md").write_text("content")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "nested.md").write_text("content")
        result = _walk_md(tmp_path)
        assert len(result) == 2

    def test_excludes_archive_dirs(self, tmp_path):
        (tmp_path / "archive").mkdir()
        (tmp_path / "archive" / "old.md").write_text("content")
        (tmp_path / "current.md").write_text("content")
        result = _walk_md(tmp_path)
        assert len(result) == 1
        assert result[0].name == "current.md"

    def test_excludes_node_modules(self, tmp_path):
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "pkg.md").write_text("content")
        result = _walk_md(tmp_path)
        assert len(result) == 0


class TestCLIIntegration:
    def test_single_file_input(self, tmp_path):
        src = tmp_path / "prd.md"
        src.write_text("Entity: Users\nEntity: Products\n", encoding="utf-8")
        out = str(tmp_path / "result.json")
        result = _run([str(src)], out)
        assert result["totals"]["entities"] == 2
        assert result["warn"] is None
        assert len(result["files_read"]) == 1

    def test_directory_input(self, tmp_path):
        (tmp_path / "doc1.md").write_text("Entity: Orders\n", encoding="utf-8")
        (tmp_path / "doc2.md").write_text("Entity: Payments\n", encoding="utf-8")
        out = str(tmp_path / "result.json")
        result = _run([str(tmp_path)], out)
        assert result["totals"]["entities"] == 2
        assert result["totals"]["files"] == 2

    def test_empty_extraction_warns(self, tmp_path):
        src = tmp_path / "empty.md"
        src.write_text("No entities here.\n", encoding="utf-8")
        out = str(tmp_path / "result.json")
        result = _run([str(src)], out)
        assert result["totals"]["entities"] == 0
        assert result["warn"] == "entity_extraction_empty"

    def test_nonexistent_source_skipped(self, tmp_path):
        src = tmp_path / "exists.md"
        src.write_text("Entity: Users\n", encoding="utf-8")
        out = str(tmp_path / "result.json")
        result = _run([str(src), str(tmp_path / "nonexistent.md")], out)
        assert result["totals"]["entities"] == 1
        assert len(result["files_read"]) == 1

    def test_cross_file_dedup(self, tmp_path):
        (tmp_path / "a.md").write_text("Entity: Users\n", encoding="utf-8")
        (tmp_path / "b.md").write_text("Entity: users\n", encoding="utf-8")
        out = str(tmp_path / "result.json")
        result = _run([str(tmp_path)], out)
        assert result["totals"]["entities"] == 1

    def test_attributes_and_relations(self, tmp_path):
        src = tmp_path / "doc.md"
        src.write_text(
            "Entity: Users\n- `name`: string\nUsers has many Orders\n",
            encoding="utf-8",
        )
        out = str(tmp_path / "result.json")
        result = _run([str(src)], out)
        assert result["totals"]["attributes"] >= 1
        assert result["totals"]["relations"] >= 1
