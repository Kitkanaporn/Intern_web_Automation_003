# Promote Notification Automation

## ภาพรวม

ระบบตรวจสอบ Jira เพื่อหา Epic ที่มี Promote Date กำลังจะถึง แล้วเตรียม email draft พร้อม comment บน Jira โดยอัตโนมัติ สำหรับแจ้งฝ่ายที่เกี่ยวข้องให้เตรียมความพร้อมก่อนการ Promote

---

## วิธีใช้งาน (สำหรับ Claude)

เมื่อผู้ใช้ขอให้รัน Promote Notification:

1. อ่าน `instructions/SETUP.md` — logic Phase Setup
2. อ่าน `SKILL.md` — logic Phase 0–6
3. อ่าน `shared_config.yaml` และ `project/project_config.yaml`
4. รันตาม Phase ตามลำดับ

---

## โครงสร้างไฟล์

```
📁 Promote-Notification/             ← root folder (ชี้ Cowork มาที่นี่)
├── SKILL.md                          ← logic Phase 0–6
├── shared_config.yaml                ← email, schedule — ใช้ร่วมทุก project
├── Map_User_Email.xlsx               ← รายชื่อ member + email
├── Promote_Template_Email.html       ← template email
│
├── 📁 instructions/                  ← คู่มือและ config setup
│   ├── AGENT.md                      ← ไฟล์นี้
│   └── SETUP.md                      ← logic Phase Setup (รันครั้งแรกเท่านั้น)
│
└── 📁 project/
    └── project_config.yaml           ← jira fields ของ project ที่เลือกตอน Setup
```

---

## เพิ่ม Project ใหม่

ไม่ต้องสร้างไฟล์เอง — รัน Promote Notification แล้วเลือก project ใหม่ในขั้นตอน Setup Claude จะ detect fields จาก Jira และสร้าง `project_config.yaml` ให้อัตโนมัติ

---

## Prerequisites

| สิ่งที่ต้องมี | วิธีตรวจสอบ |
|---|---|
| **Jira MCP** เชื่อมต่อแล้ว | Settings → Connections → Atlassian |
| **Map_User_Email.xlsx** อยู่ใน root | sheet ชื่อ `map`, คอลัมน์: Group / Group Mail / Member / Member Mail |
| **Promote_Template_Email.html** อยู่ใน root | ห้ามแก้โครงสร้าง HTML |
| **shared_config.yaml** | Claude ถามและกรอกให้อัตโนมัติครั้งแรก |
| **project/project_config.yaml** | Claude detect จาก Jira และสร้างให้อัตโนมัติ |

---

## ผลลัพธ์ต่อการรัน

- **Summary Table** — แสดงทุก Epic ใน window พร้อมสถานะ (🟡 ยังไม่แจ้ง / ✓ แจ้งแล้ว)
- **Email Card** — หัวข้อ + เนื้อหา พร้อมกรอบ To / CC และปุ่ม Copy แยกตาม Promote Date ไม่ได้ทำออกมาเป็นไฟล์ แต่จะแสดงบนหน้าของ claude เพื่อง่ายในการทำงาน
- **Comment Jira** — "Promote Notification Complete" บน ticket ที่ยังไม่แจ้ง (เมื่อผู้ใช้กด Complete Process button)
- **สรุปผล** — แสดงจำนวน ticket ที่แจ้งแล้วท้าย card เสมอ

---

## หมายเหตุ

- **Excel Group match อัตโนมัติ** — Jira service field display name ตรงกับคอลัมน์ Group ใน Excel
- **Recipients** มาจาก service field ของทุก ticket ใน window (ทั้ง notified + unnotified) แล้ว deduplicate
- **แยก card ตาม Promote Date** — ถ้ามีหลายวันจะได้หลาย card set

---

## สิ่งที่ห้ามทำเด็ดขาด

- **ห้ามแก้ไขไฟล์ใดๆ** ในโฟลเดอร์นี้โดยไม่ได้รับอนุญาต ยกเว้น config ที่ต้องกรอกตอน Setup
- **ห้ามสร้าง HTML ใหม่เอง** — ต้อง replace placeholder ใน template เท่านั้น
- **ห้ามใช้ข้อมูลจาก session ก่อน** — ต้องดึงจาก Jira และอ่านไฟล์ใหม่ทุกครั้ง
- **ห้าม post comment Jira** โดยไม่ได้รับ confirm จากผู้ใช้ก่อน
- **ห้ามส่ง email จริง** — แสดง draft บนหน้าจอ Claude เท่านั้น ผู้ใช้ forward เอง
- **ห้ามสร้างไฟล์ output** — แสดงผลบนหน้าจอ Claude เท่านั้น

---

## การจัดการเมื่อเกิดปัญหา

| ปัญหา | สิ่งที่ต้องทำ |
|---|---|
| หาไฟล์ไม่เจอ (xlsx, html, yaml) | หยุดทันที แจ้งชื่อไฟล์ที่หายไป อย่ารันต่อ |
| Jira API ไม่ตอบสนอง | แจ้งผู้ใช้ว่า Jira ไม่ตอบสนอง ให้ตรวจสอบการเชื่อมต่อ |
| ไม่พบ Epic ใน window | แจ้ง "วันนี้ไม่มี Promote ที่ต้องแจ้ง" แล้วหยุด ไม่ใช่ error |
| config ไม่ครบ | รัน Phase Setup ก่อน ไม่รัน Phase อื่นต่อ |
| Match email ไม่ได้บาง field | แจ้ง warning แต่รันต่อด้วย field ที่ match ได้ |
| Post comment ล้มเหลวบาง ticket | แจ้ง ticket ที่ล้มเหลว แต่รันต่อด้วย ticket อื่น |
