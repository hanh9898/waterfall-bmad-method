#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-21 API Specification document.

Checks endpoint completeness, REQ-xxx traceability to D-02,
entity consistency with D-19, and returns structured JSON.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("概要", "Overview"),
    ("認証", "Authentication"),
    ("共通仕様", "Common Specifications"),
    ("エンドポイント一覧", "Endpoint List"),
    ("エンドポイント詳細", "Endpoint Details"),
    ("データモデル", "Data Models"),
]

ENDPOINT_TABLE_RE = re.compile(
    r"\|\s*\d+\s*\|\s*(\w+)\s*\|\s*([^\|]+)\|\s*([^\|]+)\|\s*([^\|]*)\|"
)

REQ_ID_RE = re.compile(r"REQ-(\d{3,})")

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def _section_has_content(text: str) -> bool:
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


def check_sections(content: str) -> list[dict]:
    issues: list[dict] = []

    for ja_name, en_name in REQUIRED_SECTIONS:
        pattern_ja = re.compile(rf"#+\s.*{re.escape(ja_name)}.*", re.IGNORECASE)
        pattern_en = re.compile(rf"#+\s.*{re.escape(en_name)}.*", re.IGNORECASE)
        match = pattern_ja.search(content) or pattern_en.search(content)
        if not match:
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{ja_name}' / '{en_name}' not found",
                "section": ja_name,
                "auto_fixable": False,
            })
            continue

        heading_level = len(match.group().split()[0])
        start = match.end()
        same_level_pattern = re.compile(r"\n#{1," + str(heading_level) + r"}\s")
        next_heading = same_level_pattern.search(content[start:])
        section_body = (
            content[start : start + next_heading.start()]
            if next_heading
            else content[start:]
        )

        stripped = re.sub(r"<!--.*?-->", "", section_body, flags=re.DOTALL)
        if not _section_has_content(stripped):
            issues.append({
                "type": "SECTION_EMPTY",
                "message": f"Section '{ja_name}' exists but has no content",
                "section": ja_name,
                "auto_fixable": False,
            })

    return issues


def check_endpoints(content: str) -> list[dict]:
    issues: list[dict] = []

    rows = ENDPOINT_TABLE_RE.findall(content)
    if not rows:
        issues.append({
            "type": "NO_ENDPOINTS",
            "message": "No endpoints found in endpoint list table",
            "auto_fixable": False,
        })
        return issues

    seen_urls: dict[str, str] = {}
    for method, url, _desc, req_ids in rows:
        method_clean = method.strip().upper()
        url_clean = url.strip()
        key = f"{method_clean} {url_clean}"

        if method_clean not in HTTP_METHODS:
            issues.append({
                "type": "INVALID_METHOD",
                "message": f"Invalid HTTP method '{method_clean}' for {url_clean}",
                "endpoint": key,
                "auto_fixable": False,
            })

        if key in seen_urls:
            issues.append({
                "type": "DUPLICATE_ENDPOINT",
                "message": f"Duplicate endpoint: {key}",
                "endpoint": key,
                "auto_fixable": True,
            })
        seen_urls[key] = url_clean

        req_refs = REQ_ID_RE.findall(req_ids)
        if not req_refs:
            issues.append({
                "type": "NO_REQ_REFERENCE",
                "message": f"Endpoint {key} has no REQ-xxx reference",
                "endpoint": key,
                "auto_fixable": False,
            })

    return issues


def check_req_traceability(content: str, d02_path: str | None) -> list[dict]:
    issues: list[dict] = []

    if not d02_path:
        return issues

    try:
        d02_content = Path(d02_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return issues

    d02_req_ids = set(REQ_ID_RE.findall(d02_content))
    d21_req_ids = set(REQ_ID_RE.findall(content))

    orphans = d21_req_ids - d02_req_ids
    for req_num in sorted(orphans):
        issues.append({
            "type": "ORPHAN_REQ",
            "message": f"REQ-{req_num} referenced in D-21 but not found in D-02",
            "req_id": f"REQ-{req_num}",
            "auto_fixable": False,
        })

    return issues


def check_entity_consistency(content: str, d19_path: str | None) -> list[dict]:
    issues: list[dict] = []

    if not d19_path:
        return issues

    try:
        d19_content = Path(d19_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return issues

    entity_re = re.compile(r"```mermaid.*?erDiagram(.*?)```", re.DOTALL)
    er_match = entity_re.search(d19_content)
    if not er_match:
        return issues

    entity_names = set(
        re.findall(r"^\s*(\w+)\s*\{", er_match.group(1), re.MULTILINE)
    )
    if not entity_names:
        return issues

    model_section = re.search(
        r"#+\s.*(?:データモデル|Data Models)(.*?)(?=\n##\s|\Z)",
        content, re.DOTALL | re.IGNORECASE,
    )
    if not model_section:
        return issues

    model_names = set(
        re.findall(r"###\s+\d+\.\d+\s+(\w+)", model_section.group(1))
    )

    for model in model_names:
        close_match = any(
            model.lower() in e.lower() or e.lower() in model.lower()
            for e in entity_names
        )
        if not close_match and model.lower() not in {e.lower() for e in entity_names}:
            issues.append({
                "type": "ENTITY_MISMATCH",
                "message": f"Data model '{model}' in D-21 has no matching entity in D-19",
                "model": model,
                "auto_fixable": False,
            })

    return issues


def validate(
    doc_path: str,
    d02_path: str | None = None,
    d19_path: str | None = None,
) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_endpoints(content))
    all_issues.extend(check_req_traceability(content, d02_path))
    all_issues.extend(check_entity_consistency(content, d19_path))

    auto_fixable = [i for i in all_issues if i.get("auto_fixable")]
    manual_fix = [i for i in all_issues if not i.get("auto_fixable")]

    endpoint_rows = ENDPOINT_TABLE_RE.findall(content)

    return {
        "valid": len(all_issues) == 0,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "endpoint_count": len(endpoint_rows),
        "issues": all_issues,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate D-21 API Specification."
    )
    parser.add_argument("document", help="Path to D-21 API spec document")
    parser.add_argument("--d02", help="Path to D-02 requirements (for traceability)")
    parser.add_argument("--d19", help="Path to D-19 database design (for entity check)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        error = {
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-api-spec' first to generate D-21.",
        }
        print(json.dumps(error, indent=2, ensure_ascii=False))
        sys.exit(1)

    result = validate(str(doc_path), args.d02, args.d19)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
