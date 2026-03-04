import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learning.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User

client = Client()

user, _ = User.objects.get_or_create(username='testuser', defaults={'password': 'testpassword'})
client.force_login(user)

payload = {
    "action": "save_job",
    "job": {
        "job_no": "TEST-123",
        "date": "2023-10-10",
        "requester": "John Doe",
        "dept": "Maintenance",
        "tel": "1234567890",
        "machine": "Lathe A",
        "cust_machine": "Pump 1",
        "topic": "Fixing the pump",
        "job_type": ["Repair", "Fabrication"],
        "priority": "Normal",
        "req_date": "2023-10-15",
        "has_drawing": False,
        "has_sample": True,
        "has_material": False,
        "plan_status": "Accepted",
        "plan_reject_reason": "",
        "plan_due_date": "2023-10-14",
        "maker": "Smith",
        "material_cost": 500,
        "hours": 2.5,
        "pieces": 1,
        "qc_result": "Pass",
        "qc_note": "Looks good",
        "receiver": "John",
        "status": "Done"
    }
}

response = client.post('/api/lathe/', data=json.dumps(payload), content_type='application/json')
print(f"Status Code: {response.status_code}")
try:
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Response Text: {response.content}")
