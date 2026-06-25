# SKILL.md — Promote Notification Automation

ไฟล์นี้คือ logic หลักทั้งหมดของระบบ Claude จะอ่านและทำตามทุก Phase ตามลำดับ

---

## ⛔ กฎห้ามฝ่าฝืนเด็ดขาด ⛔

1. ต้องอ่าน `AGENT.md` และ `SKILL.md` ให้เข้าใจก่อนรันทุกครั้ง
2. ต้องดึงข้อมูลใหม่จาก Jira ก่อนรันทุกครั้ง — ห้ามใช้ข้อมูล ticket จาก session ก่อน
3. ต้องอ่าน `shared_config.yaml` และ `project_config.yaml` ก่อนรันทุกครั้ง
4. ห้ามแก้ไขไฟล์ใดๆ ในโฟลเดอร์นี้โดยไม่ได้รับอนุญาตจากผู้ดูแลระบบ
5. ห้ามสร้างโครงสร้าง HTML ขึ้นมาใหม่เอง — ต้องอ่าน `Promote_Template_Email.html` ทุกครั้ง และ replace placeholder เท่านั้น โดยเอา template มาใช้เลย
6. ห้ามใช้รายชื่อ/email จาก session ก่อน — ต้องอ่าน `Map_User_Email.xlsx` ใหม่ทุกครั้ง
7. Output บนหน้าจอ Claude เท่านั้น — ไม่สร้างไฟล์
8. ต้องแยก card หากจับ Promote Date ได้ต่างวันกัน

---

## ภาพรวม Flow

```
[ทุกครั้งที่รัน]
       ↓
 Phase Setup ──── draft_to ใน shared_config มีค่าแล้วไหม? ──→ มีแล้ว → Phase 0
       │ (ยังว่าง)
       ↓
  Setup 1 ตรวจ config
  Setup 2 ถาม draft_to
  Setup 3 Auto-detect Jira site
  Setup 4 Auto-detect Project + Fields
  Setup 5 แก้ไข config อัตโนมัติ
  Setup 6 ยืนยัน + เริ่มใช้งาน
       ↓
 Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
```

---

## PHASE SETUP — กรอก Config ครั้งแรก (รันครั้งเดียว)

> รันเฉพาะตอนที่ config ยังไม่ครบ หลังจากนั้น Claude จะข้ามไป Phase 0 เสมอ
>
> **หลักการ: ถามผู้ใช้เฉพาะสิ่งที่ Claude ไม่มีทางรู้ — ข้อมูลที่ดึงจาก Jira API ได้ ไม่ถาม**

---

### Setup 1 — ตรวจสอบความครบถ้วนของ Config

1. อ่าน `shared_config.yaml`
2. ตรวจว่า `draft_to` มีค่าแล้วหรือยัง:
   - **มีค่าแล้ว** → ข้าม Setup ทั้งหมด ไป **Phase 0** ทันที
   - **ยังว่างอยู่** → เริ่ม Setup 2

---

### Setup 2 — ถามข้อมูลที่ยังว่างอยู่

ถามเฉพาะช่องที่ยังว่าง:

| ช่อง | คำถาม | เงื่อนไข |
|---|---|---|
| `draft_to` | "Email สำหรับรับ Draft ก่อน Forward จริง?" | ต้องเป็น `@set.or.th` |

**หลังตอบครบ** → เขียนค่าลง `shared_config.yaml` ทันที แล้วไป Setup 3

---

### Setup 3 — Auto-detect Jira Site (ไม่ถาม)

เรียก `getAccessibleAtlassianResources`:
- **มี site เดียว** → บันทึก `cloud_id` และ `base_url` ลง `project_config.yaml` อัตโนมัติ ไม่ถาม
- **มีหลาย site** → แสดงรายการให้ผู้ใช้เลือก 1 site แล้วบันทึก

---

### Setup 4 — เลือก Project และ Auto-detect Fields

**4A — เลือก Project**

เรียก `getVisibleJiraProjects` → ได้รายการ project ทั้งหมด

- **มี project เดียว** → ใช้อัตโนมัติ ไม่ถาม
- **มีหลาย project** → แสดงรายการให้เลือก:
  ```
  พบ {N} projects — เลือก project ที่ต้องการตั้งค่า:
  1. CSD — DRS-CSD
  2. ABC — Project ABC
  ```

---

**4B — Auto-detect Promote & Workflow fields**

เรียก `searchJiraIssuesUsingJql` ด้วย `fields: ["*all"], expand: "names", maxResults: 3`
แล้ววิเคราะห์ `names` จาก response:

