# ระบบการแจ้งเตือน UAT และ Promote ด้วย Claude AI

## ภาพรวมของระบบ

ระบบนี้ใช้ Claude AI ร่วมกับ Jira เพื่อดึงข้อมูล Epic ที่มีกำหนด UAT หรือ Promote Date ที่กำลังจะถึง จากนั้นสร้าง Draft Email อัตโนมัติสำหรับแจ้งฝ่ายที่เกี่ยวข้อง โดยทำงานตามเวลาที่กำหนดผ่าน Scheduled Work ของ Claude โดยไม่ต้องดำเนินการด้วยตนเอง

---

## รายละเอียดของ Fields ใน JIRA Ticket

ส่วนสำคัญใน JIRA Ticket ที่ Claude ใช้ดึงข้อมูลเพื่อสร้าง Draft Mail

- **Text block**
  - Workflow Main Task
- **Period time**
  - Promote Date
  - UAT Start Date
  - UAT End Date
- **Service Units** (Checklist block)
  - Account Services Unit
  - Counter Services Unit
  - Issuer Services Unit
  - Investor Service Unit
  - CA Service Unit
  - Distribution Unit

---

## การเชื่อมต่อ Claude เข้ากับ JIRA

**ขั้นตอนการเชื่อมต่อ Jira**

1. คลิกที่ account → **Settings** (บริเวณซ้ายล่างของหน้าต่าง Claude application)
2. คลิก **Connectors** ที่ sidebar → คลิก **Customize**
3. หา **Atlassian Rovo** ในช่อง Connectors จากนั้นคลิกเพื่อ connect
   - หากไม่พบ Atlassian ROVO สามารถแก้ไขได้ดังนี้:
     - กดปุ่ม `+` (บวก) บริเวณด้านขวาของ sidebar เพื่อเปิดหน้า Directory
     - ค้นหา "Atlassian ROVO" และคลิกเข้าไป
     - > **หมายเหตุ:** หากติด Request ให้กด Request และติดต่อแผนก Service Desk เพื่อปลดล็อก
4. ระบบจะเปิดหน้า browser ของ Atlassian จากนั้นเลื่อนลงด้านล่างสุด และกดยินยอมการเข้าถึงของ AI ในการอ่าน/เขียน JIRA

> **หมายเหตุ:** หากไม่มีการเชื่อมต่อกับ Jira ระบบจะแจ้งเตือนว่า `เชื่อมต่อ Jira ไม่ได้` และหยุดการทำงานทันที

---

## โครงสร้างไฟล์ในโปรเจค

```
📁 08_Test_UAT_DOCKER_AUTOMATION/
├── README.md                        ← คู่มือหลัก (ไฟล์นี้)
├── 📁 UAT-Notification/             ← workflow แจ้ง UAT
│   ├── SKILL.md
│   ├── PROMPT.txt
│   ├── shared_config.yaml
│   ├── Map_User_Email.xlsx
│   ├── UAT_Template_Email.html
│   ├── 📁 instructions/
│   │   ├── AGENT.md
│   │   └── SETUP.md
│   └── 📁 project/
│       └── project_config.yaml
├── 📁 Promote_Notification/         ← workflow แจ้ง Promote
│   ├── SKILL.md
│   ├── PROMPT.txt
│   ├── shared_config.yaml
│   ├── Map_User_Email.xlsx
│   ├── Promote_Template_Email.html
│   ├── 📁 instructions/
│   │   ├── AGENT.md
│   │   └── SETUP.md
│   └── 📁 project/
│       └── project_config.yaml

```

---

## การตั้งค่าและใช้งาน Claude Cowork — Scheduled Work

**Download:** `https://github.com/Kitkanaporn/Intern_web_Automation_003.git`

---

### UAT Notification

#### 1. สร้าง Project สำหรับ UAT Notification

