# UAT Notification Automation

## ภาพรวม

ระบบตรวจสอบ Jira ทุกวัน หา Epic ที่มี UAT กำลังจะถึง (ภายใน 5 วัน) หรืออยู่ระหว่าง UAT period แล้วสร้าง email draft พร้อม comment Jira โดยอัตโนมัติ รองรับหลาย Jira project ในโฟลเดอร์เดียว

---

## วิธีใช้งาน (สำหรับ Claude)

เมื่อผู้ใช้ขอให้รัน UAT Notification:

1. อ่าน `SKILL.md` ใน root folder
2. อ่าน `shared_config.yaml` + เลือก project subfolder → อ่าน `{project}/project_config.yaml`
3. ถ้าค่าใดว่าง → อ่าน `instructions/SETUP.md` แล้วทำ First-time Setup
4. ดำเนินการตาม Phase 1–5 โดยไม่ต้องถาม

**ห้ามถาม ไม่ต้องยืนยัน — ทุกอย่างทำอัตโนมัติ**

---

## โครงสร้างไฟล์

```
📁 UAT-Notification/             ← root folder (ชี้ Cowork มาที่นี่)
├── SKILL.md                     ← logic หลัก (Phase 0–5)
├── shared_config.yaml           ← email, schedule, files — ใช้ร่วมทุก project
├── Map_User_Email.xlsx          ← รายชื่อ member + email
├── UAT_Template_Email.html      ← template email
├── 📁 instructions/
│   ├── AGENT.md                 ← ไฟล์นี้
│   └── SETUP.md                 ← First-time Setup (Phase 0C)
├── 📁 project/                  ← project แรก (CSD)
│   └── project_config.yaml     ← jira fields เฉพาะ CSD
└── 📁 [ProjectB]/               ← เพิ่ม project ใหม่ได้เลย
    └── project_config.yaml     ← copy จาก project/ แล้วแก้ค่า
```

---

## เพิ่ม Project ใหม่

1. สร้างโฟลเดอร์ใหม่ใน `UAT-Notification/` (ชื่อ = Project Key)
2. Copy `project/project_config.yaml` ไปวาง
3. กรอก jira fields ของ project นั้น (หรือให้ Claude ถามในครั้งแรกที่รัน)
4. `shared_config.yaml` ไม่ต้องแตะ — ใช้ข้อมูลเดิมได้เลย
5. เมื่อสร้าง folder ให้นำข้อมูลเข้าให้ครบถ้วน
6. เมื่อสร้าง Schedule ให้เอาข้อมูล template และข้อมูลต่างให้ครบ โดยไม่มีการเปลี่ยนแปลงจากไฟล์ประกอบดังกล่าว

---

## Prerequisites

| สิ่งที่ต้องมี | วิธีตรวจสอบ |
|---|---|
| **Jira MCP** เชื่อมต่อแล้ว | Settings → Connections → Atlassian/Jira |
| **Gmail MCP** เชื่อมต่อแล้ว | Settings → Connections → Gmail |
| **Map_User_Email.xlsx** อยู่ใน root | sheet ชื่อ `map`, คอลัมน์: Group / Group Mail / Member / Member Mail |
| **shared_config.yaml** กรอกแล้ว | Claude ถามอัตโนมัติเมื่อรันครั้งแรก |
| **project_config.yaml** กรอกแล้ว | Claude ถามอัตโนมัติต่อ project |

---

## ผลลัพธ์ต่อการรัน

- **สำคัญที่สุด** : คือต้องมีการแจ้งเตือนหากต้องแจ้งเตือนที่มี Unnotification ต้องเขียนบอกว่ามี uat ต้องแจ้ง หากไม่มีก็รันโดยที่บอกว่าวันนี้ไม่มี uat ต้องแจ้ง

- **2 card** — หัวข้อ + เนื้อความ พร้อมปุ่ม Copy (format ติดไปใน Outlook/Gmail)
    - เนื้อความ ขอให้ประกอบด้วย ชื่อเรื่อง ,รายชื่อผู้รับที่ต้องส่งจริงที่มีชื่อใน jira (เป็นกรอบข้อความ), CC:Unit group mail (เป็นกรอบข้อความ) , เนื้อความของเมลที่ต้องส่ง
    - จะไม่ทำออกมาเป็นไฟล์ แต่จะออกมาตรงหน้าจอของ claude 
- **Comment Jira** — "UAT Notification Complete" บน ticket ที่ยังไม่แจ้ง
- แถวสีเหลือง = ticket ใหม่ | แถวสีขาว = แจ้งแล้ว ยังใน window

---

## หมายเหตุ

- **Excel Group match อัตโนมัติ** — Jira field display name ตรงกับคอลัมน์ Group ใน Excel (ไม่ต้อง config เพิ่ม)
- **Test Period cross-month**: `UAT 30/06 - 02/07 2026` | Same month: `UAT 22 - 26/06 2026`
- **Recipients** มาจาก service field ของทุก ticket ใน window (ทั้ง notified + unnotified), deduplicated