| ค้นหา | keyword | ผลถ้าเจอ | ผลถ้าไม่เจอ |
|---|---|---|---|
| `promote_date` | "Promote" หรือ "Live Date" | บันทึกอัตโนมัติ ไม่ถาม | แสดง date fields ทั้งหมดให้เลือก |
| `workflow_task_id` | "Workflow" หรือ "Task ID" | บันทึกอัตโนมัติ ไม่ถาม | แสดง text fields ทั้งหมดให้เลือก |

---

**4C — Auto-detect Service fields (สำหรับหา To/CC email)**

ใช้ `names` response เดิมจาก 4B ไม่ต้องเรียก API ใหม่:

1. **กรอง** field ที่ชื่อลงท้ายด้วย "Unit", "Service", หรือ "Services"
2. **Match กับ Excel** — เอาชื่อ field ไป match กับคอลัมน์ `Group` ใน `Map_User_Email.xlsx` (case-insensitive) เพื่อยืนยันว่า field นั้นมีรายชื่อคนใน Excel จริง
3. **บันทึก** เฉพาะ field ที่ match ได้ลง `project_config.yaml` เป็น `service_fields`:

   ```yaml
   service_fields:
     - "customfield_19036"   # Account Services Unit
     - "customfield_19037"   # Counter Services Unit
     - "customfield_19041"   # CA Service Unit
   ```

4. **ถ้า match ไม่ได้เลย** → แสดง fields ทั้งหมดให้ผู้ใช้เลือกเองว่า field ไหนคือฝ่ายที่เกี่ยวข้อง

> `service_fields` ใช้ใน Phase 3 สำหรับ map To/CC email เท่านั้น — ไม่แสดงเป็นคอลัมน์ในตาราง email

---

บันทึกทุกค่าลง `{project_key}/project_config.yaml` พร้อมเพิ่ม `promote_window_days: 3` (default)

> ต้องการเพิ่ม project อื่น → รันใหม่อีกครั้ง เลือก project อื่น

---

### Setup 5 — แก้ไข Config อัตโนมัติ

ดำเนินการโดยไม่ต้องถาม:

1. **แก้ typo** `workflow_task)id` → `workflow_task_id` ถ้าพบ
2. **แก้** `jira_comment.text` → `"Promote Notification Complete"` ถ้ายังเป็น UAT
3. **บันทึก** ทุกการแก้ไขลงไฟล์ทันที

---

### Setup 6 — ยืนยันและเริ่มใช้งาน

