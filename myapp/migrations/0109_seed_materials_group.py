from django.db import migrations


def seed_materials_group(apps, schema_editor):
    """สร้าง Group 'Materials Staff' ผูก permission write_materials
       แล้วเพิ่ม staff เดิมทุกคนเข้ากลุ่มนี้ (รูปแบบเดียวกับ 0097_seed_energy_group.py)"""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User = apps.get_model('auth', 'User')

    profile_ct, _ = ContentType.objects.get_or_create(app_label='myapp', model='profile')

    group, _ = Group.objects.get_or_create(name='Materials Staff')
    perm, _ = Permission.objects.get_or_create(
        content_type=profile_ct,
        codename='write_materials',
        defaults={'name': 'เขียนข้อมูล: Material Master (รหัสวัสดุ SAP)'},
    )
    group.permissions.add(perm)

    for user in User.objects.filter(is_staff=True, is_superuser=False):
        user.groups.add(group)


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0108_materialmaster'),
    ]

    operations = [
        migrations.RunPython(seed_materials_group, migrations.RunPython.noop),
    ]
