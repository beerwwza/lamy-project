"""สคริปต์ตรวจ Lathe แบบเร็ว (ไม่ใช่ test suite หลัก — ใช้ `python manage.py test myapp` แทน)

รัน: python test_lathe.py
ใช้ test database ชั่วคราวผ่าน Django test runner จึงไม่แตะ db.sqlite3 จริง
"""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learning.settings")
django.setup()

from django.test.utils import get_runner
from django.conf import settings

if __name__ == "__main__":
    TestRunner = get_runner(settings)
    failures = TestRunner(verbosity=1).run_tests(["myapp.tests.LatheModuleTests"])
    sys.exit(bool(failures))
