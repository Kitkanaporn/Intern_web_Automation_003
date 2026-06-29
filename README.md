# การใช้งานระบบการแจ้งเตือน UAT และ Promote ด้วย Claude AI

## รายละเอียดของ Fields ใน JIRA Ticket

ส่วนสำคัญในการสร้าง Ticket ใน JIRA ที่ claude จะเข้าไปทำการจับเพื่อเก็บข้อมูลสำหรับการสร้าง Draft Mail
```
- Text block 
    - Workflow Main Task 
- Period time
    - Promote Date
    - UAT Start Date
    - UAT End Date
- Service Units (Checklish block)
    - Account Services Unit
    - Counter Services Unit
    - Issuer Services Unit
    - Investor Service Unit
    - CA Service Unit
    - Distribution Unit
```
---
## รายละเอียดของการทำงานด้วย Claude AI

### การเชื่อมต่อ Cluade เข้ากับ JIRA

**ขั้นตอนการเชื่อมต่อ Jira**
```
1. คลิกที่ account -> setting (บริเวณซ้ายล่างของหน้าต่างของ claude application)
2. คลิก Connectors ที่บริเวณ sidebar ของหน้าต่าง setting -> คลิกที่ Customize
3. หา Atlassian Rovo ที่ช่องของ Connectors จาหนั้นคลิกเข้าไปทำการ connect
    - หากไม่พบส่วนของ Atlassian ROVO นั้นสามารถแก้ไขได้ดังนี้
        - กดปุ่ม + (บวก) บริเวณทางขวาของ sidebar ที่ 2 เพิ่มเข้าไปหาต่างของ Directory
        - ทำการ Search "Atlassian ROVO" และคลิกเข้าไป 
        ** หากติด Request ให้กด Request และติดต่อแผนก servicedesk เพื่อปลดล็อก
4. จะเด้งเข้ามายังหน้า brownser ของ ATLASSIAN จากนั้นเลื่อนลงล่างสุด และกดยินยิมการเข้าถึงของ AI ในการอ่านเขียน JIRA
```

ในการทำงานของ cluade นั้นหากไม่มีการเชื่อมต่อกับ Jira นั้นระบบจะมีการแจ้งเตือนว่า
`เชื่อมต่อ jira ไม่ได้` และหยุดการทำงานทันที

---

### Set up Claude cowork - Scheduled