1. คลิกที่ **Projects** → กดปุ่ม **New Project**
2. ในหน้าต่าง **Create a new project** จะมี 3 ตัวเลือก:
   - **Start from scratch** — เปิดโปรเจคในโฟลเดอร์หลักของ Claude และเพิ่มไฟล์เอง
   - **Import a project** — เชื่อมต่อกับ Project ของ Claude Chat
   - **Use an existing folder** — เชื่อมต่อกับ folder ในเครื่อง *(แนะนำ)*
3. เลือก **Use an existing folder** → เลือก folder ชื่อ `UAT-Notification` จากนั้นตั้งชื่อโปรเจค

   เป็นอันเสร็จสิ้นการเชื่อม Project Claude เข้ากับ folder ภายในเครื่อง

#### 2. สร้าง Scheduled UAT Notification

เข้าไปในโปรเจคที่สร้างไว้ จากนั้นใส่ Prompt นี้ในช่องข้อความ

> บริเวณ `xxx` ที่ส่วนหัวนั้นเป็นส่วนสำหรับใส่เวลาที่ต้องการให้ดำเนินงาน ในรูปแบบ `HH:MM`

```
/schedule   xxx

You are executing the UAT Notification Workflow for the CSD Jira project. Run fully automatically — no confirmation, no questions, no pauses at any step.

WORKSPACE: All files are in the UAT-Notification/ folder.
- SKILL.md — core logic (Phase 0–5)
- shared_config.yaml — global email config
- project/project_config.yaml — Jira project config
- Map_User_Email.xlsx — user-to-email mapping (sheet: map)
- UAT_Template_Email.html — email HTML template

EXECUTION: Read SKILL.md then execute Phase 0–5 exactly as defined. Do not deviate.

PHASE 0 (mandatory before anything else):
- Read shared_config.yaml + project/project_config.yaml
- Jira fields empty → auto-detect from Jira API, write to config, continue
- email.sender_email / sender_name / sender_phone empty → DO NOT STOP, DO NOT ASK, continue immediately with placeholders [ชื่อผู้ส่ง] / [เบอร์โทร] / [sender@set.or.th] in output
- RULE: Empty sender fields are NEVER a reason to stop or ask. Always proceed to Phase 1.

OUTPUT: Screen only. Do not create files.
- Notifications needed → show 2 cards (Subject + Email body with 3 separate Copy buttons: To, CC, HTML body)
- No notifications needed → show: "✅ วันนี้ไม่มี UAT ต้องแจ้ง — ticket ทั้งหมดได้รับการแจ้งเตือนแล้ว ({today})"

TICKET SKIP RULE — apply per ticket before Phase 2 (CRITICAL, no exceptions):
Skip a ticket ONLY when BOTH conditions are true:
  (1) ticket has a comment whose body contains the jira_comment.text value, AND
  (2) DATE(that comment's created) < DATE(today)   ← strictly before today

All other cases → include the ticket in output:
  • No matching comment exists → INCLUDE
  • Matching comment exists but DATE(created) = DATE(today) → INCLUDE  (same-day rerun)

"A comment was posted today" is NOT a reason to skip. Only a comment from a previous day qualifies as skip.
If ≥1 ticket is included → run Phase 2 and Phase 3. Do not stop early.

POST COMMENT (Phase 4 only): For each included ticket — call addCommentToJiraIssue ONLY IF no matching comment with DATE(created) = DATE(today) exists. If already commented today → skip silently, continue.
```

จากนั้นระบบจะทำการสร้างงาน schedule ขึ้นมา

เมื่อสร้างเสร็จแล้ว ให้เข้าไปที่ **Scheduler** ที่ sidebar จะพบงานที่รอดำเนินการตามเวลา

> **แนะนำ:** หากดำเนินการครั้งแรก ให้กด **Run now** โดยเข้าไปที่จุด 3 จุดของงานที่สร้างขึ้นมา จากนั้นกด **Run now**

---

### Promote Notification

#### 1. สร้าง Project สำหรับ Promote Notification

1. คลิกที่ **Projects** → กดปุ่ม **New Project**
2. ในหน้าต่าง **Create a new project** จะมี 3 ตัวเลือก:
   - **Start from scratch** — เปิดโปรเจคในโฟลเดอร์หลักของ Claude และเพิ่มไฟล์เอง
   - **Import a project** — เชื่อมต่อกับ Project ของ Claude Chat
   - **Use an existing folder** — เชื่อมต่อกับ folder ในเครื่อง *(แนะนำ)*
