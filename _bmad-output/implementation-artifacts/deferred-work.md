# Deferred Work

Findings surfaced incidentally during review but out of scope for the current story.

## From spec-hbc-shared-validation-lib (Đợt 0) review — 2026-06-02

- **JP templates will now fail section checks** — `templates/D-02_要件定義書_template.md`, `D-03_用語集_*`, and worktree copies still use Japanese-only headings. After dropping JP recognition, documents generated from them fail every `SECTION_MISSING` check. → Belongs to **Đợt 1 / E-1** (strip Japanese from BMad templates the skills emit). Until then, consider a friendly aggregate error when ZERO required sections are found (e.g. "no required sections found — document language may not be supported; regenerate from the current template") instead of a silent six-error cascade.
- **find_section substring breadth** — a label is matched as a substring within a level-1/2 heading. Deep subsections are now excluded, but two same-level headings sharing a token (e.g. "Scope" vs a hypothetical "Out of Scope" at `##`) could still collide. Low risk with current templates; revisit if a real collision appears (consider word-boundary or trimmed-title matching).

## E-1 follow-up (2026-06-04)
- Root `templates/` dir chứa 31 file template JP nguyên bản BMad (D-00..D-31). KHÔNG được skill HBC nào tham chiếu (các skill dùng `assets/` riêng, đã de-JP). Cleanup/đổi tên 31 file này là tùy chọn, không ảnh hưởng chức năng — tách thành task riêng nếu muốn bộ template gốc cũng thuần Việt/Anh.

## Deferred from: code review of HBC refactor (2026-06-04)
- **F4** `hbc_validation.find_section` — khi 2 heading cùng cấp đều chứa nhãn, lấy cái đầu. Rủi ro thấp với template hiện tại (nhãn section duy nhất). Cân nhắc anchor chặt hơn nếu xảy ra va chạm thật.
- **F5** `evaluate-gate-checklist._expand_matches` — thư mục match nhưng không có .md → FAIL với message "No files matching" khó hiểu. Thêm evidence rõ "dir tồn tại nhưng rỗng .md".
- **F6** `parse_table` — hàng toàn dấu gạch giữa bảng bị coi là separator lần 2 (im lặng gộp rows sau). Thường đúng ý; document hành vi.
- **F8** `validate-mermaid._render_check` — timeout 60s/block × N block → có thể treo lâu khi nhiều block + có mmdc. Thêm tổng-ngân-sách wall-clock.
- **test-spec d02 prescan** — `validate-test-spec` quét REQ toàn file D-02 cho coverage% (pre-existing, không thuộc diff này). Cùng class prose-leak; cân nhắc scope theo bảng functional sau.

## Deferred from: code re-review of fixes (2026-06-05) — low-risk residual edges
- **F1 residual** `parse_table` — nếu HAI bảng nằm SÁT nhau không có dòng prose/heading/blank ở giữa, header bảng thứ 2 lọt vào data. Không xảy ra với template (sub-table luôn cách nhau bởi `###` + dòng trống). Guarantee thực tế: "các block cách nhau bởi dòng non-pipe".
- **F7 residual** `functional_req_ids` — `.match` neo đầu ô, nên ô bắt đầu bằng REQ-id rồi nối prose ("REQ-001 must precede") vẫn được tính. Đúng ý cho cột ID; chỉ sai nếu một ô KHÔNG-phải-ID lại mở đầu bằng REQ-id (hiếm).
