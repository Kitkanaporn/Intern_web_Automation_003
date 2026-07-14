# SKILL.md — Promote Notification Automation

ไฟล์นี้คือ logic หลักทั้งหมดของระบบ Claude จะอ่านและทำตามทุก Phase ตามลำดับ

---

## ⛔ กฎห้ามฝ่าฝืนเด็ดขาด ⛔

1. ต้องอ่าน `instructions/AGENT.md` และ `SKILL.md` ให้เข้าใจก่อนรันทุกครั้ง
2. ต้องดึงข้อมูลใหม่จาก Jira ก่อนรันทุกครั้ง — ห้ามใช้ข้อมูล ticket จาก session ก่อน
3. ต้องอ่าน `shared_config.yaml` และ `project/project_config.yaml` ก่อนรันทุกครั้ง
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
 Phase Setup ──── มี field ที่ tag #importance ว่างอยู่ไหม? ──→ ไม่มี → Phase 0
       │ (มีว่าง)                                  (ดู instructions/SETUP.md)
       ↓
 Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
```

> **Phase Setup** — ดู `instructions/SETUP.md` (รันเฉพาะครั้งแรกที่ config ยังว่าง)

---

## PHASE 0 — Bootstrap

> โหลด config และข้อมูลทั้งหมดเข้าหน่วยความจำ ทำครั้งเดียวต่อการรัน

**0A — Pre-flight: ตรวจสอบการเชื่อมต่อ Jira (ทำก่อนทุกอย่าง)**

เรียก `getAccessibleAtlassianResources`:
- **สำเร็จ** → ดำเนินการต่อ
- **ล้มเหลว / ไม่มี resource** → หยุดทันที แจ้ง:
  ```
  ❌ เชื่อมต่อ Jira ไม่ได้ — กรุณาตรวจสอบที่ Settings → Connections → Atlassian แล้วลองใหม่อีกครั้ง
  ```

**0B — โหลดไฟล์และ config**

1. อ่าน `shared_config.yaml` → เก็บ: jira_comment text, cc_email, exclude_recipients
2. อ่าน `project/project_config.yaml` → เก็บ: cloud_id, project_key, customfield IDs, promote_window_days, service_fields
3. โหลด `Map_User_Email.xlsx` sheet `map` → สร้าง lookup table:
   ```
   Group (fill-down) → { group_mail, members: [ { name, email } ] }
   ```
4. โหลด `Promote_Template_Email.html` → เก็บเป็น template string

**Edge cases:**
- ถ้าหาไฟล์ไม่เจอ → หยุดทันที แจ้งชื่อไฟล์ที่หายไปชัดเจน
- ถ้ามี field #importance ว่างอยู่ → หยุดทันที แจ้งให้รัน Setup ก่อน

---

**0C — ตรวจ required fields ก่อน Phase 1**

อ่าน `project/project_config.yaml` เป็น raw text — ตรวจทุก field ใน `jira.fields.*` และ `jira.service_fields[]`

**เฉพาะ field ที่ว่างเท่านั้น** (ว่าง = `""`, `''`, หรือไม่มีค่า) → auto-detect ก่อนดำเนินการต่อ:

1. เรียก `getJiraIssueTypeMetaWithFields` เพื่อดึง field names ทั้งหมดของ project
2. ใช้ keyword matching ตาม `instructions/SETUP.md` 4B เพื่อหา customfield ID
3. เขียนค่ากลับลง `project/project_config.yaml` ทันที
4. แจ้งผู้ใช้ว่า auto-detect ได้ค่าอะไรบ้าง

**ถ้ามีค่าอยู่แล้ว → ข้ามไปเลย ไม่ต้องเรียก API**

| กลุ่ม | Fields | วิธีจัดการเมื่อว่าง |
|---|---|---|
| **Auto-detect จาก Jira** | `jira.cloud_id`, `jira.base_url`, `jira.project_key`, `jira.fields.*` ทุกตัว, `jira.service_fields[].jira_field` | detect → เขียนลง config → ดำเนินการต่อ |
| **Validate structure** | `jira.service_fields[]` — ทุก entry ต้องมี `jira_field` และ `table_column` ครบ | ถ้าไม่ครบ → แจ้ง warning แต่รันต่อ |

> ห้ามข้ามขั้นตอนนี้ — ถ้า `jira.fields.*` ตัวไหนว่าง ต้อง detect และ save ก่อน Phase 1 เสมอ

---

## PHASE 1 — Query Jira

> หา Epic ทุกตัวที่ Promote Date อยู่ใน window

**คำนวณ window:**
```
today      = วันที่รัน
window_end = today + promote_window_days (จาก project_config, default = 3)
```

> วันนี้ไม่นับ — ถ้า Promote Date = today ถือว่า promote แล้ว ไม่ต้องแจ้ง

**JQL:**
```
project = {project_key}
AND issuetype = Epic
AND cf[{promote_date_field}] > "{today}"
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

