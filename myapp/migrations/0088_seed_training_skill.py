from django.db import migrations

TRAINING_SKILL_SEED = [
    'Bolt&nut',
    'สารหล่อลื่น',
    'เครื่องมือวัด',
    'วัสดุ',
    'เชื่อม,ตัด',
    'เนมเพลท',
    'ลูกปืน',
    'พิกัดงานสวม',
    'อัลลายเม้นท์',
    'ไฮโดรลิค',
]


def seed_training_skills(apps, schema_editor):
    TrainingSkill = apps.get_model('myapp', 'TrainingSkill')
    for order, name in enumerate(TRAINING_SKILL_SEED):
        TrainingSkill.objects.get_or_create(name=name, defaults={'display_order': order})


def unseed_training_skills(apps, schema_editor):
    # Best-effort reverse: no-op, since skills may have been edited via
    # Django Admin by the time of rollback.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0087_trainingrecord_video_completed_at'),
    ]

    operations = [
        migrations.RunPython(seed_training_skills, unseed_training_skills),
    ]
