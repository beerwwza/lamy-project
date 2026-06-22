"""Quick test: run the dashboard view end-to-end and print any errors."""
import os, django, traceback
os.environ["DJANGO_SETTINGS_MODULE"] = "learning.settings"
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.template import TemplateSyntaxError

c = Client(SERVER_NAME='localhost')
user = User.objects.first()
if not user:
    print("ERROR: No user in database!")
else:
    c.force_login(user)
    try:
        resp = c.get('/dashboard/', HTTP_HOST='localhost')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500:
            print("=== 500 Error Content ===")
            print(resp.content[:5000].decode('utf-8', errors='replace'))
    except Exception as e:
        traceback.print_exc()

# Also test without login (should redirect)
c2 = Client(SERVER_NAME='localhost')
resp2 = c2.get('/dashboard/', HTTP_HOST='localhost')
print(f"Unauthenticated status: {resp2.status_code} (should be 302 redirect)")
