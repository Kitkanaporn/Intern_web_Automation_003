---
name: jira-uat-daily-reminder
description: ตรวจสอบ JIRA project ทุกวัน — หา ticket ที่กำลังจะถึง UAT (ใน 5 วัน) และ ticket ที่อยู่ระหว่าง UAT period แล้วสร้าง email draft พร้อม comment Jira
---

## AUTOMATION RULES (ห้ามฝ่าฝืน)

- **อ่าน config ก่อนทุกรัน** — ค่าทุกอย่างต้องมาจาก config ห้าม hardcode
- **Query Jira + อ่าน `UAT_Template_Email.html` + อ่าน `Map_User_Email.xlsx` ใหม่ทุกครั้ง** — ห้ามใช้ข้อมูลจาก session ก่อน
- **ไม่ถาม ไม่รอ ไม่ยืนยัน ไม่ขอ permission** — ทุก phase รันต่อเนื่องอัตโนมัติ
- **Output บนหน้าจอ Claude เท่านั้น** — ไม่สร้างไฟล์

---

## PRE-CHECK

เรียก `getAccessibleAtlassianResources`:
- สำเร็จ → Phase 0
- error → หยุด แสดง: `❌ ไม่สามารถเชื่อมต่อ Jira ได้ — กรุณาตรวจสอบ Settings → Connections → Atlassian แล้วรันใหม่อีกครั้ง`

---

## PHASE 0 — Setup Check

### 0A — อ่าน config

1. อ่าน `shared_config.yaml` จาก root folder
2. ตรวจหา project subfolder (โฟลเดอร์ที่มี `project_config.yaml`) — ถ้ามีหลายตัวให้ถามผู้ใช้เลือก 1
3. อ่าน `{project}/project_config.yaml` → merge เป็น config เดียวใน memory
4. Resolve path ของ `files.service_map` และ `files.email_template` จาก root folder

### 0B — ตรวจ required fields

อ่าน config ทั้งสองในรูป raw text — ทุกบรรทัดที่มี `#importance` คือ required field  
ตรวจว่า value ว่างหรือไม่ (ว่าง = `""`, `''`, หรือไม่มีค่า)

Required เพิ่มเติม (hardcoded):
- `jira.fields.uat_start`, `jira.fields.uat_end`, `jira.fields.workflow_task_id`
- `jira.service_fields[]` — ทุก entry ต้องมี `jira_field` และ `table_column` ครบ

**ก่อนไป Phase 1 ต้อง loop `jira.fields.*` ทุกตัวก่อนเสมอ (mandatory):**

สำหรับทุก field ใน `jira.fields.*` ที่ value = `""` หรือไม่มีค่า:
1. เรียก `getJiraIssueTypeMetaWithFields` เพื่อดึง field names ทั้งหมดของ project
2. ใช้ keyword matching ตาม `instructions/SETUP.md` B3 เพื่อหา customfield ID
3. เขียนค่ากลับลง `project_config.yaml` ทันที
4. แจ้งผู้ใช้ว่า auto-detect ได้ค่าอะไรบ้าง

**ห้ามข้ามขั้นตอนนี้** — ถ้า `jira.fields.*` ตัวไหนว่าง ต้อง detect และ save ก่อนเสมอ ไม่ว่าจะรันอัตโนมัติหรือไม่

**แบ่งเป็น 2 กลุ่ม:**

| กลุ่ม | Fields | วิธีจัดการ |
|---|---|---|
| **Auto-detect จาก Jira** | `jira.cloud_id`, `jira.base_url`, `jira.project_key`, `jira.fields.*` ทุกตัว, `jira.service_fields[].jira_field` | ทำตามขั้นตอนด้านบน → เขียนลง config → ดำเนินการต่อ |
| **ต้องถามผู้ใช้** | `email.sender_email`, `email.sender_name`, `email.sender_phone` | บันทึกว่าว่าง → ดำเนินการต่อได้ (แสดง placeholder ใน output) |

> `jira.fields.*` ว่าง = detect ก่อน Phase 1 เสมอ | `email.*` ว่าง = ดำเนินการต่อได้

---

## PHASE 1 — Search tickets

| | รายละเอียด |
|---|---|
| **Tool** | `searchJiraIssuesUsingJql` |
| **cloudId** | `jira.cloud_id` |
| **jql** | `project = "{project_key}" AND issuetype = Epic AND ((cf[{uat_start}] >= startOfDay() AND cf[{uat_start}] <= endOfDay("+5")) OR (cf[{uat_start}] < startOfDay() AND cf[{uat_end}] >= startOfDay())) ORDER BY cf[{uat_start}] ASC` |
| **fields** | `summary`, `description`, ทุก field จาก `jira.fields.*` (รวม promote_date, remark ถ้าไม่ว่าง), ทุก field จาก `jira.service_fields[].jira_field` |
| **expand** | `names` |
| **maxResults** | 50 |
| **หลัง response** | สร้าง `field_display_names` map จาก `.names` (`customfield_xxxxx` → display name) ใช้ใน Phase 2 |

