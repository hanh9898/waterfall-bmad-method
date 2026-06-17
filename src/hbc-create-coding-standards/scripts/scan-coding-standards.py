#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan for existing D-12 coding standards and detect project framework."""

import argparse
import glob
import json
import os
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---", re.DOTALL
)
FIELD_RE = re.compile(r"^(\w+)\s*:\s*(.+)$", re.MULTILINE)

FRAMEWORK_KEYWORDS: dict[str, list[str]] = {
    "odoo": ["odoo", "openerp", "_inherit", "ir.model", "@api.model"],
    "django": ["django", "wsgi", "asgi", "manage.py", "settings.py"],
    "nextjs": ["next.js", "nextjs", "next.config", "app router", "pages router"],
    "react": ["react", "jsx", "tsx", "create-react-app", "vite"],
    "laravel": ["laravel", "artisan", "eloquent", "blade"],
    "spring": ["spring boot", "spring", "maven", "gradle", "@RestController"],
    "flask": ["flask", "werkzeug", "jinja2"],
    "fastapi": ["fastapi", "uvicorn", "pydantic"],
    "vue": ["vue", "vuex", "pinia", "nuxt"],
    "angular": ["angular", "@angular", "ng serve"],
}


def read_frontmatter(filepath: str) -> dict[str, str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(4096)
    except (OSError, UnicodeDecodeError):
        return {}

    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}

    fields = {}
    for m in FIELD_RE.finditer(match.group(1)):
        fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fields


def detect_framework(project_context_path: str | None) -> str | None:
    if not project_context_path or not os.path.isfile(project_context_path):
        return None

    try:
        with open(project_context_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
    except (OSError, UnicodeDecodeError):
        return None

    scores: dict[str, int] = {}
    for framework, keywords in FRAMEWORK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in content)
        if score > 0:
            scores[framework] = score

    if not scores:
        return None

    return max(scores, key=lambda k: scores[k])


def find_project_context(project_root: str) -> str | None:
    patterns = [
        os.path.join(project_root, "project-context.md"),
        os.path.join(project_root, "_bmad", "project-context.md"),
        os.path.join(project_root, "**", "project-context.md"),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
    return None


def scan_project_knowledge(project_knowledge: str | None) -> list[dict]:
    """Enumerate bmad-document-project output for brownfield convention ingestion.

    Returns the document-project index plus its sibling project docs so D-12
    derives from the REAL codebase conventions, not just project-context.md.
    Greenfield (dir absent / empty) → []."""
    if not project_knowledge:
        return []
    root = project_knowledge
    if not os.path.isdir(root):
        return []

    docs: list[dict] = []
    seen: set[str] = set()
    index_path = os.path.join(root, "index.md")
    if os.path.isfile(index_path):
        seen.add(os.path.normpath(index_path))
        docs.append({"path": index_path, "name": "index.md", "role": "index"})

    for path in sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True)):
        norm = os.path.normpath(path)
        if norm in seen or not os.path.isfile(path):
            continue
        seen.add(norm)
        docs.append({"path": path, "name": os.path.basename(path)})
    return docs


def scan(project_root: str, output_dir: str, project_knowledge: str | None = None) -> dict:
    d12_matches = glob.glob(os.path.join(output_dir, "D-12*"))

    existing_d12 = None
    state = "fresh"

    if d12_matches:
        filepath = d12_matches[0]
        fm = read_frontmatter(filepath)
        last_step = fm.get("lastStep", "")

        if last_step == "complete":
            state = "update"
        elif last_step:
            state = "resume"
        else:
            state = "resume"

        existing_d12 = {
            "path": filepath,
            "file": os.path.basename(filepath),
            "frontmatter": fm,
        }

    project_context_path = find_project_context(project_root)
    framework = detect_framework(project_context_path)

    project_knowledge_docs = scan_project_knowledge(project_knowledge)

    return {
        "state": state,
        "existing_d12": existing_d12,
        "framework": framework,
        "project_context_path": project_context_path,
        "output_dir": output_dir,
        "project_knowledge_docs": project_knowledge_docs,
        "project_knowledge_count": len(project_knowledge_docs),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scan for existing D-12 and detect framework."
    )
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory to scan for D-12"
    )
    parser.add_argument(
        "--project-knowledge",
        help="bmad-document-project output dir (brownfield code conventions); "
        "typically {project-root}/docs. Greenfield: omit or point at a missing dir.",
    )
    parser.add_argument("-o", "--output", help="Write JSON to file instead of stdout")
    args = parser.parse_args()

    result = scan(args.project_root, args.output_dir, args.project_knowledge)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
