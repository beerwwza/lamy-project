from django.core.management.base import BaseCommand
from myapp.models import InventoryItem, ToolUnit


class Command(BaseCommand):
    help = 'Create ToolUnit rows for existing InventoryItem(category=tools) so their stock count matches individually tracked units'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Actually create the units (default is dry-run preview)')

    def handle(self, *args, **options):
        apply = options['apply']
        items = InventoryItem.objects.filter(category='tools')
        total_to_create = 0

        for item in items:
            existing = item.tool_units.count()
            target = int(item.stock)
            missing = max(0, target - existing)
            if missing == 0:
                continue
            total_to_create += missing
            self.stdout.write(f'  {item.code} - {item.name}: stock={target}, existing units={existing}, will create {missing}')
            if apply:
                for _ in range(missing):
                    seq = item.tool_units.count() + 1
                    ToolUnit.objects.create(item=item, unit_code=f'{item.code}-{seq:03d}')

        if not apply:
            self.stdout.write(self.style.WARNING(
                f'\nDry-run: {total_to_create} ToolUnit row(s) would be created. Re-run with --apply to create them.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDone — created {total_to_create} ToolUnit row(s).'))
