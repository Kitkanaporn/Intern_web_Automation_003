# SETUP.md — Phase Setup: กรอก Config ครั้งแรก

> รันเฉพาะตอนที่ config ยังไม่ครบ หลังจากนั้น Claude จะข้ามไป Phase 0 เสมอ
>
> **หลักการ: ถามผู้ใช้เฉพาะสิ่งที่ Claude ไม่มีทางรู้ — ข้อมูลที่ดึงจาก Jira API ได้ ไม่ถาม**

---

## ภาพรวม Flow

```
[ทุกครั้งที่รัน]
       ↓
 Phase Setup ──── มี field ที่ tag #importance ว่างอยู่ไหม? ──→ ไม่มี → Phase 0
       │ (มีว่าง)
       ↓
  Setup 1 ตรวจ config
  Setup 2 ถามข้อมูลที่ auto-detect ไม่ได้
  Setup 3 Auto-detect Jira site
  Setup 4 Auto-detect Project + Fields
  Setup 5 แก้ไข config อัตโนมัติ
  Setup 6 ยืนยัน + เริ่มใช้งาน
       ↓
 Phase 0 → Phase 1 → ... → Phase 6
```

---

## Setup 1 — ตรวจสอบความครบถ้วนของ Config

1. อ่าน `shared_config.yaml` และ `project/project_config.yaml`
2. สแกนทุก field ที่มี comment `#importance`
3. ตรวจว่า field เหล่านั้นมีค่าแล้วหรือยัง:
   - **ทุก field มีค่าแล้ว** → ข้าม Setup ทั้งหมด ไป **Phase 0** ทันที
   - **มี field ว่างอยู่** → แสดงรายการ field ที่ยังว่าง แล้วเริ่ม Setup 2

---

## Setup 2 — ถามข้อมูลที่ยังว่างอยู่

สำหรับแต่ละ field ที่มี `#importance` และยังว่าง:
- ถ้า field นั้น **auto-detect จาก Jira API ได้** → ข้ามไป Setup 3 (ไม่ถาม)
- ถ้า field นั้น **ดึงอัตโนมัติไม่ได้** → ถามผู้ใช้ แล้วเขียนค่าลงไฟล์ทันที

**หลังตอบครบ** → ไป Setup 3

---

## Setup 3 — Auto-detect Jira Site (ไม่ถาม)

เรียก `getAccessibleAtlassianResources`:
- **มี site เดียว** → บันทึก `cloud_id` และ `base_url` ลง `project/project_config.yaml` อัตโนมัติ ไม่ถาม
- **มีหลาย site** → แสดงรายการให้ผู้ใช้เลือก 1 site แล้วบันทึก

---

## Setup 4 — เลือก Project และ Auto-detect Fields

### 4A — เลือก Project (Space)

เรียก `getVisibleJiraProjects` → ได้รายการ project ทั้งหมด

แสดงรายการให้ผู้ใช้เลือกเสมอ ไม่ว่าจะมีกี่ project:
```
พบ {N} projects — เลือก project ที่ต้องการทำงาน:
1. CSD — DRS-CSD
2. ABC — Project ABC
```

บันทึก `project_key` ที่เลือกลง `project/project_config.yaml`

---

### 4B — Auto-detect Promote & Workflow fields

เรียก `searchJiraIssuesUsingJql` ด้วย `fields: ["*all"], expand: "names", maxResults: 3`
แล้ววิเคราะห์ `names` จาก response:

| ค้นหา | keyword | ผลถ้าเจอ | ผลถ้าไม่เจอ |
|---|---|---|---|
| `promote_date` | "Promote" หรือ "Live Date" | บันทึกอัตโนมัติ ไม่ถาม | แสดง date fields ทั้งหมดให้เลือก |
| `workflow_task_id` | "Workflow" หรือ "Task ID" | บันทึกอัตโนมัติ ไม่ถาม | แสดง text fields ทั้งหมดให้เลือก |

---

### 4C — Auto-detect Service fields (สำหรับหา To/CC email)

ใช้ `names` response เดิมจาก 4B ไม่ต้องเรียก API ใหม่:

1. **กรอง** field ที่ชื่อลงท้ายด้วย "Unit", "Service", หรือ "Services"
2. **Match กับ Excel** — เอาชื่อ field ไป match กับคอลัมน์ `Group` ใน `Map_User_Email.xlsx` (case-insensitive) เพื่อยืนยันว่า field นั้นมีรายชื่อคนใน Excel จริง
3. **บันทึก** เฉพาะ field ที่ match ได้ลง `project/project_config.yaml` เป็น `service_fields`:

   ```yaml
   service_fields:
     - "customfield_19036"   # Account Services Unit
     - "customfield_19037"   # Counter Services Unit
     - "customfield_19041"   # CA Service Unit
   ```

4. **ถ้า match ไม่ได้เลย** → แสดง fields ทั้งหมดให้ผู้ใช้เลือกเองว่า field ไหนคือฝ่ายที่เกี่ยวข้อง

> `service_fields` ใช้ใน Phase 3 สำหรับ map To/CC email เท่านั้น — ไม่แสดงเป็นคอลัมน์ในตาราง email

บันทึกทุกค่าลง `project/project_config.yaml` พร้อมเพิ่ม `promote_window_days: 3` (default)

> ต้องการเพิ่ม project อื่น → รันใหม่อีกครั้ง เลือก project อื่น

---

## Setup 5 — แก้ไข Config อัตโนมัติ

ดำเนินการโดยไม่ต้องถาม:

1. **แก้ typo** `workflow_task)id` → `workflow_task_id` ถ้าพบ
2. **แก้** `jira_comment.text` → `"Promote Notification Complete"` ถ้ายังเป็น UAT
3. **บันทึก** ทุกการแก้ไขลงไฟล์ทันที

---

## Setup 6 — ยืนยันและเริ่มใช้งาน

1. แสดง **Summary** ค่าทั้งหมดที่ได้มา (ทั้งที่ถามและที่ดึง API):

   ```
   ✦ project_config ({project_key})
     cloud_id         : 6732a23f-...
     promote_date     : customfield_10854
     workflow_task_id : customfield_10653
     service_fields   : customfield_19036, customfield_19037, ...
     window           : 3 วัน
   ```

2. ถาม: "ข้อมูลถูกต้องไหม? พิมพ์ **ใช่** เพื่อเริ่มใช้งาน หรือบอกช่องที่ต้องการแก้"
   - แก้ → กลับไปถามช่องนั้น แล้วกลับมา Setup 6
   - ใช่ → บันทึกทุกไฟล์ แจ้ง "✓ Setup เสร็จแล้ว"
3. **รัน Phase 0 ต่อทันที** ไม่ต้องรอ
