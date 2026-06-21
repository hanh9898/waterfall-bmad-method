# D-27 Review Stages — Adversarial (B3-9) + Semantic (B3-8 / T2.12)

Run both BEFORE saving (Stage 4 → here → Stage 5). Feed all findings back into
Stage 3 / 3a, then finalize.

## Stage 4a: Adversarial + edge-case review (B3-9, before P2-gate)

Run two independent review lenses over the TCs:
- `bmad-review-adversarial-general` — find false-greens, over-claimed coverage,
  assertions that pass vacuously.
- `bmad-review-edge-case-hunter` — walk every boundary/branch for unhandled cases.

**Availability-check + fallback.** These ship with bmm/core. If a consumer hasn't
installed them, **fall back** to applying both lenses inline (as in the parallel-lens
menu) and record _"ran inline"_ in the decision log. Never hard-block on their
absence. The Phase-2 gate wants evidence both reviews ran — inline counts.

## Stage 4b: Semantic Review (Layer 2)

Structural validation + the facet metric only prove **structure + declared facets**.
Run the **semantic review** per the shared rubric
(`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an
**independent skeptic lens** — challenge each REQ:

- Do the TCs **meaningfully** exercise it, or only the happy path?
- Apply the **facet-split discipline** (read/write · api/admin/ui/batch · lifecycle):
  for every applicable facet ask whether a TC exercises it (not merely "≥1 TC
  exists") and whether **edge / negative** paths are covered.
- A facet cut from REST/admin must still be tested or **explicitly marked
  out-of-scope with an owner** — don't let a facet be implied but unowned.
- Each TC's **technique↔source** pairing sound (B3-5)? Severity proposals ratified
  by the user for critical-path TCs (B3-6)?

**Supporting automated check (M-1).** Declare each TC's `**Facets:**` and each REQ's
Coverage-Matrix `Facets` column, then run:
```
python3 {skill-root}/scripts/check-facet-coverage.py --d27 "<D-27>" [--d02 "<D-02>"]
```
`facet_covered: false` ⇒ list `uncovered_facets` in `openFacets` and keep
`status: pending`. The metric checks only **declared** facets — your judgment decides
whether the declared set is COMPLETE and the TCs behind it meaningful (edge/negative),
not just present. A vacuous green (zero declared facets) means nothing was measured —
confirm whether facets should be declared.

**Record the outcome** in the D-27 frontmatter — `status: passed` **only when
`openFacets` is empty AND the user signs off** (you reviewed depth: facets + edge +
negative); else `pending` with the gaps listed (headless: Autonomy mode):

```yaml
semanticReview:
  status: passed        # passed only when openFacets empty + user sign-off
  reviewedBy: llm
  date: "{date}"
  openFacets: []        # e.g. ["REQ-013 admin/write facet has no TC", "REQ-007 no negative-path TC"]
```

The Phase 2 gate REVIEW item (#5) reads this status. Headless: if any facet/REQ
remains open, set `status: pending`, list `openFacets`, return `blocked`.
