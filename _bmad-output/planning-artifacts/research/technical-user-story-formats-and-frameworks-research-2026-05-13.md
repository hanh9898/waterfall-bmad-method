---
stepsCompleted: [1, 2]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'User Story Formats & Frameworks — INVEST, 3Cs, BDD, Job Stories và cách kết hợp để triển khai'
research_goals: 'Tìm hiểu tổng quan các format viết user stories, deep dive vào INVEST + 3Cs, và cải thiện skill hbc-create-invest-epics-and-stories'
user_name: 'Hanhnt2'
date: '2026-05-13'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-05-13
**Author:** Hanhnt2
**Research Type:** technical

---

## Research Overview

[Research overview and methodology will be appended here]

---

## Technical Research Scope Confirmation

**Research Topic:** User Story Formats & Frameworks — INVEST, 3Cs, BDD, Job Stories và cách kết hợp để triển khai
**Research Goals:** Tìm hiểu tổng quan các format viết user stories, deep dive vào INVEST + 3Cs, và cải thiện skill hbc-create-invest-epics-and-stories

**Technical Research Scope:**

- Các framework viết stories — INVEST, 3C's, BDD/Gherkin, Job Stories, FDD, Connextra template
- So sánh & kết hợp — framework nào bổ sung cho nhau, xung đột gì
- Triển khai thực tế — format nào được dùng nhiều nhất, best practices từ industry
- Áp dụng vào skill hiện tại — gap analysis và đề xuất cải thiện

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-05-13

---

## Các Framework Viết User Stories

### 1. Connextra Template (2001)

**Nguồn gốc:** Rachel Davies và team tại Connextra (UK), ~2001. Được phổ biến bởi Mike Cohn.

**Format:**
```
As a [role],
I want [capability],
So that [benefit].
```

**Bản chất:** Đây là **template viết** (writing template) — không phải framework đánh giá. Nó trả lời 3 câu hỏi: AI dùng? (role), Muốn gì? (capability), Tại sao? (benefit). Phần "So that" là optional.

**Ưu điểm:** Đơn giản, buộc người viết nghĩ về user và giá trị. Được coi là "training wheels" cho người mới.

**Hạn chế:** Dễ trở thành template máy móc — người viết điền form mà không thực sự hiểu context. Không capture được motivation hay situation.

