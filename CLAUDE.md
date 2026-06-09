# CLAUDE.md — LAMY Project Development Guide

This file is the authoritative guide for Claude Code when developing, extending, or maintaining the LAMY industrial monitoring system. Read this before making any changes.

---

## Project Identity

**LAMY** is a Django 5.2 web application for a Thai sugar mill. It manages:
- Boiler operation logs (6 units, 25–100+ params/entry)
- Condition-Based Monitoring (CBM) for equipment (5 inspection types)
- Maintenance failure logging and KPI tracking
- Mill production daily reports
- Equipment master registry with spare parts (BOM)
- Lathe job tracking

**Primary language in UI:** Thai (`verbose_name` in models/forms uses Thai strings)
**Users:** Plant operators and maintenance engineers — non-technical audience

---

## Architecture

### File Map

```
learning/
  settings.py     → Django config, DB, static/media paths
  urls.py         → Root router (admin + myapp.urls)

myapp/
  models.py       → ALL models in one file (~815 lines)
  views.py        → ALL view functions in one file (function-based only)
  urls.py         → ALL URL patterns for the app
  forms.py        → ALL ModelForms (Bootstrap-styled widgets)
  admin.py        → Django Admin registration for all models
  migrations/     → 49 migration files (do not edit manually)
  templates/myapp/
    base.html     → Master layout with nav bar
    *.html        → One template per view/module
    css/          → Custom Bootstrap-derived stylesheets
```

### Key Architectural Decisions

1. **Single-app design** — Everything lives in `myapp/`. Do not create additional Django apps.
2. **Function-based views only** — No class-based views. All views are plain Python functions.
3. **No REST framework** — JSON endpoints are plain Django views returning `JsonResponse`.
4. **SQLite** — Default database. Do not introduce migrations requiring PostgreSQL-only features.
5. **No JavaScript framework** — Frontend uses inline JS + Bootstrap + AJAX `fetch()`. No React/Vue/etc.
6. **Inline JavaScript** — JS logic lives inside `{% block %}` in templates, not separate `.js` files.

---

## How to Add a New Module

Follow this checklist exactly — every module needs all 5 layers.

### Step 1: Model (`myapp/models.py`)

Add the new model at the bottom of the file.

```python
class MyNewLog(models.Model):
    date = models.DateField(verbose_name="วันที่")
    shift = models.CharField(max_length=10, verbose_name="กะ")
    # ... fields
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ชื่อภาษาไทย"
        ordering = ['-date']
```

Rules:
- Use `verbose_name` with Thai strings for all operator-facing fields.
- Timestamps: use `DateField` + `TimeField` separately, not `DateTimeField`, for shift-based data.
- Numeric sensor values: use `DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)`.
- Optional fields: always add `null=True, blank=True` — operators skip fields they don't have data for.

### Step 2: Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

Never edit migration files manually.

### Step 3: Form (`myapp/forms.py`)

Add a `ModelForm` at the bottom of the file.

```python
class MyNewLogForm(forms.ModelForm):
    class Meta:
        model = MyNewLog
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shift': forms.Select(attrs={'class': 'form-control'}),
            # apply 'class': 'form-control' to every widget
        }
```

Rules:
- Every widget must have `'class': 'form-control'` for Bootstrap styling.
- Date inputs: `forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})`.
- Dropdowns: `forms.Select(attrs={'class': 'form-control'})`.

### Step 4: View (`myapp/views.py`)

Add view functions at the bottom of the file. Pattern for a form-based add view:

```python
@login_required
def my_new_log_add(request):
    if request.method == 'POST':
        form = MyNewLogForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('my_new_log_list')
    else:
        form = MyNewLogForm()
    return render(request, 'myapp/my_new_log_form.html', {'form': form})


@login_required
def my_new_log_list(request):
    logs = MyNewLog.objects.all().order_by('-date')
    return render(request, 'myapp/my_new_log_list.html', {'logs': logs})
```

Rules:
- All views must have `@login_required`.
- POST handlers: validate with `form.is_valid()` before saving.
- After a successful POST, always `redirect()` — never re-render the POST response.
- JSON API views return `JsonResponse({'data': [...]})`.

### Step 5: URL (`myapp/urls.py`)

Add URL patterns to the existing `urlpatterns` list:

```python
path('mynew/', views.my_new_log_list, name='my_new_log_list'),
path('mynew/add/', views.my_new_log_add, name='my_new_log_add'),
```

