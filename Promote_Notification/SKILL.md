# SKILL.md — Promote Notification Automation

ไฟล์นี้คือ logic หลักทั้งหมดของระบบ Claude จะอ่านและทำตามทุก Phase ตามลำดับ

---

## ⛔ กฎห้ามฝ่าฝืนเด็ดขาด ⛔

1. ต้องอ่าน `instructions/AGENT.md` และ `SKILL.md` ให้เข้าใจก่อนรันทุกครั้ง
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
       │ (ยังว่าง)                                (ดู instructions/SETUP.md)
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
| `{{วัน/วันที่/เดือน/ปี}}` | Promote Date จาก Jira — format ภาษาไทย เช่น "วันพุธที่ 24 มิถุนายน 2026" **ใช้ปีพุทธศักราช** เช่น 2569 |
| `{{email of department}}` | Group Mail รวมทุก Unit ที่ service field มีค่า คั่นด้วย `;` |

**ตาราง Promote (สำคัญ — หลาย Epic = หลายแถว):**

template มี `<tr>` แค่แถวเดียว — ถ้ามีหลาย Epic ในวันเดียวกัน ให้ **duplicate `<tr>` ให้ครบทุก Epic** (ทั้ง NOTIFIED + UNNOTIFIED) โดยแต่ละแถวประกอบด้วย:

| Column | ค่า |
|---|---|
| `{{ตัวย่อแผนก}}` | แสดง `___` ไว้ก่อน — ผู้ใช้ใส่เองก่อน forward |
| `{{Task Workflow ID}}` | Workflow Task ID ของ Epic นั้น (extract จาก Phase 3) |
| `{{รายละเอียดงาน (ชื่อ task)}}` | ชื่อ Epic นั้น โดยตัดส่วน `[***]` ที่อยู่หน้าชื่อออก |

ตัวอย่างกรณี 3 Epic วันเดียวกัน:
```html
<tr>
  <td class="col-dept">___</td>
  <td class="col-task">WF-10001</td>
  <td class="col-detail">ระบบสมาชิกออนไลน์ - ปรับปรุง Login</td>
</tr>
<tr>
  <td class="col-dept">___</td>
  <td class="col-task">WF-10002</td>
  <td class="col-detail">ระบบ Report รายวัน</td>
</tr>
<tr>
  <td class="col-dept">___</td>
  <td class="col-task">CSD-103</td>
  <td class="col-detail">ระบบแจ้งเตือน Push Notification</td>
</tr>
```

**ผู้ใช้ใส่เองก่อน Forward จริง:**

| Placeholder | หมายเหตุ |
|---|---|
| `{{VERSION}}` | แสดง `xxx` ไว้ก่อน — ผู้ใช้แก้เป็นเลข version จริง |
| `{{ตัวย่อแผนก}}` | แสดง `___` ในทุกแถว — ผู้ใช้ใส่ตัวย่อแผนก เช่น CSD |

> **บังคับ:** ต้องรวม signature (ข้อความ disclaimer ภาษาอังกฤษ) จาก template ทุกครั้ง — ห้ามตัดออก

พร้อมปุ่ม **Copy** (format ติดไปใน Outlook ได้เลย) ให้เป็นการคัดลอก HTML พร้อม styling สำหรับวางบน email

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