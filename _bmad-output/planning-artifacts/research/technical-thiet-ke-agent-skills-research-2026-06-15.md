---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
workflowType: 'research'
lastStep: 5
research_type: 'technical'
research_topic: 'Cách thiết kế Agent Skills (cho LLM/Claude)'
research_goals: 'Nắm best practice mới nhất để thiết kế một Agent Skill tốt — cấu trúc SKILL.md, prompt/context design, progressive disclosure, và cách đánh giá chất lượng'
user_name: 'Hanhnt2'
date: '2026-06-15'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-06-15
**Author:** Hanhnt2
**Research Type:** technical

---

## Research Overview

[Research overview and methodology will be appended here]

---

<!-- Content will be appended sequentially through research workflow steps -->

## Technical Research Scope Confirmation

**Research Topic:** Cách thiết kế Agent Skills (cho LLM/Claude)
**Research Goals:** Nắm best practice mới nhất để thiết kế một Agent Skill tốt — cấu trúc SKILL.md, prompt/context design, progressive disclosure, và cách đánh giá chất lượng

**Technical Research Scope (đã điều chỉnh cho chủ đề Agent Skills):**

- Kiến trúc skill — cấu trúc thư mục (SKILL.md, references/, assets/, scripts/), YAML frontmatter, định dạng name/description/trigger
- Progressive disclosure — nạp ngữ cảnh theo tầng, ngân sách token, khi nào carve file
- Prompt & context design — viết "đích đến" thay vì "lộ trình", phân tầng script vs prompt, gotchas, tránh over-structure
- Spec & nền tảng — Agent Skills spec của Anthropic, cách Claude Code/API nạp skill, ranh giới skill vs subagent vs MCP
- Đánh giá chất lượng & failure modes — tiêu chí skill tốt, eval/trigger validation, các lỗi phổ biến

**Research Methodology:**

- Current web data với xác minh nguồn nghiêm ngặt (ưu tiên docs chính thức Anthropic)
- Multi-source validation cho các claim quan trọng
- Confidence level cho thông tin chưa chắc chắn
- Đối chiếu với chuẩn nội bộ repo (prompt-quality-canon, skill-quality-principles)

**Scope Confirmed:** 2026-06-15

---

## Phân tích nền tảng & công cụ (Technology Landscape)

> Bản chất "tech stack" của việc thiết kế Agent Skills không phải ngôn ngữ/DB/cloud, mà là: **định dạng file skill, runtime nạp skill, và các cơ chế mở rộng lân cận**. Phần này map đúng các trục đó.

### Định dạng & cấu trúc skill

Một Skill là **một thư mục tự chứa** gồm `SKILL.md` (instructions + metadata) cùng các tài nguyên tùy chọn: `references/`, `assets/` (template), `scripts/` (code chạy được). Đây là tài nguyên dựa trên filesystem mà agent **khám phá và nạp động** để chuyển từ general-purpose sang specialist.