### ตรวจ ticket skip condition (ต่อ ticket)

`getJiraIssue` ดึง `comment` field ต่อทุก ticket แล้วตัดสินว่า INCLUDE หรือ SKIP:

```
สำหรับแต่ละ ticket:
  1. หา comment ที่ body มีข้อความจาก jira_comment.text
  2. แปลง created timestamp → เอาเฉพาะ DATE (YYYY-MM-DD) ห้ามใช้ time
  3. ตัดสิน:
       ไม่มี comment                        →  INCLUDE
       DATE(comment.created) = DATE(today)  →  INCLUDE  (รีรันวันเดิม)
       DATE(comment.created) < DATE(today)  →  SKIP
```

SKIP ได้เฉพาะเมื่อ comment มีอยู่ **และ** date < today เท่านั้น — ทุกกรณีอื่น INCLUDE  
มี INCLUDE ≥ 1 → ดำเนินการต่อ Phase 2 ทันที  
ทุก ticket เป็น SKIP → แสดง "✅ วันนี้ไม่มี UAT ต้องแจ้ง..." แล้วหยุด

---

## PHASE 2 — Prepare email data

### อ่าน Excel service map

อ่าน `files.service_map` sheet `map` (คอลัมน์: `Group` | `Group Mail` | `Member` | `Member Mail`) สร้าง:
- `name_email`: Member → Member Mail
- `group_members`: Group → [Members]
- `group_mail`: Group → Group Mail

Auto-match service field → Excel group: ดึง display name จาก `field_display_names[jira_field]` แล้ว match กับ key ใน `group_members` (case-insensitive exact match)

### Extract per-ticket values

**Workflow Task ID** (ต่อ ticket):
1. อ่านจาก `jira.fields.workflow_task_id`
2. Parse description หา `IT Workflow Task ID:\s*(\d+)`
3. ถ้าสองค่าต่างกัน → ใช้จาก description | มีแค่อย่างเดียว → ใช้อันนั้น | ไม่มีเลย → Jira key

**Remark** (ต่อ ticket): ถ้า `jira.fields.remark` ไม่ว่าง → ดึงค่า field นั้น | ว่าง → `""`

### สร้างรายการ ticket

- **all_tickets** — ทุก ticket เรียง Promote Date ASC → UAT Start ASC
- **unnotified_tickets** — ticket ที่ผ่านเงื่อนไข INCLUDE จาก Phase 1 (ไม่มี comment / comment วันนี้) — ใช้สำหรับ Phase 3 แถวสีเหลือง และ Phase 4 post comment

### Subject months (`{thai_months_str}`)

ใช้ Promote Date months ของ **unnotified_tickets** (distinct, ASC)  
ถ้ามีเดือนเดียวแต่มี notified tickets ในเดือนอื่นด้วย → รวมเดือนของ notified ด้วย

Format:
- 1 เดือน: `ส.ค. 2026`
- 2 เดือน: `มิ.ย. และ ส.ค. 2026`
- 3+ เดือน: `มิ.ย., ส.ค. และ ต.ค. 2026`
- ปีเดียวกัน → ระบุปีแค่เดือนสุดท้าย | ข้ามปี → ทุกเดือนระบุปี

### Group tickets by Promote Date month

แบ่ง all_tickets เป็น groups ตามเดือน+ปีของ Promote Date (ASC) — แต่ละ group จะมี separator row ใน UAT Table

### Build To / CC lists

**CC** (จาก all_tickets): service field ไหนมีค่า → ดึง Group Mail → union deduplicated, คั่นด้วย `;`

**To** (จาก all_tickets): รวมชื่อจากทุก service field → lookup email ด้วย case-insensitive prefix match (min chars จาก `recipient_matching.prefix_min_chars`) → union deduplicated → ไม่รวม `email.exclude_recipients`

### Service / Marketing QA columns (ต่อ ticket)

- service field มีชื่อ → `✓` | ว่าง → เว้นว่าง
- Marketing QA: รวม `extractNames()` จากทุก service field ที่ไม่ว่าง → deduplicate → join `,`

---

## PHASE 3 — Build output

ใช้ `mcp__visualize__show_widget` สร้าง 2 card:

### Card 1 — Subject

