from django.db import migrations


def seed_process_categories(apps, schema_editor):
    Equipment = apps.get_model('myapp', 'Equipment')
    ProcessCategory = apps.get_model('myapp', 'ProcessCategory')
    names = (
        Equipment.objects.exclude(process__isnull=True)
        .exclude(process__exact='')
        .values_list('process', flat=True)
        .distinct()
        .order_by('process')
    )
    for name in names:
        ProcessCategory.objects.get_or_create(name=name.strip(), defaults={'is_active': True})


def unseed_process_categories(apps, schema_editor):
    # Best-effort reverse: no-op, since categories may have been edited via
    # Django Admin by the time of rollback.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0085_processcategory'),
    ]

    operations = [
        migrations.RunPython(seed_process_categories, unseed_process_categories),
    ]
