import re

path = r'd:\lamy\lamy-project\myapp\templates\myapp\equipment_data.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Make sure all forms have method, action, csrf, and cbm_type
# 1. Visual
html = re.sub(
    r'<form class="grid grid-cols-1 md:grid-cols-2 gap-6"\s*onsubmit="event.preventDefault\(\); alert\(\'บันทึก Visual Test สำเร็จ\'\);">',
    r'<form class="grid grid-cols-1 md:grid-cols-2 gap-6" method="POST" action="{% url \'equipment_cbm\' equipment.equipment_id %}" enctype="multipart/form-data">\n                                {% csrf_token %}\n                                <input type="hidden" name="cbm_type" value="visual">',
    html
)
html = re.sub(
    r'<input type="date"\s*class="pl-10 block w-full[^>]+value="2024-03-10">',
    r'{{ form_visual.inspection_date }}',
    html, count=1 # First one is visual
)
html = re.sub(r'<input type="text" value="นายสมชาย \(ME\)"[^>]+>', r'{{ form_visual.inspector }}', html)
html = re.sub(r'<select[^>]+>\s*<option value="good">ปกติ \(Good - No Action\)</option>\s*<option value="fair">เฝ้าระวัง \(Fair - Monitor\)</option>\s*<option value="poor">ผิดปกติ \(Poor - Action Required\)</option>\s*</select>', r'{{ form_visual.overall_condition }}', html)
html = re.sub(r'<textarea rows="3"[^>]+placeholder="ระบุสิ่งที่พบผิดปกติ\.\.\."></textarea>', r'{{ form_visual.remark }}', html)
html = re.sub(r'<input type="file" accept="image/\*"[^>]+border-slate-300 rounded-md bg-white p-2">', r'{{ form_visual.image_attachment }}', html, count=1)

# 2. Vibration
html = re.sub(
    r'<form class="grid grid-cols-1 md:grid-cols-3 gap-6"\s*onsubmit="event.preventDefault\(\); alert\(\'บันทึก Vibration สำเร็จ\'\);">',
    r'<form class="grid grid-cols-1 md:grid-cols-3 gap-6" method="POST" action="{% url \'equipment_cbm\' equipment.equipment_id %}">\n                                {% csrf_token %}\n                                <input type="hidden" name="cbm_type" value="vibration">',
    html
)
html = re.sub(r'<input type="date"\s*class="pl-10[^>]+value="2024-03-10">', r'{{ form_vibration.inspection_date }}', html, count=1)
html = re.sub(r'<input type="text" value="นายสมศักดิ์ \(ทีม CBM\)"[^>]+>', r'{{ form_vibration.inspector }}', html, count=1)
html = re.sub(r'<select[^>]+>\s*<option>Pump - Drive End \(ฝั่งขับ\)</option>\s*<option>Pump - Non-Drive End \(ฝั่งตรงข้ามขับ\)</option>\s*<option>Motor - Drive End</option>\s*<option>Motor - Non-Drive End</option>\s*</select>', r'{{ form_vibration.measurement_point }}', html)
html = re.sub(r'<input type="number" step="0\.01"\s*class="w-full[^>]+placeholder="ความเร็วการสั่น">', r'{{ form_vibration.velocity }}', html)
html = re.sub(r'<input type="number" step="0\.01"\s*class="w-full[^>]+placeholder="ความเร่งการสั่น">', r'{{ form_vibration.acceleration }}', html)
html = re.sub(r'<input type="number" step="0\.1"\s*class="w-full[^>]+placeholder="อุณหภูมิแบริ่ง">', r'{{ form_vibration.bearing_temp }}', html)
html = re.sub(r'<select[^>]+>\s*<option value="normal">Normal \(อยู่ในเกณฑ์มาตรฐาน ISO\)</option>\s*<option value="warning">Warning \(เฝ้าระวัง/เริ่มมีปัญหา\)</option>\s*<option value="alarm">Alarm \(อันตราย/ต้องวางแผนซ่อม\)</option>\s*</select>', r'{{ form_vibration.status }}', html)