### Step 6: Template

Create `myapp/templates/myapp/my_new_log_form.html`:

```html
{% extends 'myapp/base.html' %}
{% block content %}
<div class="container mt-4">
  <h4>เพิ่มข้อมูล</h4>
  <form method="post">
    {% csrf_token %}
    {% for field in form %}
      <div class="mb-3">
        <label class="form-label">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}<div class="text-danger">{{ field.errors }}</div>{% endif %}
      </div>
    {% endfor %}
    <button type="submit" class="btn btn-primary">บันทึก</button>
  </form>
</div>
{% endblock %}
```

Rules:
- Always extend `base.html`.
- Always include `{% csrf_token %}` in every form.
- Use Bootstrap classes (`container`, `mb-3`, `form-label`, `btn btn-primary`).
- Show field errors inline.

### Step 7: Admin (`myapp/admin.py`)

Register the model:

```python
@admin.register(MyNewLog)
class MyNewLogAdmin(admin.ModelAdmin):
    list_display = ['date', 'shift', ...]
    list_filter = ['date', 'shift']
    search_fields = ['shift']
```

### Step 8: Navigation

Add a link to the new module in `myapp/templates/myapp/base.html` in the navigation bar.

---

## How to Add a Field to an Existing Model

1. Add the field to the model in `models.py` with `null=True, blank=True` (required for existing rows).
2. Add the field to the corresponding form in `forms.py` (in `fields` list or `fields = '__all__'`).
3. Add widget styling for the new field if it needs a specific input type.
4. Run `python manage.py makemigrations && python manage.py migrate`.
5. Update templates if the field should appear in the view.
6. Update `list_display` in `admin.py` if the field is important for admin review.

---

## Boiler Module Pattern

All 6 boiler units follow the same pattern. When adding a new boiler unit or modifying an existing one:

| File | What to change |
|---|---|
| `models.py` | Add/modify `<Name>Log` model |
| `forms.py` | Add/modify `<Name>Form` |
| `views.py` | Add `<name>_add()` and `<name>_list()` views |
| `urls.py` | Add `/boiler/<name>/add/` and `/boiler/<name>/` routes |
| `templates/` | Add `<name>_form.html` and `<name>_list.html` |
| `admin.py` | Register `<Name>Log` with appropriate `list_display` |

Reference: `BoilerOperationLog` (JT boiler) is the canonical example — study it before adding a new boiler unit.

---

## CBM Module Pattern

CBM data is linked to `Equipment` via ForeignKey. All 5 CBM types follow the same structure:

```python
class CBMSomeType(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    date = models.DateField()
    inspector = models.CharField(max_length=100, null=True, blank=True)
    # ... type-specific measurement fields
    notes = models.TextField(null=True, blank=True)
```

CBM forms are submitted from the equipment CBM dashboard at `/equipment/cbm/<eq_id>/`. All CBM types are handled by a single view `equipment_cbm()` which dispatches based on a `cbm_type` POST field.

---

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Models | PascalCase | `BoilerOperationLog`, `CBMVibration` |
| Views | snake_case functions | `equipment_data`, `add_boiler_operation` |
| Forms | PascalCase + Form suffix | `BoilerOperationForm`, `CBMVibrationForm` |
| URL patterns | kebab-style paths | `/boiler/operation/add/` |
| Templates | snake_case filenames | `boiler_operation_form.html` |
| URL names | snake_case | `name='boiler_operation_add'` |

---

## Do Not

- **Do not** create a second Django app (`python manage.py startapp`). All code goes in `myapp/`.
- **Do not** use class-based views (CreateView, ListView, etc.). Use function-based views.
- **Do not** install Django REST Framework. Use `JsonResponse` for JSON endpoints.
- **Do not** introduce React, Vue, or any JS bundler. Frontend is vanilla JS + Bootstrap.
- **Do not** use `DateTimeField` for shift-based log entries — use `DateField` + `TimeField` separately.
- **Do not** make fields non-nullable without a default value — operators skip fields frequently.
- **Do not** hardcode the `SECRET_KEY` in `settings.py` for production. Use `.env`.
- **Do not** commit `db.sqlite3` or `.env` — both are in `.gitignore`.
- **Do not** edit migration files manually. Always use `makemigrations`.

---

## Common Tasks

