import json
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import MaterialMaster

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
    'me_inspection_list',
    'me_inspection_add',
    'me_inspection_dashboard',
    'me_equipment_import',
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


class METoleranceTests(TestCase):
    """ME Inspection: เกณฑ์ผ่าน/เฝ้าระวัง/ไม่ผ่าน ต้องตรงกับฟอร์ม ME เดิม (JS) ที่ขอบทุกเกณฑ์"""

    def test_runout_limit_is_inclusive_and_symmetric(self):
        from .models import me_runout_status
        self.assertEqual(me_runout_status(Decimal('0.05')), 'pass')
        self.assertEqual(me_runout_status('-0.05'), 'pass')
        self.assertEqual(me_runout_status(0.0501), 'fail')
        self.assertIsNone(me_runout_status(None))
        self.assertIsNone(me_runout_status(''))

    def test_alignment_limit(self):
        from .models import me_alignment_status
        self.assertEqual(me_alignment_status(Decimal('-0.06')), 'pass')
        self.assertEqual(me_alignment_status(Decimal('0.061')), 'fail')

    def test_vibration_limits_depend_on_motor_kw(self):
        from .models import me_vibration_status
        # มอเตอร์ไม่เกิน 15 kW (หรือไม่ระบุ): 1.8 / 2.8
        self.assertEqual(me_vibration_status('1.8', Decimal('15')), 'pass')
        self.assertEqual(me_vibration_status('2.8', Decimal('15')), 'warn')
        self.assertEqual(me_vibration_status('2.81', Decimal('15')), 'fail')
        self.assertEqual(me_vibration_status('2.0', None), 'warn')
        # มอเตอร์เกิน 15 kW: 2.8 / 4.5
        self.assertEqual(me_vibration_status('2.8', Decimal('15.01')), 'pass')
        self.assertEqual(me_vibration_status('4.5', Decimal('15.01')), 'warn')
        self.assertEqual(me_vibration_status('4.51', Decimal('15.01')), 'fail')

    def test_temperature_limits(self):
        from .models import me_temp_status
        self.assertEqual(me_temp_status(70), 'pass')
        self.assertEqual(me_temp_status(70.01), 'warn')
        self.assertEqual(me_temp_status(85), 'warn')
        self.assertEqual(me_temp_status(85.01), 'fail')

    def test_iso_tolerance_band_boundaries(self):
        from .models import me_iso_tolerance_um
        self.assertEqual(me_iso_tolerance_um(18, 'K7'), (-12, 6))
        self.assertEqual(me_iso_tolerance_um(18.001, 'K7'), (-15, 6))
        self.assertEqual(me_iso_tolerance_um(18, 'k7'), (1, 19))  # ตัวพิมพ์ต่างกัน = คนละพิกัด
        self.assertEqual(me_iso_tolerance_um(500, 'h7'), (-57, 0))  # เกิน 400 ใช้ช่วงสุดท้าย
        self.assertIsNone(me_iso_tolerance_um(0, 'H7'))
        self.assertIsNone(me_iso_tolerance_um(None, 'H7'))
        self.assertIsNone(me_iso_tolerance_um(50, 'X9'))

    def test_iso_fit_evaluates_readings_with_slack(self):
        from .models import me_iso_fit
        # 50 h7 → 49.975 – 50.000 (เผื่อ 0.0001)
        res = me_iso_fit(Decimal('50'), Decimal('49.975'), Decimal('50.000'), 'h7')
        self.assertAlmostEqual(res['min_mm'], 49.975)
        self.assertAlmostEqual(res['max_mm'], 50.0)
        self.assertEqual(res['status'], 'pass')
        self.assertAlmostEqual(res['average'], 49.9875)
        self.assertAlmostEqual(res['ovality'], 0.025)
        self.assertEqual(me_iso_fit(50, 50.0001, None, 'h7')['status'], 'pass')
        self.assertEqual(me_iso_fit(50, 50.0002, None, 'h7')['status'], 'fail')
        self.assertIsNone(me_iso_fit(50, 50.0002, None, 'h7')['ovality'])
        self.assertIsNone(me_iso_fit(50, None, None, 'h7')['status'])
        self.assertIsNone(me_iso_fit(None, 50, 50, 'h7'))

    def test_worst_status_ignores_blanks(self):
        from .models import me_worst_status
        self.assertEqual(me_worst_status(['pass', None, 'warn']), 'warn')
        self.assertEqual(me_worst_status(['warn', 'fail', 'pass']), 'fail')
        self.assertIsNone(me_worst_status([None, '']))



class MEInspectionModuleTests(TestCase):
    """ME Inspection: สิทธิ์ (write_maintenance / write_cbm / superuser), สร้าง-แก้ใบงาน และ API ค้นหาเครื่องจักร"""

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment, MEInspection
        cls.MEInspection = MEInspection
        cls.superuser = User.objects.create_superuser('me_admin', 'me@example.com', 'pass-12345-x')
        cls.tech = User.objects.create_user('me_tech', password='pass-12345-x', is_staff=True)
        cls.tech.user_permissions.add(Permission.objects.get(codename='write_maintenance'))
        cls.cbm = User.objects.create_user('me_cbm', password='pass-12345-x', is_staff=True)
        cls.cbm.user_permissions.add(Permission.objects.get(codename='write_cbm'))
        cls.staff_no_perm = User.objects.create_user('me_staff', password='pass-12345-x', is_staff=True)
        cls.reader = User.objects.create_user('me_reader', password='pass-12345-x')
        cls.pump = Equipment.objects.create(
            equipment_id='P-101', name='ปั๊มน้ำดิบ', process='ระบบน้ำ', manufacturer='Grundfos',
            model='NK 80', capacity='120', head_size='35 m', power_kw=Decimal('22'), rpm='2950')
        Equipment.objects.create(equipment_id='P-102', name='ปั๊มสำรอง (ปลดระวาง)', process='ระบบน้ำ', is_active=False)
        cls.inspection = MEInspection.objects.create(equipment=cls.pump, created_by='me_tech')

    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def _payload(self, **extra):
        data = {'equipment': 'P-101', 'record_date': '2026-11-03', 'repair_group': 'G2',
                'department': 'ระบบน้ำ', 'brand': 'Grundfos', 'model_no': 'NK 80',
                'flow_m3h': '120', 'head_m': '35', 'motor_kw': '22', 'rpm': '2950', 'remark': 'เปลี่ยนลูกปืน'}
        data.update(extra)
        return data

    def test_writers_can_create_and_are_redirected_to_edit(self):
        for user in (self.tech, self.cbm, self.superuser):
            with self.subTest(user=user.username):
                resp = self._client(user).post(reverse('me_inspection_add'), self._payload())
                created = self.MEInspection.objects.latest('id')
                self.assertRedirects(resp, reverse('me_inspection_edit', args=[created.pk]))
                self.assertEqual(created.created_by, user.username)
                self.assertEqual(created.updated_by, user.username)
                self.assertEqual(created.status, 'repairing')
                self.assertEqual(created.motor_kw, Decimal('22'))

    def test_users_without_write_permission_cannot_create_or_edit(self):
        for user in (self.reader, self.staff_no_perm):
            with self.subTest(user=user.username):
                c = self._client(user)
                self.assertEqual(c.post(reverse('me_inspection_add'), self._payload()).status_code, 403)
                self.assertEqual(c.get(reverse('me_inspection_add')).status_code, 403)
                resp = c.post(reverse('me_inspection_edit', args=[self.inspection.pk]), self._payload(remark='แอบแก้'))
                self.assertEqual(resp.status_code, 403)
        self.inspection.refresh_from_db()
        self.assertIsNone(self.inspection.remark)

    def test_any_logged_in_user_can_view_list_and_inspection_read_only(self):
        c = self._client(self.reader)
        self.assertContains(c.get(reverse('me_inspection_list')), f'ME-{self.inspection.pk}')
        resp = c.get(reverse('me_inspection_edit', args=[self.inspection.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['can_edit'])
        self.assertEqual(Client().get(reverse('me_inspection_list')).status_code, 302)  # ต้อง login

    def test_edit_updates_record_and_updated_by(self):
        resp = self._client(self.cbm).post(reverse('me_inspection_edit', args=[self.inspection.pk]), self._payload(remark='ตรวจซ้ำ'))
        self.assertRedirects(resp, reverse('me_inspection_edit', args=[self.inspection.pk]))
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.remark, 'ตรวจซ้ำ')
        self.assertEqual(self.inspection.updated_by, 'me_cbm')
        self.assertEqual(self.inspection.created_by, 'me_tech')

    def test_missing_or_unknown_equipment_is_a_form_error(self):
        c = self._client(self.tech)
        before = self.MEInspection.objects.count()
        for value in ('', 'NOPE-999'):
            with self.subTest(equipment=value):
                resp = c.post(reverse('me_inspection_add'), self._payload(equipment=value))
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.context['form'].errors['equipment'])
        self.assertEqual(self.MEInspection.objects.count(), before)

    def test_add_prefills_snapshot_from_equipment(self):
        resp = self._client(self.tech).get(reverse('me_inspection_add'), {'equipment': 'P-101'})
        initial = resp.context['form'].initial
        self.assertEqual(initial['brand'], 'Grundfos')
        self.assertEqual(initial['flow_m3h'], Decimal('120'))
        self.assertIsNone(initial['head_m'])  # '35 m' แปลงเป็นตัวเลขไม่ได้ ปล่อยว่างให้ช่างกรอก
        self.assertEqual(initial['rpm'], Decimal('2950'))

    def test_record_date_defaults_to_thai_local_date(self):
        from datetime import datetime, timezone as dt_timezone
        from django.utils import timezone
        # 17:30 UTC = 00:30 ของวันถัดไปตามเวลาไทย
        utc_now = datetime(2026, 11, 2, 17, 30, tzinfo=dt_timezone.utc)
        with mock.patch.object(timezone, 'now', return_value=utc_now):
            resp = self._client(self.tech).get(reverse('me_inspection_add'))
            obj = self.MEInspection.objects.create(equipment=self.pump)
        self.assertEqual(str(resp.context['form'].initial['record_date']), '2026-11-03')
        self.assertEqual(str(obj.record_date), '2026-11-03')

    def test_equipment_search_returns_active_matches_only(self):
        c = self._client(self.reader)
        data = c.get(reverse('me_equipment_search_api'), {'q': 'ปั๊ม'}).json()['data']
        self.assertEqual([d['id'] for d in data], ['P-101'])
        self.assertEqual(data[0]['kw'], '22.00')
        self.assertEqual(data[0]['department'], 'ระบบน้ำ')
        self.assertEqual(c.get(reverse('me_equipment_search_api'), {'process': 'ลูกหีบ'}).json()['data'], [])

    def test_equipment_search_is_limited(self):
        from .models import Equipment
        Equipment.objects.bulk_create([Equipment(equipment_id=f'X-{i:03d}', name=f'เกียร์ {i}') for i in range(40)])
        data = self._client(self.reader).get(reverse('me_equipment_search_api'), {'q': 'เกียร์'}).json()['data']
        self.assertEqual(len(data), 30)


