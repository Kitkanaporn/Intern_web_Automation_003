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

# UAT_Notification Workflow

## Files to use

- `instructions/AGENT.md` — workflow overview and instructions
- `SKILL.md` — core logic Phase 0–5
- `shared_config.yaml` — global email and schedule config
- `{project_key}/project_config.yaml` — Jira project config (e.g. `CSD/project_config.yaml`)
- `Map_User_Email.xlsx` — user-to-email mapping (use the "map" sheet)
- `UAT_Template_Email.html` — email HTML template

## Steps

1. Read `instructions/AGENT.md` and `SKILL.md` to load workflow logic.
2. Read `shared_config.yaml` and `{project_key}/project_config.yaml` to get all config values.
3. Connect to Jira and fetch all Epic issues from the CSD project where:
   - UAT Start Date is within the next 5 days, OR
   - today falls within the UAT period (UAT Start ≤ today ≤ UAT End)
4. Cross-reference with `Map_User_Email.xlsx` (sheet: map) to find recipients from service fields.
5. Execute Phase 1–5 as defined in `SKILL.md` — fully automated, no confirmation needed.

## Output rules
- Display results on screen only — do NOT create any files.
- Run fully automatically without asking for confirmation at any step.

### If UAT notifications are needed today:
Display **2 cards**:
1. **Subject card** — email subject line with a Copy button
2. **Email body card** — 3 separate sections, each with its own Copy button:
   - Recipient box (กล่องสีเขียว) — Copy button copies email addresses only (plain text)
   - CC box (กล่องสีส้ม) — Copy button copies CC addresses only (plain text)
   - Email body — Copy button copies HTML body ONLY (must NOT include recipient/CC boxes)

### If no UAT notifications are needed today:
Display a message: "ไม่จำเป็นต้องส่ง UAT notification วันนี้"

## After processing
Post a Jira comment `"UAT Notification Complete"` on every ticket that was included in the notification (notified tickets only).
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

You are running the UAT_Notification Workflow for the CSD Jira project. Execute fully automatically — no confirmation needed at any step.

Workspace folder
All config files are in the user's selected folder (UAT-Notification):

instructions/AGENT.md — workflow overview and instructions
SKILL.md — core logic Phase 0–5
shared_config.yaml — global email and schedule config
CSD/project_config.yaml — Jira project config
Map_User_Email.xlsx — user-to-email mapping (use the "map" sheet)
UAT_Template_Email.html — email HTML template

Steps
Read instructions/AGENT.md and SKILL.md to load workflow logic.
Read shared_config.yaml and CSD/project_config.yaml to get all config values.
Connect to Jira and fetch all Epic issues from the CSD project where:
UAT Start Date is within the next 5 days, OR
today falls within the UAT period (UAT Start ≤ today ≤ UAT End)
Cross-reference with Map_User_Email.xlsx (sheet: map) to find recipients from service fields.
Execute Phase 1–5 as defined in SKILL.md — fully automated, no confirmation needed.

Output rules
Display results on screen only — do NOT create any files.
Run fully automatically without asking for confirmation at any step.
If UAT notifications are needed today:
Display 2 cards:

Subject card — email subject line with a Copy button
Email body card — 3 separate sections, each with its own Copy button:
Recipient box (กล่องสีเขียว) — Copy button copies email addresses only (plain text)
CC box (กล่องสีส้ม) — Copy button copies CC addresses only (plain text)
Email body — Copy button copies HTML body ONLY (must NOT include recipient/CC boxes)
If no UAT notifications are needed today:
Display a message: "ไม่จำเป็นต้องส่ง UAT notification วันนี้"

After processing — Post Jira comment (with duplicate guard)
For every ticket included in the notification:

Fetch the existing comments on that ticket.
Check if any comment with the exact text "UAT Notification Complete" was already posted today (compare comment creation date to today's date, ignoring time).
Only if no such comment exists for today, post a new comment "UAT Notification Complete".
If a comment already exists for today, skip that ticket silently — do NOT post a duplicate.
```

จากนั้นระบบจะทำการสร้างงาน schedule ขึ้นมา

เมื่อสร้างเสร็จแล้ว ให้เข้าไปที่ **Scheduler** ที่ sidebar จะพบงานที่รอดำเนินการตามเวลา

> **แนะนำ:** หากดำเนินการครั้งแรก ให้กด **Run now** โดยเข้าไปที่จุด 3 จุดของงานที่สร้างขึ้นมา จากนั้นกด **Run now**