### Reset the database (development only)

```bash
# Delete SQLite database and all migrations (WARNING: destroys all data)
del db.sqlite3
# Then remove migration files (keep __init__.py):
# myapp/migrations/000*.py
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Add a superuser

```bash
python manage.py createsuperuser
```

### Check migration status

```bash
python manage.py showmigrations myapp
```

### Open Django ORM shell

```bash
python manage.py shell
# Example: query all equipment
from myapp.models import Equipment
Equipment.objects.filter(is_active=True).count()
```

### Run tests

```bash
python manage.py test myapp
python test_view.py    # standalone view tests
python test_form.py    # standalone form tests
```

### Debug data issues

```bash
python check_mill_data.py     # verify mill data integrity
python check_tags.py          # verify data tags
python fix_tags.py            # fix incorrect tags
```

---

## Environment Variables

Never set these in code. Use a `.env` file (gitignored):

```env
SECRET_KEY=<random 50+ char string>
DEBUG=False
ALLOWED_HOSTS=lamy23.cloud,www.lamy23.cloud
```

For production, `DEBUG` must be `False` and `ALLOWED_HOSTS` must not be `['*']`.

---

## Deployment

The project runs via Docker Compose:

```
docker-compose.yml
  web   → Python 3.10-slim, runs Django on :8000
  nginx → Reverse proxy on :80/:443, serves staticfiles/
```

Deployment sequence:
```bash
docker-compose up --build -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py createsuperuser
```

Production domain: `https://lamy23.cloud` (configured in `CSRF_TRUSTED_ORIGINS`)

---

## Security Checklist (Before Production)

- [ ] Move `SECRET_KEY` to `.env`
- [ ] Set `DEBUG = False`
- [ ] Set `ALLOWED_HOSTS` to specific domain(s)
- [ ] Run `collectstatic`
- [ ] Verify `media/` volume is mounted persistently in Docker
- [ ] Confirm Nginx SSL certificate is configured

---

## Known Constraints

| Constraint | Detail |
|---|---|
| SQLite concurrency | SQLite locks on write — not suitable for >10 simultaneous users writing data |
| No RBAC | All authenticated users have equal access to all modules |
| No audit log | No record of who changed what (Django Admin tracks its own changes only) |
| No real-time data | No sensor/PLC integration — all data is manually entered |
| Google Drive optional | `file_id` fields in Equipment/CBM models reference Drive files, but Drive API is not required to run the system |

---

## เมื่อต้องอัปเดต README.md

`README.md` คือเอกสารหลักสำหรับมนุษย์และทีมงานที่เข้ามาใหม่ ต้องอัปเดตทันทีเมื่อเกิดเหตุการณ์ต่อไปนี้:

| เหตุการณ์ | Section ที่ต้องอัปเดต |
|---|---|
| เพิ่ม Django model ใหม่ | `9. Database Models` |
| เพิ่ม URL endpoint ใหม่ | `10. API Endpoints` |
| เพิ่มหรือเปลี่ยน Python dependency (`requirements.txt`) | `2. Tech Stack` |
| เพิ่ม module / feature หลักใหม่ | `1. Project Overview` และ `8. Key Modules` |
| เปลี่ยน Docker หรือ deployment config | `11. Deployment` |
| เพิ่ม environment variable ใหม่ | `12. Environment Variables` |
| เปลี่ยนโครงสร้างโฟลเดอร์หลัก | `4. Project Structure` |
| เพิ่ม utility script ใหม่ | `3. Commands — Utility Scripts` |

### วิธีปฏิบัติ

เมื่อทำงานเสร็จในแต่ละ session ให้ตรวจรายการนี้ก่อน commit:

```
[ ] แก้ models.py → อัปเดต Database Models ใน README.md หรือไม่?
[ ] แก้ urls.py   → อัปเดต API Endpoints ใน README.md หรือไม่?
[ ] แก้ requirements.txt → อัปเดต Tech Stack ใน README.md หรือไม่?
[ ] เพิ่ม feature ใหม่ → อัปเดต Overview / Key Modules ใน README.md หรือไม่?
```

> หากไม่แน่ใจว่าต้องอัปเดตส่วนไหน ให้บอก Claude Code ว่า "อัปเดต README.md ตามสิ่งที่เพิ่งแก้ไข" — Claude จะตรวจ diff และอัปเดตให้ตรงจุด