class MEInspectionPartsAndMemoryTests(TestCase):
    """ME Inspection ticket 03: ช่องอะไหล่, รูปก่อน/หลัง และ smart memory API"""

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment, MEInspection
        cls.MEInspection = MEInspection
        cls.tech = User.objects.create_user('me3_tech', password='pass-12345-x', is_staff=True)
        cls.tech.user_permissions.add(Permission.objects.get(codename='write_maintenance'))
        cls.reader = User.objects.create_user('me3_reader', password='pass-12345-x')
        cls.pump = Equipment.objects.create(equipment_id='P-201', name='ปั๊มป้อนหม้อน้ำ', process='หม้อน้ำ 20 Bar')
        cls.other = Equipment.objects.create(equipment_id='P/202', name='ปั๊มรหัสมีทับ', process='หม้อน้ำ 20 Bar')
        cls.older = MEInspection.objects.create(
            equipment=cls.pump, record_date='2026-09-01', repair_group='G1', bearing_de_no='6205')
        cls.latest = MEInspection.objects.create(
            equipment=cls.pump, record_date='2026-10-15', repair_group='G3',
            bearing_de_no='6306-2RS', bearing_de_action='replace', oil_seal_nde_action='replace',
            seal_device_type='mech_seal', seal_device_action='replace',
            sleeve_od_mm=Decimal('45.000'), shaft_de_nominal=Decimal('30.000'), impeller_action='keep')
        MEInspection.objects.create(equipment=cls.other, record_date='2026-12-01', bearing_de_no='9999')

    def setUp(self):
        import shutil, tempfile
        from django.test import override_settings
        self._media = tempfile.mkdtemp()
        self._override = override_settings(MEDIA_ROOT=self._media)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(shutil.rmtree, self._media, ignore_errors=True)

    def _client(self, user):
        c = Client()
        c.force_login(user)
        return c

    def _api(self, eq_id, **params):
        return self._client(self.reader).get(reverse('me_inspection_last_api', args=[eq_id]), params)

    def test_last_api_returns_latest_inspection_of_that_machine(self):
        data = self._api('P-201').json()['data']
        self.assertEqual(data['inspection_id'], self.latest.pk)
        self.assertEqual(data['record_date'], '2026-10-15')
        self.assertEqual(data['repair_group'], 'G3')
        self.assertEqual(data['fields']['bearing_de_no'], '6306-2RS')
        self.assertEqual(data['fields']['sleeve_od_mm'], '45.000')
        self.assertEqual(data['fields']['shaft_de_nominal'], '30.000')
        self.assertNotIn('bearing_de_action', data['fields'])  # ไม่ดึงผลการเปลี่ยน มาเฉพาะสเปค
        self.assertNotIn('lube_grade', data['fields'])  # ช่องว่างไม่ส่ง
        self.assertEqual(data['replaced'], ['ลูกปืน DE', 'ออยซีล', 'แมคซีล'])

    def test_last_api_exclude_and_empty_and_slash_ids(self):
        self.assertEqual(self._api('P-201', exclude=self.latest.pk).json()['data']['inspection_id'], self.older.pk)
        self.assertIsNone(self._api('NO-SUCH').json()['data'])
        self.assertEqual(self._api('P/202').json()['data']['fields']['bearing_de_no'], '9999')

    def test_last_api_requires_login(self):
        self.assertEqual(Client().get(reverse('me_inspection_last_api', args=['P-201'])).status_code, 302)

    def _png_bytes(self):
        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.new('RGB', (20, 10), 'red').save(buf, format='PNG')
        return buf.getvalue()

    def _payload(self, **extra):
        data = {'equipment': 'P-201', 'record_date': '2026-11-03', 'bearing_de_no': '6306',
                'bearing_de_action': 'replace', 'impeller_action': 'keep', 'impeller_reason': '',
                'sleeve_od_mm': '45.125', 'coupling_type': 'jaw', 'sight_glass_action': 'none'}
        data.update(extra)
        return data

    def test_create_saves_parts_and_photos(self):
        photo = SimpleUploadedFile('before.png', self._png_bytes(), content_type='image/png')
        resp = self._client(self.tech).post(reverse('me_inspection_add'), self._payload(photo_before=photo))
        created = self.MEInspection.objects.latest('id')
        self.assertRedirects(resp, reverse('me_inspection_edit', args=[created.pk]))
        self.assertEqual(created.bearing_de_action, 'replace')
        self.assertEqual(created.sleeve_od_mm, Decimal('45.125'))
        self.assertEqual(created.coupling_type, 'jaw')
        self.assertEqual(created.sight_glass_action, 'none')
        self.assertTrue(created.photo_before.name.startswith('me_inspection/photos/'))
        self.assertFalse(created.photo_after)

    def test_edit_without_new_photo_keeps_existing(self):
        photo = SimpleUploadedFile('after.png', self._png_bytes(), content_type='image/png')
        self._client(self.tech).post(reverse('me_inspection_edit', args=[self.latest.pk]), self._payload(photo_after=photo))
        self.latest.refresh_from_db()
        saved = self.latest.photo_after.name
        self.assertTrue(saved)
        self._client(self.tech).post(reverse('me_inspection_edit', args=[self.latest.pk]), self._payload(remark='แก้ข้อความ'))
        self.latest.refresh_from_db()
        self.assertEqual(self.latest.photo_after.name, saved)

    def test_non_image_or_oversized_photo_is_form_error(self):
        c = self._client(self.tech)
        before = self.MEInspection.objects.count()
        fake = SimpleUploadedFile('x.jpg', b'not an image', content_type='image/jpeg')
        resp = c.post(reverse('me_inspection_add'), self._payload(photo_before=fake))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['form'].errors['photo_before'])
        with mock.patch('myapp.forms.ME_PHOTO_MAX_BYTES', 10):
            big = SimpleUploadedFile('big.png', self._png_bytes(), content_type='image/png')
            resp = c.post(reverse('me_inspection_add'), self._payload(photo_after=big))
        self.assertIn('ไฟล์รูปใหญ่เกิน 5 MB', resp.context['form'].errors['photo_after'])
        self.assertEqual(self.MEInspection.objects.count(), before)

    def test_invalid_part_choice_is_form_error(self):
        resp = self._client(self.tech).post(reverse('me_inspection_add'), self._payload(bearing_de_action='เปลี่ยน'))
        self.assertTrue(resp.context['form'].errors['bearing_de_action'])

    def test_new_form_defaults_parts_to_keep(self):
        form = self._client(self.tech).get(reverse('me_inspection_add')).context['form']
        self.assertEqual(form.initial['bearing_de_action'], 'keep')
        self.assertEqual(form.initial['shaft_action'], 'keep')
        self.assertNotIn('seal_device_type', form.initial)


