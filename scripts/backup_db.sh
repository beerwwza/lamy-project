#!/bin/bash
# =============================================================
# LAMY — Daily Database Backup Script
# =============================================================
# ทำงาน: สำรอง db.sqlite3 ไว้ทั้ง Local และ Google Drive
# รองรับ: ลบ backup เก่าอัตโนมัติ, log ทุกครั้ง
# =============================================================

# --- CONFIG (แก้ไขตาม path จริงของ server) ---
PROJECT_DIR="/app/lamy-project"           # path โปรเจกต์บน server
BACKUP_LOCAL_DIR="/app/backups/lamy-db"  # โฟลเดอร์เก็บ backup local
GDRIVE_REMOTE="gdrive"                    # ชื่อ remote ของ rclone
GDRIVE_FOLDER="lamy-backups"             # ชื่อโฟลเดอร์ใน Google Drive
KEEP_DAYS=30                              # เก็บ backup กี่วัน (local)
LOG_FILE="/var/log/lamy_backup.log"       # ไฟล์ log

# --- ไม่ต้องแก้ไขด้านล่าง ---
DB_SOURCE="$PROJECT_DIR/db.sqlite3"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_LOCAL_DIR/lamy_db_${TIMESTAMP}.sqlite3"
LOG_DATE=$(date +"%Y-%m-%d %H:%M:%S")

# ฟังก์ชัน log
log() {
    echo "[$LOG_DATE] $1" | tee -a "$LOG_FILE"
}

log "====== เริ่ม backup ======"

# 1) ตรวจสอบว่า db.sqlite3 มีอยู่จริง
if [ ! -f "$DB_SOURCE" ]; then
    log "ERROR: ไม่พบไฟล์ $DB_SOURCE"
    exit 1
fi

# 2) สร้างโฟลเดอร์ backup ถ้ายังไม่มี
mkdir -p "$BACKUP_LOCAL_DIR"

# 3) Backup อย่างปลอดภัยด้วย SQLite .backup
#    (ทำงานได้แม้ระบบกำลัง write อยู่ — ไม่ต้องหยุด server)
log "กำลัง backup: $DB_SOURCE → $BACKUP_FILE"
sqlite3 "$DB_SOURCE" ".backup '$BACKUP_FILE'"

if [ $? -ne 0 ]; then
    log "ERROR: backup ล้มเหลว"
    exit 1
fi

# 4) บีบอัดด้วย gzip ประหยัดพื้นที่
gzip "$BACKUP_FILE"
COMPRESSED="${BACKUP_FILE}.gz"
SIZE=$(du -sh "$COMPRESSED" | cut -f1)
log "บีบอัดสำเร็จ: $COMPRESSED (ขนาด: $SIZE)"

# 5) อัปโหลดไป Google Drive ด้วย rclone
if command -v rclone &> /dev/null; then
    log "กำลังอัปโหลดไป Google Drive: ${GDRIVE_REMOTE}:${GDRIVE_FOLDER}/"
    rclone copy "$COMPRESSED" "${GDRIVE_REMOTE}:${GDRIVE_FOLDER}/" --log-level INFO 2>> "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log "อัปโหลด Google Drive สำเร็จ"
    else
        log "WARNING: อัปโหลด Google Drive ล้มเหลว (local backup ยังมีอยู่)"
    fi
else
    log "WARNING: ไม่พบ rclone — ข้าม Google Drive upload"
fi

# 6) ลบ backup local ที่เก่ากว่า KEEP_DAYS วัน
DELETED=$(find "$BACKUP_LOCAL_DIR" -name "*.sqlite3.gz" -mtime +$KEEP_DAYS -print)
if [ -n "$DELETED" ]; then
    find "$BACKUP_LOCAL_DIR" -name "*.sqlite3.gz" -mtime +$KEEP_DAYS -delete
    log "ลบ backup เก่า (เกิน ${KEEP_DAYS} วัน):"
    echo "$DELETED" | while read f; do log "  - $f"; done
fi

# 7) แสดงรายการ backup ที่มีอยู่
TOTAL=$(ls -1 "$BACKUP_LOCAL_DIR"/*.sqlite3.gz 2>/dev/null | wc -l)
log "backup ที่เก็บอยู่ใน local: $TOTAL ไฟล์"
log "====== backup เสร็จสิ้น ======"
echo ""