# 3. Thermoscan
html = re.sub(
    r'<form class="grid grid-cols-1 md:grid-cols-3 gap-6"\s*onsubmit="event.preventDefault\(\); alert\(\'บันทึก Thermography สำเร็จ\'\);">',
    r'<form class="grid grid-cols-1 md:grid-cols-3 gap-6" method="POST" action="{% url \'equipment_cbm\' equipment.equipment_id %}" enctype="multipart/form-data">\n                                {% csrf_token %}\n                                <input type="hidden" name="cbm_type" value="thermoscan">',
    html
)
html = re.sub(r'<input type="date"\s*class="pl-10[^>]+value="2024-03-10">', r'{{ form_thermoscan.inspection_date }}', html, count=1)
html = re.sub(r'<input type="text" value="นายสมศักดิ์ \(ทีม CBM\)"[^>]+>', r'{{ form_thermoscan.inspector }}', html, count=1)
html = re.sub(r'<input type="text"\s*class="block w-full[^>]+placeholder="เช่น Motor Terminal Box, Pump Bearing">', r'{{ form_thermoscan.location_target }}', html)
html = re.sub(r'<input type="number" step="0.1"\s*class="block w-full[^>]+placeholder="อุณหภูมิจุดที่ร้อนที่สุด">', r'{{ form_thermoscan.max_temp }}', html)
html = re.sub(r'<input type="number" step="0.1"\s*class="block w-full[^>]+placeholder="อุณหภูมิอ้างอิง">', r'{{ form_thermoscan.ambient_temp }}', html)
html = re.sub(r'<input type="number" step="0.1"\s*readonly\s*class="block w-full[^>]+placeholder="ระบบคำนวณอัตโนมัติ">', r'{{ form_thermoscan.delta_t }}', html)
html = re.sub(r'<input type="file" accept="image/\*"[^>]+border-slate-300 rounded-md bg-white p-2">', r'{{ form_thermoscan.image_attachment }}', html, count=1)

# 4. Oil Analysis
html = re.sub(
    r'<form class="grid grid-cols-1 md:grid-cols-2 gap-6"\s*onsubmit="event.preventDefault\(\); alert\(\'บันทึก Oil Analysis สำเร็จ\'\);">',
    r'<form class="grid grid-cols-1 md:grid-cols-2 gap-6" method="POST" action="{% url \'equipment_cbm\' equipment.equipment_id %}" enctype="multipart/form-data">\n                                {% csrf_token %}\n                                <input type="hidden" name="cbm_type" value="oil">',
    html
)
html = re.sub(r'<input type="date"\s*class="pl-10[^>]+value="2024-03-10">', r'{{ form_oil.collection_date }}', html, count=1)
html = re.sub(r'<input type="text" value="นายสมศักดิ์ \(ทีม CBM\)"[^>]+>', r'{{ form_oil.inspector }}', html, count=1)
html = re.sub(r'<input type="text" value="ISO VG 68"[^>]+>', r'{{ form_oil.oil_type }}', html)
html = re.sub(r'<input type="number" step="0\.1"\s*class="block w-full[^>]+placeholder="เช่น 65\.5">', r'{{ form_oil.viscosity }}', html)
html = re.sub(r'<input type="number" step="0\.01"\s*class="block w-full[^>]+placeholder="เช่น 0\.05">', r'{{ form_oil.water_content }}', html)
# This was added manually to the regex: <input type="text" class="block w-full ... placeholder="เช่น 18/16/13 หรือ พบอนุภาคเหล็กสูง">
html = re.sub(r'<input type="text"\s*class="block w-full[^>]+placeholder="เช่น 18/16/13 หรือ พบอนุภาคเหล็กสูง">', r'{{ form_oil.wear_particle }}', html)
html = re.sub(r'<input type="file" accept="\.pdf"[^>]+border-slate-300 rounded-md bg-white p-2">', r'{{ form_oil.lab_report }}', html, count=1)

# 5. Acoustic
html = re.sub(
    r'<form class="grid grid-cols-1 md:grid-cols-2 gap-6"\s*onsubmit="event.preventDefault\(\); alert\(\'บันทึก Acoustic สำเร็จ\'\);">',
    r'<form class="grid grid-cols-1 md:grid-cols-2 gap-6" method="POST" action="{% url \'equipment_cbm\' equipment.equipment_id %}" enctype="multipart/form-data">\n                                {% csrf_token %}\n                                <input type="hidden" name="cbm_type" value="acoustic">',
    html
)
html = re.sub(r'<input type="date"\s*class="pl-10[^>]+value="2024-03-10">', r'{{ form_acoustic.inspection_date }}', html, count=1)
html = re.sub(r'<input type="text" value="นายสมศักดิ์ \(ทีม CBM\)"[^>]+>', r'{{ form_acoustic.inspector }}', html, count=1)
html = re.sub(r'<input type="text"\s*class="block w-full[^>]+placeholder="เช่น Bearing Housing">', r'{{ form_acoustic.inspection_point }}', html)
html = re.sub(r'<input type="number" step="0\.1"\s*class="block w-full[^>]+placeholder="ค่าความดังที่วัดได้">', r'{{ form_acoustic.decibel }}', html)
html = re.sub(r'<select[^>]+>\s*<option value="normal">เสียงราบเรียบปกติ \(Smooth\)</option>\s*<option value="hissing">เสียงฟู่/รั่ว \(Hissing\)</option>\s*<option value="rubbing">เสียงเสียดสีต่อเนื่อง \(Rubbing\)</option>\s*<option value="impacting">เสียงกระแทก/แตกหัก \(Impacting/Clicking\)</option>\s*</select>', r'{{ form_acoustic.sound_pattern }}', html)
html = re.sub(r'<input type="file" accept="audio/\*,\.pdf"[^>]+border-slate-300 rounded-md bg-white p-2">', r'{{ form_acoustic.audio_attachment }}', html, count=1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated equipment_data.html successfully")
