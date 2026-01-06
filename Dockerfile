# ใช้ Python 3.10 (หรือเปลี่ยนตามเวอร์ชันที่คุณใช้อยู่)
FROM python:3.10-slim

# ตั้งค่าพื้นฐาน
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# สร้างโฟลเดอร์ทำงานใน Docker
WORKDIR /app

# ติดตั้ง Library ตามไฟล์ requirements.txt ของคุณ
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# ก๊อปปี้โค้ดทั้งหมดเข้า Docker
COPY . /app/