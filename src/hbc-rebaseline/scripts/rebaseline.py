#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""HBC cross-feature re-baseline engine (TA.7) — blast-radius via graph rollup.

WHAT THIS IS
============
When a SHARED / core model changes after Phase 3 (e.g. shared D-19, shared D-12, or
a core Odoo model like ``project.project`` that several features build on), every
in-flight feature that derives from it becomes potentially STALE. This engine answers
the one machine question that gate-by-gate, per-feature tooling cannot: *which
features, and which artifacts inside them, are in the BLAST RADIUS of this shared
change?* — then routes a re-baseline PLAN per affected feature.

It is a SEPARATE engine from ``hbc-migrate`` (B14-6). Migrate is a one-time
layout/D-code upgrade WITHIN the per-feature shape; rebaseline is the CROSS-feature
ripple of a shared-model change ABOVE the feature level. They share discipline
(dry-run plan → confirm → apply, idempotent) but no code.

THE EPIC / BASELINE-CHANGE LEVEL (A6)
=====================================
A shared change is a unit-of-work that spans features — it is NOT a per-feature task.
This engine introduces an explicit **baseline-change** record (an "epic" above the
feature in the layout): one ``baseline-change/<id>/`` envelope holding the changed
shared node, the computed blast-radius, and one re-baseline plan row per affected
feature. The layout level is data the engine emits, not just a concept:

    _bmad-output/baseline-change/<change-id>/
        rebaseline-plan.json     # this engine's --json, frozen at plan time
        .decision-log.md         # appended on apply

BLAST-RADIUS ALGORITHM (the L·needs-design core)
================================================
1. Load every feature dir into a per-feature ``BuildGraph`` via the TA.1 kernel
   (``load_corpus`` / ``feature_dirs``). The kernel owns graph/hash/dirty/drift; this
   engine only adds the CROSS-feature rollup the kernel deliberately deferred.
2. Extract each feature's referenced **model tokens** (the shared surface) from its
   ground-truth code node + its D-19 design node: Odoo ``_name='x.y'`` declarations
   and relation targets (``Many2one/Many2many/One2many('x.y', ...)``), plus D-19
   physical names. This is structure-only regex (model NAMES, never meaning).
3. A node is SHARED if (a) the caller names it as the changed shared node, or (b) it
   is referenced by >= 2 features (a core model nobody feature owns alone). The
   ``--changed`` token is authoritative; the >=2 heuristic only *suggests* shared
   candidates when the caller does not name one.
4. BLAST-RADIUS of the changed shared node = every feature whose code/design
   references that token. For each such feature we ROLL UP the downstream artifacts
   that go stale: the design node that names it, then (transitively, via the kernel's
   own ``dirty_set`` edge model) matrix → task-breakdown → gate, plus a drift flag
   when the feature's code references the shared token (its model surface moved).
   A feature that does NOT reference the token is NOT in the radius (no false flag).

The verdict for each affected feature is ``rebaseline`` (downstream artifacts to
re-derive). The reconcile VERDICT ladder (machine-floor + semantic-ceiling) is TA.2;
the gate RECYCLE state-machine is TA.3 — both deliberately out of scope here. This
engine MODELS the radius + plan; it never auto-edits a feature's artifacts.

DRY-RUN → APPLY
===============
Default is a non-destructive PLAN (writes nothing). ``--apply`` writes the
baseline-change envelope (plan JSON + decision-log) and marks each affected feature's
gate as ``REBASELINE-PENDING`` is left to the human/skill — the engine records intent,
it does not silently re-open gates. Idempotent: an already-recorded baseline-change id
with an unchanged plan is detected and skipped (never written twice).

stdlib-only; importable; run with ``python`` (Windows dev) / ``python3`` (CI). The
``--json`` shape is the single source of truth for ``references/headless-contract.md``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- shared kernel bootstrap (parents[2] → hbc-shared/lib) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_buildgraph import BuildGraph, load_corpus, feature_dirs  # noqa: E402
except Exception as exc:  # pragma: no cover - import wiring
    print(json.dumps({"error": f"cannot import hbc_buildgraph: {exc}"}), file=sys.stderr)
    raise SystemExit(2)

# Odoo model name (dotted, lowercase): `_name = 'resource.plan'`
_NAME_RE = re.compile(r"_name\s*=\s*['\"]([a-z][\w.]+)['\"]")
# Relation targets: Many2one('project.project', ...) / One2many / Many2many
_REL_RE = re.compile(r"(?:Many2one|One2many|Many2many)\s*\(\s*['\"]([a-z][\w.]+)['\"]")
# D-19 physical name line: **... (Physical name)**: `resource.plan`
_PHYS_RE = re.compile(r"`([a-z][\w.]+)`")
# A dotted model token (used to validate a --changed arg looks like a model name).
_MODEL_TOKEN_RE = re.compile(r"^[a-z][\w.]+$")

