from django.db import migrations


def copy_material_cost_to_job_value(apps, schema_editor):
    """มูลค่าเดิมของใบสั่งงานคือ "ค่าวัสดุ" ช่องเดียว — คัดลอกไป job_value เพื่อไม่ให้ยอดหาย"""
    LatheJob = apps.get_model('myapp', 'LatheJob')
    for job in LatheJob.objects.filter(material_cost__gt=0):
        job.job_value = job.material_cost
        job.save(update_fields=['job_value'])


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0105_lathejob_value_attachment_cleanup'),
    ]

    operations = [
        migrations.RunPython(copy_material_cost_to_job_value, migrations.RunPython.noop),
    ]
