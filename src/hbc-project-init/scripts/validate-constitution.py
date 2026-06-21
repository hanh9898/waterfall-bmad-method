#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Structural validator for the Phase-0 constitution.md (T3.13a).

Layer 1 (structure only): the five invariant principles are present and
non-empty, no `[NEEDS CLARIFICATION]` marker remains, and the semantic-review
frontmatter is readable. Meaning ("is test-first actually right for this
project?") is the LLM semantic-review layer's job — out of scope here.

Imports the shared primitives via the standard parents[2] bootstrap. Prints JSON
to stdout; errors to stderr + non-zero exit.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
from hbc_validation import (  # noqa: E402
    check_required_sections,
    semantic_review_status,
    verdict,
    SEMANTIC_PASSED,
    SEMANTIC_PENDING,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# The five cross-phase invariants. English canonical label + (optional) configured
# label per the language policy — never hardcode a third language here. Section
# headings are numbered ("## 1. Test-First …") so substring match on the keyword
# is enough and language-robust for the principle names that stay English.
REQUIRED_PRINCIPLES = [
    ("Test-First", "Test-First"),
    ("Language Policy", "Language Policy"),
    ("Separation of Duties", "Separation of Duties"),
    ("Handoff Through Artifact", "Handoff Through Artifact"),
    ("Simplicity Caps", "Simplicity Caps"),
]

CLARIFICATION_MARKER = "[NEEDS CLARIFICATION"


def validate(path: str, lang_label: str | None = None) -> dict:
    text = Path(path).read_text(encoding="utf-8")

    # Build (english, configured-language) section tuples for find_section.
    sections = []
    for en, _ in REQUIRED_PRINCIPLES:
        sections.append((en, lang_label or en))

    issues = check_required_sections(text, sections, empty_check=True)

    # No unresolved [NEEDS CLARIFICATION] markers (the convention).
    clarifications = text.count(CLARIFICATION_MARKER)
    if clarifications:
        issues.append({
            "section": "clarification-markers",
            "problem": f"{clarifications} unresolved {CLARIFICATION_MARKER}] marker(s)",
            "auto_fixable": False,
        })

    sr = semantic_review_status(text)
    structure_ok = not issues

    # Semantic state carried into the honest verdict: a present-and-passed review
    # → passed; otherwise pending (the LLM layer still owes the review).
    semantic = SEMANTIC_PASSED if sr["passed"] else SEMANTIC_PENDING

    v = verdict(
        structure_ok,
        semantic_review=semantic,
        checked=["required-principles", "clarification-markers", "semantic-review-frontmatter"],
        not_checked=["principle-meaning", "project-fit"],
    )
    return {
        "path": path,
        "issues": issues,
        "clarification_markers": clarifications,
        "semantic_review": sr,
        "verdict": v,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate Phase-0 constitution.md")
    parser.add_argument("path", help="Path to constitution.md")
    parser.add_argument("--lang-label",
                        help="Configured-language label for the principle headings "
                             "(document_output_language); English-only if omitted")
    parser.add_argument("-o", "--output", help="Write JSON to file instead of stdout")
    args = parser.parse_args()

    if not Path(args.path).is_file():
        print(json.dumps({"error": "file_not_found", "path": args.path}), file=sys.stderr)
        sys.exit(2)

    try:
        result = validate(args.path, args.lang_label)
    except OSError as e:
        print(json.dumps({"error": "read_error", "detail": str(e)}), file=sys.stderr)
        sys.exit(2)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        import os
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
