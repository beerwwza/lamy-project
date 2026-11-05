import re
from datetime import datetime

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from myapp.models import MaterialMaster

# หัวคอลัมน์ในไฟล์ Excel (normalize แล้ว: ตัวพิมพ์เล็ก ตัดสัญลักษณ์/ช่องว่าง) -> field ใน MaterialMaster
HEADER_ALIASES = {
    'material_id': ['materialid', 'material', 'materialnumber', 'materialno'],
    'plant': ['plant'],
    'material_type': ['materialtype', 'mtyp', 'type'],
    'uom': ['uom', 'baseunitofmeasure', 'bun', 'unit'],
    'material_group': ['materialgroup', 'matlgroup'],
    'purchasing_group': ['purchasinggroup', 'purchgroup', 'pgr'],
    'short_desc': ['materialdescription', 'shortdesc', 'description'],
    'po_text': ['potexten', 'potext', 'fulldesc'],
    'sap_last_change': ['lastchange', 'lastchangedate', 'changedon', 'saplastchange'],
}
REQUIRED = ['material_id', 'short_desc']
VALID_TYPES = {code for code, _ in MaterialMaster.TYPE_CHOICES}
UPDATE_FIELDS = ['plant', 'material_type', 'uom', 'material_group', 'purchasing_group',
                 'short_desc', 'po_text', 'sap_last_change', 'status', 'source']


def _norm_header(h):
    return re.sub(r'[^a-z0-9]', '', str(h).lower())


def _parse_date(value):
    """รองรับ d/m/yyyy (รูปแบบในไฟล์ SAP) และ ISO ที่ pandas อาจแปลงมาให้"""
    value = (value or '').strip()
    if not value:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class Command(BaseCommand):
    help = 'Import SAP Material IDs from Excel into MaterialMaster (idempotent: re-running updates, never duplicates)'

    def add_arguments(self, parser):
        parser.add_argument('xlsx', help='Path to the .xlsx file')
        parser.add_argument('--sheet', default='All Materials', help="Sheet name (default 'All Materials', falls back to first sheet)")
        parser.add_argument('--dry-run', action='store_true', help='Report what would change without writing')

    def handle(self, *args, **options):
        path, sheet, dry_run = options['xlsx'], options['sheet'], options['dry_run']
        try:
            xl = pd.ExcelFile(path)
        except FileNotFoundError:
            raise CommandError(f'ไม่พบไฟล์: {path}')
        sheet_name = sheet if sheet in xl.sheet_names else xl.sheet_names[0]
        if sheet_name != sheet:
            self.stdout.write(self.style.WARNING(f"ไม่พบชีต '{sheet}' — ใช้ชีตแรก '{sheet_name}' แทน"))
        # dtype=str เพื่อไม่ให้รหัสที่ขึ้นต้นด้วย 0 กลายเป็นตัวเลข
        df = xl.parse(sheet_name, dtype=str, keep_default_na=False)

        by_norm = {_norm_header(c): c for c in df.columns}
        col = {}
        for field, aliases in HEADER_ALIASES.items():
            for alias in aliases:
                if alias in by_norm:
                    col[field] = by_norm[alias]
                    break
        missing = [f for f in REQUIRED if f not in col]
        if missing:
            raise CommandError(f'หาคอลัมน์ไม่เจอ: {missing} — หัวคอลัมน์ในไฟล์: {list(df.columns)}')
        unmapped = [c for c in df.columns if c not in col.values()]
        self.stdout.write(f'จับคู่คอลัมน์: {col}')
        if unmapped:
            self.stdout.write(f'คอลัมน์ที่ไม่ได้ใช้: {unmapped}')

        def cell(row, field):
            return str(row[col[field]]).strip() if field in col else ''

        existing = {m.material_id: m for m in MaterialMaster.objects.all()}
        to_create, to_update, seen = [], [], set()
        skipped = {'blank_id': 0, 'duplicate_in_file': 0, 'too_long': 0, 'bad_type': 0}

        for _, row in df.iterrows():
            mid = cell(row, 'material_id')
            if not mid:
                skipped['blank_id'] += 1
                continue
            if len(mid) > 20:
                skipped['too_long'] += 1
                continue
            if mid in seen:
                skipped['duplicate_in_file'] += 1
                continue
            seen.add(mid)
            mtype = cell(row, 'material_type').upper() or 'ZSP'
            if mtype not in VALID_TYPES:
                skipped['bad_type'] += 1
                continue
            values = dict(
                plant=cell(row, 'plant') or '1010',
                material_type=mtype,
                uom=cell(row, 'uom'),
                material_group=cell(row, 'material_group'),
                purchasing_group=cell(row, 'purchasing_group'),
                short_desc=cell(row, 'short_desc')[:100],
                po_text=cell(row, 'po_text'),
                sap_last_change=_parse_date(cell(row, 'sap_last_change')),
                status='active',
                source='sap_import',
            )
            obj = existing.get(mid)
            if obj is None:
                to_create.append(MaterialMaster(material_id=mid, **values))
            else:
                for k, v in values.items():
                    setattr(obj, k, v)
                to_update.append(obj)

        self.stdout.write(
            f'พบ {len(df)} แถว → เพิ่มใหม่ {len(to_create)} · อัปเดต {len(to_update)} · '
            f'ข้าม {sum(skipped.values())} {skipped}'
        )
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: ยังไม่เขียนข้อมูล'))
            return
        with transaction.atomic():
            MaterialMaster.objects.bulk_create(to_create, batch_size=1000)
            MaterialMaster.objects.bulk_update(to_update, UPDATE_FIELDS, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(
            f'เสร็จสิ้น — ใน MaterialMaster ตอนนี้มี {MaterialMaster.objects.count()} รหัส'
        ))