class MEInspectionMeasurementTests(TestCase):
    """ME Inspection ticket 04: ค่าวัด Tab 2–5 — server คำนวณผลเองและไม่เชื่อค่าที่ client ส่งมา"""

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment, MEInspection
        cls.MEInspection = MEInspection
        cls.cbm = User.objects.create_user('me4_cbm', password='pass-12345-x', is_staff=True)
        cls.cbm.user_permissions.add(Permission.objects.get(codename='write_cbm'))
        cls.pump = Equipment.objects.create(equipment_id='P-301', name='ปั๊มน้ำเย็น')

    def _post(self, **fields):
        data = {'equipment': 'P-301', 'record_date': '2026-11-03', **fields}
        c = Client()
        c.force_login(self.cbm)
        resp = c.post(reverse('me_inspection_add'), data)
        self.assertEqual(resp.status_code, 302, getattr(resp, 'context', None) and resp.context['form'].errors)
        return self.MEInspection.objects.latest('id')

    def test_iso_fit_results_are_computed_and_spoofed_values_ignored(self):
        obj = self._post(
            # 50 K7 → 49.982 – 50.007: ผ่าน
            housing_de_nominal='50', housing_de_m1='49.990', housing_de_m2='50.000',
            # 30 k7 → 30.002 – 30.023: 30.030 ไม่ผ่าน
            shaft_de_nominal='30', shaft_de_m1='30.010', shaft_de_m2='30.030',
            housing_de_result='fail', shaft_de_result='pass')  # ค่าปลอมจาก client
        self.assertEqual(obj.housing_de_result, 'pass')
        self.assertEqual(obj.shaft_de_result, 'fail')
        self.assertIsNone(obj.housing_nde_result)  # ไม่กรอก = ไม่ประเมิน

    def test_shaft_key_result_is_overridden_only_when_both_readings_present(self):
        auto = self._post(shaft_key_nominal='40', shaft_key_m1='39.990', shaft_key_m2='40.000', shaft_key_result='fail')
        self.assertEqual(auto.shaft_key_result, 'pass')  # 40 h7 → 39.975 – 40.000
        manual = self._post(shaft_key_nominal='40', shaft_key_m1='39.990', shaft_key_result='fail')
        self.assertEqual(manual.shaft_key_result, 'fail')  # วัดไม่ครบ ใช้ผลที่ผู้ตรวจเลือก

    def test_runout_result_is_worst_point(self):
        ok = self._post(runout_0_p1='0.02', runout_90_p4='-0.05', runout_result='fail')
        self.assertEqual(ok.runout_result, 'pass')
        bad = self._post(runout_0_p1='0.02', runout_270_p3='0.051')
        self.assertEqual(bad.runout_result, 'fail')
        self.assertIsNone(self._post().runout_result)

    def test_alignment_results_per_reading(self):
        obj = self._post(align_before_v_offset='0.12', align_after_v_offset='-0.06', align_after_h_angle='0.061',
                         align_after_v_offset_result='fail')
        self.assertEqual(obj.align_before_v_offset_result, 'fail')
        self.assertEqual(obj.align_after_v_offset_result, 'pass')
        self.assertEqual(obj.align_after_h_angle_result, 'fail')
        self.assertIsNone(obj.align_before_h_angle_result)

    def test_vibration_result_depends_on_motor_kw_and_includes_temperature(self):
        small = self._post(motor_kw='11', vib_onload_pump_de_h='2.5')
        self.assertEqual(small.vib_result, 'warn')  # ≤15 kW: 1.8 / 2.8
        large = self._post(motor_kw='22', vib_onload_pump_de_h='2.5')
        self.assertEqual(large.vib_result, 'pass')  # >15 kW: 2.8 / 4.5
        hot = self._post(motor_kw='22', vib_onload_pump_de_h='2.5', vib_onload_pump_nde_temp='86', vib_result='pass')
        self.assertEqual(hot.vib_result, 'fail')

    def test_manual_results_and_section_metadata_are_saved(self):
        obj = self._post(bore_result='fail', bore_reason='รูหลวม', pressure_2_result='pass',
                         vib_inspector='สมชาย', vib_date='2026-11-02', vib_onload_current='35.5',
                         key_h='8', bore_type='pulley')
        self.assertEqual(obj.bore_result, 'fail')
        self.assertEqual(obj.pressure_2_result, 'pass')
        self.assertEqual(obj.vib_inspector, 'สมชาย')
        self.assertEqual(str(obj.vib_date), '2026-11-02')
        self.assertEqual(obj.vib_onload_current, Decimal('35.50'))
        self.assertEqual(obj.key_h, Decimal('8.000'))
        self.assertEqual(obj.bore_type, 'pulley')

    def test_edit_recomputes_results(self):
        obj = self._post(align_after_h_offset='0.10')
        self.assertEqual(obj.align_after_h_offset_result, 'fail')
        c = Client()
        c.force_login(self.cbm)
        c.post(reverse('me_inspection_edit', args=[obj.pk]),
               {'equipment': 'P-301', 'record_date': '2026-11-03', 'align_after_h_offset': '0.03'})
        obj.refresh_from_db()
        self.assertEqual(obj.align_after_h_offset_result, 'pass')

    def test_form_page_renders_all_measurement_tabs(self):
        c = Client()
        c.force_login(self.cbm)
        html = c.get(reverse('me_inspection_add')).content.decode()
        for marker in ('id="me-tab-2"', 'id="me-tab-5"', 'name="runout_270_p4"', 'name="vib_onload_pump_nde_temp"',
                       'data-me-tol="align"', 'id="me-fit-hint-shaft_key"', '"K7": [-12, 6]'):
            self.assertIn(marker, html)
        self.assertNotIn('name="housing_de_result"', html)  # ช่องผลที่ระบบคำนวณไม่ให้กรอก

    def test_edit_succeeds_when_existing_photo_file_is_missing_on_disk(self):
        # ไฟล์รูปเดิมหายจากดิสก์ (เช่น ย้ายเซิร์ฟเวอร์) ต้องยังแก้ใบงานได้ ไม่ใช่ error 500
        obj = self._post()
        self.MEInspection.objects.filter(pk=obj.pk).update(photo_before='me_inspection/photos/missing.jpg')
        c = Client()
        c.force_login(self.cbm)
        resp = c.post(reverse('me_inspection_edit', args=[obj.pk]),
                      {'equipment': 'P-301', 'record_date': '2026-11-03', 'remark': 'แก้ไข'})
        self.assertEqual(resp.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.photo_before.name, 'me_inspection/photos/missing.jpg')


