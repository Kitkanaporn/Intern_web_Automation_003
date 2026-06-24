<!-- ---------------------------------------------------
name : Promote_Notification
version : 1.0.0
Description : แจ้งเตือน UAT ผ่าน email อัตโนมัติเมื่อ Epic กำลังจะมีการโปรโมทในวันจันทร์หน้า โดยเครื่องมือ Cladue-cowork และ Jira
----------------------------------------------------

# อ่านส่วนนี้ก่อนทำงาน

## กฏห้ามฝ่าฝืนเด็ดขาด
1. ต้องอ่าน `AGENT.md` และ `SKILL.md` ให้เข้าใจ ก่อนรัน Promote Notification ทุกครั้ง
2. ต้องทำการดึงข้อมูลใหม่จาก Jira ก่อนรัน Promote Notification ทุกครั้ง
3. อ่าน `shared_config.yaml` และ `project_config.yaml` ให้เข้าใจ ก่อนรัน Promote Notification ทุกครั้ง
4. ห้ามแก้ไขไฟล์ใด ๆ ในโฟลเดอร์ Promote_Notification โดยไม่ได้รับอนุญาตจากผู้ดูแลระบบ
5. ห้ามแก้ไข  `Promote_Template_Email.html` ให้อ่านทุกครั้ง หากมีการเปลี่ยนแปลงให้ถามก่อนทุกครั้งที่รัน Promote Notification

# PHASES การทำงาน

## Phase 0 : Set up check
ตรวจสอบก่อนรันทุกครั้ง

### 0A : อ่านไฟล์ config 2 ระดับ
- `shared_config.yaml` : ใช้ร่วมทุก project
- `project_config.yaml` : ใช้เฉพาะ project นั้น ๆ

### 0B : ตรวจสอบ config ว่าครบถ้วนหรือไม่
- หากไม่ครบให้ทำการถามผู้ใช้เพื่อกรอกค่าให้ครบถ้วนก่อนรันต่อ
  - โดยจะให้ถามภายใน claude เลยเพื่อความสะดวกในการทำงานของผู้ใช้ (ทำงานขั้น 0C)

- หากข้อมูลครบถ้วนแล้วให้ทำการบันทึกลงไฟล์ config นั้น ๆ เพื่อให้ครั้งต่อไปไม่ต้องถามซ้ำ

### 0C : ถามผู้ใช้เพื่อกรอกค่า config ที่ขาดหายไป

ส่วนนี้จะถามเพียงส่วนที่ Claude ไม่ทราบจริง ๆ เท่าทั้น หากส่วนไหนที่ไม่ทราบแล้วสามารถดึงข้อมูลจาก JIRA ได้นั้น Claude จะไม่ถามผู้ใช้ แต่จะดึงข้อมูลจาก JIRA มาแทน

#### 0C-1 : ถามค่า config ของ shared_config.yaml
#### 0C-2 : ถามค่า config ของ project_config.yaml

#### 0C-3 : หากมีหลาย space
  จะมีการถามผู้ใช้เพื่อเลือก space ที่ต้องการรัน Promote Notification
  และจะมีการสร้างไฟล์ project_config.yaml ของ project นั้น ๆ ขึ้นมาใหม่ หากยังไม่มีอยู่ในโฟลเดอร์ Promote_Notification

  - นี้คือส่วนที่ต้องใส่ค่า project_key ของ project นั้น ๆ ให้ถูกต้อง โดย claude จะพยายามดึงมาเองจาก JIRA หากไม่พบจะถามผู้ใช้ให้กรอกเอง
  project_key: "[Project Key]"  # เช่น CSD, ProjectB, ProjectC
  
  fields :
    workflow_task_id : ""   # IT Workflow Task ID
    promote_date : ""  # Promote Date (Tentative Live Date)

## Phase 0.1 : Bootstrap
- ตรวจสอบว่าไฟล์ `Map_User_Email.xlsx` อยู่ในโฟลเดอร์
- อ่าน Shared Config และ Project Config เก็บข้อมูลทั้งหมดไว้ใน memory ของ Claude
- ตรวจสอบว่าไฟล์ `Promote_Template_Email.html` อยู่ในโฟลเดอร์ ให้อ่านและเก็บไว้ใน memory ของ Claude
- ตรวจสอบว่าไฟล์ `Map_User_Email.xlsx` อยู่ในโฟลเดอร์ ให้อ่านและสร้าง lookup table : Group (fill-down) → { group_mail, members: [ { name, email } ] } เก็บไว้ใน memory ของ Claude

