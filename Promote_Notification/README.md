# Promote Notification Automation

ระบบอัตโนมัติสำหรับตรวจสอบ Jira และเตรียม email draft แจ้งฝ่ายที่เกี่ยวข้องก่อนการ Promote ระบบ

---

## ภาพรวม

ระบบจะดึง Epic จาก Jira ที่มี Promote Date อยู่ใน window (default 3 วัน) แล้วสร้าง email draft พร้อม Subject และ CC โดยอัตโนมัติ จากนั้น post comment "Promote Notification Complete" บน ticket ที่แจ้งแล้ว

---

## โครงสร้างไฟล์

```
📁 Promote-Notification/
├── SKILL.md                        ← logic หลัก Phase 0–6
├── shared_config.yaml              ← config ร่วม (draft_to, exclude_recipients)
├── Map_User_Email.xlsx             ← รายชื่อ member + email แยกตาม Group
├── Promote_Template_Email.html     ← template email (ห้ามแก้โครงสร้าง)
│
├── 📁 instructions/
│   ├── AGENT.md                    ← คู่มือภาพรวมและกฎการใช้งาน
│   └── SETUP.md                    ← logic Phase Setup (รันครั้งแรกเท่านั้น)
│
└── 📁 CSD/
    └── project_config.yaml         ← Jira fields เฉพาะ project CSD
```

---

## Prerequisites

| สิ่งที่ต้องมี | รายละเอียด |
|---|---|
| **Jira MCP** เชื่อมต่อแล้ว | Settings → Connections → Atlassian |
| **Map_User_Email.xlsx** | sheet ชื่อ `map`, คอลัมน์: Group / Group Mail / Member / Member Mail |
| **Promote_Template_Email.html** | อยู่ใน root folder |
| **shared_config.yaml** | Claude กรอกให้อัตโนมัติตอน Setup ครั้งแรก |
| **project_config.yaml** | Claude detect จาก Jira และสร้างให้อัตโนมัติ |

---

## วิธีใช้งาน

พิมพ์ใน Claude: **"รัน Promote Notification"**

Claude จะดำเนินการตาม Phase อัตโนมัติ:

| Phase | สิ่งที่เกิดขึ้น |
|---|---|
| **Setup** | กรอก config ครั้งแรก (ข้ามถ้า config ครบแล้ว) |
| **Phase 0** | โหลด config, Excel, template เข้า memory |
| **Phase 1** | Query Jira หา Epic ใน window |
| **Phase 2** | แยก ticket ที่แจ้งแล้ว vs ยังไม่แจ้ง |
| **Phase 3** | Map service fields → email จาก Excel |
| **Phase 4** | แสดง email card บนหน้าจอ (Subject + CC + เนื้อหา) |
| **Phase 5** | Post comment บน Jira (ต้อง confirm ก่อน) |
| **Phase 6** | แสดงสรุปผล |

---

## ผลลัพธ์

- **Summary Table** — รายการ Epic ทั้งหมดใน window พร้อมสถานะ
- **Email Card** — Subject + CC + เนื้อหา พร้อมปุ่ม Copy แยกตาม Promote Date
- **Jira Comment** — "Promote Notification Complete" บน ticket ที่ยังไม่แจ้ง
- **สรุปผล** — จำนวน ticket ที่แจ้งแล้วท้าย session

> ทุก output แสดงบนหน้าจอ Claude เท่านั้น — ไม่สร้างไฟล์ ไม่ส่ง email จริง

---

## เพิ่ม Project ใหม่

รัน Promote Notification แล้วเลือก project ใหม่ในขั้นตอน Setup — Claude จะ detect fields จาก Jira และสร้าง `project_config.yaml` ให้อัตโนมัติ

---

## ข้อควรระวัง

- **ห้ามแก้โครงสร้าง** `Promote_Template_Email.html`
- **ห้าม post comment** โดยไม่ confirm กับผู้ใช้ก่อน
- **ห้ามใช้ข้อมูลจาก session ก่อน** — ดึงจาก Jira ใหม่ทุกครั้ง