1. แสดง **Summary** ค่าทั้งหมดที่ได้มา (ทั้งที่ถามและที่ดึง API):

   ```
   ✦ shared_config
     draft_to : xxx@set.or.th

   ✦ project_config (CSD)
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

---

## PHASE 0 — Bootstrap

> โหลด config และข้อมูลทั้งหมดเข้าหน่วยความจำ ทำครั้งเดียวต่อการรัน

1. อ่าน `shared_config.yaml` → เก็บ: draft_to, jira_comment text, exclude_recipients
2. อ่าน `project_config.yaml` ทุกไฟล์ใน subfolder → เก็บ: cloud_id, project_key, customfield IDs, promote_window_days, service_fields
3. โหลด `Map_User_Email.xlsx` sheet `map` → สร้าง lookup table:
   ```
   Group (fill-down) → { group_mail, members: [ { name, email } ] }
   ```
4. โหลด `Promote_Template_Email.html` → เก็บเป็น template string

**Edge cases:**
- ถ้าหาไฟล์ไม่เจอ → หยุดทันที แจ้งชื่อไฟล์ที่หายไปชัดเจน
- ถ้า shared_config มีช่องว่างที่บังคับ → แจ้งให้รัน Setup ก่อน

---

## PHASE 1 — Query Jira

> หา Epic ทุกตัวที่ Promote Date อยู่ใน window

**คำนวณ window:**
```
today      = วันที่รัน
window_end = today + promote_window_days (จาก project_config, default = 3)
```

**JQL:**
```
project = {project_key}
AND issuetype = Epic
AND cf[{promote_date_field}] >= "{today}"
AND cf[{promote_date_field}] <= "{window_end}"
ORDER BY cf[{promote_date_field}] ASC
```

**Fields ที่ดึง:**
- `summary` — ชื่อ Epic
- `workflow_task_id` (จาก config) — IT Workflow Task ID
- `promote_date` (จาก config) — Promote Date
- service_fields ทุกตัวจาก `project_config.yaml` — ใช้ map To/CC ใน Phase 3
- `comment` — ใช้ใน Phase 2

**เก็บผลลัพธ์เป็น lookup table:**
```
promote_date → [ { epic_key, workflow_task_id, summary } ]
```
เพื่อให้ Phase 4 แยก card ตามวันได้ถูกต้อง

**Edge cases:**
- ไม่มี Epic ใน window เลย → แสดง "วันนี้ไม่มี Promote ที่ต้องแจ้ง" แล้วหยุด

---

## PHASE 2 — แยก Notified vs Unnotified

> เช็คแต่ละ ticket ว่าเคยแจ้งแล้วหรือยัง

สำหรับแต่ละ Epic ที่ได้จาก Phase 1:

1. แสดง **Summary Table** ก่อนดำเนินการต่อ:

   | Epic | Workflow Task ID | Promote Date | สถานะ |
   |---|---|---|---|
   | ชื่อ Epic | WF-XXXXX | วันที่ | 🟡 ยังไม่แจ้ง / ✓ แจ้งแล้ว |

**Edge cases:**
- ทุก ticket แจ้งครบหมดแล้ว → แจ้ง "แจ้งครบทุก Epic ใน window แล้ว" แล้วหยุด
- **สำคัญ**: Recipients ใน email ต้องรวมจาก **ทุก ticket** ใน window (ทั้ง NOTIFIED + UNNOTIFIED) แล้วค่อย deduplicate

---

## PHASE 3 — Map Recipients

> แปลง service fields จาก Jira → email จาก Excel

**สร้าง 2 structure จาก Excel:**
```
group_members = { "Account Services Unit": [name, name, ...], ... }
group_mail    = { "Account Services Unit": "AccountServicesUnit@set.or.th", ... }
```

**Auto-match Jira field → Excel Group:**

สำหรับแต่ละ Epic ใน window (รวมทั้ง NOTIFIED):

1. ดึงค่าจาก `service_fields` ทุกตัวใน `project_config.yaml` โดยต้องการแบ่งออกมาตามวันที่ promote เพราะไม่ได้ส่งเหมือนกันหากต้องส่งมากกว่า 1 card
2. Match display name ของแต่ละ field กับคอลัมน์ `Group` ใน Excel (case-insensitive)
3. ผลลัพธ์ต่อ Group ที่ match:
   - **CC** = Group Mail ของกลุ่มนั้น (คั่นด้วย `;`)
4. รวม recipient จากทุก Epic และทุก service field แล้ว **deduplicate**
5. ลบ email ที่อยู่ใน `exclude_recipients` ออกทุกครั้ง

**Extract Workflow Task ID (ต่อ Epic):**

1. อ่านค่าจาก field `workflow_task_id` (จาก config)
2. Parse `description` หา pattern `IT Workflow Task ID:\s*(\d+)` (case-insensitive)
3. ถ้าทั้งสองมีและต่างกัน → ใช้ค่าจาก `description` (source of truth)
4. ถ้ามีแค่อย่างเดียว → ใช้อันที่มี
5. ถ้าไม่มีเลย → fallback = Jira key (เช่น `CSD-215`)

**VERSION:**
- ให้ผู้ใช้ใส่เอง — default แสดงเป็น `xxx` ไว้ก่อน ไม่ดึงจาก Epic อัตโนมัติ

**วันที่ Promote:**
- แปลง Promote Date เป็นภาษาไทย เช่น `24/06/2026` → `"วันพุธที่ 24 มิถุนายน 2026"`
- ใช้ปีคริสตศักราช (ไม่ใช่พุทธศักราช)

**Edge cases:**
- `service_fields` ว่างเปล่าใน config → แจ้ง warning ให้รัน Setup 4C ใหม่ แล้วหยุด
- Match ไม่ได้สำหรับ field ใด → แสดง warning แต่รัน field อื่นต่อ
- หนึ่ง Epic มีหลาย service field → รวม recipient แล้ว deduplicate

---

## PHASE 4 — Render Email Card

> แสดงผลบนหน้าจอ Claude — ไม่สร้างไฟล์
> **บังคับ: อ่าน `Promote_Template_Email.html` และ `Map_User_Email.xlsx` ใหม่ก่อนสร้าง output ทุกครั้ง**

**แยก card ตาม Promote Date:**

จาก lookup table ใน Phase 1 — ถ้ามีหลาย Promote Date → สร้างหลาย card set แยกกัน เรียงตามวันที่ ASC

ตัวอย่าง:
```
[Card set 1] — Promote 24/06/2026  (2 งาน)
[Card set 2] — Promote 25/06/2026  (3 งาน)
```

แต่ละ card set ประกอบด้วย **2 card**:

---

### Card 1 — หัวข้อ (Subject Line)

```
แจ้ง Promote ระบบ CSD/Subscription Version {VERSION} วันที่ {วัน/วันที่/เดือน/ปี ภาษาไทย}
```

พร้อมปุ่ม **Copy** (plain text)

---

### Card 2 — เนื้อหา Email

ประกอบด้วย:

1. **กรอบ CC** — Group Mail รวม (deduplicated, คั่นด้วย `;`) ทำออกมาเป็น กรอบ สีเขียว พร้อมปุ่ม copy
2. **เนื้อ email** — render จาก `Promote_Template_Email.html` โดยแทน placeholder:

**Claude ใส่ให้อัตโนมัติ:**

| Placeholder | ค่าที่แทน |
|---|---|
| `{{วัน/วันที่/เดือน/ปี}}` | Promote Date จาก Jira — format ภาษาไทย เช่น "วันพุธที่ 24 มิถุนายน 2026" ปีคริสตศักราช |
| `{{email of department}}` | Group Mail รวมทุก Unit ที่ service field มีค่า คั่นด้วย `;` |
| `{{Task Workflow ID}}` | Workflow Task ID ที่ extract ได้จาก Phase 3 |
| `{{รายละเอียดงาน (ชื่อ task)}}` | ชื่อ Epic โดยตัดส่วน `[***]` ที่อยู่หน้าชื่อออก |

**ผู้ใช้ใส่เองก่อน Forward จริง:**

| Placeholder | หมายเหตุ |
|---|---|
| `{{VERSION}}` | แสดง `xxx` ไว้ก่อน — ผู้ใช้แก้เป็นเลข version จริง |
| `{{ตัวย่อแผนก}}` | แสดง `___` ไว้ก่อน — ผู้ใช้ใส่ตัวย่อแผนก เช่น CSD |

พร้อมปุ่ม **Copy** (format ติดไปใน Outlook/Gmail ได้เลย) ให้เป็นการก๊อปปี้ HTMl และ รูปแบบออกมา สำหรับการวางบน email
**อย่าลืม**เอาข้อความยาว ๆ มาด้วยที่ปรากฏอยู่ใน template

---

## PHASE 5 — Post Comment บน Jira

> เฉพาะ ticket ที่ไม่มีการคอมเมนต์ว่า "Promote Notification Complet"

1. แสดงรายชื่อ ticket ที่จะ post comment ก่อน:
   ```
   จะ comment "Promote Notification Complete" บน ticket ต่อไปนี้:
   - CSD-XXXX: {ชื่อ Epic}
   - CSD-YYYY: {ชื่อ Epic}
   ```
2. → post comment `"Promote Notification Complete"` บนแต่ละ ticket
3. แสดง checklist หลัง post:
   ```
   ✓ CSD-XXXX — comment แล้ว
   ✓ CSD-YYYY — comment แล้ว
   ```

**Edge cases:**
- post ล้มเหลว ticket ใด → แจ้ง "✗ CSD-XXXX — ล้มเหลว ({เหตุผล})" แต่รัน ticket อื่นต่อ

---

## PHASE 6 — สรุปผล

แสดงข้อความสรุปท้าย card เสมอ:

**กรณีมี unnotified:**
```
✅ Promote Notification เสร็จสิ้น ({today})
   - แจ้งแล้ว : {N} ticket(s) — {key1}, {key2}, ...
   - Comment Jira : เสร็จแล้ว
```

**กรณีไม่มีอะไรต้องแจ้ง:**
```
✅ วันนี้ไม่มี Promote ต้องแจ้ง — ticket ทั้งหมดได้รับการแจ้งเตือนแล้ว ({today})
```

---

## หมายเหตุสำคัญ

- **Recipients** รวมจากทุก Epic ใน window เสมอ ไม่ใช่แค่ UNNOTIFIED
- **exclude_recipients** ต้องลบออกก่อน render ทุกครั้ง
- **Phase 5** ต้อง confirm ก่อน post เสมอ ห้าม post อัตโนมัติ
- **Setup** รันแค่ครั้งเดียว ตรวจจากค่าจริงในไฟล์ว่าช่องบังคับครบหรือยัง ไม่ใช้ flag แยกต่างหาก
- **VERSION** ใส่ default `xxx` เสมอ — ผู้ใช้แก้เองก่อน forward จริง