# PHASE 0C — First-time Setup (รันครั้งแรกเท่านั้น)

**หลักการ: Claude ดึงข้อมูลจาก Jira เองให้มากที่สุด — ถามผู้ใช้เฉพาะสิ่งที่ Claude ไม่มีทางรู้**

---

#### ส่วน A — Shared Config (ถาม — Claude ไม่รู้ข้อมูลส่วนตัว)

ถามครั้งเดียว ใช้ได้ทุก project → บันทึกลง `shared_config.yaml` ทันที:
```
1. Email ของผู้ส่ง (ต้องเป็น email ขององค์กร): ___
2. ชื่อผู้ส่ง: ___
3. เบอร์โทรศัพท์: ___
4. เวลาที่ต้องการให้รันทุกวัน (HH:MM เช่น 16:15): ___
```
*(ฝ่าย/แผนก และ องค์กร ตั้งค่าไว้ถาวรแล้วใน shared_config.yaml — ไม่ต้องถาม)*

---

#### ส่วน B — Project Config (AUTO-DETECT จาก Jira API)

**B1 — Auto-detect Jira site (cloud_id + base_url)**

เรียก `getAccessibleAtlassianResources`:
- ถ้ามี site เดียว → ใช้อัตโนมัติ ไม่ถาม
- ถ้ามีหลาย site → แสดงรายการให้เลือก 1 site

บันทึก `cloud_id` และ `base_url` ทันที

---

**B2 — เลือก project (1 ครั้ง = 1 space)**

เรียก `getVisibleJiraProjects` → ได้รายการ projects ทั้งหมดที่เข้าถึงได้

**ถ้ามี project เดียว** → ใช้อัตโนมัติ ไม่ถาม ดำเนินการ B3 ทันที

**ถ้ามีหลาย project** → แสดงรายการให้เลือก 1 project:
```
พบ {N} projects — กรุณาพิมพ์หมายเลขที่ต้องการตั้งค่า:
1. CSD — DRS-CSD
2. ABC — Project ABC
...
```

- รับคำตอบ → ได้ project key 1 ตัว
- สร้างโฟลเดอร์ `{project_key}/` พร้อม `project_config.yaml`
- ดำเนินการ B3–B5 สำหรับ project นี้

> ต้องการตั้งค่า space อื่น → รันใหม่อีกครั้ง เลือก project อื่น

---

**B3 — Auto-detect UAT fields**

เรียก `searchJiraIssuesUsingJql`:
- jql: `project = "{project_key}" AND issuetype = Epic ORDER BY created DESC`
- fields: `["*all"]`, expand: `"names"`
- maxResults: 3

วิเคราะห์ `names` จาก response:
- หา fields ที่ชื่อมีคำว่า **"UAT"** → เรียงตามชื่อ (Start ก่อน End)
  - ถ้าหาเจอทั้งคู่ → บันทึก `uat_start` / `uat_end` อัตโนมัติ ไม่ถาม
  - ถ้าหาได้แค่บางส่วน → แสดง date fields ทั้งหมดให้ user ระบุ
- หา fields ที่ชื่อมีคำว่า **"Workflow"** หรือ **"Task ID"** → บันทึก `workflow_task_id` อัตโนมัติ
  - ถ้าหาไม่เจอ → แสดง fields ที่เกี่ยวข้องให้ user เลือก

---

**B4 — Auto-detect service fields**

จาก `names` response เดิม:
1. กรองหา fields ที่ชื่อลงท้ายด้วย **"Unit"** หรือ **"Services"** หรือ **"Service"**
2. อ่าน Excel `Map_User_Email.xlsx` sheet `map` คอลัมน์ `Group`
3. Match field display name กับ Excel Group (case-insensitive) → ได้ service field list
4. สร้าง proposed `table_column` โดย: ตัด "Unit" suffix + trim (เช่น "Account Services Unit" → "Account service")
5. แสดง proposed mapping ให้ user ยืนยัน/แก้ table_column names:

```
[{project_key}] พบ Service fields อัตโนมัติ — ยืนยัน/แก้ชื่อคอลัมน์ในตาราง UAT email:
  customfield_19036 (Account Services Unit)  → "Account service"  [Enter = ใช้เลย / พิมพ์ชื่อใหม่]
  customfield_19037 (Counter Services Unit)  → "Counter Service"
  ...
```

บันทึก service_fields ทันทีหลัง user ยืนยัน

---

**B5 — เขียน project_config.yaml**

เขียนลงไฟล์ `{project_key}/project_config.yaml` แล้วแจ้ง:
> ✅ ตั้งค่า {project_key} เสร็จแล้ว — พร้อมใช้งานทันที

จากนั้นดำเนินการต่อ Phase 1 โดยไม่ต้องถามซ้ำอีก