`แจ้งกำหนดการทดสอบ UAT : {project_key} งาน CR ที่มี Tentative Live เดือน {thai_months_str}`  
+ ปุ่ม Copy (plain text)

### Card 2 — Email body

3 ส่วน แต่ละส่วนมีปุ่ม Copy แยก:
1. **กล่อง To (สีเขียว)** — copy email addresses เท่านั้น (plain text) ใช้ `navigator.clipboard.writeText()`
2. **กล่อง CC (สีส้ม)** — copy email addresses เท่านั้น (plain text) ใช้ `navigator.clipboard.writeText()`
3. **เนื้อความ Email** — copy เฉพาะ HTML body จาก template (**ห้ามรวมกล่อง To/CC**) ใช้ `ClipboardItem` กับ `text/html` mime type เพื่อให้ paste ลง Outlook แล้ว render เป็น formatted email

⚠️ **htmlString ต้องเป็น raw HTML string เท่านั้น — ห้าม escape โดยเด็ดขาด:**
- ห้ามใช้ `JSON.stringify()`, `encodeURIComponent()`, `.replace(/</g,'&lt;')` หรือ escape ใดๆ กับ htmlString
- ต้องมี tag จริงๆ เช่น `<table>` ไม่ใช่ `&lt;table&gt;`
- ใช้ template literal (backtick) ครอบ HTML ทั้งหมดโดยตรง

```javascript
async function copyEmailHtml() {
  const htmlString = `<html><body>...raw HTML from template...</body></html>`;
  const blob = new Blob([htmlString], { type: 'text/html' });
  const item = new ClipboardItem({ 'text/html': blob });
  await navigator.clipboard.write([item]);
}
```

**HTML body** — ใช้โครงสร้างจาก `UAT_Template_Email.html` ทั้งหมด ห้ามสร้างใหม่ แทนที่ placeholder:

| Placeholder | ค่า |
|---|---|
| `{{THAI_MONTH}} {{YEAR}}` | `{thai_months_str}` |
| `{{UNNOTIFIED_TICKET_LINES}}` | `<p style="margin-left:20px;">{WORKFLOW_TASK_ID} {ชื่องาน ตัด prefix [xxx]}</p>` ต่อ unnotified ticket |
| `{{UAT_TABLE_ROWS}}` | separator rows + ticket rows (ดูโครงสร้างด้านล่าง) |
| `{{SENDER_NAME}}` `{{SENDER_EMAIL}}` `{{SENDER_PHONE}}` | จาก shared_config.yaml |

**UAT_TABLE_ROWS:**

Separator row (1 ต่อ Promote Date month group):
```html
<tr>
  <td colspan="11" style="background:#D6E4F0;font-weight:bold;font-style:italic;border:1px solid #999;padding:5px 8px;text-align:center;">
    Tentative Live Date : {Month Year}
  </td>
</tr>
```

Ticket row — notified (ไม่มี background):
```html
<tr>
  <td ...>{WORKFLOW_TASK_ID}</td>
  <td ...>{SUMMARY}</td>
  <td ...>✓</td>
  <!-- service columns ตามลำดับใน jira.service_fields[] -->
  <td ...>{MARKETING_QA_NAMES}</td>
  <td ...>{TEST_PERIOD}</td>
  <td ...>{remark}</td>
</tr>
```

Ticket row — unnotified: เหมือนกันทุก `<td>` เพิ่ม `background:#FFFDE7;`

**Test Period format:**
- Same month: `UAT 22 - 26/06 2026`
- Cross month: `UAT 30/06 - 02/07 2026`
- Cross year: `UAT 28/12/2026 - 03/01/2027`

---

## PHASE 4 — Comment Jira

สำหรับทุก ticket ใน unnotified_tickets (INCLUDE tickets):
- ตรวจ comment ที่มี body มีข้อความจาก `jira_comment.text` และ DATE(created) = DATE(today)
- **มีแล้ววันนี้ → ข้ามทันที** ห้าม comment ซ้ำ
- **ยังไม่มี → `addCommentToJiraIssue`**:
  - cloudId: `jira.cloud_id`
  - issueIdOrKey: Jira key
  - body: `jira_comment.text`

---

## PHASE 5 — สรุปผล

มี unnotified:
```
✅ UAT Notification เสร็จสิ้น ({today})
   - แจ้งแล้ว: {N} ticket(s) — {key1}, {key2}, ...
   - Comment Jira: เสร็จแล้ว
```

ไม่มีอะไรต้องแจ้ง:
```
✅ วันนี้ไม่มี UAT ต้องแจ้ง — ticket ทั้งหมดได้รับการแจ้งเตือนแล้ว ({today})
```
