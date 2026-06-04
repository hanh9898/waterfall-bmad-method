# Deferred Work

Findings surfaced incidentally during review but out of scope for the current story.

## From spec-hbc-shared-validation-lib (Đợt 0) review — 2026-06-02

- **JP templates will now fail section checks** — `templates/D-02_要件定義書_template.md`, `D-03_用語集_*`, and worktree copies still use Japanese-only headings. After dropping JP recognition, documents generated from them fail every `SECTION_MISSING` check. → Belongs to **Đợt 1 / E-1** (strip Japanese from BMad templates the skills emit). Until then, consider a friendly aggregate error when ZERO required sections are found (e.g. "no required sections found — document language may not be supported; regenerate from the current template") instead of a silent six-error cascade.
- **find_section substring breadth** — a label is matched as a substring within a level-1/2 heading. Deep subsections are now excluded, but two same-level headings sharing a token (e.g. "Scope" vs a hypothetical "Out of Scope" at `##`) could still collide. Low risk with current templates; revisit if a real collision appears (consider word-boundary or trimmed-title matching).

## E-1 follow-up (2026-06-04)
- Root `templates/` dir chứa 31 file template JP nguyên bản BMad (D-00..D-31). KHÔNG được skill HBC nào tham chiếu (các skill dùng `assets/` riêng, đã de-JP). Cleanup/đổi tên 31 file này là tùy chọn, không ảnh hưởng chức năng — tách thành task riêng nếu muốn bộ template gốc cũng thuần Việt/Anh.
