import json
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
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
    'lathe_list',
    'lathe_add',
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


class LatheModuleTests(TestCase):
    """Lathe: สิทธิ์ (module_required('general') / superuser) และ flow add-edit-status-delete-import-export"""

    @classmethod
    def setUpTestData(cls):
        from .models import LatheJob
        cls.LatheJob = LatheJob
        cls.superuser = User.objects.create_superuser('lathe_admin', 'a@example.com', 'pass-12345-x')
        cls.writer = User.objects.create_user('lathe_writer', password='pass-12345-x', is_staff=True)
        cls.writer.user_permissions.add(Permission.objects.get(codename='write_general'))
        cls.staff_no_perm = User.objects.create_user('lathe_staff', password='pass-12345-x', is_staff=True)
        cls.reader = User.objects.create_user('lathe_reader', password='pass-12345-x')
        cls.job = LatheJob.objects.create(job_no='JOB-T-001', topic='กลึงเพลา', status='Pending', hours=1, pieces=2)

    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def _payload(self, **extra):
        data = {'date': '2026-10-08', 'requester': 'สมชาย', 'machine': 'กลึง1', 'topic': 'ทดสอบ',
                'job_type': ['ทำใหม่', 'ซ่อมแซม'], 'priority': 'Normal', 'status': 'Pending',
                'material_cost': '10.50', 'hours': '2', 'pieces': '3'}
        data.update(extra)
        return data

    def test_read_pages_open_to_any_logged_in_user(self):
        c = self._client(self.reader)
        for name in ('lathe_list', 'lathe_export'):
            self.assertEqual(c.get(reverse(name)).status_code, 200, name)
        self.assertEqual(c.get(reverse('lathe_print', args=[self.job.id])).status_code, 200)

    def test_write_requires_general_permission(self):
        for user in (self.reader, self.staff_no_perm):
            c = self._client(user)
            self.assertEqual(c.get(reverse('lathe_add')).status_code, 403)
            self.assertEqual(c.post(reverse('lathe_add'), self._payload()).status_code, 403)
            self.assertEqual(c.post(reverse('lathe_status_update', args=[self.job.id]), {'status': 'Done'}).status_code, 403)
        self.assertEqual(self.LatheJob.objects.count(), 1)

    def test_add_edit_status_flow(self):
        c = self._client(self.writer)
        self.assertNotContains(c.get(reverse('lathe_add')), 'name="job_no"')
        resp = c.post(reverse('lathe_add'), self._payload(job_no='HACK-1'))
        self.assertEqual(resp.status_code, 302)
        job = self.LatheJob.objects.exclude(pk=self.job.pk).get()
        self.assertRegex(job.job_no, r'^JOB-\d{4}-\d{3}$')
        self.assertEqual(job.job_type, 'ทำใหม่,ซ่อมแซม')
        self.assertEqual(job.updated_by, 'lathe_writer')

        resp = c.post(reverse('lathe_edit', args=[job.id]), self._payload(topic='แก้ไขแล้ว', job_no='IGNORED'))
        self.assertEqual(resp.status_code, 302)
        job.refresh_from_db()
        self.assertEqual(job.topic, 'แก้ไขแล้ว')
        self.assertNotEqual(job.job_no, 'IGNORED')

        c.post(reverse('lathe_status_update', args=[job.id]), {'status': 'Done'})
        job.refresh_from_db()
        self.assertEqual(job.status, 'Done')
        c.post(reverse('lathe_status_update', args=[job.id]), {'status': 'bogus'})
        job.refresh_from_db()
        self.assertEqual(job.status, 'Done')

    def test_negative_numbers_rejected(self):
        c = self._client(self.writer)
        resp = c.post(reverse('lathe_add'), self._payload(hours='-1'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.LatheJob.objects.count(), 1)

    def test_delete_superuser_only_and_post_only(self):
        url = reverse('lathe_delete', args=[self.job.id])
        self.assertEqual(self._client(self.writer).post(url).status_code, 403)
        self.assertEqual(self._client(self.superuser).get(url).status_code, 405)
        self.assertEqual(self._client(self.superuser).post(url).status_code, 302)
        self.assertFalse(self.LatheJob.objects.filter(pk=self.job.pk).exists())

    def test_export_and_import_roundtrip(self):
        c = self._client(self.writer)
        data = json.loads(c.get(reverse('lathe_export'), {'format': 'json'}).content)
        self.assertEqual(data['jobs'][0]['job_no'], 'JOB-T-001')
        csv_resp = c.get(reverse('lathe_export'))
        self.assertIn('JOB-T-001', csv_resp.content.decode('utf-8-sig'))

        payload = {'jobs': [{'job_no': 'JOB-IMP-1', 'topic': 'นำเข้า', 'status': 'Done', 'job_type': 'ทำใหม่',
                             'hours': '1.5', 'job_value': '250', 'attachment': 'DRIVEID123', 'attachment_name': 'a.pdf'},
                            {'job_no': 'JOB-IMP-2', 'status': 'not-a-status'}]}
        upload = SimpleUploadedFile('x.json', json.dumps(payload).encode(), content_type='application/json')
        self.assertEqual(c.post(reverse('lathe_import'), {'file': upload}).status_code, 302)
        imported = self.LatheJob.objects.get(job_no='JOB-IMP-1')
        self.assertEqual(imported.job_value, Decimal('250'))
        self.assertEqual((imported.attachment, imported.attachment_name), ('DRIVEID123', 'a.pdf'))
        self.assertFalse(self.LatheJob.objects.filter(job_no='JOB-IMP-2').exists())

    def test_import_requires_permission(self):
        upload = SimpleUploadedFile('x.csv', b'job_no\nJOB-X\n')
        self.assertEqual(self._client(self.staff_no_perm).post(reverse('lathe_import'), {'file': upload}).status_code, 403)

    def test_invalid_date_filter_does_not_500(self):
        resp = self._client(self.reader).get(reverse('lathe_list'), {'date_from': 'not-a-date'})
        self.assertEqual(resp.status_code, 302)

    # ── ฟอร์ม: เครื่องจักร / มูลค่า / ไฟล์แนบ ───────────────────────────────

    def test_form_has_no_checkbox_fields_and_machine_is_free_text(self):
        c = self._client(self.writer)
        html = c.get(reverse('lathe_add')).content.decode()
        for gone in ('has_drawing', 'has_sample', 'has_material', 'name="attachment"'):
            self.assertNotIn(gone, html)
        self.assertIn('name="attachment_file"', html)
        self.assertIn('<input type="text" name="machine"', html)
        c.post(reverse('lathe_add'), self._payload(machine='เครื่องกลึง CNC พิเศษ'))
        self.assertTrue(self.LatheJob.objects.filter(machine='เครื่องกลึง CNC พิเศษ').exists())

    def test_job_value_sums_factors_or_uses_manual_value(self):
        c = self._client(self.writer)
        c.post(reverse('lathe_add'), self._payload(
            topic='A', job_value='999', labor_cost='100', material_cost='50.5', machine_cost='20', service_cost='10'))
        a = self.LatheJob.objects.get(topic='A')
        self.assertEqual(a.job_value, Decimal('180.50'))
        c.post(reverse('lathe_add'), self._payload(
            topic='B', job_value='300', labor_cost='0', material_cost='0', machine_cost='0', service_cost='0'))
        self.assertEqual(self.LatheJob.objects.get(topic='B').job_value, Decimal('300'))
        resp = c.post(reverse('lathe_add'), self._payload(topic='C', labor_cost='-5'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.LatheJob.objects.filter(topic='C').exists())

    def test_upload_success_stores_drive_id_and_folder_path(self):
        c = self._client(self.writer)
        upload = SimpleUploadedFile('drawing.pdf', b'%PDF-1.4 test', content_type='application/pdf')
        with mock.patch('myapp.views._upload_to_drive', return_value='FILEID1') as up:
            resp = c.post(reverse('lathe_add'), self._payload(topic='UP', attachment_file=upload))
        self.assertEqual(resp.status_code, 302)
        job = self.LatheJob.objects.get(topic='UP')
        self.assertEqual((job.attachment, job.attachment_name), ('FILEID1', 'drawing.pdf'))
        self.assertEqual(job.attachment_url, 'https://drive.google.com/file/d/FILEID1/view')
        folder = up.call_args[0][2]
        self.assertRegex(folder, r'^LAMY/Lathe/\d{4}/' + job.job_no + '$')

    def test_upload_failure_saves_nothing(self):
        c = self._client(self.writer)
        upload = SimpleUploadedFile('x.pdf', b'data', content_type='application/pdf')
        with mock.patch('myapp.views._upload_to_drive', return_value=None):
            resp = c.post(reverse('lathe_add'), self._payload(topic='FAIL', attachment_file=upload))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'อัปโหลดไฟล์ไป Google Drive ไม่สำเร็จ')
        self.assertFalse(self.LatheJob.objects.filter(topic='FAIL').exists())

    def test_upload_failure_on_edit_keeps_old_data(self):
        c = self._client(self.writer)
        upload = SimpleUploadedFile('x.pdf', b'data', content_type='application/pdf')
        with mock.patch('myapp.views._upload_to_drive', return_value=None):
            resp = c.post(reverse('lathe_edit', args=[self.job.id]), self._payload(topic='CHANGED', attachment_file=upload))
        self.assertEqual(resp.status_code, 200)
        self.job.refresh_from_db()
        self.assertEqual(self.job.topic, 'กลึงเพลา')

    def test_upload_rejects_bad_extension(self):
        c = self._client(self.writer)
        upload = SimpleUploadedFile('virus.exe', b'MZ', content_type='application/octet-stream')
        with mock.patch('myapp.views._upload_to_drive', return_value='X') as up:
            resp = c.post(reverse('lathe_add'), self._payload(topic='EXE', attachment_file=upload))
        self.assertEqual(resp.status_code, 200)
        up.assert_not_called()
        self.assertFalse(self.LatheJob.objects.filter(topic='EXE').exists())

    def test_remove_attachment(self):
        self.job.attachment, self.job.attachment_name = 'OLD', 'old.pdf'
        self.job.save()
        c = self._client(self.writer)
        c.post(reverse('lathe_edit', args=[self.job.id]), self._payload(remove_attachment='on'))
        self.job.refresh_from_db()
        self.assertIsNone(self.job.attachment)
        self.assertIsNone(self.job.attachment_name)

    def test_print_page_shows_value_breakdown(self):
        self.job.job_value, self.job.labor_cost = Decimal('100'), Decimal('100')
        self.job.save()
        html = self._client(self.reader).get(reverse('lathe_print', args=[self.job.id])).content.decode()
        self.assertIn('มูลค่าชิ้นงาน', html)
        self.assertNotIn('มีแบบ Drawing', html)

    def test_maker_ranking_orders_by_pieces_with_ties_and_skips_blank(self):
        mk = lambda n, m, p: self.LatheJob.objects.create(job_no=n, maker=m, pieces=Decimal(p), hours=Decimal('1'))
        mk('R1', 'สมชาย', '10'); mk('R2', 'สมชาย', '5'); mk('R3', 'วิภา', '15')
        mk('R4', 'ประเสริฐ', '2'); mk('R5', 'นภา', '2'); mk('R6', '  ', '99')
        resp = self._client(self.reader).get(reverse('lathe_list'))
        ranking = [(r['rank'], r['name'], r['pieces']) for r in resp.context['maker_ranking']]
        self.assertEqual(ranking[:2], [(1, 'สมชาย', Decimal('15')), (1, 'วิภา', Decimal('15'))])  # เสมอกัน: ชั่วโมงมากกว่าขึ้นก่อน
        self.assertEqual([r[0] for r in ranking[2:]], [3, 3])
        self.assertNotIn('', [r[1].strip() for r in ranking])
        self.assertContains(resp, 'อันดับการผลิตชิ้นงาน')

    def test_maker_ranking_follows_list_filters(self):
        self.LatheJob.objects.create(job_no='F1', maker='สมชาย', pieces=Decimal('7'), machine='M1')
        self.LatheJob.objects.create(job_no='F2', maker='วิภา', pieces=Decimal('3'), machine='M2')
        resp = self._client(self.reader).get(reverse('lathe_list'), {'machine': 'M2'})
        self.assertEqual([r['name'] for r in resp.context['maker_ranking']], ['วิภา'])