**เกณฑ์ตัดสิน "แจ้งแล้ว":**

comment ที่นับว่า "แจ้งแล้ว" ต้องผ่านเงื่อนไข **ทั้งสอง** ข้อ:
1. มี comment ข้อความ `"Promote Notification Complete"` อยู่บน ticket
2. comment นั้นถูก post **ก่อนวันนี้** (created date < today)

> **Re-run same day:** ถ้า comment ถูก post วันเดียวกับที่รัน (created date = today) → ถือว่า **ยังไม่แจ้ง** เพื่อให้รันซ้ำในวันเดียวกันได้ผลลัพธ์เหมือนกันทุกครั้ง

สรุปตรรกะ:

| มี comment? | วันที่ post comment | สถานะ |
|---|---|---|
| ไม่มี | — | 🟡 ยังไม่แจ้ง |
| มี | = today (re-run) | 🟡 ยังไม่แจ้ง |
| มี | < today | ✓ แจ้งแล้ว |

สำหรับแต่ละ Epic ที่ได้จาก Phase 1:

1. แสดง **Summary Table** ก่อนดำเนินการต่อ:

   | Epic | Workflow Task ID | Promote Date | สถานะ |
   |---|---|---|---|
   | ชื่อ Epic | WF-XXXXX | วันที่ | 🟡 ยังไม่แจ้ง / ✓ แจ้งแล้ว |

**Edge cases:**
- ทุก ticket แจ้งครบหมดแล้ว (ทุกอันเป็น ✓ และ comment date < today) → แจ้ง "แจ้งครบทุก Epic ใน window แล้ว" แล้วหยุด
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

1. ดึงค่าจาก `service_fields` ทุกตัวใน `project/project_config.yaml` — แบ่ง recipient ตาม Promote Date เพราะแต่ละวันส่ง email แยกกัน
2. Match display name ของแต่ละ field กับคอลัมน์ `Group` ใน Excel (case-insensitive)
3. ผลลัพธ์ต่อ Group ที่ match:
   - **Recipients (To)** = Group Mail ของกลุ่มนั้น (คั่นด้วย `;`)
4. รวม recipient จากทุก Epic และทุก service field แล้ว **deduplicate**
5. ลบ email ที่อยู่ใน `exclude_recipients` ออกทุกครั้ง

**Extract Workflow Task ID (ต่อ Epic):**

1. อ่านค่าจาก field `workflow_task_id` (จาก config)
2. Parse `description` หา pattern `IT Workflow Task ID:\s*(\d+)` (case-insensitive)
3. ถ้าทั้งสองมีและต่างกัน → ใช้ค่าจาก `description` (source of truth)
4. ถ้ามีแค่อย่างเดียว → ใช้อันที่มี
5. ถ้าไม่มีเลย → fallback = Jira key (เช่น `CSD-215`)

**VERSION:**
- ให้ผู้ใช้ใส่เอง — default แสดงเป็น `x.x.x` ไว้ก่อน ไม่ดึงจาก Epic อัตโนมัติ

**วันที่ Promote:**
- แปลง Promote Date เป็นภาษาไทย เช่น `24/06/2026` → `"วันพุธที่ 24 มิถุนายน 2569"`
- ใช้ปีพุทธศักราช (ค.ศ. + 543) เช่น 2026 → 2569

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

แต่ละ card set ประกอบด้วย **4 card**:

---

### Card 1 — หัวข้อ (Subject Line)

```
แจ้งโปรโมทระบบ CSD ณ {วัน/วันที่/เดือน/ปี ภาษาไทย}
```

พร้อมปุ่ม **Copy** (plain text)

---

### Card 2 — Recipients (Unit)

**กรอบสีเขียว** — Group Mail รวมทุก Unit ที่ service field มีค่า (deduplicated, คั่นด้วย `;`) พร้อมปุ่ม **Copy**

> Copy ใช้ `navigator.clipboard.writeText(...)` — plain text

---

### Card 3 — CC