class MEInspectionWorkflowTests(TestCase):
    """ME Inspection ticket 06: ลายเซ็น, ขั้นตอนอนุมัติ (สิทธิ์ตามสถานะ), การล็อก, เปิดกลับ และการลบ"""

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment, MEInspection
        cls.MEInspection = MEInspection
        cls.su = User.objects.create_superuser('me6_head', 'h@example.com', 'pass-12345-x')
        cls.tech = User.objects.create_user('me6_tech', password='pass-12345-x', is_staff=True)
        cls.tech.user_permissions.add(Permission.objects.get(codename='write_maintenance'))
        cls.cbm = User.objects.create_user('me6_cbm', password='pass-12345-x', is_staff=True)
        cls.cbm.user_permissions.add(Permission.objects.get(codename='write_cbm'))
        cls.reader = User.objects.create_user('me6_reader', password='pass-12345-x')
        cls.pump = Equipment.objects.create(equipment_id='P-601', name='ปั๊มน้ำมันเตา')

    def setUp(self):
        import shutil, tempfile
        from django.test import override_settings
        media = tempfile.mkdtemp()
        override = override_settings(MEDIA_ROOT=media)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)

    def _signature(self, size=(40, 20)):
        import base64, io
        from PIL import Image
        buf = io.BytesIO()
        Image.new('RGB', size, 'white').save(buf, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

    def _make(self, status='repairing', **sigs):
        obj = self.MEInspection.objects.create(equipment=self.pump, status=status, **sigs)
        return obj

    def _post(self, user, obj, action='save', **extra):
        c = Client()
        c.force_login(user)
        data = {'equipment': 'P-601', 'record_date': '2026-11-03', 'action': action, **extra}
        return c.post(reverse('me_inspection_edit', args=[obj.pk]), data)

    def _status_after(self, user, status, action, sigs=None, **extra):
        obj = self._make(status, **(sigs or {}))
        resp = self._post(user, obj, action, **extra)
        obj.refresh_from_db()
        return resp.status_code, obj.status

    def test_allowed_transitions(self):
        sig = {'tech_signature': 'me_inspection/signatures/t.png', 'cbm_signature': 'me_inspection/signatures/c.png',
               'head_signature': 'me_inspection/signatures/h.png'}
        cases = [
            (self.tech, 'repairing', 'forward', 'wait_cbm'),
            (self.cbm, 'wait_cbm', 'forward', 'wait_approval'),
            (self.cbm, 'wait_cbm', 'back', 'repairing'),
            (self.su, 'wait_approval', 'forward', 'approved'),
            (self.su, 'wait_approval', 'back', 'wait_cbm'),
            (self.su, 'approved', 'reopen', 'wait_approval'),
            (self.su, 'repairing', 'forward', 'wait_cbm'),
        ]
        for user, start, action, expected in cases:
            with self.subTest(user=user.username, start=start, action=action):
                code, status = self._status_after(user, start, action, sig)
                self.assertEqual(code, 302)
                self.assertEqual(status, expected)

    def test_disallowed_transitions_do_not_change_status(self):
        sig = {'tech_signature': 'me_inspection/signatures/t.png', 'cbm_signature': 'me_inspection/signatures/c.png'}
        cases = [
            # (ผู้ใช้, สถานะเริ่ม, ปุ่ม, status code ที่คาด)
            (self.cbm, 'repairing', 'forward', 200),      # แก้ได้ แต่ส่งต่อได้เฉพาะ write_maintenance
            (self.tech, 'repairing', 'back', 200),        # ไม่มี transition นี้
            (self.tech, 'repairing', 'approve', 200),     # ปุ่มที่ไม่มีอยู่จริง
            (self.tech, 'wait_cbm', 'forward', 403),      # ช่างแก้ใบที่รอ CBM ไม่ได้
            (self.cbm, 'wait_approval', 'forward', 403),  # อนุมัติได้เฉพาะ superuser
            (self.reader, 'repairing', 'forward', 403),
        ]
        for user, start, action, expected_code in cases:
            with self.subTest(user=user.username, start=start, action=action):
                code, status = self._status_after(user, start, action, sig)
                self.assertEqual(code, expected_code)
                self.assertEqual(status, start)

    def test_forward_requires_signature_of_that_stage(self):
        for user, start in ((self.tech, 'repairing'), (self.cbm, 'wait_cbm'), (self.su, 'wait_approval')):
            with self.subTest(start=start):
                obj = self._make(start)
                resp = self._post(user, obj, 'forward')
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.context['form'].non_field_errors())
                obj.refresh_from_db()
                self.assertEqual(obj.status, start)
                self.assertFalse(obj.tech_signature)

    def test_sign_and_forward_in_one_submit(self):
        obj = self._make()
        resp = self._post(self.tech, obj, 'forward', tech_name='สมชาย', tech_signature_data=self._signature())
        self.assertEqual(resp.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.status, 'wait_cbm')
        self.assertEqual(obj.tech_name, 'สมชาย')
        self.assertTrue(obj.tech_signature.name.startswith('me_inspection/signatures/'))

    def test_signature_blank_keeps_clear_removes_and_wrong_stage_ignored(self):
        obj = self._make()
        self._post(self.tech, obj, tech_signature_data=self._signature())
        obj.refresh_from_db()
        saved = obj.tech_signature.name
        self._post(self.tech, obj, tech_signature_data='')
        obj.refresh_from_db()
        self.assertEqual(obj.tech_signature.name, saved)
        # ช่างเซ็นแทนหัวหน้าไม่ได้ (ไม่ใช่ขั้นของตัวเอง) — ระบบไม่นำไปใช้
        self._post(self.tech, obj, head_signature_data=self._signature())
        obj.refresh_from_db()
        self.assertFalse(obj.head_signature)
        self._post(self.tech, obj, tech_signature_clear='True')
        obj.refresh_from_db()
        self.assertFalse(obj.tech_signature)

    def test_cbm_cannot_sign_as_technician(self):
        # write_cbm แก้ใบสถานะ "กำลังซ่อม" ได้ แต่ลายเซ็นช่องช่างต้องเป็นผู้มี write_maintenance
        obj = self._make()
        resp = self._post(self.cbm, obj, tech_signature_data=self._signature())
        self.assertEqual(resp.status_code, 302)
        obj.refresh_from_db()
        self.assertFalse(obj.tech_signature)
        c = Client()
        c.force_login(self.cbm)
        cards = c.get(reverse('me_inspection_edit', args=[obj.pk])).context['signature_cards']
        self.assertFalse(any(signable for *_, signable in cards))

    def test_invalid_signature_is_form_error(self):
        import base64
        bad_cases = [
            'data:image/jpeg;base64,AAAA',
            'data:image/png;base64,@@not-base64@@',
            'data:image/png;base64,' + base64.b64encode(b'not a png').decode(),
        ]
        obj = self._make()
        for data in bad_cases:
            with self.subTest(data=data[:30]):
                resp = self._post(self.tech, obj, tech_signature_data=data)
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.context['form'].errors['tech_signature_data'])
        with mock.patch('myapp.forms.ME_SIGNATURE_MAX_BYTES', 10):
            resp = self._post(self.tech, obj, tech_signature_data=self._signature())
        self.assertIn('ไฟล์ลายเซ็นใหญ่เกิน 500 KB', resp.context['form'].errors['tech_signature_data'])

    def test_approve_sets_approved_at_and_reopen_clears_it(self):
        obj = self._make('wait_approval')
        self._post(self.su, obj, 'forward', head_signature_data=self._signature())
        obj.refresh_from_db()
        self.assertEqual(obj.status, 'approved')
        self.assertIsNotNone(obj.approved_at)
        self._post(self.su, obj, 'reopen')
        obj.refresh_from_db()
        self.assertEqual(obj.status, 'wait_approval')
        self.assertIsNone(obj.approved_at)

    def test_approved_is_locked_for_non_superusers(self):
        obj = self._make('approved')
        for user in (self.tech, self.cbm):
            with self.subTest(user=user.username):
                self.assertEqual(self._post(user, obj, remark='แอบแก้').status_code, 403)
                c = Client()
                c.force_login(user)
                ctx = c.get(reverse('me_inspection_edit', args=[obj.pk])).context
                self.assertFalse(ctx['can_edit'])
                self.assertEqual(ctx['workflow_actions'], [])
        obj.refresh_from_db()
        self.assertIsNone(obj.remark)
        self.assertEqual(self._post(self.su, obj, remark='แก้โดยหัวหน้า').status_code, 302)

    def test_buttons_follow_permissions(self):
        obj = self._make('wait_cbm')
        c = Client()
        c.force_login(self.cbm)
        actions = [a for a, _, _ in c.get(reverse('me_inspection_edit', args=[obj.pk])).context['workflow_actions']]
        self.assertEqual(sorted(actions), ['back', 'forward'])
        c.force_login(self.tech)
        self.assertEqual(c.get(reverse('me_inspection_edit', args=[obj.pk])).context['workflow_actions'], [])

    def test_create_and_forward_from_add_page(self):
        c = Client()
        c.force_login(self.tech)
        resp = c.post(reverse('me_inspection_add'), {'equipment': 'P-601', 'record_date': '2026-11-03',
                                                     'action': 'forward', 'tech_signature_data': self._signature()})
        created = self.MEInspection.objects.latest('id')
        self.assertRedirects(resp, reverse('me_inspection_edit', args=[created.pk]))
        self.assertEqual(created.status, 'wait_cbm')
        self.assertEqual(created.created_by, 'me6_tech')

    def test_delete_is_superuser_only_and_post_only(self):
        obj = self._make()
        url = reverse('me_inspection_delete', args=[obj.pk])
        for user in (self.tech, self.cbm):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.post(url).status_code, 403)
        c = Client()
        c.force_login(self.su)
        self.assertEqual(c.get(url).status_code, 405)
        self.assertRedirects(c.post(url), reverse('me_inspection_list'))
        self.assertFalse(self.MEInspection.objects.filter(pk=obj.pk).exists())


class MEInspectionReadinessTests(TestCase):
    """ME Inspection ticket 05: ความพร้อมเครื่องจักร 10 ข้อ (radio)"""

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment, MEInspection
        cls.MEInspection = MEInspection
        cls.tech = User.objects.create_user('me5_tech', password='pass-12345-x', is_staff=True)
        cls.tech.user_permissions.add(Permission.objects.get(codename='write_maintenance'))
        cls.pump = Equipment.objects.create(equipment_id='P-501', name='ปั๊มน้ำทิ้ง')

    def _client(self):
        c = Client()
        c.force_login(self.tech)
        return c

    def _post(self, **fields):
        return self._client().post(reverse('me_inspection_add'),
                                   {'equipment': 'P-501', 'record_date': '2026-11-03', **fields})

    def test_valid_readiness_values_are_saved(self):
        values = {
            'ready_adjust_bolt_pump': 'wrong', 'ready_adjust_bolt_motor': 'none', 'ready_base': 'damaged',
            'ready_bolt_mark': 'no', 'ready_rotation_mark': 'yes', 'ready_coupling_guard': 'not_installed',
            'ready_air_breather': 'pink', 'ready_oil_seal': 'leak', 'ready_oil_level_gauge': 'grease',
            'ready_oil_level': 'abnormal',
        }
        self.assertEqual(self._post(**values).status_code, 302)
        obj = self.MEInspection.objects.latest('id')
        for name, value in values.items():
            self.assertEqual(getattr(obj, name), value, name)

    def test_unanswered_items_stay_empty(self):
        self.assertEqual(self._post(ready_base='ok').status_code, 302)
        obj = self.MEInspection.objects.latest('id')
        self.assertEqual(obj.ready_base, 'ok')
        self.assertIsNone(obj.ready_oil_seal)

    def test_value_outside_choices_is_form_error(self):
        before = self.MEInspection.objects.count()
        for name, value in (('ready_air_breather', 'green'), ('ready_oil_seal', 'ไม่รั่ว')):
            with self.subTest(field=name):
                resp = self._post(**{name: value})
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.context['form'].errors[name])
        self.assertEqual(self.MEInspection.objects.count(), before)

    def test_page_renders_ten_radio_groups_with_normal_values(self):
        resp = self._client().get(reverse('me_inspection_add'))
        cards = resp.context['readiness_cards']
        self.assertEqual(len(cards), 10)
        self.assertEqual([normal for _, _, _, normal in cards],
                         ['ok', 'ok', 'ok', 'yes', 'yes', 'yes', 'blue', 'no_leak', 'yes', 'ok'])
        html = resp.content.decode()
        self.assertIn('type="radio" name="ready_coupling_guard" value="not_installed"', html)
        self.assertNotIn('name="ready_base" value=""', html)  # ไม่มีตัวเลือกว่าง "---------"
        self.assertIn('id="meReadyAllNormal"', html)


