---
name: jira-uat-daily-reminder
description: ตรวจสอบ JIRA project ทุกวัน — หา ticket ที่กำลังจะถึง UAT (ใน 5 วัน) และ ticket ที่อยู่ระหว่าง UAT period แล้วสร้าง email draft พร้อม comment Jira
---

Daily UAT reminder workflow. Runs automatically every day at the time set in shared_config.yaml.

---

## AUTOMATION RULES (ห้ามฝ่าฝืน)

- **อ่าน config ก่อนทุกรัน** — ค่าทุกอย่างต้องมาจาก config ห้าม hardcode
- **Query Jira ใหม่ทุกครั้ง** — ห้ามใช้ข้อมูล ticket จาก session ก่อน
- **อ่าน `UAT_Template_Email.html` ใหม่ทุกครั้ง** — ห้ามสร้าง HTML โครงสร้างใหม่เอง
- **อ่าน `Map_User_Email.xlsx` ใหม่ทุกครั้ง** — ห้ามใช้รายชื่อ/email จาก session ก่อน
- **ไม่ถาม ไม่รอ ไม่ยืนยัน** — ทุก phase รันต่อเนื่องอัตโนมัติ
- **ไม่ขอ permission** ก่อน action ใดๆ (draft, comment, field update)

---

## PHASE 0 — Setup Check (ตรวจสอบ config ก่อนทุกรัน)

### 0A — อ่าน config 2 ระดับ

**โครงสร้างไฟล์:**
```
📁 UAT-Notification/         ← root folder
├── SKILL.md
├── shared_config.yaml       ← config ร่วม (email, files, schedule)
├── Map_User_Email.xlsx
├── UAT_Template_Email.html
├── 📁 instructions/
│   ├── AGENT.md
│   └── SETUP.md             ← First-time Setup (Phase 0C)
├── 📁 CSD/
│   └── project_config.yaml  ← config เฉพาะ project (jira fields)
└── 📁 ProjectB/
    └── project_config.yaml
```

**ขั้นตอน:**
1. อ่าน `shared_config.yaml` จาก root folder
2. ตรวจสอบว่ามี project subfolder ไหนบ้าง (โฟลเดอร์ที่มี `project_config.yaml` อยู่ข้างใน)
3. ถ้ามีหลาย project → ถามผู้ใช้ว่าต้องการรัน project ไหน
4. อ่าน `{selected_project}/project_config.yaml`
5. Merge ทั้งสองเป็น config เดียวใน memory: `config = shared + project`
6. Path ของ files (service_map, email_template) ให้ resolve จาก root folder

### 0B — ตรวจสอบว่า config ครบหรือยัง

ตรวจสอบ required fields เหล่านี้ว่าว่างอยู่หรือไม่:

**จาก shared_config.yaml:**
- `email.sender_email`, `email.sender_name`, `email.draft_to`

**จาก project_config.yaml:**
- `jira.cloud_id`, `jira.base_url`, `jira.project_key`
- `jira.fields.uat_start`, `jira.fields.uat_end`, `jira.fields.workflow_task_id`
- `jira.service_fields[]` — ทุก entry ต้องมี jira_field และ table_column ครบ

**ถ้า config ครบแล้ว** → ข้ามไป Phase 1 ทันที

**ถ้า config ยังว่างอยู่** → อ่านไฟล์ `instructions/SETUP.md` แล้วทำตามขั้นตอนในนั้น

---

## PHASE 1 — Search ALL tickets in the UAT window

**Step 1A — JQL search:**
Use `searchJiraIssuesUsingJql`:
- cloudId: จาก config `jira.cloud_id`
- jql: `project = "{project_key}" AND issuetype = Epic AND ((cf[{uat_start}] >= startOfDay() AND cf[{uat_start}] <= endOfDay("+5")) OR (cf[{uat_start}] < startOfDay() AND cf[{uat_end}] >= startOfDay())) ORDER BY cf[{uat_start}] ASC`
- fields: `["summary", "description", "{uat_start}", "{uat_end}", "{promote_date}", "{workflow_task_id}", "{service_field_1}", ..., "{service_field_N}"]`
  (ดึงจาก config `jira.fields.*` + `jira.service_fields[].jira_field` ทุกตัว รวม `jira.fields.promote_date`)
