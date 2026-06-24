#!/bin/bash
# =============================================================
# LAMY — Database Restore Script
# =============================================================
# วิธีใช้: ./restore_db.sh <ชื่อไฟล์ backup>
# ตัวอย่าง: ./restore_db.sh lamy_db_2025-01-15_02-00-00.sqlite3.gz
# =============================================================

PROJECT_DIR="/app/lamy-project"
BACKUP_LOCAL_DIR="/app/backups/lamy-db"
DB_TARGET="$PROJECT_DIR/db.sqlite3"
LOG_FILE="/var/log/lamy_backup.log"
LOG_DATE=$(date +"%Y-%m-%d %H:%M:%S")

log() {
    echo "[$LOG_DATE] $1" | tee -a "$LOG_FILE"
}

# ตรวจ argument
if [ -z "$1" ]; then
    echo "วิธีใช้: $0 <ชื่อไฟล์ backup>"
    echo ""
    echo "ไฟล์ backup ที่มีอยู่:"
    ls -lh "$BACKUP_LOCAL_DIR"/*.sqlite3.gz 2>/dev/null || echo "  ไม่มีไฟล์ backup"
    exit 1
fi

BACKUP_FILE="$BACKUP_LOCAL_DIR/$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: ไม่พบไฟล์ $BACKUP_FILE"
    exit 1
fi

# ยืนยันก่อน restore
echo "คำเตือน: จะแทนที่ db.sqlite3 ปัจจุบันด้วย $1"
read -p "ยืนยัน? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "ยกเลิก"
    exit 0
fi

log "====== เริ่ม restore ======"
log "ไฟล์ที่จะ restore: $BACKUP_FILE"

# 1) สำรอง db ปัจจุบันก่อน restore
CURRENT_BACKUP="$BACKUP_LOCAL_DIR/before_restore_$(date +%Y%m%d_%H%M%S).sqlite3"
log "สำรอง db ปัจจุบันไว้ที่: $CURRENT_BACKUP"
sqlite3 "$DB_TARGET" ".backup '$CURRENT_BACKUP'"
gzip "$CURRENT_BACKUP"

# 2) แตกไฟล์ gz
TEMP_FILE="/tmp/lamy_restore_$$.sqlite3"
log "แตกไฟล์ backup..."
gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"

# 3) แทนที่ db
cp "$TEMP_FILE" "$DB_TARGET"
rm "$TEMP_FILE"

log "Restore สำเร็จ"
log "หมายเหตุ: restart Docker เพื่อให้ระบบรับรู้การเปลี่ยนแปลง"
log "  docker-compose restart web"
log "====== restore เสร็จสิ้น ======"