**กรอบสีฟ้า** — อีเมลที่กำหนดอยู่ในไฟล์ `shared_config.yaml` ในส่วน `cc_email` โดยเอาค่าที่ไม่ว่างทั้งหมดมาเชื่อมกันด้วย `;` พร้อมปุ่ม **Copy**

> Copy ใช้ `navigator.clipboard.writeText(...)` — plain text

---

### Card 4 — เนื้อหา Email

> ⚠️ **บังคับ: ต้องเรียก `show_widget` tool ทุกครั้ง — ห้าม output HTML เป็น code block หรือ plain text เด็ดขาด**

**ขั้นตอน (ทำตามลำดับ):**

1. อ่าน `Promote_Template_Email.html` เป็น string
2. แทน placeholder ทุกตัวด้วยค่าจริง (ดูตารางด้านล่าง)
3. สร้าง `widget_code` สำหรับส่งให้ `show_widget`:
   - ดึง CSS ออกจาก `<style>...</style>` block
   - ดึงเนื้อหาออกจาก `<body>...</body>` block
   - รวมเป็น: `<style>...css...</style>` + เนื้อหา body
   - ⛔ ห้ามใส่ `<!DOCTYPE>`, `<html>`, `<head>`, `<body>` tags
4. ต่อท้าย `widget_code` ด้วยปุ่ม Copy:
   ```html
   <button onclick="
     const blob = new Blob([document.querySelector('.email-container').outerHTML], {type:'text/html'});
     navigator.clipboard.write([new ClipboardItem({'text/html': blob})]);
   " style="margin-top:12px;padding:8px 20px;font-size:14px;cursor:pointer;border:1px solid #ccc;border-radius:4px;">📋 Copy Email</button>
   ```
5. เรียก `show_widget` tool พร้อม parameter:
   - `widget_code` = ค่าจากข้อ 3+4
   - `title` = `"promote_email"`
   - `loading_messages` = `["กำลัง render email..."]`

**placeholder ที่ต้องแทน:**

| Placeholder | ค่าที่แทน |
|---|---|
| `{{วัน/วันที่/เดือน/ปี}}` | Promote Date — ภาษาไทย ปีพุทธศักราช เช่น "วันพุธที่ 24 มิถุนายน 2569" |
| `{{VERSION}}` | `x.x.x` (ผู้ใช้แก้เองก่อน forward) |

**ตาราง Promote (สำคัญ — หลาย Epic = หลายแถว):**

template มี `<tr>` แค่แถวเดียว — ถ้ามีหลาย Epic ในวันเดียวกัน ให้ **duplicate `<tr>` ให้ครบทุก Epic** (ทั้ง NOTIFIED + UNNOTIFIED):

| Column | ค่า |
|---|---|
| `{{Task Workflow ID}}` | Workflow Task ID ของ Epic นั้น (extract จาก Phase 3) |
| `{{รายละเอียดงาน (ชื่อ task)}}` | ชื่อ Epic นั้น โดยตัดส่วน `[***]` ที่อยู่หน้าชื่อออก |

ตัวอย่างกรณี 3 Epic วันเดียวกัน:
```html
<tr>
  <td class="col-task">WF-10001</td>
  <td class="col-detail">ระบบสมาชิกออนไลน์ - ปรับปรุง Login</td>
</tr>
<tr>
  <td class="col-task">WF-10002</td>
  <td class="col-detail">ระบบ Report รายวัน</td>
</tr>
<tr>
  <td class="col-task">CSD-103</td>
  <td class="col-detail">ระบบแจ้งเตือน Push Notification</td>
</tr>
```

---

## PHASE 5 — Post Comment บน Jira

> รันเมื่อผู้ใช้กด **Complete Process** button เท่านั้น — ห้าม post อัตโนมัติ
> เฉพาะ ticket ที่ยังไม่มี comment "Promote Notification Complete"

1. แสดงรายชื่อ ticket ที่จะ post comment:
   ```
   จะ comment "Promote Notification Complete" บน ticket ต่อไปนี้:
   - {key1}: {ชื่อ Epic}
   - {key2}: {ชื่อ Epic}
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
- **Phase 5** trigger เฉพาะเมื่อผู้ใช้กด Complete Process button — ห้าม post อัตโนมัติ
- **Setup** รันแค่ครั้งเดียว ตรวจจากค่าจริงในไฟล์ว่าช่องบังคับครบหรือยัง ไม่ใช้ flag แยกต่างหาก
- **VERSION** ใส่ default `x.x.x` เสมอ — ผู้ใช้แก้เองก่อน forward จริง