- expand: `"names"` — เพื่อให้ได้ display name ของแต่ละ field (เช่น `customfield_19036` → `"Account Services Unit"`)
- maxResults: 50

**Step 1A.1 — Build field_display_names map:**
จาก response `.names` สร้าง map:
```
field_display_names = {
  "customfield_19036": "Account Services Unit",
  "customfield_19041": "CA Service Unit",
  ...
}
```
ใช้ใน Phase 2 สำหรับ auto-match กับ Excel Group column

**Step 1B — ตรวจสอบ comment ต่อ ticket (เช็คทั้งเนื้อหา + วันที่):**
สำหรับแต่ละ ticket ที่ได้จาก JQL → ใช้ `getJiraIssue` ดึง `comment` field แล้วตรวจสอบ **ทั้งเนื้อหาและวันที่สร้าง**:

- ถ้ามี comment ที่:
  1. body ประกอบด้วยข้อความจาก config `jira_comment.text` **และ**
  2. comment นั้นถูกสร้าง**วันก่อนหน้า** (created date < today)
  → **notified**

- ถ้าไม่มี comment ดังกล่าว **หรือ** มี comment แต่ถูกสร้าง**วันนี้** (created date = today)
  → **unnotified**

> **เหตุผล:** ถ้า comment ถูกสร้างวันนี้ ยังถือว่า unnotified — ทำให้รีรันในวันเดิมได้และทุกคนในทีมเห็นสถานะเดียวกัน

**ถ้าทุก ticket เป็น notified** → output:
> ✅ ไม่มี ticket ที่ต้องส่ง email แจ้งเตือนเพิ่ม — ticket ทั้งหมดได้รับการแจ้งเตือนแล้ว ({today})

หยุดทำงาน ไม่สร้าง draft

**ถ้ามี unnotified อย่างน้อย 1 ตัว** → ดำเนินการต่อ Phase 2

---

## PHASE 2 — Prepare email data

### Read SERVICE_MAP from Excel

อ่านไฟล์จาก config `files.service_map` (path สัมพัทธ์จาก root folder, sheet: `map`)
คอลัมน์ใน sheet: `Group` | `Group Mail` | `Member` | `Member Mail`

สร้าง 3 structures:

**1. name→email map** (สำหรับ lookup recipients):
```
name_email = { "CHANAPORN BOONCHOM": "CHANAPORN@set.or.th", ... }
```

**2. group→members map** (สำหรับ auto-match กับ Jira field):
```
group_members = {
  "Account Services Unit": ["CHANAPORN BOONCHOM", "CHATSARAN PRASONGPHOL", ...],
  "CA Service Unit": ["KANISORN KAMPRAPHAI", ...],
  ...
}
```

**3. group→group_mail map** (สำหรับ CC recipients — Unit-level email):
```
group_mail = {
  "Account Services Unit": "AccountServicesUnit@set.or.th",
  "CA Service Unit":       "CAServiceUnit@set.or.th",
  ...
}
```
(อ่านจากคอลัมน์ `Group` และ `Group Mail` ใน sheet `map`)

**Auto-match Jira field → Excel Group:**
สำหรับแต่ละ `jira_field` ใน config `jira.service_fields[]`:
1. ดึง display name จาก `field_display_names[jira_field]` (ได้จาก Step 1A.1)
2. ใช้ display name นั้น match กับ key ใน `group_members` (case-insensitive exact match)
3. ได้รายชื่อ member ของ group นั้นสำหรับใช้ lookup email และแสดงใน Marketing QA

### Extract Workflow Task ID

สำหรับแต่ละ ticket:
1. อ่าน field จาก config `jira.fields.workflow_task_id`
2. Parse `description` หา pattern: `IT Workflow Task ID:\s*(\d+)` (case-insensitive)
3. ถ้าทั้งสองมีและต่างกัน → ใช้ค่าจาก description (source of truth)
4. ถ้ามีแค่อย่างเดียว → ใช้อันที่มี
5. ถ้าไม่มีเลย → fallback = Jira key (เช่น CSD-215)

