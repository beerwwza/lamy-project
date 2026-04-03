import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning.settings')
django.setup()

from myapp.models import Equipment
from myapp.forms import EquipmentForm
from django.http import QueryDict

eq, created = Equipment.objects.get_or_create(equipment_id='123_TEST', defaults={'name': 'V2'})

post_data = QueryDict(mutable=True)
post_data.update({
    'equipment_id': '123_TEST',
    'name': 'Updated Test',
    'priority_level': '3',
    'mtbf': '0',
    'mttr': '0',
    'acc_cost': '0',
})

form = EquipmentForm(post_data, instance=eq)
if form.is_valid():
    form.save()
    count = Equipment.objects.filter(equipment_id='123_TEST').count()
    print(f"Count of 123_TEST: {count}")
    print(f"Total Equipments: {Equipment.objects.count()}")
else:
    print("Form invalid:", form.errors)
