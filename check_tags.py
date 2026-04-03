import re

with open(r'd:\lamy\lamy-project\myapp\templates\myapp\equipment_data.html', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
stack = []
for i, line in enumerate(lines):
    import re
    # Find all {% if ... %} and {% endif %}
    for match in re.finditer(r'{%\s*(if|endif)[\s%]', line):
        if match.group(1) == 'if':
            stack.append(i + 1)
        else:
            if stack:
                stack.pop()
            else:
                print(f"Extra endif at line {i + 1}")

if stack:
    print(f"Unclosed if tags starting at lines: {stack}")
else:
    print("All if tags are closed properly")
