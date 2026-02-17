
import os
import django
import sys

# Setup Django environment
sys.path.append('d:\\lamy\\lamy-project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lamy_project.settings')
django.setup()

from myapp.models import MillReport

def check_data():
    print("Checking MillReport Data...")
    total_count = MillReport.objects.count()
    print(f"Total Records: {total_count}")

    line_a_first = MillReport.objects.filter(line='A').order_by('-date').first()
    line_b_first = MillReport.objects.filter(line='B').order_by('-date').first()

    if line_a_first:
        print(f"Line A Latest: {line_a_first.date}, Cane: {line_a_first.cane_weight}")
    else:
        print("Line A: No Data")

    if line_b_first:
        print(f"Line B Latest: {line_b_first.date}, Cane: {line_b_first.cane_weight}")
    else:
        print("Line B: No Data")

    # Check mapping keys
    if line_a_first:
        print(f"Line A Object: {line_a_first.__dict__}")

if __name__ == '__main__':
    check_data()
