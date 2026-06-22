import os
import django
os.environ["DJANGO_SETTINGS_MODULE"] = "learning.settings"
django.setup()

from django.test import Client
from django.contrib.auth.models import User

c = Client(SERVER_NAME='localhost')
user = User.objects.first()
if not user:
    print("No user found!")
else:
    print(f"Testing with user: {user.username}")
    c.force_login(user)
    resp = c.get('/dashboard/', HTTP_HOST='localhost')
    print('Status:', resp.status_code)
    if resp.status_code != 200:
        print('Content:', resp.content[:3000].decode('utf-8', errors='replace'))
    else:
        content = resp.content.decode('utf-8', errors='replace')
        print('Page length:', len(content))
        if 'Error' in content or 'error' in content[:500]:
            print('Possible error in first 500 chars:', content[:500])
        print('Has React root:', '<div id="root">' in content)
        print('Has mill data:', 'server-mill-data' in content)
        print('Has boiler data:', 'server-boiler-data' in content)
