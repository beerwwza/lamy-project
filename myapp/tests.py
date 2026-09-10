from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

# หน้าเพจหลักที่ไม่ต้อง login — ต้องไม่ error 500 แม้ยังไม่มี session
# (บั๊กจริงที่เจอ: login.html มี {% url 'register' %} แต่ path ถูก comment
#  ออกจาก urls.py ทำให้ NoReverseMatch ตอน render หน้าแรกของเว็บ)
PUBLIC_URL_NAMES = [
    'login',
    'register',
]

# หน้าเพจหลักหลัง login — ใช้ GET เฉย ๆ ไม่ต้องมี query param/object เฉพาะ
AUTHENTICATED_URL_NAMES = [
    'dashboard',
    'dashboard_api',
    'boiler',
    'operation_dashboard',
    'maintenance_dashboard',
    'mill',
    'lathe_dashboard',
    'equipment_data',
    'equipment_list',
    'equipment_form',
    'equipment_bom',
    'doc_repository',
    'inventory_dashboard',
    'inventory_list',
    'inventory_dept_summary',
    'inventory_tx_list',
    'inventory_readiness_list',
    'tools_dashboard',
    'tools_type_list',
    'tools_overdue_list',
    'training_overview',
    'training_employees',
    'training_exam',
    'training_matrix',
    'training_progress',
    'training_courses',
    'training_career',
    'training_gap',
    'manual_list',
    'machine_task_list',
]


class SmokeTestPagesLoad(TestCase):
    """
    เช็คว่าหน้าเพจหลักของระบบ render ได้โดยไม่ error 500
    (จับ NoReverseMatch / TemplateSyntaxError / view crash ก่อนขึ้น production)

    รันก่อน deploy ทุกครั้งด้วย: python manage.py test myapp
    """

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username='smoketest_admin', password='smoketest-pass-12345',
            email='smoketest@example.com',
        )

    def test_public_pages_do_not_500(self):
        client = Client()
        for name in PUBLIC_URL_NAMES:
            with self.subTest(url_name=name):
                response = client.get(reverse(name))
                self.assertLess(
                    response.status_code, 500,
                    f"หน้า '{name}' error {response.status_code} (ไม่ควร 500)",
                )

    def test_authenticated_pages_do_not_500(self):
        client = Client()
        client.force_login(self.superuser)
        for name in AUTHENTICATED_URL_NAMES:
            with self.subTest(url_name=name):
                response = client.get(reverse(name))
                self.assertLess(
                    response.status_code, 500,
                    f"หน้า '{name}' error {response.status_code} (ไม่ควร 500)",
                )
