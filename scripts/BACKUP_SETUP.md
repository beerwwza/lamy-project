# คู่มือตั้งค่า Backup อัตโนมัติ — LAMY Database

ระบบ backup จะ copy `db.sqlite3` ทุกวันอัตโนมัติ เก็บทั้ง Local และ Google Drive

---

## ขั้นตอนที่ 1 — ติดตั้ง rclone (สำหรับ Google Drive)

SSH เข้า server แล้วรัน:

```bash
# ติดตั้ง rclone
curl https://rclone.org/install.sh | sudo bash

# ตรวจสอบว่าติดตั้งสำเร็จ
rclone --version
```

---

## ขั้นตอนที่ 2 — เชื่อมต่อ Google Drive

```bash
rclone config
```

ทำตามขั้นตอนนี้:

```
n     → New remote
gdrive   → ชื่อ remote (ต้องตรงกับ GDRIVE_REMOTE ในสคริปต์)
drive → เลือก Google Drive (พิมพ์ "drive" หรือเลือกหมายเลข)
        → กด Enter ข้ามช่อง client_id และ client_secret (ใช้ค่าเริ่มต้น)
1     → scope: drive (full access)
        → กด Enter ข้ามช่องที่เหลือจนถึง "Use auto config?"
n     → ถ้า server ไม่มี browser ให้ตอบ n แล้วทำบน PC แทน
```

**กรณี server ไม่มี browser (ทั่วไป):**

```bash
# รันบน PC ของตัวเอง (ต้องติดตั้ง rclone บน PC ด้วย)
rclone authorize "drive"
# จะเปิด browser ให้ login Google → copy token ที่ได้
# นำ token ไป paste ใน server ตามที่ระบบถาม
```

ทดสอบการเชื่อมต่อ:
```bash
rclone lsd gdrive:
# ถ้าเห็นรายการโฟลเดอร์ใน Drive = สำเร็จ
```

---

## ขั้นตอนที่ 3 — แก้ไข path ในสคริปต์

เปิดไฟล์ `scripts/backup_db.sh` แล้วแก้ไขส่วน CONFIG ด้านบน:

```bash
PROJECT_DIR="/app/lamy-project"    # path โปรเจกต์บน server (ตรวจสอบด้วย pwd)
BACKUP_LOCAL_DIR="/app/backups/lamy-db"  # ที่เก็บ backup local
GDRIVE_REMOTE="gdrive"             # ชื่อ remote ที่ตั้งใน rclone config
GDRIVE_FOLDER="lamy-backups"       # ชื่อโฟลเดอร์ที่ต้องการสร้างใน Google Drive
KEEP_DAYS=30                       # เก็บ backup local กี่วัน
```

ตรวจสอบ path จริงบน server:
```bash
# หา path โปรเจกต์
find / -name "db.sqlite3" 2>/dev/null

# หรือดูจาก Docker
docker inspect lamy-project_web_1 | grep -A5 "Mounts"
```

---

## ขั้นตอนที่ 4 — ให้สิทธิ์และทดสอบสคริปต์

```bash
# ไปที่โฟลเดอร์โปรเจกต์บน server
cd /path/to/lamy-project

# ให้สิทธิ์ execute
chmod +x scripts/backup_db.sh
chmod +x scripts/restore_db.sh

# ทดสอบรันครั้งแรก
sudo bash scripts/backup_db.sh

# ดู log
cat /var/log/lamy_backup.log

# ดูไฟล์ที่สร้าง
ls -lh /app/backups/lamy-db/
```

---

## ขั้นตอนที่ 5 — ตั้ง Cron Job (รันทุกวัน 04:00 น.)

```bash
# เปิด crontab
sudo crontab -e
```

เพิ่มบรรทัดนี้:
```
0 4 * * * /path/to/lamy-project/scripts/backup_db.sh >> /var/log/lamy_backup.log 2>&1
```

> แก้ `/path/to/lamy-project` ให้ตรงกับ path จริง เช่น `/app/lamy-project`

บันทึกและออก (Ctrl+X → Y → Enter ถ้าใช้ nano)

ตรวจสอบ cron ที่ตั้งไว้:
```bash
sudo crontab -l
```

---

## วิธี Restore เมื่อต้องการกู้ข้อมูล

```bash
# ดูรายการ backup ที่มี
ls -lh /app/backups/lamy-db/

# Restore จากไฟล์ที่ต้องการ
sudo bash scripts/restore_db.sh lamy_db_2025-01-15_02-00-00.sqlite3.gz

# Restart web container หลัง restore
docker-compose restart web
```

> สคริปต์จะสำรอง db ปัจจุบันให้อัตโนมัติก่อน restore เสมอ

---

## ตรวจสอบ Backup ประจำวัน

```bash
# ดู log วันนี้
grep "$(date +%Y-%m-%d)" /var/log/lamy_backup.log

# ดู backup ใน Google Drive
rclone ls gdrive:lamy-backups/

# ดู backup ที่เก็บใน local
ls -lh /app/backups/lamy-db/
```

---

## สรุปสิ่งที่ระบบทำทุกวัน

```
04:00 น.   → สคริปต์รันอัตโนมัติ
            → SQLite safe backup (ไม่ต้องหยุด server)
            → บีบอัดเป็น .gz
            → อัปโหลดไป Google Drive (lamy-backups/)
            → ลบ backup local ที่เกิน 30 วัน
            → บันทึก log ที่ /var/log/lamy_backup.log
```
