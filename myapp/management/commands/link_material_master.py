from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from myapp.models import EquipmentBOM, InventoryItem, MaterialMaster

REPORT_LIMIT = 50


class Command(BaseCommand):
    help = ('Link existing EquipmentBOM.part_no and InventoryItem.code to MaterialMaster by exact match with '
            'material_id (whitespace trimmed). Only rows without a material are touched; unmatched codes are reported.')

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Report only, do not write')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        by_code = dict(MaterialMaster.objects.values_list('material_id', 'pk'))

        to_link, unmatched = [], Counter()
        for bom in EquipmentBOM.objects.filter(material__isnull=True):
            code = (bom.part_no or '').strip()
            pk = by_code.get(code)
            if pk:
                bom.material_id = pk
                to_link.append(bom)
            else:
                unmatched[code] += 1

        self.stdout.write(f'BOM: จับคู่ได้ {len(to_link)} แถว · จับคู่ไม่ได้ {sum(unmatched.values())} แถว ({len(unmatched)} รหัสต่างกัน)')
        if unmatched:
            self.stdout.write(f'รหัสที่ผูกไม่ได้ (แสดง {REPORT_LIMIT} อันดับแรก) — ผูกเองผ่านหน้าเว็บ:')
            for code, n in unmatched.most_common(REPORT_LIMIT):
                self.stdout.write(f'  {code!r} × {n}')

        # Inventory/เครื่องมือ: 1 Material = 1 รายการ -> ข้าม Material ที่มีรายการคลังผูกอยู่แล้ว
        taken = set(InventoryItem.objects.filter(material__isnull=False).values_list('material_id', flat=True))
        inv_link, inv_unmatched, inv_conflict = [], [], []
        for item in InventoryItem.objects.filter(material__isnull=True):
            pk = by_code.get((item.code or '').strip())
            if not pk:
                inv_unmatched.append(item.code)
            elif pk in taken:
                inv_conflict.append(item.code)
            else:
                item.material_id = pk
                taken.add(pk)
                inv_link.append(item)
        self.stdout.write(
            f'Inventory/เครื่องมือ: จับคู่ได้ {len(inv_link)} รายการ · จับคู่ไม่ได้ {len(inv_unmatched)} · '
            f'ซ้ำกับรายการที่ผูกแล้ว {len(inv_conflict)}')
        if inv_unmatched:
            self.stdout.write(f'รหัสคลังที่ผูกไม่ได้ (แสดง {REPORT_LIMIT} อันดับแรก): ' + ', '.join(inv_unmatched[:REPORT_LIMIT]))
        if inv_conflict:
            self.stdout.write('รหัสคลังที่ Material ถูกใช้แล้ว: ' + ', '.join(inv_conflict[:REPORT_LIMIT]))

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: ยังไม่เขียนข้อมูล'))
            return
        with transaction.atomic():
            EquipmentBOM.objects.bulk_update(to_link, ['material'], batch_size=500)
            InventoryItem.objects.bulk_update(inv_link, ['material'], batch_size=500)
        self.stdout.write(self.style.SUCCESS(f'เสร็จสิ้น — ผูก BOM {len(to_link)} แถว · Inventory {len(inv_link)} รายการ'))