### สองรายการ ticket

- **all_tickets** — ทุก ticket ใน UAT window เรียงตาม Promote Date ASC แล้ว UAT Start ASC
- **unnotified_tickets** — เฉพาะที่ไม่มี comment `jira_comment.text`

### Determine email months (ใช้ Promote Date — ไม่ใช่ UAT Start)

รวบรวม Promote Date months ของทุก **unnotified_tickets** (distinct, เรียง ASC):
```
unnotified_months = ["มิ.ย.", "ส.ค."]   ← ถ้ามีหลายเดือน
unnotified_months = ["ส.ค."]             ← ถ้าเดือนเดียว 

ในกรณีที่เป็นเดือนเดียว ให้ใส่เดือนที่ notification ไปแล้วด้วย เช่น
หาก unnotfied_months = ["ส.ค."] แต่มี ticket ที่ได้รับการแจ้งเตือนแล้วในเดือน มิ.ย. ด้วย → ให้แสดงเป็น "มิ.ย. และ ส.ค." เพื่อให้ครอบคลุมถึง ticket ที่แจ้งเตือนไปแล้วด้วย
```

**สร้าง `{thai_months_str}` สำหรับ Subject:**
- 1 เดือน → `ส.ค. 2026`
- 2 เดือน → `มิ.ย. และ ส.ค. 2026`
- 3+ เดือน → `มิ.ย., ส.ค. และ ต.ค. 2026`  (คั่นด้วย `,` ยกเว้นตัวสุดท้ายใช้ `และ`)
- ปีใช้ปีของเดือนสุดท้าย (หรือปีเดียวกันทั้งหมด)

**English months** (สำหรับ Tentative Live Date separator row) — ยังคงใช้แยกตาม group เหมือนเดิม

### Group tickets by Promote Date month

แบ่ง all_tickets ออกเป็น groups ตามเดือน+ปีของ Promote Date (เรียง ascending):
```
promote_groups = [
  { month: "June 2026",   thai: "มิ.ย.", year: 2026, tickets: [...] },
  { month: "August 2026", thai: "ส.ค.", year: 2026,  tickets: [...] },
  ...
]
```
แต่ละ group จะมี Tentative Live Date separator row ใน UAT Table

### Build CC list (Group Mail — ระดับ Unit)

สำหรับทุก ticket ใน **all_tickets**:
1. ดูว่า service field ไหนมีค่า (ไม่ว่าง) → ได้ชื่อ group นั้น
2. ดึง Group Mail จาก `group_mail[group_name]`
3. Union ทุก Group Mail email, deduplicated → **cc_emails** list
        4. ใช้ `;` คั่นระหว่าง email ในกล่อง CC

### Build recipients list (Member Mail — รายบุคคล)

สำหรับทุก ticket ใน **all_tickets**:
1. รวบรวมทุกชื่อจาก `jira.service_fields[].jira_field` ทุกตัว
2. ค้นหา email ด้วย case-insensitive prefix match (min chars จาก config `recipient_matching.prefix_min_chars`)
3. Union ทุก email, deduplicated
4. ไม่รวม email ใดๆ ที่อยู่ใน config `email.exclude_recipients`

### Service column logic (ต่อ ticket)

วนซ้ำตาม `jira.service_fields[]`:
- jira_field มีชื่ออยู่ → `✓`
- jira_field ว่าง → `☐`
- table_column → ชื่อคอลัมน์ในตาราง UAT

**Marketing QA column:**
- ใช้ `extractNames(ticket[jira_field])` จากทุก service field ที่ไม่ว่างของ ticket นั้น
- รวม names ทั้งหมด → deduplicate → join ด้วย `,`
- ถ้าทุก field ว่าง → แสดงช่องว่าง

---

## PHASE 3 — Build output (2 card พร้อมปุ่ม Copy)

### ⚠️ บังคับ — อ่าน Template และ Excel ก่อนสร้าง output ทุกครั้ง

**ก่อนสร้าง card ใดๆ ต้องอ่านไฟล์เหล่านี้จาก root folder:**