3. เลือก **Use an existing folder** → เลือก folder ชื่อ `Promote_Notification` จากนั้นตั้งชื่อโปรเจค

   เป็นอันเสร็จสิ้นการเชื่อม Project Claude เข้ากับ folder ภายในเครื่อง

#### 2. สร้าง Scheduled Promote Notification

เข้าไปในโปรเจคที่สร้างไว้ จากนั้นใส่ Prompt นี้ในช่องข้อความ

> บริเวณ `xxx` ที่ส่วนหัวนั้นเป็นส่วนสำหรับใส่เวลาที่ต้องการให้ดำเนินงาน ในรูปแบบ `HH:MM`

```
/schedule   xxx

# Promote Notification Workflow

## Files to Use

Use only the following files:

* `instructions/AGENT.md` — overview and project instructions
* `SKILL.md` — first-time setup logic and operation phases from Phase 0 to Phase 6
* `shared_config.yaml` — global email and schedule configuration
* `project/project_config.yaml` — Jira project configuration
* `Map_User_Email.xlsx` — user and email mapping file, using the `map` sheet
* `Promote_Template_Email.html` — HTML email template

## Steps

1. Read `instructions/AGENT.md` and `SKILL.md` to load the workflow logic.
2. Read `shared_config.yaml` and `project/project_config.yaml` to get all configuration values.
   2.1. If any field tagged `#importance` is empty, run Phase Setup before proceeding.
3. Connect to Jira and fetch all Epic issues from the configured project where today is within the Promote notification window:
   `Promote Date - 3 days <= today < Promote Date`
   Only include Epic issues that have not been notified yet. An Epic is considered notified if it already contains the Jira comment:
   `"Promote Notification Complete"`
4. Cross-reference each Epic with `Map_User_Email.xlsx` to find the email addresses of the service units referenced by the Jira service fields.
5. Execute Phase 0–6 as defined in `SKILL.md`.
6. Run the workflow fully automatically after the initial setup is completed. User input is required only during the initial setup when required configuration values are missing.

## Output Rules

1. Display the result on screen only. Do not generate output files. Do not make artifact too illustate result in screen cowork only.
2. Do not ask for confirmation during the workflow execution, except for the initial setup step when required configuration values are missing.

## If Promote Notifications Are Needed Today
If Promote Notifications are needed for more than one Promote Date, separate the email drafts by Promote Date.

Example:
* 22/06 has 2 Epics
* 23/06 has 3 Epics

The system must create 2 separate sets of email draft cards, one set for each Promote Date.
Each set must display 4 cards:

1. Subject
   * Shows subject name and copy button
2. Recipients Card
   * Shows the email addresses of the responsible service units
   * Includes a Copy button
   * The box color should be green
3. CC units
   * Shows the email addresses in file `shared_config` in `cc_email` field
   * Includes a Copy button
4. Full Email Body Card
   * Shows the full rendered HTML email body from `Promote_Template_Email.html`
   * Includes a Copy button
   * The Copy button must copy the full rendered HTML content, including the email template formatting, not plain text only

## If No Promote Notifications Are Needed Today
Display this message:
`วันนี้ไม่มีรายการที่ต้องส่ง Promote Notification`

## After Processing
After displaying the result, show a summary section with a `Complete Process` button.
When the user clicks `Complete Process`, post the Jira comment: `"Promote Notification Complete"` on every ticket that was included in the notification
```

จากนั้นระบบจะทำการสร้างงาน schedule ขึ้นมา

เมื่อสร้างเสร็จแล้ว ให้เข้าไปที่ **Scheduler** ที่ sidebar จะพบงานที่รอดำเนินการตามเวลา

> **แนะนำ:** หากดำเนินการครั้งแรก ให้กด **Run now** โดยเข้าไปที่จุด 3 จุดของงานที่สร้างขึ้นมา จากนั้นกด **Run now**
