#!/usr/bin/env python3
"""Check relative Markdown links AND #anchors in the docs tree and READMEs.

Dependency-free (stdlib only). Scans *.md under docs/ plus README.md and
README.vi.md, extracts inline links [text](target), and verifies:
  1. every relative target file exists;
  2. every #anchor (cross-file or in-page) matches a heading in the target file.

External links (http/https, mailto) are skipped. Anchor slugs are computed with
a GitHub-compatible slugger (lowercase; keep letters/digits incl. Unicode; drop
punctuation/emoji; each whitespace char -> '-'; duplicates get -1, -2 suffixes).

Usage:
    python _bmad/scripts/check_doc_links.py [project_root]

Exit code 0 if all links + anchors resolve, 1 otherwise (CI-friendly).
"""

import os
import re
import sys

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
SKIP_PREFIXES = ("http://", "https://", "mailto:")

_slug_cache = {}


def slugify(text):
    """Approximate GitHub's heading-to-anchor algorithm."""
    out = []
    for ch in text.strip().lower():
        if ch.isalnum():
            out.append(ch)
        elif ch.isspace() or ch == "-":
            out.append("-")
        # everything else (punctuation, backticks, emoji, em-dash) is dropped
    return "".join(out)


def heading_slugs(path):
    """Return the set of anchor slugs a Markdown file exposes."""
    if path in _slug_cache:
        return _slug_cache[path]
    slugs = set()
    counts = {}
    in_fence = False
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                m = HEADING_RE.match(line)
                if not m:
                    continue
                base = slugify(m.group(2))
                if not base:
                    continue
                if base not in counts:
                    counts[base] = 0
                    slugs.add(base)
                else:
                    counts[base] += 1
                    slugs.add("{}-{}".format(base, counts[base]))
    except OSError:
        pass
    _slug_cache[path] = slugs
    return slugs


def collect_md_files(root):
    targets = []
    docs_dir = os.path.join(root, "docs")
    for base, _dirs, files in os.walk(docs_dir):
        for name in files:
            if name.endswith(".md"):
                targets.append(os.path.join(base, name))
    for readme in ("README.md", "README.en.md"):
        path = os.path.join(root, readme)
        if os.path.isfile(path):
            targets.append(path)
    return targets


def check_file(path):
    broken = []
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    src_dir = os.path.dirname(path)
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or target.startswith(SKIP_PREFIXES):
            continue
        file_part, _, anchor = target.partition("#")
        if not file_part:
            # in-page anchor: validate against this file's headings
            if anchor and anchor not in heading_slugs(path):
                broken.append((target, "anchor not found in this file"))
            continue
        resolved = os.path.normpath(os.path.join(src_dir, file_part))
        if not os.path.exists(resolved):
            broken.append((target, "file missing: " + os.path.relpath(resolved)))
            continue
        if anchor and resolved.endswith(".md"):
            if anchor not in heading_slugs(resolved):
                broken.append((target, "anchor not found in target"))
    return broken


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    files = collect_md_files(root)
    total_broken = 0
    for path in sorted(files):
        broken = check_file(path)
        if broken:
            print("BROKEN in {}:".format(os.path.relpath(path, root)))
            for target, reason in broken:
                print("  -> {}  ({})".format(target, reason))
            total_broken += len(broken)
    if total_broken:
        print("\nFAIL: {} broken link(s)/anchor(s) across {} file(s).".format(total_broken, len(files)))
        return 1
    print("OK: all relative links + anchors resolve across {} file(s).".format(len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
