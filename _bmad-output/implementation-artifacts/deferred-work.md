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

## Deferred from: code review of P-1/M-1 engines (2026-06-05)
- **W1 test collection** — `test-check-readiness.py` / `test-check-facet-coverage.py` (tên toàn-hyphen) KHÔNG được `pytest <dir>` hay `run-tests.py` (glob `test_*.py`) thu thập; chỉ chạy qua đường-dẫn-file tường minh hoặc `__main__`. Đã xác nhận: `pytest <tests-dir>` → "no tests collected"; chạy explicit → 9 passed. Convention toàn repo (nhiều `test-*.py`), không riêng change này. Rủi ro: sweep tổng báo "0 collected" trông như sạch. Cân nhắc đổi tên `test_*` hoặc thêm config `python_files = test-*.py test_*.py`.
- **W2 REQ regex** — `REQ-\d{3,}` không `IGNORECASE` và đòi ≥3 chữ số: `REQ-1`/`req-001` bị âm thầm loại khỏi tập authoritative (D-02) hoặc khỏi reference (downstream). Format đã được `validate-requirements` enforce ở nơi khác → defer.
- **W3 TC split** — `re.split(r"^###\s+TC-")` không nhận biết code-fence (block ```` ``` ```` chứa `### TC-` tạo block ảo) và bỏ qua `#### TC-` (4 hash). Phụ thuộc kỷ luật template.
- **W4 facet vocabulary** — không validate facet token theo từ vựng chuẩn (read/write/api/admin/ui/batch); typo `wirte` → false gap vĩnh viễn, không cảnh báo.
- **W5 D-02 empty functional table** — section có nhưng bảng rỗng → `defined=∅`. Refine: nếu downstream có REQ → chúng thành orphan → `ready=False` (fail ồn, không xanh-giả); chỉ khi downstream cũng không có REQ mới `ready=True` với `d02_req_count:0`. Rủi ro thực thấp; `d02_req_count:0` là tín hiệu nhưng không gì gate lên nó.

## Deferred from: P-1/M-1 re-review rounds 2-4 (2026-06-05) — contrived header edges (doc-note, not code)
- **W6 facet column resolution** — `check-facet-coverage.py` resolve cột req/facet bằng scoring + data-tiebreak + exclude. Còn 3 edge CONTRIVED (header không template nào sinh ra): (a) header gộp `Facet/REQ` đứng trước cột `Facets` thật → facet resolve nhầm; (b) hai cột synonym chứa REQ-id, cột non-canonical đứng trước, tie 1 row → first wins; (c) matrix đổi tên cột `REQ ID` thành thứ không chứa "req" → source bị skip, facet riêng của matrix rơi → false green. Khuyến nghị: **doc-note "Coverage Matrix phải giữ cột định-danh REQ + cột Facets"** thay vì hardening thêm code (gold-plating). Default-path (template chuẩn) không dính. Verdict re-review: production-ready as structural gate = YES.

## Deferred from: adversarial review of P-1/M-1 (2026-06-05) — design-debatable / cross-cutting
- **A#2 facet false-safety** — `facet_covered:true` khi không REQ nào khai facet (`reqs_with_declared_facets:0`). KHÔNG vá: hợp đồng M-1 đã ký "absent = no facet requirements, backward-compatible"; "tập facet khai có đủ chưa" được delegate cho LLM (gate P2-08 note). Đảo sẽ phá backward-compat + test hiện có.
- **A#3 mention = coverage** — `referenced_reqs` quét toàn file; gate P2-11 coi "nhắc tên REQ" = covered → có thể bị qua mặt bằng cách dán phụ lục REQ. By-design (mention-level structural; adequacy thuộc LLM layer). Bảo đảm yếu cho một gate "required" — cân nhắc nâng lên TC-block-scoped như engine facet ở đợt sau.
- **A#5 test-runner convention (nâng cấp W1)** — tên file test đụng convention chéo: lint đòi `test_<script-name>` mirror (có hyphen) nhưng pytest không import được tên có hyphen; `run-tests.py` là unittest-loader, không bắt test dạng pytest-function. Fix sạch nhất = thêm `pytest.ini` repo-root: `python_files = test_*.py test-*.py` + `--import-mode=importlib` (importlib import được tên có hyphen) → fix W1 cho TẤT CẢ file test all-hyphen toàn repo, không cần đổi tên. Là quyết định cấu hình repo-wide, ngoài phạm vi 2 skill → cần chốt riêng.
- **A#6 matcher bất đối xứng** — `d02_defined_reqs` dùng `.match` neo đầu ô; coverage dùng `.findall`/`.search`. Lệch về phía báo uncovered giả khi ô ID dạng `(REQ-001)`. Pre-existing (F7 residual).
- **A#7 facet vocabulary** — không whitelist; typo facet → gap/miss thầm lặng (trùng W4).
- **A#8 regex REQ-id lặp ≥3 nơi** — `REQ-\d{3,}` nên đưa vào `hbc-shared/lib` để 1 nguồn sự thật (cùng `validate-requirements`).
- **A#10/#11/#13 (LOW)** — test facet dùng `mkdtemp` không cleanup (rò tmp); key `note` của readiness là field có-điều-kiện chưa tài-liệu-hoá/chưa test; `-o` mode để stdout rỗng + exit 0/1 (caller parse stdout nhận rỗng).

## W1 / A#5 test collection — INVESTIGATED, fix retracted (2026-06-05)
- **Đính chính:** tôi từng tưởng một `pytest.ini` repo-root vá được W1. SAI — điều tra cho thấy:
  - Skills nằm RẢI ở `src/` (20 dir) và `.claude/skills/` (71 dir, độc lập); P-1/M-1 CHỈ ở `.claude/skills/`.
  - pytest mặc định bỏ thư mục dot (`norecursedirs=.*`) → root `pytest` KHÔNG bao giờ collect `.claude/` (kể cả khi đổi `python_files`). 512 test "repo-wide" tôi báo trước đó là bản `src/`, KHÔNG phải P-1/M-1.
  - `.claude/worktrees/*` là bản sao full-repo → đưa `.claude` vào recursion sẽ kéo trùng hàng loạt.
  - Bản `testpaths = src .claude/skills` (đủ rộng để gồm P-1/M-1) collect 1131 test nhưng **lộ 2 test fail có sẵn** ở skill khác (`bmad-module-builder`, `hbc-agent-dev/test-scan-impl-state`) → làm CI đỏ vì test không-liên-quan.
  - **Không có CI/Makefile/test-runner nào in-repo** → "vô hình với CI" thực ra moot: chẳng có gì chạy tự động.
- **Đã revert pytest.ini.** P-1/M-1 tests chạy & xanh qua đường-dẫn tường minh (`pytest <test-file>`) và block `__main__` (`pytest.main([__file__])`) — đã verify 30/30 pass.
- **Việc thực sự cần (ops/architecture, ngoài phạm vi review):** (a) thêm CI workflow chạy tường minh các thư mục test của skill, HOẶC (b) thống nhất vị trí skill (src/ vs .claude/skills/), VÀ (c) sửa 2 test đang fail sẵn ở `.claude/skills/` trước khi gộp chúng vào bất kỳ sweep nào.

## RESOLVED (2026-06-05): edge-case-hunter 8 paths — TC parsing hardened
- Đưa helper TC dùng chung vào `hbc-shared/lib/hbc_validation.py`: `strip_code_fences`, `iter_tc_blocks` (split `^#{3,6}\s+TC-`, bỏ fence), `tc_field` (đọc field `**Label:**` qua nhiều dòng, strip comment). Additive — 625 test .claude/skills xanh (1 fail pre-existing bmad-module-builder không liên quan).
- Vá: #1 readiness surface `tc_without_req_id`; #2 `#### TC-`; #3 fence-aware; #4 REQ-id wrap dòng; #5 `check_readiness` trả error-dict thay vì raise (library-safe); #6 facet surface `malformed_tc`; #7 facet `#### TC-`+fence; #8 tie-break per-id. (W3 cũ nay đóng.)
- **Residual #8 (LOW, contrived):** tie-break cột req theo số-id chỉ là best-effort — cột nhiễu chứa NHIỀU id vẫn có thể thắng cột thật. Không có fix tuyệt đối cho header bịa; template chuẩn không dính.

## RESOLVED + deferred from: full 3-layer code review (2026-06-05, post-edge-fixes)
- **RESOLVED C1 (CRITICAL)** `tc_field` — `\s*` sau label nuốt dòng kế khi field rỗng → `**REQ ID:**` rỗng hút `**Trace:** REQ-555` → false-bind + né mọi safety net. Fix: `[ \t]*` (chỉ ws ngang). +test lib & engine.
- **RESOLVED M1/M2 (MED)** `strip_code_fences` — đổi từ regex sang line-scanner: xử lý ```/~~~, indent, info-string; unclosed fence → strip tới EOF (fail-safe, không để TC ảo lọt). +tests.
- **RESOLVED M3 (MED)** `check_readiness` error-path trả full verdict shape (structure_ok/checked_documents/…) → library caller không KeyError. +assert trong test exit-2.
- **RESOLVED (LOW)** `iter_tc_blocks` thêm IGNORECASE (`### tc-` khớp).
- **Deferred (LOW/contrived):** (a) `_req_col` khi 2 cột tie có SỐ-ID BẰNG nhau → first wins (cùng class #8, header bịa, template chuẩn không dính); (b) `**Facets:** , ,` present-nhưng-rỗng-sau-split → không bị flag malformed, ra false-RED (an toàn/ồn, input hiếm); (c) `--output` mode để stdout rỗng (CLI semantics by-design; caller dùng `-o` đọc file, không đọc stdout); (d) heading `####### TC-` (7 hash, vượt giới hạn markdown) / `###TC-` thiếu space → bị bỏ (false-RED, sai convention). Tất cả hướng an-toàn (false-RED hoặc input dị); doc-note thay vì hardening.

## Deferred from: SECOND independent review of P-1/M-1 (2026-06-05) — net-new vs first review
> Chạy song song sau khi engine đã hardening (HEAD 0feda92). Chỉ ghi phần CHƯA có trong các mục review trước. 0 CRITICAL; engine cốt lõi đúng, tests xanh (lib 27 + engine 37).
- **N1 (HIGH)** `check-facet-coverage.py::table_with_header` — early-break `if header or rows: break` chỉ đọc bảng ĐẦU trong section. Coverage Matrix có 2 bảng (cách nhau bởi prose/sub-heading) → bảng 2 bị bỏ → required facets mất → false-green. Cùng class F1 nhưng ở hàm riêng (parse_table đã fix, table_with_header thì chưa). Fix: reset header/rows mỗi block (như logic in_data của parse_table) hoặc quét mọi block pipe trong section.
- **N2 (HIGH)** `check-readiness.py::referenced_reqs` — `REQ_ID_RE.findall(text)` toàn file trên D-26/D-21/matrix KHÔNG strip code-fence → REQ-id trong ví dụ fenced bị tính: (a) false-ORPHAN từ D-21/D-26 example → `ready:false` chặn oan gate; (b) false-coverage che gap thật. Khác A#3 (A#3 chỉ bàn mention=coverage, chưa bàn false-orphan-chặn-gate). Fix: `referenced_reqs(strip_code_fences(text))`.
- **N3 (MED)** `hbc_validation.py::strip_code_fences` — đóng fence so theo KÝ TỰ ĐẦU (`m.group(1)[0] == fence`), không theo độ dài. Một dòng 3-backtick đóng sớm block 4-backtick (````) → `### TC-` giữa hai mốc lọt thành TC thật. Fix: lưu nguyên chuỗi fence mở, đóng khi `char khớp AND len >= len(mở)`.
- **N4 (MED)** `hbc_validation.py::_TC_HEADING_RE` — `^#{3,6}[ \t]+TC-` không khớp heading đánh số `### 3.1 TC-001` → TC bị bỏ đếm (REQ của nó báo uncovered). Template chuẩn không dính; doc/user có thể. Fix: `^#{3,6}[ \t]+(?:[\d.]+\s+)?TC-`.
- **N5 (HIGH-edge/LOW-blind)** `check-readiness.py` — D-02 functional table RỖNG (header+separator, 0 data) + có downstream → `defined=∅` → `ready:true` vacuous, không `note`. (Engine facet có `note` cho ca vacuous; readiness thì không — bất đối xứng.) Fix: khi `len(defined)==0 && gated_any` → thêm `note` cảnh báo hoặc coi là not-ready.
- **N6 (LOW)** `bmad-help.csv` — menu-code `[IR]` của `hbc-check-implementation-readiness` TRÙNG với `bmad-check-implementation-readiness` (cũng IR). Gõ `[IR]` → ambiguous. Fix: đổi code HBC (vd `[RD]`/`[IRH]`).
- **Đồng thuận với review trước (không vá lại):** Gap1/Gap2 "P2-08/P2-11 type QUALITY → PENDING_LLM, không hard-block tất định" = A#3 (by-design; gate required nghĩa LLM PHẢI xử lý output script, không phải script auto-reject). Cân nhắc nâng P2-11/P2-08 thành item chạy-script-tất-định ở đợt sau nếu muốn chặn cứng.

## DONE (2026-06-09): phase-flow hardening — nhóm 3 (B/E/C) + bug A1/A2
Theo quyết định: B=enforced-overridable, E=gate-driven auto-feed, C=chuỗi tuyến tính.
- **B2** engine `evaluate-gate-checklist.py`: thêm `_is_entry_gate` + `entry_gate_failed` trong summary; entry-gate (prior-gate PASSED) KHÔNG bị lenient hạ → overall FAILED bất kể mode. SKILL step 4 cập nhật. +3 test.
- **B1** task-breakdown (P3 entry→check P2 gate) & test-execution (P4 entry→check P3 gate): activation chạy gate headless, HALT nếu !PASSED, chỉ qua khi user override; headless→blocked.
- **B3** P3-00b: re-run IR readiness ở P3 entry (chống stale "P2 PASSED").
- **E** `on_complete = "invoke hbc-traceability update"` (auto-feed matrix khi gate PASSED) + item P2-13 (design_ref+test_ref) & P3-07 (code_ref) → matrix incremental, P4-06 chỉ còn confirm.
- **C1** CSV: `api-spec.followed-by=hbc-create-test-plan` (hết dead-end); `test-plan.preceded-by=hbc-create-api-spec` (hết mis-parent) → chuỗi er→cs→(api)→test-plan→test-spec→IR→gate.
- **A1** sửa tên skill sai trong gate checklist (hbc-task-breakdown, hbc-acceptance-check).
- **A2** toàn bộ checklist path `_bmad-output/` → `{output_folder}/`; SKILL truyền `--var output_folder` + `--var gate_mode`.
- Regression: gate 32, CSV-merge 27, broad .claude/skills 636 pass (1 fail pre-existing bmad-module-builder, không liên quan).

### CHƯA làm (nhóm 1/2 — chưa được chọn):
- A3 (3 validator còn JP: test-plan/test-execution/acceptance-check), D3 (wire check-fr/entity-coverage vào gate P1/P2 — script sẵn), F1 (port validate-test-spec sang iter_tc_blocks/tc_field), D1 (validate-test-execution --d27), D2 (validate-implementation).

## DONE (2026-06-09): nhóm 1 quick-wins (A3 + D3 + F1)
- **A3** Bỏ hardcode tiếng Nhật khỏi 3 validator (validate-test-plan: リスク管理/マイルストーン/リスク; validate-test-execution: 総テスト数/成功/失敗/カバレッジ/不具合トリアージ; validate-acceptance-check: 基準). Giữ EN canonical. 74 test pass.
- **D3** Wire 2 script coverage SẴN CÓ vào gate: P1-06b (check-fr-coverage.py D-06↔PRD FR) + P2-03b (check-entity-coverage.py D-19↔PRD entity), QUALITY đòi passed:true → bắt PRD churn sau khi author.
- **F1** Port `validate-test-spec.py` TC parsing sang shared helper: thêm `_tc_blocks_with_num` (strip_code_fences + `^#{3,6}[ \t]+TC-`, mirror iter_tc_blocks) + `tc_field` cho field-check → D-27 structural check KHÔNG còn lệch readiness/facet trên cùng file (nhận #### TC-, bỏ fenced example, empty REQ ID = missing). +3 test.
- Regression: focused 83 pass; broad .claude/skills 639 pass (1 fail pre-existing bmad-module-builder, không liên quan).

### Còn lại (nhóm 2): D1 (validate-test-execution --d27), D2 (validate-implementation reconcile DONE task↔code/test↔matrix).

## DONE (2026-06-09): nhóm 2 — 2 seam CRITICAL downstream đóng
- **D1** `validate-test-execution.py --d27`: reconcile TC chạy (report) vs TC đặc tả (D-27) qua lib `tc_ids` → TC_UNEXECUTED / TC_PHANTOM_RESULT. Wire gate P4-02 (thay LLM eyeball). +lib helper `tc_ids`. +4 test.
- **D2** `validate-implementation.py` (mới, hbc-implement): DONE task thiếu test (DONE_TASK_NO_TEST) · matrix code_ref trỏ file không tồn tại (MISSING_CODE_FILE) · REQ designed+tested nhưng code_ref rỗng (REQ_NOT_IMPLEMENTED). Wire gate P3-02b + closeout SKILL hbc-implement. +7 test.
- SKILL: hbc-implement closeout chạy validate-implementation + update matrix code_ref; hbc-test-execution validation thêm --d27.
- Regression: focused 54 pass; broad .claude/skills 650 pass (1 fail pre-existing bmad-module-builder, không liên quan); 4 gate checklist parse+run OK qua engine.

## TỔNG KẾT review-phase-flow → fix (toàn bộ nhóm 1+2+3 DONE)
Mọi finding HIGH/CRITICAL từ review 4-explorer đã đóng bằng code + test, trừ các mục pre-existing/contrived đã ghi defer (bmad-module-builder fail không liên quan; F2/F3/F4 convention drift LOW; story_id/gate_status dead columns; staleness content-hash).