1. **อ่าน `UAT_Template_Email.html`** → ใช้โครงสร้าง HTML จากไฟล์นี้เป็นฐานทั้งหมด:
   - โครงสร้างตาราง UAT (thead, tbody, colspan, rowspan)
   - ชื่อหัวคอลัมน์ทุกคอลัมน์
   - Environment table (static ทั้งหมด — copy มาตรงๆ ห้ามสร้างใหม่)
   - CSS inline style ทุก element
   - Signature block format

2. **อ่าน `Map_User_Email.xlsx`** (sheet: `map`) → ดึงข้อมูล Group / Member / Member Mail สดทุกครั้ง ห้ามใช้ค่าจาก memory เดิม

**ห้ามสร้างโครงสร้าง HTML ขึ้นมาใหม่เอง** — ต้อง replace placeholder ใน template เท่านั้น:
- `{{THAI_MONTH}}`, `{{YEAR}}`, `{{ENGLISH_MONTH}}`
- `{{RECIPIENT_REVIEW_BOX}}`, `{{UNNOTIFIED_TICKET_LINES}}` โดยส่วนนี้ให้คั่นด้วยเครื่องหมาย ";" โดยให้ต่อกันได้ไม่เกินแถวละ 5 address
- `{{WORKFLOW_TASK_ID}}`, `{{SUMMARY}}`, `{{SVC_*}}`, `{{MARKETING_QA_NAMES}}`
- `{{START_DD}}`, `{{END_DD_MM}}` (ใช้ date format rule: same-month vs cross-month)
- `{{SENDER_NAME}}`, `{{SENDER_EMAIL}}`

---

ใช้ `mcp__visualize__show_widget` สร้าง 2 card:

### Card 1 — หัวข้อ (Subject)
- header: "หัวข้อ (Subject)" + ปุ่ม Copy (plain text)
- Subject: `แจ้งกำหนดการทดสอบ UAT : {project_key} งาน CR ที่มี Tentative Live เดือน {thai_months_str}`

**Format ของ `{thai_months_str}`:**
- 1 เดือน → `ส.ค. 2026`
- 2 เดือน → `มิ.ย. และ ส.ค. 2026`
- 3+ เดือน → `มิ.ย., ส.ค. และ ต.ค. 2026` (คั่น `,` ยกเว้นตัวสุดท้ายใช้ `และ`)
- ปีใช้ปีของเดือนสุดท้าย

---

### Card 2 — เนื้อความ Email
- header: "เนื้อความ Email" + ปุ่ม Copy (HTML สำหรับการวางบน email) 
- ใช้โครงสร้าง HTML จาก `UAT_Template_Email.html` ทั้งหมด — **ห้ามสร้าง HTML โครงสร้างใหม่เอง**
- แทนที่ placeholder ดังนี้:

| Placeholder | ค่าที่แทน |
|---|---|
| `{{THAI_MONTH}} {{YEAR}}` | เดือนภาษาไทย + ปี ค.ศ. (ใช้ `{thai_months_str}`) |
| `{{RECIPIENT_REVIEW_BOX}}` | HTML กล่องสีเขียว — member emails คั่น `;` ไม่เกิน 5 ต่อบรรทัด |
| `{{CC_REVIEW_BOX}}` | HTML กล่องสีส้ม — Group Mail emails คั่น `;` |
| `{{UNNOTIFIED_TICKET_LINES}}` | `<p style="margin-left:20px;">ชื่องาน (ตัด prefix [xxx] ออก)</p>` ต่อ unnotified ticket |
| `{{UAT_TABLE_ROWS}}` | tbody rows ทั้งหมด (separator + ticket rows) |
| `{{SENDER_NAME}}` | ชื่อผู้ส่ง (จาก shared_config.yaml) |
| `{{SENDER_EMAIL}}` | email ผู้ส่ง |
| `{{SENDER_PHONE}}` | เบอร์โทร |

**UAT_TABLE_ROWS — โครงสร้าง:**

