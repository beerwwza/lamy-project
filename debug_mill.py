
from myapp.models import MillReport
from django.db.models import Max

print("--- Debugging MillReport ---")

# Check Line A
latest_a = MillReport.objects.filter(line='A').order_by('-date').first()
if latest_a:
    print(f"Latest Line A Record:")
    print(f"  Date: {latest_a.date}")
    print(f"  Cane Weight: {latest_a.cane_weight}")
    print(f"  CCS: {latest_a.ccs}")
    print(f"  1st Mill Extraction: {latest_a.first_mill_extraction}")
    print(f"  Reduced Pol Extraction: {latest_a.reduced_pol_extraction}")
    print(f"  Purity Drop: {latest_a.purity_drop}")
else:
    print("No records for Line A")

# Check Line B
latest_b = MillReport.objects.filter(line='B').order_by('-date').first()
if latest_b:
    print(f"\nLatest Line B Record:")
    print(f"  Date: {latest_b.date}")
    print(f"  Cane Weight: {latest_b.cane_weight}")
    print(f"  CCS: {latest_b.ccs}")
else:
    print("No records for Line B")

print("\nAttempting to find latest NON-ZERO cane weight record:")
valid_a = MillReport.objects.filter(line='A', cane_weight__gt=0).order_by('-date').first()
if valid_a:
    print(f"  Line A (Valid): {valid_a.date} - Cane: {valid_a.cane_weight}")
    print(f"  Other Data: CCS={valid_a.ccs}, Ext={valid_a.first_mill_extraction}")
else:
    print("  Line A: No valid non-zero records found")
