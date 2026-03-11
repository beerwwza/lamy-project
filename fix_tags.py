import os
import re

template_path = r"d:\lamy\lamy-project\myapp\templates\myapp\equipment_data.html"

with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix the specific multi-line {% if %} blocks found near "อัปเดต:"
# Note: The issue is lines like:
# <p class="text-[10px] text-slate-500">อัปเดต: {% if latest_cbm.vibration
#                                                 %}{{ latest_cbm.vibration.inspection_date|date:"d M Y" }}{% else
#                                                 %}ยังไม่มีข้อมูล{% endif %}</p>

# Regex to find multi-line {% if ... %}...{% endif %} inside the 'อัปเดต:' block.
# Taking a simpler approach: just replace the literal strings since we know what they are.

targets = [
    ('vibration', r'อัปเดต: \{% if latest_cbm\.vibration\s+%\}\{\{ latest_cbm\.vibration\.inspection_date\|date:"d M Y" \}\}\{% else\s+%\}ยังไม่มีข้อมูล\{% endif %\}'),
    ('visual', r'อัปเดต: \{% if latest_cbm\.visual\s+%\}\{\{ latest_cbm\.visual\.inspection_date\|date:"d M Y" \}\}\{% else\s+%\}ยังไม่มีข้อมูล\{% endif %\}'),
    ('thermoscan', r'อัปเดต: \{% if latest_cbm\.thermoscan\s+%\}\{\{ latest_cbm\.thermoscan\.inspection_date\|date:"d M Y" \}\}\{% else\s+%\}ยังไม่มีข้อมูล\{% endif %\}'),
    ('oil', r'อัปเดต: \{% if latest_cbm\.oil\s+%\}\{\{ latest_cbm\.oil\.inspection_date\|date:"d M Y" \}\}\{% else\s+%\}ยังไม่มีข้อมูล\{% endif %\}'),
    ('acoustic', r'อัปเดต: \{% if latest_cbm\.acoustic\s+%\}\{\{ latest_cbm\.acoustic\.inspection_date\|date:"d M Y" \}\}\{% else\s+%\}ยังไม่มีข้อมูล\{% endif %\}'),
]

for key, pattern in targets:
    replacement = f'อัปเดต: {{% if latest_cbm.{key} %}}{{{{ latest_cbm.{key}.inspection_date|date:"d M Y" }}}}{{% else %}}ยังไม่มีข้อมูล{{% endif %}}'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Let's use a more generic approach to catch any split block tags:
# Replace {% \n with {%
content = re.sub(r'\{%\s*\n\s*', '{% ', content)
# Replace \n %} with %}
content = re.sub(r'\n\s*%\}', ' %}', content)


with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed multi-line template tags in equipment_data.html")

