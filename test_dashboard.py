import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learning.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from myapp import views

rf = RequestFactory()
req = rf.get("/dashboard/")
req.user = User.objects.first()
try:
    resp = views.dashboard(req)
    print("SUCCESS:", resp.status_code)
except Exception as e:
    import traceback
    traceback.print_exc()
