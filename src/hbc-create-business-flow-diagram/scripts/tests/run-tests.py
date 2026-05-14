#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Loader for test files whose names contain hyphens.

The scripts-standards lint expects `test_<script-name>.py` to mirror the
script name exactly, so the test files keep their hyphens — but
`python -m unittest discover` can't import hyphenated module names.
This runner uses importlib path-based loading so the tests stay
runnable.

Usage:
    python scripts/tests/run-tests.py        # run all
    python scripts/tests/run-tests.py -v     # verbose
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def load_test_module(path: Path) -> unittest.TestSuite:
    # Path-based import bypasses the dotted-module-name requirement.
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load test file: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return unittest.defaultTestLoader.loadTestsFromModule(module)


def main() -> int:
    tests_dir = Path(__file__).resolve().parent
    suite = unittest.TestSuite()
    for path in sorted(tests_dir.glob("test_*.py")):
        suite.addTests(load_test_module(path))

    verbosity = 2 if "-v" in sys.argv or "--verbose" in sys.argv else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