class MEInspectionHistoryPrintTests(TestCase):
    """ME Inspection ticket 07: ตัวกรองหน้าประวัติ และหน้าพิมพ์ A4"""

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment, MEInspection
        cls.reader = User.objects.create_user('me7_reader', password='pass-12345-x')
        pump = Equipment.objects.create(equipment_id='P-701', name='ปั๊มน้ำอ้อย')
        gear = Equipment.objects.create(equipment_id='G-702', name='เกียร์ลูกหีบ')
        cls.a = MEInspection.objects.create(equipment=pump, record_date='2026-10-01', department='ลูกหีบ',
                                            repair_group='G1', status='repairing', tech_name='สมชาย')
        cls.b = MEInspection.objects.create(equipment=gear, record_date='2026-10-15', department='หม้อต้ม',
                                            repair_group='G2', status='wait_cbm', remark='เปลี่ยนซีล')
        cls.c = MEInspection.objects.create(equipment=pump, record_date='2026-11-01', department='ลูกหีบ',
                                            repair_group='G2', status='approved',
                                            bearing_de_no='6306', bearing_de_action='replace',
                                            shaft_de_nominal=Decimal('30.000'), shaft_de_m1=Decimal('30.010'),
                                            shaft_de_result='pass', runout_0_p1=Decimal('0.020'),
                                            vib_onload_pump_de_h=Decimal('2.50'), ready_oil_seal='leak')

    def _ids(self, **params):
        c = Client()
        c.force_login(self.reader)
        resp = c.get(reverse('me_inspection_list'), params)
        self.assertEqual(resp.status_code, 200)
        return {obj.pk for obj in resp.context['page_obj']}, resp

    def test_each_filter(self):
        a, b, c = self.a.pk, self.b.pk, self.c.pk
        self.assertEqual(self._ids()[0], {a, b, c})
        self.assertEqual(self._ids(q='เกียร์')[0], {b})
        self.assertEqual(self._ids(q='P-701')[0], {a, c})
        self.assertEqual(self._ids(q='สมชาย')[0], {a})
        self.assertEqual(self._ids(q='ซีล')[0], {b})
        self.assertEqual(self._ids(process='ลูกหีบ')[0], {a, c})
        self.assertEqual(self._ids(group='G2')[0], {b, c})
        self.assertEqual(self._ids(status='approved')[0], {c})
        self.assertEqual(self._ids(date_from='2026-10-15')[0], {b, c})
        self.assertEqual(self._ids(date_to='2026-10-15')[0], {a, b})

    def test_filters_combine_and_keep_querystring(self):
        ids, resp = self._ids(process='ลูกหีบ', group='G2', date_from='2026-10-01', date_to='2026-11-30')
        self.assertEqual(ids, {self.c.pk})
        self.assertIn('process=', resp.context['querystring'])
        self.assertEqual(resp.context['process_choices'], ['ลูกหีบ', 'หม้อต้ม'])

    def test_bad_dates_are_ignored_with_message(self):
        for bad in ('2026-13-01', '2026-02-30', 'abc'):
            with self.subTest(date=bad):
                ids, resp = self._ids(date_from=bad)
                self.assertEqual(ids, {self.a.pk, self.b.pk, self.c.pk})
                self.assertIn('รูปแบบวันที่', ' '.join(str(m) for m in resp.context['messages']))

    def test_print_page_shows_values_with_thai_labels(self):
        c = Client()
        c.force_login(self.reader)
        resp = c.get(reverse('me_inspection_print', args=[self.c.pk]))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        for text in ('ME-%d' % self.c.pk, 'เสร็จสมบูรณ์ (อนุมัติแล้ว)', '6306', 'เปลี่ยน', 'ปั๊มน้ำอ้อย',
                     'ขนาด 30 · 0°–180° 30.01', '0.02', '2.5', 'รั่ว', 'ผ่าน'):
            self.assertIn(text, html)

    def test_print_page_without_photos_or_signatures(self):
        c = Client()
        c.force_login(self.reader)
        resp = c.get(reverse('me_inspection_print', args=[self.a.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('รูปถ่ายหน้างาน', resp.content.decode())
        self.assertEqual(Client().get(reverse('me_inspection_print', args=[self.a.pk])).status_code, 302)

    def test_print_page_with_photo_and_signature(self):
        import shutil, tempfile
        from django.test import override_settings
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        with override_settings(MEDIA_ROOT=media):
            self.b.photo_after = SimpleUploadedFile('a.png', b'x', content_type='image/png')
            self.b.tech_signature = SimpleUploadedFile('t.png', b'x', content_type='image/png')
            self.b.save()
            c = Client()
            c.force_login(self.reader)
            html = c.get(reverse('me_inspection_print', args=[self.b.pk])).content.decode()
        self.assertIn('รูปถ่ายหน้างาน', html)
        self.assertIn(self.b.photo_after.url, html)
        self.assertIn(self.b.tech_signature.url, html)



class MEInspectionDashboardTests(TestCase):
    """ME Inspection ticket 08: KPI, ข้อมูลกราฟ และกรองช่วงวันที่"""

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment, MEInspection
        cls.reader = User.objects.create_user('me8_reader', password='pass-12345-x')
        cls.pump = Equipment.objects.create(equipment_id='P-801', name='ปั๊ม A')
        cls.gear = Equipment.objects.create(equipment_id='G-802', name='เกียร์ B')
        Equipment.objects.create(equipment_id='X-803', name='ยังไม่เคยตรวจ')
        Equipment.objects.create(equipment_id='X-804', name='ปลดระวาง', is_active=False)
        mk = MEInspection.objects.create
        mk(equipment=cls.pump, record_date='2026-09-01', department='ลูกหีบ', repair_group='G1', status='approved',
           bearing_de_action='replace', vib_onload_pump_de_h=Decimal('2.10'), vib_onload_motor_nde_a=Decimal('1.20'))
        mk(equipment=cls.pump, record_date='2026-10-01', department='ลูกหีบ', repair_group='G1',
           oil_seal_nde_action='replace', seal_device_action='replace', runout_result='fail',
           vib_onload_pump_nde_v=Decimal('3.40'))
        mk(equipment=cls.gear, record_date='2026-10-20', department='หม้อต้ม', repair_group='G3',
           align_after_h_angle_result='fail', align_before_v_offset_result='fail', bearing_de_action='keep')
        mk(equipment=cls.gear, record_date='2026-11-02', align_before_v_offset_result='fail')  # alignment "ก่อน" ไม่นับ alert

    def _ctx(self, **params):
        c = Client()
        c.force_login(self.reader)
        resp = c.get(reverse('me_inspection_dashboard'), params)
        self.assertEqual(resp.status_code, 200)
        return resp.context

    def test_kpis(self):
        k = self._ctx()['kpis']
        self.assertEqual(k['total'], 4)
        self.assertEqual((k['inspected_equipment'], k['active_equipment']), (2, 3))
        self.assertEqual(k['coverage'], 66.7)
        self.assertEqual(k['approved'], 1)
        self.assertEqual(k['replaced'], 2)
        self.assertEqual(k['cbm_alert'], 2)  # runout fail + alignment หลัง fail

    def test_chart_rows(self):
        charts = {chart_id: dict(rows) for chart_id, _, rows in self._ctx()['bar_charts']}
        self.assertEqual(charts['meDeptChart'], {'ลูกหีบ': 2, 'หม้อต้ม': 1, 'ไม่ระบุ': 1})
        self.assertEqual(charts['meGroupChart']['G1'], 2)
        self.assertEqual(charts['meGroupChart']['G3'], 1)
        self.assertEqual(charts['meGroupChart']['ไม่ระบุ'], 1)
        self.assertEqual(charts['meSpareChart'],
                         {'ลูกปืน DE/NDE': 1, 'ออยซีล DE/NDE': 1, 'แมคซีล/ปะเก็น': 1, 'ปลอกเพลา': 0, 'ใบพัดปั๊ม': 0, 'เพลา': 0})

    def test_date_range_filters_everything(self):
        ctx = self._ctx(date_from='2026-10-01', date_to='2026-10-31')
        self.assertEqual(ctx['kpis']['total'], 2)
        self.assertEqual(ctx['kpis']['approved'], 0)
        self.assertEqual(dict(ctx['bar_charts'][0][2]), {'ลูกหีบ': 1, 'หม้อต้ม': 1})

    def test_vibration_trend_uses_max_onload_value_per_inspection(self):
        ctx = self._ctx(equipment='P-801')
        rows = [(str(day), motor, pump) for day, motor, pump in ctx['trend_rows']]
        self.assertEqual(rows, [('2026-09-01', Decimal('1.20'), Decimal('2.10')), ('2026-10-01', None, Decimal('3.40'))])
        self.assertEqual(self._ctx(equipment='G-802')['trend_rows'], [])
        self.assertIsNone(self._ctx(equipment='NOPE')['trend_equipment'])

    def test_coverage_ignores_inactive_equipment_and_replaced_counts_any_part(self):
        from .models import Equipment, MEInspection
        retired = Equipment.objects.get(pk='X-804')
        MEInspection.objects.create(equipment=retired, record_date='2026-10-05', lube_action='replace')
        MEInspection.objects.create(equipment=self.gear, record_date='2026-10-06', cover_action='replace')
        k = self._ctx()['kpis']
        self.assertEqual((k['inspected_equipment'], k['active_equipment']), (2, 3))  # เครื่องปลดระวางไม่นับ
        self.assertLessEqual(k['coverage'], 100)
        self.assertEqual(k['replaced'], 4)  # + สารหล่อลื่น + ฝาชน (นอก 6 กลุ่มในกราฟ)

    def test_empty_data_and_no_active_equipment(self):
        from .models import Equipment, MEInspection
        MEInspection.objects.all().delete()
        Equipment.objects.update(is_active=False)
        c = Client()
        c.force_login(self.reader)
        resp = c.get(reverse('me_inspection_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['kpis']['total'], 0)
        self.assertIsNone(resp.context['kpis']['coverage'])
        self.assertNotIn('chart.js@', resp.content.decode())  # ไม่มีข้อมูล = ไม่โหลดไลบรารีกราฟ
        self.assertContains(resp, 'ยังไม่มีใบตรวจเช็คในช่วงที่เลือก')



class MEEquipmentImportTests(TestCase):
    """ME Inspection ticket 09: นำเข้ารายชื่อเครื่องจักรจาก Excel (ชีต PUMP/GEAR) เข้า Equipment"""

    PUMP_HEADER = ['ลำดับ', 'รหัสทรัพย์สิน', 'แผนก', 'List', 'ยี่ห้อ', 'รุ่น', 'Flow [m3/hr.]', 'Head [m.]',
                   'Motor [kW]', 'รอบมอเตอร์ [RPM]']
    GEAR_HEADER = ['Code.', 'Location', 'List', 'ยี่ห้อ', 'รุ่น', 'Motor [kW]', 'I [ Ratio ]', 'สารหล่อลืน']

    @classmethod
    def setUpTestData(cls):
        from .models import Equipment
        cls.Equipment = Equipment
        cls.admin = User.objects.create_user('me9_eq', password='pass-12345-x', is_staff=True)
        cls.admin.user_permissions.add(Permission.objects.get(codename='write_equipment'))
        cls.tech = User.objects.create_user('me9_tech', password='pass-12345-x', is_staff=True)
        cls.tech.user_permissions.add(Permission.objects.get(codename='write_maintenance'))
        Equipment.objects.create(equipment_id='P-002', name='ปั๊มเดิม', manufacturer='KSB', model='',
                                 power_kw=Decimal('15.00'), is_active=False)

    def _xlsx(self, pump_rows=(), gear_rows=(), sheets=('PUMP', 'GEAR')):
        import io
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
        for name, header, rows in (('PUMP', self.PUMP_HEADER, pump_rows), ('GEAR', self.GEAR_HEADER, gear_rows)):
            if name in sheets:
                ws = wb.create_sheet(name)
                ws.append(header)
                for r in rows:
                    ws.append(list(r))
        if not wb.sheetnames:
            wb.create_sheet('Sheet1')  # ไฟล์ Excel ต้องมีอย่างน้อย 1 ชีต
        buf = io.BytesIO()
        wb.save(buf)
        return SimpleUploadedFile('รายการเครื่องจักรแผนก.xlsx', buf.getvalue(),
                                  content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def _sample(self):
        return self._xlsx(
            pump_rows=[
                (1, 'P-001', 'ลูกหีบ ราง A', 'ปั๊มน้ำอ้อย', 'Grundfos', 'NK80', 120, 35.5, 22.0, 2950),
                (2, 'P-002', 'หม้อต้ม', 'ปั๊มเดิม (ชื่อใหม่)', 'Ebara', 'X1', '-', 'nan', 18.5, ''),
                (3, '', 'หม้อต้ม', 'ไม่มีรหัส', '', '', '', '', '', ''),
                (4, 'P-001', 'ลูกหีบ', 'แถวซ้ำ', '', '', '', '', '', ''),
                (5, None, None, None, None, None, None, None, None, None),  # แถวว่างทั้งแถว ไม่นับ
            ],
            gear_rows=[('G-010', 'ลูกหีบ ราง B', 'เกียร์ลูกหีบ 1', 'Flender', 'H3', 'สามสิบ', '1:40', 'น้ำมันเบอร์ 320')],
        )

    def _client(self, user=None):
        c = Client()
        c.force_login(user or self.admin)
        return c

    def test_upload_shows_preview_without_saving(self):
        c = self._client()
        resp = c.post(reverse('me_equipment_import'), {'action': 'upload', 'file': self._sample()})
        self.assertRedirects(resp, reverse('me_equipment_import'))
        self.assertFalse(self.Equipment.objects.filter(pk__in=['P-001', 'G-010']).exists())
        preview = c.get(reverse('me_equipment_import')).context['preview']
        self.assertEqual(preview['new_count'], 2)
        self.assertEqual(preview['update_count'], 1)
        self.assertEqual(preview['overwrite_count'], 1)
        self.assertEqual([reason for _, _, reason in preview['skipped']],
                         ['ไม่มีรหัสทรัพย์สินหรือชื่อเครื่อง', 'รหัสซ้ำในไฟล์ (ใช้แถวแรก)'])
        new = {r['equipment_id']: r for r in preview['new_rows']}
        self.assertEqual(new['P-001']['process'], 'ลูกหีบ')
        self.assertEqual(new['P-001']['location'], 'ลูกหีบ ราง A')
        self.assertEqual(new['P-001']['head_size'], '35.5')
        self.assertEqual(new['P-001']['power_kw'], '22.00')
        self.assertEqual(new['G-010']['power_kw'], '')  # 'สามสิบ' ไม่ใช่ตัวเลข

    def test_confirm_fills_blanks_only_by_default(self):
        c = self._client()
        c.post(reverse('me_equipment_import'), {'action': 'upload', 'file': self._sample()})
        resp = c.post(reverse('me_equipment_import'), {'action': 'confirm'})
        self.assertRedirects(resp, reverse('me_equipment_import'))
        p1 = self.Equipment.objects.get(pk='P-001')
        self.assertEqual((p1.name, p1.process, p1.manufacturer, p1.capacity, p1.power_kw, p1.rpm, p1.updated_by),
                         ('ปั๊มน้ำอ้อย', 'ลูกหีบ', 'Grundfos', '120', Decimal('22.00'), '2950', 'me9_eq'))
        self.assertTrue(p1.is_active)
        self.assertEqual(self.Equipment.objects.get(pk='G-010').process, 'ลูกหีบ')
        p2 = self.Equipment.objects.get(pk='P-002')
        self.assertEqual(p2.name, 'ปั๊มเดิม')            # มีค่าอยู่แล้ว ไม่ทับ
        self.assertEqual(p2.manufacturer, 'KSB')
        self.assertEqual(p2.power_kw, Decimal('15.00'))
        self.assertEqual(p2.model, 'X1')                 # ช่องว่าง เติมให้
        self.assertEqual(p2.process, 'หม้อต้ม')
        self.assertFalse(p2.is_active)                   # ไม่แตะสถานะใช้งาน
        self.assertNotIn('me_equipment_import', c.session)

    def test_confirm_with_overwrite(self):
        c = self._client()
        c.post(reverse('me_equipment_import'), {'action': 'upload', 'file': self._sample()})
        c.post(reverse('me_equipment_import'), {'action': 'confirm', 'overwrite': '1'})
        p2 = self.Equipment.objects.get(pk='P-002')
        self.assertEqual((p2.name, p2.manufacturer, p2.power_kw), ('ปั๊มเดิม (ชื่อใหม่)', 'Ebara', Decimal('18.50')))

    def test_cancel_clears_preview(self):
        c = self._client()
        c.post(reverse('me_equipment_import'), {'action': 'upload', 'file': self._sample()})
        c.post(reverse('me_equipment_import'), {'action': 'cancel'})
        self.assertIsNone(c.get(reverse('me_equipment_import')).context['preview'])
        c.post(reverse('me_equipment_import'), {'action': 'confirm'})  # ไม่มี preview แล้ว ไม่นำเข้า
        self.assertFalse(self.Equipment.objects.filter(pk='P-001').exists())

    def test_requires_write_equipment(self):
        for user in (self.tech,):
            c = self._client(user)
            self.assertEqual(c.get(reverse('me_equipment_import')).status_code, 403)
            self.assertEqual(c.post(reverse('me_equipment_import'), {'action': 'upload', 'file': self._sample()}).status_code, 403)

    def test_bad_files_are_errors_not_500(self):
        c = self._client()
        cases = [
            SimpleUploadedFile('list.csv', b'a,b', content_type='text/csv'),
            SimpleUploadedFile('fake.xlsx', b'not a zip', content_type='application/octet-stream'),
            self._xlsx(sheets=()),
        ]
        for upload in cases:
            with self.subTest(name=upload.name):
                resp = c.post(reverse('me_equipment_import'), {'action': 'upload', 'file': upload}, follow=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIsNone(resp.context['preview'])
                self.assertTrue(any(m.level_tag == 'error' for m in resp.context['messages']))


class MaterialMasterImportTests(TestCase):
    """Step 1 ของ Material Master — model + command นำเข้าจาก Excel"""

    HEADERS = ['Material', 'Plant', 'Material Type', 'Base Unit of Measure', 'Material Group',
               'Purchasing Group', 'Material Description', 'PO Text EN', 'Last Change']

    def _make_xlsx(self, rows, sheet_title='All Materials'):
        import os
        import tempfile
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_title
        ws.append(self.HEADERS)
        for r in rows:
            ws.append(r)
        fd, path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        wb.save(path)
        self.addCleanup(os.remove, path)
        return path

    def _run(self, path, *extra):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('import_material_master', path, *extra, stdout=out)
        return out.getvalue()

    ROWS = [
        ['000123', '1010', 'ZSP', 'EA', 'G01', 'P01', 'BEARING 6205', 'Bearing deep groove 6205', '05/01/2026'],
        ['4000999', '1010', 'ZOS', 'KG', 'G02', 'P02', 'GREASE EP2', 'Grease EP2 18kg', '31/12/2025'],
    ]

    def test_import_creates_rows_and_keeps_leading_zero(self):
        self._run(self._make_xlsx(self.ROWS))
        self.assertEqual(MaterialMaster.objects.count(), 2)
        m = MaterialMaster.objects.get(material_id='000123')
        self.assertEqual(m.short_desc, 'BEARING 6205')
        self.assertEqual(m.sap_last_change.isoformat(), '2026-01-05')
        self.assertEqual(m.source, 'sap_import')
        self.assertEqual(m.status, 'active')

    def test_import_is_idempotent_and_updates(self):
        path = self._make_xlsx(self.ROWS)
        self._run(path)
        self._run(path)
        self.assertEqual(MaterialMaster.objects.count(), 2)
        changed = [list(self.ROWS[0]), list(self.ROWS[1])]
        changed[0][6] = 'BEARING 6205 2RS'
        self._run(self._make_xlsx(changed))
        self.assertEqual(MaterialMaster.objects.get(material_id='000123').short_desc, 'BEARING 6205 2RS')
        self.assertEqual(MaterialMaster.objects.count(), 2)

    def test_dry_run_writes_nothing(self):
        self._run(self._make_xlsx(self.ROWS), '--dry-run')
        self.assertEqual(MaterialMaster.objects.count(), 0)

    def test_import_skips_blank_and_duplicate_ids(self):
        rows = self.ROWS + [list(self.ROWS[0]), ['', '1010', 'ZSP', 'EA', '', '', 'NO ID', '', '']]
        self._run(self._make_xlsx(rows))
        self.assertEqual(MaterialMaster.objects.count(), 2)

    def test_materials_permission_and_group_exist(self):
        from django.contrib.auth.models import Group
        group = Group.objects.get(name='Materials Staff')
        self.assertTrue(group.permissions.filter(codename='write_materials').exists())


class MaterialMasterReadPagesTests(TestCase):
    """Step 2 — หน้า list / detail / search API"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('reader', password='pw')
        for i in range(55):
            MaterialMaster.objects.create(
                material_id=f'4000{i:04d}', short_desc=f'BEARING {i}' if i % 2 == 0 else f'GREASE {i}',
                material_type='ZSP' if i % 2 == 0 else 'ZOS', uom='EA', material_group='G1')
        MaterialMaster.objects.create(material_id='9999', short_desc='OLD BEARING', status='inactive')

    def setUp(self):
        self.client.login(username='reader', password='pw')

    def test_login_required(self):
        self.client.logout()
        for url in (reverse('material_list'), reverse('api_material_search')):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_list_paginates_50(self):
        r = self.client.get(reverse('material_list'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['page']), 50)
        self.assertEqual(r.context['total'], 56)

    def test_list_search_and_filters(self):
        r = self.client.get(reverse('material_list'), {'q': 'grease', 'type': 'ZOS'})
        self.assertEqual(r.context['total'], 27)
        r = self.client.get(reverse('material_list'), {'status': 'inactive'})
        self.assertEqual(r.context['total'], 1)

    def test_detail_page(self):
        m = MaterialMaster.objects.get(material_id='40000001')
        r = self.client.get(reverse('material_detail', args=[m.pk]))
        self.assertContains(r, '40000001')
        self.assertEqual(self.client.get(reverse('material_detail', args=[999999])).status_code, 404)

    def test_search_api_json(self):
        r = self.client.get(reverse('api_material_search'), {'q': 'bearing'})
        data = r.json()['data']
        self.assertEqual(len(data), 20)
        self.assertEqual(set(data[0]), {'id', 'material_id', 'short_desc', 'po_text', 'uom', 'material_type'})
        self.assertNotIn('9999', [d['material_id'] for d in data])  # inactive ถูกซ่อน
        self.assertEqual(self.client.get(reverse('api_material_search'), {'q': 'b'}).json(), {'data': []})


class MaterialMasterFormTests(TestCase):
    """Step 3 — ฟอร์มเพิ่ม/แก้ Material, เลขซ้ำ, เตือนชื่อคล้าย, สิทธิ์"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Group
        cls.writer = User.objects.create_user('writer', password='pw', is_staff=True)
        cls.writer.groups.add(Group.objects.get(name='Materials Staff'))
        cls.plain_staff = User.objects.create_user('plain', password='pw', is_staff=True)
        cls.reader = User.objects.create_user('reader2', password='pw')
        cls.existing = MaterialMaster.objects.create(
            material_id='40001177', short_desc='Bearing 6205 ZZ', material_type='ZSP', uom='EA')

    def _login(self, name):
        self.client.login(username=name, password='pw')

    def _payload(self, **over):
        data = {'material_id': '40009999', 'material_type': 'ZSP', 'uom': 'EA', 'material_group': '',
                'purchasing_group': '', 'plant': '1010', 'short_desc': 'Hydraulic hose 1/2 inch',
                'po_text': '', 'status': 'active'}
        data.update(over)
        return data

    def test_permission_required(self):
        url = reverse('material_add')
        self.assertEqual(self.client.get(url).status_code, 302)  # ยังไม่ login
        self._login('reader2')
        self.assertEqual(self.client.get(url).status_code, 403)
        self._login('plain')
        self.assertEqual(self.client.get(url).status_code, 403)
        self._login('writer')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_add_new_material(self):
        self._login('writer')
        r = self.client.post(reverse('material_add'), self._payload())
        m = MaterialMaster.objects.get(material_id='40009999')
        self.assertRedirects(r, reverse('material_detail', args=[m.pk]))
        self.assertEqual(m.source, 'lamy_form')
        self.assertEqual(m.created_by, self.writer)
        self.assertEqual(m.updated_by, self.writer)

    def test_duplicate_or_blank_id_rejected(self):
        self._login('writer')
        r = self.client.post(reverse('material_add'), self._payload(material_id='40001177'))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['form'].errors['material_id'])
        r = self.client.post(reverse('material_add'), self._payload(material_id='  '))
        self.assertTrue(r.context['form'].errors['material_id'])
        self.assertEqual(MaterialMaster.objects.count(), 1)

    def test_similar_name_warns_then_confirms(self):
        self._login('writer')
        data = self._payload(material_id='40008888', short_desc='BEARING 6205 ZZ.')
        r = self.client.post(reverse('material_add'), data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual([m.material_id for m in r.context['similar']], ['40001177'])
        self.assertFalse(MaterialMaster.objects.filter(material_id='40008888').exists())
        data['confirm_similar'] = '1'
        r = self.client.post(reverse('material_add'), data)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(MaterialMaster.objects.filter(material_id='40008888').exists())

    def test_edit_and_deactivate(self):
        self._login('writer')
        url = reverse('material_edit', args=[self.existing.pk])
        r = self.client.post(url, self._payload(material_id='40001177', short_desc='Bearing 6205 ZZ', status='inactive'))
        self.assertEqual(r.status_code, 302)  # ชื่อไม่เปลี่ยน -> ไม่เตือนตัวเอง
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.status, 'inactive')
        self.assertEqual(self.existing.updated_by, self.writer)

    def test_similar_api(self):
        self._login('reader2')
        r = self.client.get(reverse('api_material_similar'), {'desc': 'bearing 6205 zz'})
        self.assertEqual([d['material_id'] for d in r.json()['data']], ['40001177'])
        r = self.client.get(reverse('api_material_similar'), {'desc': 'bearing 6205 zz', 'exclude': self.existing.pk})
        self.assertEqual(r.json()['data'], [])
        self.assertEqual(self.client.get(reverse('api_material_similar')).json(), {'data': []})


class MaterialMasterBOMTests(TestCase):
    """Step 4 — ผูก BOM กับ Material Master, ใช้ที่ไหน, command ผูกย้อนหลัง"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Group
        from .models import Equipment, EquipmentBOM
        cls.EquipmentBOM = EquipmentBOM
        cls.user = User.objects.create_user('eqstaff', password='pw', is_staff=True)
        cls.user.groups.add(Group.objects.get(name='Equipment Staff'))
        cls.eq = Equipment.objects.create(equipment_id='EQ-001', name='ปั๊มทดสอบ')
        cls.mat = MaterialMaster.objects.create(material_id='40001177', short_desc='BEARING 6205', uom='EA')
        cls.inactive = MaterialMaster.objects.create(material_id='40000001', short_desc='OLD PART', status='inactive')

    def setUp(self):
        self.client.login(username='eqstaff', password='pw')

    def _add(self, **data):
        base = {'qty': 2, 'location': 'Store A', 'stock_qty': 0}
        base.update(data)
        return self.client.post(reverse('bom_add', args=['EQ-001']), base)

    def test_add_bom_with_material_fills_part_fields(self):
        self._add(material=self.mat.pk)
        bom = self.EquipmentBOM.objects.get()
        self.assertEqual(bom.material, self.mat)
        self.assertEqual(bom.part_no, '40001177')
        self.assertEqual(bom.part_name, 'BEARING 6205')

    def test_add_bom_manual_still_works_and_requires_fields(self):
        self._add(part_no='X-1', part_name='ของเดิม')
        self.assertEqual(self.EquipmentBOM.objects.get().material, None)
        self._add(part_no='', part_name='')
        self.assertEqual(self.EquipmentBOM.objects.count(), 1)  # ไม่เลือก material และไม่กรอก -> ไม่บันทึก

    def test_inactive_material_cannot_be_newly_linked(self):
        self._add(material=self.inactive.pk)
        self.assertEqual(self.EquipmentBOM.objects.count(), 0)

    def test_edit_bom_relink_overrides_free_text(self):
        bom = self.EquipmentBOM.objects.create(equipment=self.eq, part_no='old', part_name='old name')
        self.client.post(reverse('bom_edit', args=[bom.pk]),
                         {'material': self.mat.pk, 'part_no': 'old', 'part_name': 'old name', 'qty': 1, 'stock_qty': 0})
        bom.refresh_from_db()
        self.assertEqual((bom.material, bom.part_no), (self.mat, '40001177'))

    def test_protect_blocks_material_delete(self):
        from django.db.models import ProtectedError
        self.EquipmentBOM.objects.create(equipment=self.eq, part_no='40001177', part_name='x', material=self.mat)
        with self.assertRaises(ProtectedError):
            self.mat.delete()

    def test_detail_shows_where_used(self):
        self.EquipmentBOM.objects.create(equipment=self.eq, part_no='40001177', part_name='x', material=self.mat)
        r = self.client.get(reverse('material_detail', args=[self.mat.pk]))
        self.assertContains(r, 'EQ-001')
        self.assertEqual(len(r.context['bom_lines']), 1)

    def test_link_command_matches_trimmed_exact_only(self):
        from io import StringIO
        from django.core.management import call_command
        a = self.EquipmentBOM.objects.create(equipment=self.eq, part_no=' 40001177 ', part_name='a')
        b = self.EquipmentBOM.objects.create(equipment=self.eq, part_no='40001177X', part_name='b')
        out = StringIO()
        call_command('link_material_master', '--dry-run', stdout=out)
        a.refresh_from_db()
        self.assertIsNone(a.material)
        call_command('link_material_master', stdout=out)
        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual(a.material, self.mat)
        self.assertIsNone(b.material)
        self.assertIn('40001177X', out.getvalue())

    def test_equipment_page_renders_material_picker(self):
        self.EquipmentBOM.objects.create(equipment=self.eq, part_no='40001177', part_name='x', material=self.mat)
        r = self.client.get(reverse('equipment_data_detail', args=['EQ-001']))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'relative" data-material-picker>', count=2)  # ฟอร์มแก้ไข 1 แถว + ฟอร์มเพิ่ม
        self.assertContains(r, reverse('material_detail', args=[self.mat.pk]))


class MaterialMasterInventoryTests(TestCase):
    """Step 5 — ผูก Inventory/เครื่องมือกับ Material Master (1 Material = 1 รายการคลัง)"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Group
        from .models import InventoryItem
        cls.InventoryItem = InventoryItem
        cls.inv_user = User.objects.create_user('invstaff', password='pw', is_staff=True)
        cls.inv_user.groups.add(Group.objects.get(name='Inventory Staff'))
        cls.tool_user = User.objects.create_user('toolstaff', password='pw', is_staff=True)
        cls.tool_user.groups.add(Group.objects.get(name='Tools Staff'))
        cls.zsp = MaterialMaster.objects.create(material_id='40001177', short_desc='BEARING 6205', uom='EA', material_type='ZSP')
        cls.zos = MaterialMaster.objects.create(material_id='40001180', short_desc='GREASE EP2', uom='KG', material_type='ZOS')
        cls.old = MaterialMaster.objects.create(material_id='40000001', short_desc='OLD', status='inactive')

    def _post(self, name, url_name, payload, args=()):
        self.client.login(username=name, password='pw')
        return self.client.post(reverse(url_name, args=args), json.dumps(payload), content_type='application/json')

    def test_add_item_with_material_fills_code_name_unit_category(self):
        r = self._post('invstaff', 'api_inventory_add_item', {'material': self.zsp.pk})
        self.assertTrue(r.json()['success'])
        item = self.InventoryItem.objects.get()
        self.assertEqual((item.code, item.name, item.unit, item.category, item.material),
                         ('40001177', 'BEARING 6205', 'EA', 'spares', self.zsp))
        self._post('invstaff', 'api_inventory_add_item', {'material': self.zos.pk})
        self.assertEqual(self.InventoryItem.objects.get(material=self.zos).category, 'consumables')

    def test_code_forced_to_material_id_even_if_client_sends_other(self):
        self._post('invstaff', 'api_inventory_add_item', {'material': self.zsp.pk, 'code': 'WRONG', 'name': 'ชื่อเอง', 'unit': 'ตัว'})
        item = self.InventoryItem.objects.get()
        self.assertEqual((item.code, item.name, item.unit), ('40001177', 'ชื่อเอง', 'ตัว'))

    def test_one_material_one_item(self):
        self._post('invstaff', 'api_inventory_add_item', {'material': self.zsp.pk})
        r = self._post('invstaff', 'api_inventory_add_item', {'material': self.zsp.pk})
        self.assertEqual(r.status_code, 400)
        self.assertIn('ถูกใช้กับรายการคลัง', r.json()['error'])
        self.assertEqual(self.InventoryItem.objects.count(), 1)

    def test_inactive_or_missing_material_rejected(self):
        self.assertEqual(self._post('invstaff', 'api_inventory_add_item', {'material': self.old.pk}).status_code, 400)
        self.assertEqual(self._post('invstaff', 'api_inventory_add_item', {'material': 999999}).status_code, 400)
        self.assertEqual(self._post('invstaff', 'api_inventory_add_item', {'material': 'abc'}).status_code, 400)

    def test_legacy_add_without_material_unchanged(self):
        r = self._post('invstaff', 'api_inventory_add_item', {'code': 'OLD-1', 'name': 'ของเดิม'})
        self.assertTrue(r.json()['success'])
        self.assertIsNone(self.InventoryItem.objects.get().material)

    def test_update_item_link_keep_and_unlink(self):
        item = self.InventoryItem.objects.create(code='OLD-1', name='ของเดิม')
        url = ('invstaff', 'api_inventory_update_item')
        # ผูก
        self._post(*url, {'material': self.zsp.pk, 'name': 'ของเดิม', 'code': 'OLD-1'}, args=[item.pk])
        item.refresh_from_db()
        self.assertEqual((item.material, item.code), (self.zsp, '40001177'))
        # ไม่ส่ง key material -> คงการผูกและคงรหัสตาม Material ID
        self._post(*url, {'code': 'HACK', 'name': 'แก้ชื่อ'}, args=[item.pk])
        item.refresh_from_db()
        self.assertEqual((item.material, item.code, item.name), (self.zsp, '40001177', 'แก้ชื่อ'))
        # ส่งค่าว่าง -> ล้างการผูก
        self._post(*url, {'material': '', 'code': '40001177', 'name': 'แก้ชื่อ'}, args=[item.pk])
        item.refresh_from_db()
        self.assertIsNone(item.material)

    def test_tools_type_add_with_material(self):
        r = self._post('toolstaff', 'api_tools_type_add', {'material': self.zsp.pk, 'department': 'lathe'})
        self.assertTrue(r.json()['success'])
        item = self.InventoryItem.objects.get()
        self.assertEqual((item.category, item.code, item.material, item.department), ('tools', '40001177', self.zsp, 'lathe'))

    def test_protect_blocks_material_delete(self):
        from django.db.models import ProtectedError
        self.InventoryItem.objects.create(code='40001177', name='x', material=self.zsp)
        with self.assertRaises(ProtectedError):
            self.zsp.delete()

    def test_detail_shows_inventory_and_pages_render(self):
        item = self.InventoryItem.objects.create(code='40001177', name='BEARING 6205', material=self.zsp)
        self.client.login(username='invstaff', password='pw')
        self.assertContains(self.client.get(reverse('material_detail', args=[self.zsp.pk])), 'BEARING 6205')
        r = self.client.get(reverse('inventory_stock_card', args=[item.pk]))
        self.assertContains(r, 'id="ei_material" value="%d"' % self.zsp.pk)
        self.assertContains(self.client.get(reverse('inventory_dashboard')), 'id="ai_msearch"')
        self.client.login(username='toolstaff', password='pw')
        self.assertContains(self.client.get(reverse('tools_type_list')), 'id="at_msearch"')

    def test_link_command_covers_inventory(self):
        from io import StringIO
        from django.core.management import call_command
        a = self.InventoryItem.objects.create(code=' 40001177 ', name='a')
        b = self.InventoryItem.objects.create(code='NOPE', name='b')
        out = StringIO()
        call_command('link_material_master', '--dry-run', stdout=out)
        a.refresh_from_db()
        self.assertIsNone(a.material)
        call_command('link_material_master', stdout=out)
        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual(a.material, self.zsp)
        self.assertIsNone(b.material)
        self.assertIn('NOPE', out.getvalue())


class SidebarStockGroupTests(TestCase):
    """Sidebar — Inventory / เครื่องมือ / Material Master รวมเป็นกลุ่ม 'คลัง & วัสดุ'"""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Group
        cls.inv = User.objects.create_user('navinv', password='pw', is_staff=True)
        cls.inv.groups.add(Group.objects.get(name='Inventory Staff'))
        cls.boiler = User.objects.create_user('navboiler', password='pw', is_staff=True)
        cls.boiler.groups.add(Group.objects.get(name='Boiler Staff'))
        cls.plain = User.objects.create_user('navplain', password='pw')

    def _get(self, user, name, *args):
        self.client.login(username=user, password='pw')
        return self.client.get(reverse(name, args=args)).content.decode()

    def test_group_contains_children_for_inventory_user(self):
        html = self._get('navinv', 'dashboard')
        self.assertEqual(html.count('<details class="group"'), 1)
        group = html[html.index('<details class="group"'):html.index('</details>')]
        self.assertIn(reverse('inventory_dashboard'), group)
        self.assertIn(reverse('material_list'), group)
        self.assertNotIn(reverse('tools_dashboard'), group)  # ไม่มีสิทธิ์ tools
        self.assertNotIn(' open>', group.split('</summary>')[0])  # หน้า dashboard -> พับอยู่

    def test_group_hidden_without_any_stock_permission(self):
        html = self._get('navboiler', 'dashboard')
        self.assertNotIn('<details class="group"', html)
        self.assertNotIn(reverse('material_list'), html)

    def test_group_open_on_child_pages_only(self):
        self.assertIn('group" open>', self._get('navinv', 'material_list'))
        self.assertIn('group" open>', self._get('navinv', 'inventory_list'))
        self.assertNotIn('group" open>', self._get('navinv', 'dashboard'))
