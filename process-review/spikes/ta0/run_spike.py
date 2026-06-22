#!/usr/bin/env python
"""TA.0 spike runner — run the build-graph kernel on BOTH corpora and print JSON.

Usage:  python process-review/spikes/ta0/run_spike.py

Output shape:
  {
    "broken": {"caught": [...4 error names...], "count": N, "detail": {...}},
    "clean":  {"false_positives": [...], "count": M, "detail": {...}}
  }

GO bar (per hbc-implementation-plan §5 TA.0):
  broken count >= 4  AND  clean count == 0  AND  clean corpus non-empty  -> GO
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "kernel"))

from buildgraph import run_graph  # noqa: E402
from loader import load_corpus    # noqa: E402

REPO_ROOT = HERE.parents[2]  # .../stc-erp-bmad-custom
BROKEN = REPO_ROOT / "process-review" / "fixtures" / "resource-plan-billable"
CLEAN = HERE / "corpus-clean"

EXPECTED_BROKEN = {
    "gate-STALE",
    "matrix-missing-reqs",
    "model-drift",
    "taskbreakdown-missing-slices",
}


def _caught_names(result: dict) -> list[str]:
    return [c["error"] for c in result["caught"]]


def _normalize_error_name(name: str) -> str:
    # detector internal name -> bar name
    return {"gate-STALE": "gate-STALE"}.get(name, name)


# Dir names that are artifact-CATEGORIES inside a single feature, not features.
_CATEGORY_DIRS = {"artifacts", "code", "planning", "planning-artifacts",
                  "traceability", "implementation", "implementation-artifacts", "gates"}


def _feature_dirs(root: Path) -> list[Path]:
    """A corpus may hold ONE feature (the fixture: root has category subdirs like
    artifacts/ + code/) or MANY (the clean corpus: one named subdir per feature).

    A feature subdir = an immediate child that (a) is NOT an artifact-category dir
    and (b) has a D-02 somewhere beneath it. If none qualify, the root itself is
    the single feature (the fixture case, where code/ and artifacts/ are siblings
    that together form ONE feature)."""
    children = [p for p in sorted(root.iterdir()) if p.is_dir()]
    feat = [
        c for c in children
        if c.name.lower() not in _CATEGORY_DIRS and any(c.rglob("D-02*.md"))
    ]
    return feat if feat else [root]


def run_on(root: Path, label: str) -> dict:
    if not root.exists():
        return {"error": f"{label} corpus path missing: {root}", "features": [],
                "artifact_files": 0, "result": {"caught": []}}
    features = _feature_dirs(root)
    per_feature = []
    all_caught = []
    total_artifacts = 0
    for fd in features:
        artifacts = (
            list(fd.rglob("D-0*.md"))
            + list(fd.rglob("matrix.md"))
            + list(fd.rglob("task-breakdown.md"))
            + list(fd.rglob("*gate*.md"))
        )
        total_artifacts += len(artifacts)
        g = load_corpus(fd)
        res = run_graph(g)
        per_feature.append({
            "feature": fd.name,
            "nodes": sorted(g.nodes),
            "caught": res["caught"],
            "dirty_set": res["dirty_set"],
            "stale_edges": res["stale_edges"],
        })
        for c in res["caught"]:
            all_caught.append({"feature": fd.name, **c})
    return {
        "features": [f.name for f in features],
        "artifact_files": total_artifacts,
        "per_feature": per_feature,
        "result": {"caught": all_caught},
    }


def main() -> int:
    broken = run_on(BROKEN, "broken")
    clean = run_on(CLEAN, "clean")

    broken_caught = _caught_names(broken["result"])
    clean_caught_full = broken_caught  # placeholder (overwritten below)
    clean_caught = [c["error"] for c in clean["result"]["caught"]]

    # A clean-corpus catch is a FALSE POSITIVE.
    out = {
        "broken": {
            "caught": broken_caught,
            "count": len(broken_caught),
            "expected": sorted(EXPECTED_BROKEN),
            "all_4_caught": EXPECTED_BROKEN.issubset(set(broken_caught)),
            "detail": broken["result"]["caught"],
            "per_feature": broken["per_feature"],
        },
        "clean": {
            "false_positives": [
                {"feature": c["feature"], "error": c["error"]} for c in clean["result"]["caught"]
            ],
            "count": len(clean_caught),
            "features": clean.get("features", []),
            "corpus_artifact_files": clean.get("artifact_files", 0),
            "corpus_non_empty": clean.get("artifact_files", 0) > 0,
            "corpus_multi_feature": len(clean.get("features", [])) >= 2,
            "per_feature": clean.get("per_feature", []),
        },
    }

    go = (
        out["broken"]["count"] >= 4
        and out["broken"]["all_4_caught"]
        and out["clean"]["count"] == 0
        and out["clean"]["corpus_non_empty"]
    )
    out["verdict"] = "GO" if go else "NO-GO"

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
