import os, django
os.environ["DJANGO_SETTINGS_MODULE"] = "learning.settings"
django.setup()

from django.test import Client
from django.contrib.auth.models import User

c = Client(SERVER_NAME='localhost')
user = User.objects.first()
c.force_login(user)
resp = c.get('/dashboard/', HTTP_HOST='localhost')
content = resp.content.decode('utf-8', errors='replace')

# Find and print the json_script tags
import re
for m in re.finditer(r'<script id="server-[^"]*"[^>]*>(.*?)</script>', content, re.DOTALL):
    script_id = re.search(r'id="([^"]*)"', m.group(0)).group(1)
    print(f"\n=== {script_id} ===")
    print(m.group(1)[:300])
