from django.core.management.base import BaseCommand
from myapp.models import Equipment


class Command(BaseCommand):
    help = 'Recalculate MTBF and MTTR for all equipment from actual maintenance logs'

    def handle(self, *args, **options):
        equipments = Equipment.objects.all()
        updated = 0
        skipped = 0
        for eq in equipments:
            count = eq.maintenance_logs.count()
            if count == 0:
                skipped += 1
                continue
            eq.update_reliability_metrics()
            updated += 1
            self.stdout.write(f'  {eq.equipment_id}: MTBF={eq.mtbf}h  MTTR={eq.mttr}h  ({count} logs)')
        self.stdout.write(self.style.SUCCESS(
            f'\nDone — updated {updated} equipment, skipped {skipped} (no maintenance logs)'
        ))
