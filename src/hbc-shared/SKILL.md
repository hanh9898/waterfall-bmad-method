---
name: hbc-shared
description: "Internal shared validation library for HBC skills (hbc_validation). Not user-invocable — imported by the create/validate skills via a sys.path bootstrap; ships so those scripts resolve `hbc_validation` at runtime."
---

# HBC Shared Library

Internal, non-invocable support component for the HBLAB BMad Custom module. It is
**not** a workflow or agent — it carries `lib/hbc_validation.py`, the single source
of truth for table parsing, language-aware section detection, the honest verdict
shape (S-3), and TC-block parsing helpers used by the create/validate skills.

Validator scripts import it via:
`sys.path.insert(0, Path(__file__).resolve().parents[2] / "hbc-shared" / "lib")`

so this folder must install alongside the other skills at `.claude/skills/hbc-shared/`.
It has no menu code and no `module-help.csv` capability row.