_Source: [Agile Alliance](https://agilealliance.org/glossary/user-story-template/), [Mountain Goat Software](https://www.mountaingoatsoftware.com/blog/why-the-three-part-user-story-template-works-so-well), [O'Reilly](https://www.oreilly.com/library/view/user-experience-mapping/9781787123502/92d21fe3-a741-49ff-8200-25abf18c98d0.xhtml)_

---

### 2. 3C's — Card, Conversation, Confirmation (2001)

**Nguồn gốc:** Ron Jeffries, đồng sáng lập Extreme Programming (XP), 2001.

**Cấu trúc:**

| C | Vai trò | Mô tả |
|---|---------|-------|
| **Card** | Viết | Mô tả ngắn gọn nhu cầu user — "vé vào cửa cho cuộc trò chuyện", KHÔNG phải tài liệu yêu cầu đầy đủ |
| **Conversation** | Thảo luận | Đối thoại giữa PO, dev team, stakeholders để làm rõ chi tiết, build shared understanding |
| **Confirmation** | Xác nhận | Acceptance criteria cụ thể, testable — đảm bảo team và stakeholders đồng ý "done" nghĩa là gì |

**Bản chất:** Đây là **process framework** (quy trình) — mô tả cách một story được tạo ra và hoàn thiện qua 3 giai đoạn. Card nhỏ gọn có chủ đích — buộc story phải nhỏ và conversation phải xảy ra.

**Quan trọng:** Ron Jeffries nhấn mạnh Card chỉ là điểm bắt đầu. Giá trị thực nằm ở Conversation. Confirmation (AC) là output cuối cùng.

_Source: [Ron Jeffries — 3Cs Revisited](https://ronjeffries.com/articles/019-01ff/3cs-revisited/), [Agile Alliance](https://agilealliance.org/glossary/three-cs/), [Scrum.org](https://www.scrum.org/resources/blog/common-pitfall-user-stories)_

---

### 3. INVEST (2003)

**Nguồn gốc:** Bill Wake, 17/08/2003. Bài viết gốc: "INVEST in Good Stories, and SMART Tasks".

**6 tiêu chí:**

| Tiêu chí | Kiểm tra | Nếu fail |
|----------|----------|----------|
| **I**ndependent | Implement được mà không chờ story khác? | Split hoặc reorder |
| **N**egotiable | AC để dev tự chọn cách implement? | Bỏ chi tiết implementation |
| **V**aluable | User thực sự được gì? | Reframe hoặc chuyển Technical Tasks |
| **E**stimable | Dev estimate được? | Thêm context hoặc split |
| **S**mall | Vừa 1-2 ngày? | Split nhỏ hơn |
| **T**estable | Mỗi AC verify được? | Viết lại AC observable |

**Bản chất:** Đây là **quality checklist** (bộ đánh giá) — không quy định cách viết, chỉ đánh giá story đã viết có tốt không. Bill Wake tạo acronym bằng cách liệt kê mọi thuộc tính của good story, rồi tìm tổ hợp tạo thành từ có nghĩa.

_Source: [XP123 — Bill Wake gốc](https://xp123.com/invest-in-good-stories-and-smart-tasks/), [Agile Alliance](https://agilealliance.org/glossary/invest/), [Wikipedia](https://en.wikipedia.org/wiki/INVEST_(mnemonic))_

---

### 4. BDD / Gherkin — Given-When-Then (2003-2006)

**Nguồn gốc:** Dan North (BDD concept, 2003), Cucumber team (Gherkin syntax, 2008). Given-When-Then có gốc từ BDD.

**Format:**
```gherkin
Feature: Tên tính năng

  Scenario: Mô tả scenario
    Given [precondition — trạng thái ban đầu]
    When [action — hành động user thực hiện]
    Then [outcome — kết quả quan sát được]
    And [thêm conditions nếu cần]
```

**Bản chất:** Đây là **specification format** — vừa là tài liệu, vừa là test tự động hóa được. Gherkin là ngôn ngữ domain-specific, executable bằng Cucumber/SpecFlow.

**Quan hệ với User Stories:** User stories mô tả WHO/WHAT/WHY, Gherkin mô tả HOW TO VERIFY. Chúng bổ sung nhau — story là Card, Gherkin là Confirmation.

**Best practices:**
- 1-3 AC per story. Nếu > 4 → story quá lớn, cần split
- AC mô tả hệ thống làm gì, KHÔNG mô tả cách code
- Cross-functional team cùng viết scenarios
- AC trở thành living documentation khi automated

_Source: [Thoughtworks](https://www.thoughtworks.com/insights/blog/applying-bdd-acceptance-criteria-user-stories), [TestQuality 2026 Guide](https://testquality.com/gherkin-user-stories-acceptance-criteria-guide/), [Cucumber docs](https://cucumber.io/docs/terms/user-story/), [Parallel HQ](https://www.parallelhq.com/blog/given-when-then-acceptance-criteria)_

---

### 5. Job Stories (2013)

**Nguồn gốc:** Team Intercom, ~2013. Alan Klement đặt tên và viết bài phân tích.

**Format:**
```
When [situation/context],
I want to [motivation/action],
So I can [expected outcome].
```

**Ví dụ:** "When an important new customer signs up, I want to be notified, so I can start a conversation with them."

**Khác biệt với User Stories:**

| | User Story | Job Story |
|---|-----------|-----------|
| Focus | Role (As a...) | Situation (When...) |
| Driver | Persona-driven | Context-driven |
| Output | Mô tả functionality | Mô tả motivation |
| Solution | Ngầm gợi ý solution | Không gợi ý solution |

**Bản chất:** Đây là **alternative writing format** — thay thế Connextra template khi role không quan trọng bằng context. Dựa trên Jobs-to-be-Done theory.

**Khi nào dùng:** Khi user personas không rõ ràng, khi cùng một feature phục vụ nhiều roles khác nhau, khi context/situation quan trọng hơn role.

_Source: [Intercom Blog](https://www.intercom.com/blog/accidentally-invented-job-stories/), [Alan Klement — JTBD](https://jtbd.info/replacing-the-user-story-with-the-job-story-af7cdee10c27), [Mountain Goat Software](https://www.mountaingoatsoftware.com/blog/job-stories-offer-a-viable-alternative-to-user-stories)_

---

## Bản đồ quan hệ giữa các Framework

```
┌─────────────────────────────────────────────────────┐
│                  USER STORY ECOSYSTEM                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  WRITING TEMPLATES (cách viết)                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │  Connextra    │  │  Job Stories  │                │
│  │  As a/I want/ │  │  When/I want/ │                │
│  │  So that      │  │  So I can     │                │
│  └──────┬───────┘  └──────┬───────┘                │
│         │                  │                         │
│         ▼                  ▼                         │
│  ┌─────────────────────────────────┐                │
│  │  3C's (process framework)       │                │
│  │                                 │                │
│  │  Card ← Connextra/Job Story     │                │
│  │  Conversation ← team discussion │                │
│  │  Confirmation ← AC (see below)  │                │
│  └──────────────┬──────────────────┘                │
│                 │                                    │
│                 ▼                                    │
│  ┌──────────────────────────────┐                   │
│  │  INVEST (quality checklist)  │                   │
│  │  Đánh giá story sau khi viết │                   │
│  │  I-N-V-E-S-T gate           │                   │
│  └──────────────────────────────┘                   │
│                                                     │
│  SPECIFICATION FORMAT (cách verify)                 │
│  ┌──────────────────────────────┐                   │
│  │  BDD / Gherkin               │                   │
│  │  Given/When/Then             │                   │
│  │  = Confirmation của 3C's     │                   │
│  │  = Testable của INVEST       │                   │
│  └──────────────────────────────┘                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Deep Dive: INVEST + 3C's hoạt động cùng nhau

### Mối quan hệ cộng sinh

3C's và INVEST **bổ sung hoàn toàn**, không xung đột:

| 3C's Phase | INVEST criteria được đảm bảo |
|------------|------------------------------|
| **Card** (viết ngắn gọn) | → **Independent** (story độc lập), **Small** (story nhỏ), **Valuable** (có giá trị cho user) |
| **Conversation** (thảo luận) | → **Negotiable** (thảo luận = không cố định), **Estimable** (thảo luận = dev hiểu scope) |
| **Confirmation** (AC) | → **Testable** (AC = có thể test) |

### Workflow kết hợp

```
1. VIẾT CARD (Connextra template)
   "As a project member, I want to create a task..."
   
2. CHECK INVEST lần 1 (sớm)
   ✓ Independent? ✓ Valuable? ✓ Small?
   ✗ Nếu fail → sửa Card trước khi conversation
   
3. CONVERSATION (team discussion)
   - Làm rõ scope, edge cases
   - Architecture references
   - Dev estimates
   
4. CHECK INVEST lần 2 (sau conversation)
   ✓ Negotiable? ✓ Estimable?
   ✗ Nếu fail → thêm conversation
   
5. CONFIRMATION (viết AC — Given/When/Then)
   - Observable behavior only
   - 1-3 AC per story
   
6. CHECK INVEST lần 3 (final gate)
   ✓ Testable? ✓ Tất cả 6 criteria?
   ✗ Nếu fail → quay lại bước tương ứng
```

### Áp dụng vào skill `hbc-create-invest-epics-and-stories`

**Hiện tại skill đã làm đúng:**
- Card dùng Connextra template (As a/I want/So that)
- Confirmation dùng Given/When/Then (BDD-style)
- INVEST validation ở Stage 4
- 3C's structure cho mỗi story (Card, Conversation, Confirmation)

**Điều này khẳng định:** Skill hiện tại đã kết hợp đúng 4 framework — Connextra (Card format), 3C's (story structure), INVEST (quality gate), BDD/Gherkin (AC format). Đây là best practice được industry công nhận.

---

## So sánh tổng hợp

| Framework | Loại | Năm | Tác giả | Trả lời câu hỏi |
|-----------|------|-----|---------|-----------------|
| Connextra | Writing template | 2001 | Rachel Davies / Connextra | Story viết thế nào? |
| 3C's | Process framework | 2001 | Ron Jeffries | Story được tạo ra qua quy trình nào? |
| INVEST | Quality checklist | 2003 | Bill Wake | Story có tốt không? |
| BDD/Gherkin | Specification format | 2003-2008 | Dan North / Cucumber | Story verify thế nào? |
| Job Stories | Alternative template | 2013 | Intercom / Alan Klement | Khi nào Connextra không phù hợp? |