- **YAML frontmatter** bắt buộc 2 trường: `name` (≤ 64 ký tự, chỉ chữ thường/số/gạch nối, không XML tag, không từ khóa reserved) và `description` (≤ 1024 ký tự, không rỗng, không XML tag).
- **Thân SKILL.md** nên giữ **dưới ~500 dòng** để tối ưu hiệu năng; vượt thì tách sang file con theo progressive disclosure.
- README.md cho người đọc đặt ở **gốc repo**, không nằm trong thư mục skill.
- _Confidence: Cao_ — khớp giữa Claude Docs (best-practices) và repo `anthropics/skills`.
- _Source: [Skill authoring best practices — Claude Docs](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices), [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [anthropics/skills](https://github.com/anthropics/skills)_

### Runtime nạp skill (môi trường thực thi)

Skill chạy trong **code execution environment**: agent truy cập filesystem, chạy bash, thực thi code. Lúc khởi động, agent **preload metadata** (chỉ `name` + `description`, vài chục token/skill) vào system prompt; thân SKILL.md nằm trên đĩa cho tới khi skill được kích hoạt.

- Hỗ trợ đa bề mặt: **Claude Code**, **Claude API / Agent SDK**, **claude.ai**, và các nền tảng AI khác adopt định dạng SKILL.md.
- _Source: [Equipping agents for the real world with Agent Skills — Anthropic](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), [Agent Skills in the SDK](https://platform.claude.com/docs/en/agent-sdk/skills), [Extend Claude with skills — Claude Code Docs](https://docs.claude.com/en/docs/claude-code/skills)_

### Công cụ tạo skill

- **skill-creator** (`anthropics/skills`) — skill để tạo & cải tiến skill lặp; nhấn mạnh dùng **concrete examples** và **eval định lượng** trong vòng lặp create→eval→iterate.
- **The Complete Guide to Building Skills for Claude** (PDF chính thức) — fundamentals, planning, testing, distribution, patterns, YAML reference.
- Hệ sinh thái cộng đồng: `obra/superpowers`, marketplace (awesomeskill.ai)…
- _Source: [skill-creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md), [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)_

### Vị trí của Skill so với cơ chế mở rộng lân cận

| Cơ chế | Bản chất | Dùng khi |
|---|---|---|
| **Skill** | Đóng gói **kiến thức/quy trình** (không cần code, portable, tái dùng) | Muốn Claude làm 1 việc theo **cùng một cách** mỗi lần (convention của team) |
| **MCP** | Lớp **kết nối** tới hệ thống ngoài (cấp *quyền truy cập* tool) | Cần nối tới hệ thống/dữ liệu ngoài |
| **Subagent** | Context window riêng, system prompt riêng, **giới hạn tool**, cô lập ngữ cảnh | Cần thực thi tác vụ độc lập, chạy model khác, cô lập context |

Ba thứ **bổ sung nhau**: Skill = "cách làm đúng", MCP = "truy cập được", Subagent = "ai làm". _Source: [Skills explained — claude.com](https://claude.com/blog/skills-explained), [Skills vs Sub-Agents vs MCP (2026) — k21academy](https://k21academy.com/claude/claude-code-skills-vs-sub-agents-vs-mcp/)_

### Nhận định nền tảng

Việc "thiết kế skill" hội tụ về **3 trụ**: (1) **metadata kích hoạt đúng** (description), (2) **progressive disclosure** để tiết kiệm context, (3) **phân tầng** giữa prompt (judgment) và script (deterministic). Các phần sau đi sâu từng trụ.

---

## Progressive Disclosure & Cơ chế tích hợp (Integration Patterns)

### 3 tầng progressive disclosure (cơ chế lõi)

| Tầng | Nạp khi | Nội dung | Chi phí token |
|---|---|---|---|
| **1. Metadata** | Khởi động (luôn) | `name` + `description` | ~100 token/skill |
| **2. SKILL.md body** | Khi skill được kích hoạt | Toàn bộ instruction | tới ~5.000 token |
| **3. Bundled resources** | Khi agent thấy cần | `references/`, `assets/`, `scripts/` | 0 cho tới khi truy cập |

Điểm mấu chốt: **file không tốn context cho tới khi được đọc**. Nhờ vậy có thể cài *nhiều* skill mà không phạt context — agent chỉ biết skill *tồn tại* và *khi nào dùng*. Một skill có thể đính kèm tài liệu API lớn, dataset, ví dụ dài… mà không tốn token nếu không dùng tới.
- _Source: [Progressive Disclosure as a System Design Pattern — SwirlAI](https://www.newsletter.swirlai.com/p/agent-skills-progressive-disclosure), [Agent Skills overview — Claude Docs](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview), [First Principles Deep Dive — leehanchung](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)_

### Ba thư mục tài nguyên

- **`scripts/`** — code Python/Bash chạy được. Khi instruction gọi script, Claude chạy qua bash và **chỉ nhận output**; *code script không bao giờ vào context*. Dùng script thay vì để Claude tự sinh code có thể **giảm tới ~90% token** và tăng độ tin cậy/ổn định.
- **`references/`** — tài liệu nạp vào context *khi cần* (API docs, schema, bảng tra).
- **`assets/`** — template & file nhị phân (không vào context, dùng khi thực thi).
- _Source: [How to create custom skills — Claude Help Center](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills), [Inside Claude Code Skills — Mikhail Shilkov](https://mikhail.io/2025/10/claude-code-skills/), [Claude Code Skills: code scripts vs markdown — MindStudio](https://www.mindstudio.ai/blog/claude-code-skills-code-scripts-vs-markdown-instructions)_

### Ranh giới script ↔ instruction (nguyên tắc đặt trí tuệ)

Script lo **plumbing** (fetch/parse/validate/count/transform — việc xác định, lặp lại); prompt lo **judgment** (interpret/classify/decide). Mỗi dòng markdown thêm vào = thêm token + thêm chỗ cho diễn giải sai. → Việc gì xác định và lặp lại thì đẩy xuống script. _(Khớp `script-opportunities-reference` nội bộ.)_

### Đóng gói & phân phối (composability)

- **Plugin** là **định dạng phân phối**, **skill** là **nội dung**: *cài plugin, dùng skill*. Một plugin có thể bundle nhiều skill + hooks + cấu hình MCP server; các skill trong cùng plugin **chia sẻ context/config**.
- Hệ sinh thái 2026 đã "platform-like": Skills/Agents/Hooks/MCP/LSP đều đóng gói–cài–cập nhật–phân phối qua **marketplace** (directory chính thức của Anthropic, ccpi CLI…). Ví dụ tháng 6/2026: *Frontend Design* ~829k, *Superpowers* ~752k lượt cài.
- Luồng phân phối: **packaging → validation → submission → versioning**.
- _Source: [Packaging Claude Code Plugins — jsmanifest](https://jsmanifest.com/claude-code-plugin-packaging-guide), [Create plugins — Claude Code Docs](https://code.claude.com/docs/en/plugins), [Plugin Marketplace Guide 2026 — agensi](https://www.agensi.io/learn/claude-code-plugin-marketplace-guide)_

### ⚠️ Mâu thuẫn nguồn cần lưu ý

Ngân sách thân SKILL.md được nêu **khác đơn vị** giữa các nguồn: best-practices chính thức nói **"< ~500 dòng"**, các deep-dive cộng đồng nói **"tới ~5.000 token"** (≈ trần spec). Chuẩn nội bộ repo của bạn còn chặt hơn: **~2.000 token (mong muốn) / ~3.000 (trần cứng)**. → Thực hành an toàn: bám mốc **chặt nhất** áp dụng được; coi 500 dòng / 5k token là *trần*, không phải mục tiêu. _(Confidence: Trung bình — đơn vị đo khác nhau giữa nguồn.)_

---

## Kiến trúc & Prompt-Design Patterns (trục giá trị cao nhất)

### A. Description — tín hiệu kích hoạt quan trọng nhất

`description` là **tín hiệu duy nhất** Claude dùng để quyết định nạp skill. Coi như "ad copy".

- **Công thức:** `Use when [hành động/ngữ cảnh người dùng]. [Skill làm gì]` — front-load điều skill *làm*; spec **cắt description ở ~250 ký tự**, nên use-case chính phải nằm sớm.
- **Ngôi thứ ba** ("Processes Excel files…", không "You can use this…") — description tiêm vào system prompt, lệch ngôi gây lỗi discovery.
- **Quy tắc "and":** nếu description có **>1 lần chữ "and"** → tách skill. Một skill "lo mọi thứ về PR" sẽ không trigger ổn định.
- **Không quá rộng, không quá hẹp:** "helps with code" (trigger mọi thứ) ✗; "reviews Flask SQL injection in PostgreSQL" (không trigger review chung) ✗.
- _Source: [Skill authoring best practices — Claude Docs](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices), [Why Intended Skills Don't Fire — Medium](https://medium.com/@taki4416/why-intended-skills-dont-fire-an-anti-pattern-in-claude-code-skill-a8c5230a9a5e), [Skills Not Working Troubleshooting 2026 — agensi](https://www.agensi.io/learn/claude-code-skills-not-working-troubleshooting)_

### B. "Degrees of freedom" — nguyên tắc thiết kế cốt lõi

Cân lượng chỉ dẫn theo độ rủi ro của đường đi (obra/superpowers):
- **Cầu hẹp, vực hai bên** (chỉ một cách an toàn) → guardrail + lệnh chính xác (**low freedom**).
- **Đồng trống, không hiểm họa** (nhiều đường tới đích) → chỉ định hướng chung, tin Claude tự tìm (**high freedom**).

→ Trùng khít chuẩn nội bộ của bạn: *"viết thứ sống sót dưới dạng goal; chỉ dùng quy trình chính xác khi sai một bước là tốn kém (script call, API có hậu quả)"*. _Source: [obra/superpowers — anthropic-best-practices.md](https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md?plain=1)_

### C. Naming & scope

- **Gerund form** (verb+-ing): `processing-pdfs`, `analyzing-spreadsheets`, `writing-documentation`. Chấp nhận noun-phrase (`pdf-processing`) hoặc action (`process-pdfs`).
- **Một skill = một capability**: đúng 1 `description`, tập trung 1 năng lực chính.
- _Source: [Skill authoring best practices — Claude Docs](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)_

### D. Conciseness (mỗi token cạnh tranh với hội thoại)

Khi SKILL.md đã nạp, **mỗi token cạnh tranh** với lịch sử hội thoại + context khác. Khuyến nghị cộng đồng: getting-started skill **< 150 từ**, skill nạp thường xuyên **< 200 từ**. _(Chuẩn nội bộ bạn đo bằng token: ~2k/3k — cùng tinh thần.)_ _Source: [obra/superpowers](https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md?plain=1)_

### E. Cross-model & time-sensitivity

- **Đa model**: hợp Opus chưa chắc đủ cho Haiku — nhắm chỉ dẫn chạy tốt trên mọi model dự định dùng.
- **Tránh thông tin theo thời điểm** (hoặc gom vào mục "old patterns") — checklist chất lượng yêu cầu "no time-sensitive information".
- _Source: [obra/superpowers](https://github.com/obra/superpowers/blob/main/skills/writing-skills/anthropic-best-practices.md?plain=1), [Skill authoring best practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)_

### Bảng anti-pattern → cách sửa

| Anti-pattern | Hậu quả | Cách sửa |
|---|---|---|
| Description mơ hồ ("helps with code") | Trigger lung tung / không trigger | Công thức "Use when…", front-load, từ khóa cụ thể |
| Description >1 "and" | Skill ôm đồm, không trigger ổn | Tách thành nhiều skill 1-capability |
| Use-case nằm ở câu thứ 3 | Bị cắt ở ~250 ký tự, Claude không thấy | Đưa use-case lên đầu |
| Nhồi mọi thứ vào SKILL.md | Tốn token, dễ diễn giải sai | Progressive disclosure: carve sang references/ |
| Để Claude tự sinh code lặp lại | Token cao, kém ổn định | Đưa xuống `scripts/` (chỉ output vào context) |
| Lệnh chính xác cho việc nhiều-đường-đúng | Bó cứng, mất adaptivity | High freedom: nêu goal, để model tự tìm |
| Thông tin theo thời điểm trong body | Skill lỗi thời nhanh | Bỏ hoặc gom vào "old patterns" |


