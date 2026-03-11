import os
import re

path = r'd:\lamy\lamy-project\myapp\templates\myapp\equipment_form.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

replacements = {
    'รหัสเครื่องจักร (Equipment ID)': 'equipment_id',
    'ชื่อเครื่องจักร (Equipment Name)': 'name',
    'ตำแหน่งที่ตั้ง (Location)': 'location',
    'สังกัดเครื่องจักรหลัก (Belongs To)': 'belongs_to',
    'รหัสสินค้า/รุ่น (Model)': 'model',
    'ผู้ผลิต (Manufacturer)': 'manufacturer',
    'หมายเลขเครื่อง (Serial No.)': 'serial_no',
    'ความจุ / อัตราไหล (Capacity)': 'capacity',
    'ระยะส่ง / ขนาด (Head/Size)': 'head_size',
    'ความเร็วรอบ (RPM)': 'rpm',
    'วันที่ติดตั้ง (Installation Date)': 'installation_date',
    'วันหมดประกัน (Warranty EXP)': 'warranty_exp',
    'ราคาซื้อ (Purchase Price)': 'purchase_price',
    'ราคาซ่อมทดแทน (Replacement Cost)': 'replacement_cost',
    'ระดับความสำคัญ (Priority Level)': 'priority_level',
    'MTBF (ระยะเวลาเฉลี่ยก่อนเสีย)': 'mtbf',
    'MTTR (เวลารวมที่หยุดซ่อม)': 'mttr',
    'ค่าใช้จ่ายสะสม BM+PM (Acc. Cost)': 'acc_cost'
}

for label, field_name in replacements.items():
    pattern = r'<label class=\"form-label small mb-1\">\s*' + re.escape(label) + r'\s*(<span class=\"text-danger\">\w*</span>)?\s*</label>'
    replacement = f'<label class="form-label small mb-1">{{{{ form.{field_name}.label }}}}\g<1></label>'
    
    html = re.sub(pattern, replacement, html)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated labels in equipment_form.html successfully!")
