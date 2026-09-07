from django.core.management.base import BaseCommand
from myapp.models import TrainingRecord, EmployeeSkillLevel


class Command(BaseCommand):
    help = (
        'Backfill EmployeeSkillLevel for employees who already passed an online '
        'exam for a course that is now linked to a skill (covers courses linked '
        'to a skill after employees had already passed them).'
    )

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Actually update levels (default is dry-run preview)')

    def handle(self, *args, **options):
        apply = options['apply']

        passed_records = (
            TrainingRecord.objects
            .filter(training_type='online', status='passed', course__skill__isnull=False)
            .select_related('employee', 'course', 'course__skill')
        )

        counts = {}       # (employee_id, skill_id) -> set of course_id
        emp_lookup = {}
        skill_lookup = {}
        for rec in passed_records:
            key = (rec.employee_id, rec.course.skill_id)
            counts.setdefault(key, set()).add(rec.course_id)
            emp_lookup[rec.employee_id] = rec.employee
            skill_lookup[rec.course.skill_id] = rec.course.skill

        existing = {
            (lvl.employee_id, lvl.skill_id): lvl
            for lvl in EmployeeSkillLevel.objects.filter(skill_id__in={s for _, s in counts})
        }

        changed = 0
        for (emp_id, skill_id), course_ids in counts.items():
            target_level = min(len(course_ids), 3)
            current = existing.get((emp_id, skill_id))
            current_level = current.level if current else None
            if current_level is not None and current_level >= target_level:
                continue

            changed += 1
            label = f'{emp_lookup[emp_id].full_name} / {skill_lookup[skill_id].name}'
            self.stdout.write(f'  {label}: {"none" if current_level is None else f"L{current_level}"} -> L{target_level}')

            if apply:
                if current is None:
                    EmployeeSkillLevel.objects.create(employee_id=emp_id, skill_id=skill_id, level=target_level)
                else:
                    current.level = target_level
                    current.save(update_fields=['level'])

        if not apply:
            self.stdout.write(self.style.WARNING(f'\nDry-run: {changed} EmployeeSkillLevel row(s) would change. Re-run with --apply to apply them.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nDone — updated {changed} EmployeeSkillLevel row(s).'))