# The downstream artifact nodes a stale design ripples into, in dependency order.
# Used to roll up which artifacts inside an affected feature go stale.
_DOWNSTREAM_ORDER = ["D-19", "matrix", "task-breakdown", "gate"]


def model_tokens(g: BuildGraph) -> set[str]:
    """The set of model NAMES a feature's graph references — its shared surface.

    Pulled from the ground-truth ``code`` node (Odoo ``_name`` + relation targets)
    and the ``D-19`` design node (physical names). Structure-only (names, not
    meaning). None-safe: a missing node contributes nothing.
    """
    toks: set[str] = set()
    code = g.get("code")
    if code is not None and code.text:
        toks |= set(_NAME_RE.findall(code.text))
        toks |= set(_REL_RE.findall(code.text))
    d19 = g.get("D-19")
    if d19 is not None and d19.text:
        # Only dotted names (x.y) — single bare words in prose are not model names.
        toks |= {t for t in _PHYS_RE.findall(d19.text) if "." in t}
    return toks


def owned_tokens(g: BuildGraph) -> set[str]:
    """Model names a feature DECLARES (its own ``_name=``) — what it owns, not merely
    references. Used to attribute a shared token to the feature(s) that define it."""
    code = g.get("code")
    return set(_NAME_RE.findall(code.text)) if (code is not None and code.text) else set()


@dataclass
class FeatureGraph:
    """One feature's build-graph plus its derived model surface."""

    name: str
    graph: BuildGraph
    tokens: set[str] = field(default_factory=set)
    owned: set[str] = field(default_factory=set)

    def references(self, token: str) -> bool:
        return token in self.tokens

    def present_downstream(self) -> list[str]:
        """Downstream artifact node-ids actually present in this feature's graph,
        in dependency order — the rollup set when a shared upstream changes."""
        return [nid for nid in _DOWNSTREAM_ORDER if self.graph.get(nid) is not None]


class CrossFeatureGraph:
    """The set of per-feature build-graphs, with a cross-feature shared-model view.

    This is the level ABOVE the kernel's single-feature ``BuildGraph``: it does not
    re-implement dirty/hash/drift (the kernel owns those) — it adds the rollup that
    answers "a shared node moved; who is downstream of it, across features?".
    """

    def __init__(self, features: list[FeatureGraph]) -> None:
        self.features = sorted(features, key=lambda f: f.name)

    @classmethod
    def from_root(cls, root: Path) -> "CrossFeatureGraph":
        feats: list[FeatureGraph] = []
        for fdir in feature_dirs(root):
            g = load_corpus(fdir)
            feats.append(FeatureGraph(name=fdir.name, graph=g,
                                      tokens=model_tokens(g), owned=owned_tokens(g)))
        return cls(feats)

    def shared_tokens(self) -> dict[str, list[str]]:
        """Model tokens referenced by >= 2 features → {token: [feature names]}.

        A core/shared model that no single feature owns alone. Sorted, deterministic.
        Used to SUGGEST shared candidates when the caller does not name ``--changed``.
        """
        ref: dict[str, list[str]] = {}
        for f in self.features:
            for t in f.tokens:
                ref.setdefault(t, []).append(f.name)
        return {t: sorted(fs) for t, fs in sorted(ref.items()) if len(fs) >= 2}

    def owners(self, token: str) -> list[str]:
        return sorted(f.name for f in self.features if token in f.owned)

    def blast_radius(self, changed: str) -> list[dict]:
        """Features in the blast radius of a change to model ``changed``.

        For each feature that REFERENCES ``changed`` (and is not the sole owner with
        no downstream — handled by including it regardless, since its own design must
        re-baseline too), roll up the downstream artifact nodes that go stale plus a
        ``code_drift`` flag when the feature's CODE references the shared token (its
        model surface moved with the change). Features that do not reference the token
        are excluded → no false positive. Deterministic ordering.
        """
        out: list[dict] = []
        for f in self.features:
            if not f.references(changed):
                continue
            code = f.graph.get("code")
            code_refs = bool(code is not None and code.text and (
                re.search(r"['\"]" + re.escape(changed) + r"['\"]", code.text)))
            out.append({
                "feature": f.name,
                "owns_changed": changed in f.owned,
                "stale_artifacts": f.present_downstream(),
                "code_references_changed": code_refs,
                "verdict": "rebaseline",
            })
        return sorted(out, key=lambda e: e["feature"])

    def plan(self, changed: str, change_id: str) -> dict:
        """A full re-baseline PLAN for a shared-model change (the dry-run object).

        ``changed`` is the shared model token; ``change_id`` names the baseline-change
        epic (the unit-of-change above feature). Returns the engine's ``--json`` shape.
        """
        radius = self.blast_radius(changed)
        return {
            "change_id": change_id,
            "changed_node": changed,
            "owners": self.owners(changed),
            "shared_candidates": self.shared_tokens(),
            "blast_radius": radius,
            "affected_features": [r["feature"] for r in radius],
            "applied": False,
            "warnings": _plan_warnings(changed, radius, self.shared_tokens()),
        }