**หากหาไฟล์ไหนไม่เจอ** แจ้งผู้ใช้ให้ตรวจสอบว่าไฟล์ถูกต้องและอยู่ในโฟลเดอร์ที่กำหนด

---

## Phase 1 : Query Jira
- ดึงข้อมูล Epic ทั้งหมดของ project ที่มี Promote Date (Tentative Live Date) 
- ตรวจสอบว่า Promote Date (Tentative Live Date) อยู่ในช่วงเวลาที่กำหนดใน config (Promote Window Day) หรือไม่

- สูตรคำนวณ
```
window_end = today + project_config.promote_window_day
```

### JQl
```
project = {project_key}
AND issuetype = Epic
AND cf[{promote_date_field}] >= "{today}"
AND cf[{promote_date_field}] <= "{window_end}"
ORDER BY cf[{promote_date_field}] ASC
```
โดยการดึงออกมาแล้วแบ่งตามวันที่ต้อง promote โดยเก็ยเป็น look up table : promote_date → [ { epic_key, workflow_task_id , name_of_epic} ]

**กรณีพิเศษ**
- หากไม่มี Epic ที่มี Promote Date (Tentative Live Date) ในช่วงเวลาที่กำหนด ให้แจ้งผู้ใช้ว่า "วันนี้ไม่มี Promote ที่ต้องแจ้งเตือน" และจบการทำงาน

---

## Phase 2 : แยกส่วนของ Notified vs Unnotified
  เช็คแต่ละ ticket ว่ามีการแจ้งหรือยัง

ให้นำเอาข้อมูลจาก Phase 1 นั้นมาเช็คว่า ticket ไหนที่ยังไม่ได้แจ้งเตือน (Unnotified) และ ticket ไหนที่ได้แจ้งเตือนแล้ว (Notified)
1. เช็ค ticket ที่มี comment "Promote Notification Complete" หรือไม่
  - ถ้ามี comment นี้อยู่แล้ว ให้ถือว่า ticket นั้นเป็น Notified 
  - ถ้าไม่มี comment นี้ ให้ถือว่า ticket นั้นเป็น Unnotified 
2. แสดง summary table ของ ticket ทั้งหมด โดยแยกเป็น 2 กลุ่ม คือ Notified และ Unnotified

**กรณีพิเศษ**
- หากเป็น notified ทั้งหมดให้แจ้งผู้ใช้ว่า "วันนี้ไม่มี Promote ที่ต้องแจ้งเตือน" และจบการทำงาน

---

## Phase 3 : Map Recipients - Prepare email data
  แปลงข้อมูลจาก jira field ของ Epic ให้เป็นรายชื่อผู้รับ email ที่ต้องส่งจริง โดยใช้ข้อมูลจาก Map_User_Email.xlsx และเก็ยข้อมูลสำหรับการสร้าง email template ไว้ใน memory ของ Claude

เอาข้อมูลจาก Jira ว่ามี UNIT ไหนบ้างที่มีข้อมูลต้องส่ว โดยการส่งข้อมูล Promote จะส่งไปที่องค์กร ไม่ได้ส่งไปของส่วนตัวของแต่ละคน ดังนั้นต้องเอา Jira field ของ Epic มาทำการ map กับ Map_User_Email.xlsx เพื่อให้ได้รายชื่อองค์กรผู้รับ email ที่ต้องส่งจริง

**สร้าง structure :**
1. group -> member map
```
group_members = {
  "Account Service Unit" : [name , name , ...] ,
  "CA Service Unit" : [name , ...] 
}
```
2. group -> group mail map
```
group_mail = {
  "Account Services Unit": "AccountServicesUnit@set.or.th",
  "CA Service Unit":       "CAServiceUnit@set.or.th",
}
```

**Auto-match jira field**
แต่ละ field ของ Jira จะมี display name ที่ตรงกับคอลัมน์ Group ใน Excel ดังนั้นจึงสามารถทำการ match ได้โดยอัตโนมัติ โดยไม่ต้อง config เพิ่ม

**Build CC list (Group Mail — ระดับ Unit)**:

1. ดูว่า service field ไหนมีค่า (ไม่ว่าง) → ได้ชื่อ group นั้น
2. ดึง Group Mail จาก group_mail[group_name]
3. Union ทุก Group Mail email, deduplicated → cc_emails list 
4. ใช้ ; คั่นระหว่าง email ในกล่อง CC

**วันที่ของ Promote**
- ดึง Promote Date (Tentative Live Date) ของ Epic นั้น ๆ มาแสดงในช่องของ {{วัน/วันที่/เดือน/ปี}} เช่น
  - 24/06/2026 ก็จะเป็น "วันพุธที่่ 24 มิถุนายน 2026"

