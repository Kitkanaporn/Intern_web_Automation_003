# UAT Notification Automation

ระบบแจ้งเตือน UAT อัตโนมัติ — ตรวจสอบ Jira ทุกวัน หา Epic ที่กำลังเข้าสู่ช่วง UAT แล้วสร้าง email draft พร้อม comment Jira โดยไม่ต้องทำอะไรด้วยตัวเอง

---

## การทำงาน

ทุกวันระบบจะดึง Epic จาก Jira ที่อยู่ในเงื่อนไขใดเงื่อนไขหนึ่ง:
- **กำลังจะถึง UAT** — UAT Start Date อยู่ในอีก 5 วันข้างหน้า
- **อยู่ระหว่าง UAT** — วันนี้อยู่ระหว่าง UAT Start ถึง UAT End

จากนั้นตรวจว่า ticket ไหน "ยังไม่แจ้ง" โดยดูจาก Jira comment — ถ้ามี comment ว่า `UAT Notification Complete` ที่สร้างก่อนวันนี้ถือว่าแจ้งแล้ว ถ้า comment เพิ่งสร้างวันนี้หรือไม่มีเลยถือว่ายังไม่แจ้ง (รีรันได้ในวันเดิม)

สำหรับ ticket ที่ยังไม่แจ้ง ระบบจะ:
1. ดึงรายชื่อผู้รับจาก `Map_User_Email.xlsx` ตาม service field ของแต่ละ ticket
2. สร้าง email subject และ email body จาก template
3. แสดง 2 card บนหน้าจอพร้อมปุ่ม Copy (ไม่ส่งอัตโนมัติ — ผู้ใช้ copy ไปวางใน Outlook เอง)
4. comment `UAT Notification Complete` บน Jira ticket ทุกตัวที่แจ้งในรอบนี้

---

## โครงสร้างไฟล์

```
📁 UAT-Notification/
├── SKILL.md                     ← logic หลัก (Phase 0–5)
├── PROMPT.txt                   ← prompt สำหรับ Scheduled Task
├── shared_config.yaml           ← config ร่วมทุก project (email, schedule)
├── Map_User_Email.xlsx          ← รายชื่อ member + email แยกตาม unit
├── UAT_Template_Email.html      ← template HTML ของ email
├── 📁 instructions/
│   ├── AGENT.md                 ← overview และวิธีใช้งาน
│   └── SETUP.md                 ← ขั้นตอน first-time setup (Phase 0C)
└── 📁 project/
    └── project_config.yaml      ← config เฉพาะ project CSD
```

---

## วิธีใช้งาน

**รันครั้งแรก** — Claude จะถามข้อมูลที่จำเป็นและกรอก config ให้อัตโนมัติ ไม่ต้องแก้ไฟล์เอง

**รันปกติ** — พิมพ์ใน Cowork:
```
/jira-uat-daily-reminder
```
หรือรันอัตโนมัติทุกวันตามเวลาที่ตั้งไว้ใน `shared_config.yaml`

---

## สิ่งที่ต้องเชื่อมต่อก่อนใช้งาน

| สิ่งที่ต้องมี | วิธีตรวจสอบ |
|---|---|
| Jira (Atlassian) MCP | Settings → Connections → Atlassian |
| Gmail MCP | Settings → Connections → Gmail |

---

## ผลลัพธ์ต่อการรัน

- **มี ticket ที่ต้องแจ้ง** → แสดง 2 card พร้อมปุ่ม Copy: หัวข้อ email + เนื้อความ (พร้อม To/CC) และ comment "UAT Notification Complete" บน Jira ticket นั้น
- **ไม่มี ticket ที่ต้องแจ้ง** → แสดงข้อความแจ้งว่าวันนี้ไม่มี UAT ต้องส่ง

---

## เพิ่ม Project ใหม่

1. สร้างโฟลเดอร์ใหม่ชื่อ Project Key (เช่น `ABC/`)
2. Copy `project/project_config.yaml` ไปวาง
3. รัน skill ตามปกติ — Claude จะ detect และถาม config ของ project ใหม่ให้อัตโนมัติ
