
import os
import django
import json
import datetime
from django.db.models import Sum, Avg

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning.settings')
django.setup()

from myapp.models import MillReport

def check_mill_data():
    print("--- Checking MillReport Data ---")
    count = MillReport.objects.count()
    print(f"Total MillReports: {count}")
    
    if count == 0:
        print("NO DATA IN DATABASE!")
        return

    latest = MillReport.objects.order_by('-date').first()
    print(f"Latest Report: {latest.date} (Line {latest.line})")
    print(f"Last 5 Reports:")
    for r in MillReport.objects.order_by('-date')[:5]:
        print(f" - {r.date} Line {r.line}: Cane={r.cane_weight}")

    print("\n--- Simulate View Logic (Line A) ---")
    line = 'A'
    latest_a = MillReport.objects.filter(line=line).order_by('-date', '-created_at').first()
    sum_cane_a = MillReport.objects.filter(line=line).aggregate(total=Sum('cane_weight'))['total'] or 0
    
    # Check avg calculation
    avg_a = MillReport.objects.filter(line=line).aggregate(
        first_mill_extraction__avg=Avg('first_mill_extraction'),
        reduced_pol_extraction__avg=Avg('reduced_pol_extraction'),
        purity_drop__avg=Avg('purity_drop'),
        # ... just checking a few
    )
    
    print(f"Latest A: {latest_a}")
    print(f"Sum Cane A: {sum_cane_a}")
    print(f"Avg A (partial): {avg_a}")

    if latest_a:
        # Mini format_data simulation
        kpi_1_current = latest_a.first_mill_extraction
        kpi_1_avg = avg_a.get('first_mill_extraction__avg')
        print(f"KPI 1 (First Mill): Current={kpi_1_current}, Avg={kpi_1_avg}")
        
        if kpi_1_current is None:
            print("WARNING: Current KPI value is None!")

if __name__ == '__main__':
    check_mill_data()