Separator row (หนึ่งต่อ Promote Date month group):
```html
<tr>
  <td colspan="11" style="background:#D6E4F0;font-weight:bold;font-style:italic;border:1px solid #999;padding:5px 8px;text-align:center;">
    Tentative Live Date : {Month Year เช่น June 2026}
  </td>
</tr>
```

Ticket row — **notified** (background ขาว):
```html
<tr>
  <td style="border:1px solid #999;padding:4px 6px;text-align:center;vertical-align:middle;color:#1F4E79;font-weight:bold;">{WORKFLOW_TASK_ID}</td>
  <td style="border:1px solid #999;padding:4px 6px;text-align:left;vertical-align:middle;">{SUMMARY}</td>
  <td style="border:1px solid #999;padding:4px 6px;text-align:center;vertical-align:middle;color:#1F4E79;font-weight:bold;font-size:13px;">✓ หรือ ☐</td>
  ... (ทุก service column)
  <td style="border:1px solid #999;padding:4px 6px;text-align:left;vertical-align:middle;font-size:10px;">{MARKETING_QA_NAMES}</td>
  <td style="border:1px solid #999;padding:4px 6px;text-align:center;vertical-align:middle;font-size:10px;">{TEST_PERIOD}</td>
  <td style="border:1px solid #999;padding:4px 6px;text-align:left;vertical-align:top;"></td>
</tr>
```

Ticket row — **unnotified** (ทุก `<td>` ต้องมี `background:#FFFDE7;`):
```html
<tr>
  <td style="border:1px solid #999;padding:4px 6px;text-align:center;vertical-align:middle;color:#1F4E79;font-weight:bold;background:#FFFDE7;">{WORKFLOW_TASK_ID}</td>
  ... (ทุก td ต้องมี background:#FFFDE7;)
</tr>
```

**Test Period format:**
- Same month: `UAT 22 - 26/06 2026`
- Cross month: `UAT 30/06 - 02/07 2026`

**Service column (✓ / ☐):**
- ใช้ `extractNames(ticket[jira_field])` คืน array ไม่ว่าง → `✓`
- คืน `[]` → `☐`

**Marketing QA cell:**
- รวม `extractNames(ticket[jira_field])` จากทุก service field ที่ไม่ว่างของ ticket นั้น → deduplicate → join ด้วย `,`

---

## PHASE 4 — Comment Jira

สำหรับทุก **unnotified** ticket → ใช้ `addCommentToJiraIssue`:
- cloudId: จาก config `jira.cloud_id`
- issueIdOrKey: Jira key ของ ticket นั้น
- comment body: ข้อความจาก config `jira_comment.text` (เช่น `"UAT Notification Complete"`)

**ทำอัตโนมัติทันที ไม่ถาม ไม่ขอ permission**

---

## PHASE 5 — สรุปผล

แสดงข้อความสรุปท้าย card:

**กรณีมี unnotified:**
```
✅ UAT Notification เสร็จสิ้น ({today})
   - แจ้งแล้ว: {N} ticket(s) — {key1}, {key2}, ...
   - Comment Jira: เสร็จแล้ว
```

**กรณีไม่มีอะไรต้องแจ้ง:**
```
✅ วันนี้ไม่มี UAT ต้องแจ้ง — ticket ทั้งหมดได้รับการแจ้งเตือนแล้ว ({today})
```

---

## กฎ Automation (ห้ามฝ่าฝืน)

- **Query Jira ใหม่ทุกรัน** — ห้ามใช้ข้อมูล ticket จาก session ก่อน
- **อ่าน `UAT_Template_Email.html` ใหม่ทุกครั้ง** — ห้ามสร้าง HTML โครงสร้างใหม่เอง
- **อ่าน `Map_User_Email.xlsx` ใหม่ทุกครั้ง** — ห้ามใช้รายชื่อ/email จาก session ก่อน
- **ไม่ถาม ไม่รอ ไม่ยืนยัน** — ทุก phase รันต่อเนื่องอัตโนมัติ
- **ไม่ขอ permission** ก่อน action ใดๆ (draft, comment, field update)
- **Output บนหน้าจอ Claude เท่านั้น** — ไม่สร้างไฟล์