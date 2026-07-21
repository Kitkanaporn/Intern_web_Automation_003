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
├── 📁 UAT-Notification/             ← workflow แจ้ง UAT (Phase 0–5)
│   ├── README.md                    ← คู่มือเฉพาะ UAT Notification
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
├── 📁 Promote_Notification/         ← workflow แจ้ง Promote (Phase 0–6)
│   ├── README.md                    ← คู่มือเฉพาะ Promote Notification
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

เข้าไปในโปรเจคที่สร้างไว้ จากนั้นพิมพ์ `/schedule` ตามด้วยเวลาที่ต้องการให้ดำเนินงาน (รูปแบบ `HH:MM`) แล้วแปะเนื้อหาจากไฟล์ `UAT-Notification/PROMPT.txt` ต่อท้ายในช่องข้อความ

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

เข้าไปในโปรเจคที่สร้างไว้ จากนั้นพิมพ์ `/schedule` ตามด้วยเวลาที่ต้องการให้ดำเนินงาน (รูปแบบ `HH:MM`) แล้วแปะเนื้อหาจากไฟล์ `Promote_Notification/PROMPT.txt` ต่อท้ายในช่องข้อความ

จากนั้นระบบจะทำการสร้างงาน schedule ขึ้นมา

เมื่อสร้างเสร็จแล้ว ให้เข้าไปที่ **Scheduler** ที่ sidebar จะพบงานที่รอดำเนินการตามเวลา

> **แนะนำ:** หากดำเนินการครั้งแรก ให้กด **Run now** โดยเข้าไปที่จุด 3 จุดของงานที่สร้างขึ้นมา จากนั้นกด **Run now**
