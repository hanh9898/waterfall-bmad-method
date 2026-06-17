# HBC Semantic Review Rubric (Layer 1 — shared contract)

> Core principle: **the machine handles structure · the human/LLM handles semantics & completeness.**
> The validator (`hbc_validation`) has already checked structure and returns a `verdict` with
> an initial `semantic_review` = `n/a`/`pending`. The SEMANTIC review step below is the part
> the human/LLM must perform, shared by every create-skill (A-2, C-2).

## When to run

After the structural validator is green (`structure_ok = true`), the create-skill runs the
**Semantic Review** step before marking the document complete. This is Layer 2 (embedded
in each skill). The result is written into the frontmatter (A-3) and checked by the
phase-gate REVIEW item (#5).

## Facet-splitting discipline (A-2)

A single REQ/function usually has **multiple facets**. Don't stop at "has ≥1 test/mention".
For each requirement, scan the facet matrix and ask "which facet applies, and has that facet
been covered?":

| Axis | Values | Question |
|---|---|---|
| Action | `read` / `write` | Is there both reading and writing/state mutation? Is each facet specified/tested? |
| Surface | `api` / `admin` / `ui` / `batch` | Is the logic exposed via REST? Via an admin/back-office screen? A background job? Does each surface have an owner? |
| Lifecycle | `create` / `update` / `suspend` / `revoke` / `rotate` | For resources with a lifecycle (key, account, subscription), is each state transition covered? |

The axes are extensible — add an axis if the domain needs it. **Seam lesson:** when D-21 carves the
admin/write facet out of REST, that facet must still have an owner in D-26/D-27 (test) or be
explicitly recorded as intentional out-of-scope — never let it drop silently.

## Output: frontmatter `semanticReview` (A-3)

```yaml
semanticReview:
  status: passed          # pending (default, not reviewed) | passed | n/a
  reviewedBy: llm         # llm | human | <name>
  date: "YYYY-MM-DD"
  openFacets: []          # facet/REQ not yet covered; must be EMPTY for status to be passed
```

- `status` may **only** be set to `passed` when `openFacets` is empty and the reviewer has
  actually checked completeness + facets. If still in doubt → leave it `pending` and list `openFacets`.
- `openFacets` example: `["REQ-013 admin/write facet has no TC", "Key approval screen has no test area"]`.
- The phase-gate item of type `REVIEW` reads exactly this `status` and **blocks** if it != `passed`.

## Decision-scope by location

- Semantics **within a single document** → review in place (this skill, using this rubric).
- Consistency **across multiple documents** (D-02 ↔ D-19/D-21/D-26/D-27/tasks) → NOT
  the scope of a single skill; leave it to `hbc-check-implementation-readiness` (inter-doc gate, P-1)
  which runs mandatorily before `hbc-phase-gate` Phase 2.
