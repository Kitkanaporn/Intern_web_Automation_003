# Speaking Script — Claude Cowork Presentation

---

## Slide 1 — Title: Claude Cowork

> "สวัสดีครับ/ค่ะ พี่ๆ ทุกคน
> วันนี้หนูจะมาแนะนำเครื่องมือชื่อ **Claude Cowork** ที่หนูใช้ระหว่าง intern
> และจะเอาโปรเจกต์ที่ทำจริงมาเป็นตัวอย่างให้ดูด้วยว่ามันช่วยลดงาน routine ได้ยังไงบ้างครับ/ค่ะ"

---

## Slide 2 — What is Claude Cowork?

> "Claude Cowork คือ desktop app ของ Anthropic
> มันรันบน Windows ได้เลยโดยไม่ต้องขอสิทธิ์ admin พิเศษ
>
> จุดเด่นคือ มันเชื่อมต่อกับเครื่องมือที่เราใช้งานอยู่แล้วได้เลย ไม่ว่าจะเป็น **Jira, Outlook, SharePoint, หรือ Excel**
>
> การ setup ก็ไม่ต้องเขียน code — แค่บอกเป็นภาษาไทยหรืออังกฤษว่าอยากให้ทำอะไร เขียนลงในไฟล์ชื่อ SKILL.md แล้ว schedule ให้มันรันเองทุกเช้าได้เลย"

---

## Slide 3 — Before Cowork: Daily Manual Friction

> "ก่อนจะไปถึง solution ขอ set context ก่อนนะครับ/ค่ะ
> งานที่หนูเจอตอน intern คืองาน UAT และ Promote Notification
>
> ปัญหาที่เจอมีหลายจุด เช่น ต้องมา mark วันเองในปฏิทิน
> ต้องจำเองว่าวันไหน UAT ของ Epic ไหนใกล้มาถึง
> ต้องไปค้นหา email ของแต่ละแผนกจากหลายที่
> แล้วก็ draft email เองซ้ำๆ ทุกครั้ง
>
> สุดท้ายไม่มี audit trail เลย ไม่รู้ว่าส่ง notification ไปแล้วหรือยัง
> พูดง่ายๆ คืองานซ้ำ เสียเวลา และ error-prone ครับ/ค่ะ"

---

## Slide 4 — Required Fields in Jira Epic

> "ก่อนที่ระบบจะดึงข้อมูลได้ มีเงื่อนไขหนึ่งคือ
> ต้องกรอก field พวกนี้ใน Jira Epic ให้ครบก่อนนะครับ/ค่ะ
>
> สำคัญที่สุดคือ **UAT Start Date, UAT End Date, และ Promote Date**
> รองลงมาคือ **Service Units** ที่เกี่ยวข้อง ว่ามีแผนกไหนบ้างที่ต้องรับ notification
>
> แค่กรอกตรงนี้ให้ครบ ระบบจะดึงทุกอย่างไปใช้เองโดยอัตโนมัติ ไม่ต้องทำอะไรเพิ่ม"

---

## Slide 5 — Target Automations Flow

> "นี่คือ flow ทั้งหมดที่ระบบทำให้ แบ่งเป็น 5 step ครับ/ค่ะ
>
> **Step 1** — Claude ดึง Epic จาก Jira ที่มีวันใกล้ถึงมาก่อน
> **Step 2** — ตรวจสอบวันและดึง Service Units ที่เกี่ยวข้อง
> **Step 3** — ไปหา email ของแต่ละแผนกจาก Excel ที่เตรียมไว้
> **Step 4** — สร้าง email draft พร้อม To, CC, Subject, และ body
> **Step 5** — บันทึก log ลงใน Jira comment ว่า notification ส่งไปแล้ว
>
> ทั้งหมดนี้รันเองทุกเช้า ไม่ต้องมาคลิกอะไรเพิ่มเลยครับ/ค่ะ"

---

## Slide 6 — UAT & Promote Workflows

> "ขยาย step ให้ละเอียดขึ้นอีกหน่อยนะครับ/ค่ะ
> จริงๆ มีอยู่ 2 workflow แยกกัน
>
> **UAT Notification** — จะยิงก่อนถึงวัน UAT ตามเกณฑ์ที่กำหนด
> ดึง email แผนก → สร้าง draft → โพสต์ comment ยืนยันใน Jira
>
> **Promote Notification** — จะเช็ค Epic ที่ Promote Date อยู่ใน 3 วันข้างหน้า
> เหมือนกันเลยคือดึง email → สร้าง draft → กด complete
>
> ทั้งสอง workflow logic คล้ายกัน แต่ trigger condition และกลุ่ม recipient ต่างกัน"

---

## Slide 7 — System Setup in 3 Simple Steps

> "ส่วนการ setup ระบบนี้ง่ายมากๆ ครับ/ค่ะ แค่ 3 ขั้นตอน
>
> **1.** เชื่อม Jira connector ใน Claude Cowork Settings เลย ใส่ account แล้วก็เสร็จ
> **2.** สร้าง project ใหม่ ชี้ไปที่โฟลเดอร์ที่มี config file และ Excel อยู่
> **3.** พิมพ์คำสั่งสั้นๆ แค่ `/schedule 08:00 check UAT` แล้ว Claude จัดการที่เหลือให้เองทุกเช้า
>
> ใครก็ทำได้ ไม่จำเป็นต้องมีพื้นฐาน coding เลยครับ/ค่ะ"

---

## Slide 8 — Automated Outcomes

> "ผลลัพธ์ที่ได้คือ email draft ที่พร้อม send ได้ทันที
>
> มี **Subject** ที่ format ถูกต้องพร้อม classify ประเภทและวันที่
> มี **To และ CC** ที่ดึงมาจาก mapping table ตรงกับแผนกที่ต้องรับ
> และมีปุ่ม **Copy-to-Clipboard** ให้ copy ทุกอย่างไปวางใน Outlook ได้เลยในคลิกเดียว
>
> ไม่ต้องพิมพ์ใหม่ ไม่ต้องหา email เอง ไม่ต้องจำอะไรเลย"

---

## Slide 9 — Built-In Platform Skills

> "นอกจาก workflow นี้ Claude Cowork มี skill อื่นๆ ในตัวด้วยครับ/ค่ะ
>
> เช่น `/schedule` สำหรับตั้ง task อัตโนมัติ
> `/digest` สรุป email และ ticket ให้ทุกเช้า
> และ skill สำหรับทำ Excel, Word, PowerPoint ได้เลยโดยไม่ต้องเปิดโปรแกรม
>
> รวมถึงเชื่อม Microsoft 365 ได้โดยตรง ทั้ง Outlook และ SharePoint"

---

## Slide 10 — Closing

> "สรุปคือสิ่งที่ทำไปช่วย**ลดงานซ้ำซาก** และ**เพิ่มประสิทธิภาพ** ได้จริงครับ/ค่ะ
>
> จากที่เคยต้องมาทำมือทุกวัน ตอนนี้ระบบรันเองทุกเช้า 8 โมง
> ทีมงานได้รับ notification ตรงเวลา มี audit trail ครบ และไม่มีงานตกหล่น
>
> Code ทั้งหมดอยู่ที่ GitHub ตามลิงก์นี้ ใครสนใจดูได้เลยครับ/ค่ะ
> มีคำถามอะไรไหมครับ/ค่ะ?"

---

*หมายเหตุ: script นี้เขียนแบบ casual พูดสบายๆ ปรับน้ำเสียงได้ตามสถานการณ์*