**version**
- เป็นข้อมูลที่จะให้ทางผู้ใช้เป็นคนใส่เอง โดยให้ใส่ default เป็น xxx ไว้ก่อน

**Extract Workflow Task ID**
1. อ่าน field จาก config jira.fields.workflow_task_id
2. Parse description หา pattern: IT Workflow Task ID:\s*(\d+) (case-insensitive)
3. ถ้าทั้งสองมีและต่างกัน → ใช้ค่าจาก description (source of truth)
4. ถ้ามีแค่อย่างเดียว → ใช้อันที่มี
5. ถ้าไม่มีเลย → fallback = Jira key (เช่น CSD-215)

---

## Phase 4 : Generate email template
**บังคับ : ต้องอ่าน Template และ excel ก่อนสร้าง Output ทุกครั้ง**
จะแบ่งตามวันที่ของแต่ละ Promote Date (Tentative Live Date) โดยสร้าง email template สำหรับแต่ละ Epic ที่ยังไม่ได้แจ้งเตือน (Unnotified) โดยใช้ข้อมูลจาก Phase 3 โดยจะแยกออกมาตามวัน promote ตานที่ Phase 1 ทำ เช่น
  - 24/06/2026 มี 2 งานที่โดยตรวจจับ promote วันนี้
  - 25/06/2026 มี 3 งานที่โดยตรวจจับ Promote วันนี้
จาก 2 อันนี้ ก็จะแยกออกมาเป็น 2 draft mail ไม่ได้เอามารวมกัน

**เนื้อหาใน card**
  - header : "เนื้อความ email" + ปุ่ม copy (html)
  - ใช้โครงสร้าง HTML จาก Promote_Template_Email.html ทั้งหมด **ห้ามคิดแบบขึ้นมาเองเด็ดขาด**
  - แทนที่ placeholder ดังนี้ :

| Placeholder | ค่าที่แทนที่ |
|---|---|
|{{วัน/วันที่/เดือน/ปี}}|วันที่ promote เป็นวันอะไร วันที่เท่าไหร่ เดือนอะไร ปีคริสศักราชอะไร|
|{{email of department}}|Group Mail ที่ช่องบน field jira ไม่ใช่ empty|
|{{Task workflow ID}}|เลขจาก filed : task workflow id|
|{{รายละเอียดงาน}}|ชื่อของงานนี้ โดยมีการตัดส่วนของ [***] ที่อยู่หน้าของชื่องานออกไป|

**โครงสร้างของ email ทั้งหมด** ต้องอิงตามไฟล์ HTML เท่านั้น (Promote_Notification_Email.html)
**แต่ละ card จะแตกต่างกันไปจามวันที่ promote**
---

## Phase 5 : comment Jira

  สำหรับทุก unnotified ticket → ใช้ addCommentToJiraIssue:

  - cloudId: จาก config jira.cloud_id
  - issueIdOrKey: Jira key ของ ticket นั้น
  - comment body: ข้อความจาก config jira_comment.text (เช่น "Promote Notification Complete")
ทำอัตโนมัติทันที ไม่ถาม ไม่ขอ permission

---

## PHASE 6 : สรุปผล

แสดงข้อความสรุปท้าย card:

**กรณีมี unnotified:**
```
✅ Promote Notification เสร็จสิ้น ({today})
   - แจ้งแล้ว: {N} ticket(s) — {key1}, {key2}, ...
   - Comment Jira: เสร็จแล้ว
```

**กรณีไม่มีอะไรต้องแจ้ง:**
```
✅ วันนี้ไม่มี Promote ต้องแจ้ง — ticket ทั้งหมดได้รับการแจ้งเตือนแล้ว ({today})
```

---

## กฎ Automation (ห้ามฝ่าฝืน)

- **Query Jira ใหม่ทุกรัน** — ห้ามใช้ข้อมูล ticket จาก session ก่อน
- **อ่าน `Promote_Template_Email.html` ใหม่ทุกครั้ง** — ห้ามสร้าง HTML โครงสร้างใหม่เอง
- **อ่าน `Map_User_Email.xlsx` ใหม่ทุกครั้ง** — ห้ามใช้รายชื่อ/email จาก session ก่อน
- **ไม่ถาม ไม่รอ ไม่ยืนยัน** — ทุก phase รันต่อเนื่องอัตโนมัติ
- **ไม่ขอ permission** ก่อน action ใดๆ (draft, comment, field update)
- **Output บนหน้าจอ Claude เท่านั้น** — ไม่สร้างไฟล์
- **ต้องแยก card หากจับวัน promote ได้ต่างวันกัน** -->