def _plan_warnings(changed: str, radius: list[dict], shared: dict[str, list[str]]) -> list[str]:
    w: list[str] = []
    if not _MODEL_TOKEN_RE.match(changed):
        w.append(f"changed_node_not_model_token:{changed}")
    if not radius:
        w.append("empty_blast_radius")
    if changed not in shared and len(radius) < 2:
        # Caller named a token only one feature touches — not actually cross-feature.
        w.append("not_cross_feature_shared")
    return w


# ===========================================================================
# APPLY — write the baseline-change envelope (the epic level on disk).
# ===========================================================================


def _envelope_dir(out_root: Path, change_id: str) -> Path:
    return Path(out_root) / "baseline-change" / change_id


def apply_plan(out_root: Path, plan: dict) -> dict:
    """Write the baseline-change envelope: plan JSON + decision-log. IDEMPOTENT — an
    existing envelope whose recorded plan matches (same changed_node + same affected
    features) is detected and SKIPPED (never written twice). Returns the plan with
    ``applied`` set and ``envelope`` / ``skipped`` recorded.
    """
    env = _envelope_dir(out_root, plan["change_id"])
    plan_path = env / "rebaseline-plan.json"
    log_path = env / ".decision-log.md"

    if plan_path.is_file():
        try:
            prior = json.loads(plan_path.read_text(encoding="utf-8"))
        except Exception:
            prior = {}
        same = (prior.get("changed_node") == plan["changed_node"]
                and prior.get("affected_features") == plan["affected_features"])
        if same:
            result = dict(plan)
            result.update(applied=True, skipped=True, envelope=str(env))
            return result

    env.mkdir(parents=True, exist_ok=True)
    applied = dict(plan)
    applied["applied"] = True
    plan_path.write_text(json.dumps(applied, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [f"# Baseline-change {plan['change_id']}", "",
             f"- changed_node: `{plan['changed_node']}`",
             f"- owners: {', '.join(plan['owners']) or '(none)'}",
             f"- affected_features ({len(plan['affected_features'])}): "
             f"{', '.join(plan['affected_features']) or '(none)'}", ""]
    for r in plan["blast_radius"]:
        lines.append(f"  - {r['feature']}: re-baseline {', '.join(r['stale_artifacts']) or '(no downstream)'}"
                     f"{' [code surface moved]' if r['code_references_changed'] else ''}")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    applied.update(skipped=False, envelope=str(env))
    return applied


# ===========================================================================
# CLI
# ===========================================================================


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Cross-feature re-baseline blast-radius engine (TA.7).")
    ap.add_argument("--root", required=True,
                    help="Output root holding feature dirs (e.g. _bmad-output/features).")
    ap.add_argument("--changed",
                    help="The shared model token that changed (e.g. project.project). "
                         "If omitted, the engine reports shared candidates only.")
    ap.add_argument("--change-id", default="baseline-change",
                    help="Id for the baseline-change epic (unit-of-change above feature).")
    ap.add_argument("--apply", action="store_true",
                    help="Write the baseline-change envelope. Absent ⇒ dry-run (default).")
    ap.add_argument("--out-root",
                    help="Where to write the baseline-change envelope on --apply "
                         "(default: parent of --root).")
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(json.dumps({"error": f"root not found: {root}"}), file=sys.stderr)
        return 2

    cfg = CrossFeatureGraph.from_root(root)
    # A real corpus has at least one feature carrying a D-02. The kernel's feature_dirs
    # falls back to [root] when nothing qualifies, so guard on D-02 presence to reject
    # an empty/non-corpus root rather than report a degenerate single feature.
    if not cfg.features or not any(f.graph.get("D-02") is not None for f in cfg.features):
        print(json.dumps({"error": f"no feature with a D-02 found under {root}"}), file=sys.stderr)
        return 2

    if not args.changed:
        # Discovery mode: report shared candidates, no plan.
        out = {
            "root": str(root),
            "features": [f.name for f in cfg.features],
            "shared_candidates": cfg.shared_tokens(),
            "hint": "pass --changed <model.token> to compute a blast-radius plan",
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    plan = cfg.plan(args.changed, args.change_id)
    if args.apply:
        out_root = Path(args.out_root) if args.out_root else root.parent
        plan = apply_plan(out_root, plan)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
