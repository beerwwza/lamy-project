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
5. **No JavaScript framework** — Frontend uses vanilla JS + Tailwind CSS + Lucide icons via CDN. **No React, Vue, Angular, Svelte, or any component framework.** No Babel, no JSX, no bundler.
6. **Inline JavaScript** — JS logic lives inside `{% block %}` in templates, not separate `.js` files.
7. **Django template rendering** — All data is rendered server-side via Django template tags (`{% if %}`, `{% for %}`, `{{ var }}`). Do not inject server data as JSON and parse it client-side with React or similar.
8. **CDN dependencies** — `base.html` loads Tailwind CSS and Lucide Icons via CDN. Templates extend `base.html` and inherit these. Do not load React, Babel, or additional heavy CDN libraries.

### Frontend Pattern (the right way)

```html
{% extends 'myapp/base.html' %}
{% block content %}
<!-- Use Django template tags for data -->
{% if some_condition %}
  <div class="...tailwind classes...">{{ value }}</div>
{% endif %}
{% for item in items %}
  <tr>...</tr>
{% endfor %}

<!-- Plain JS for interactivity (tabs, toggles, AJAX) -->
<script>
  function showTab(name) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.getElementById('tab-' + name).style.display = 'block';
  }
  lucide.createIcons(); // re-call after DOM changes
</script>
{% endblock %}
```

### Why no React on this project

React + Babel standalone requires `eval()` in the browser. In production environments this can be blocked silently, causing the entire page to render as a blank black screen with no visible error. The app crashed this way on `dashboard.html` — the React version was replaced with a plain Django template that works reliably.

---

## Responsive / Mobile Layout Standard

This project targets phones as a first-class client (shop-floor/field use — operators fill in logs from the plant floor, not just a desk). Every template — new or edited — must follow these rules. Reference implementation: `boiler_operation_form.html`, which is mobile-first throughout.

The global sidebar in `base.html` is a fixed-width drawer on desktop (`md:` and up) and an off-canvas slide-in drawer on mobile, opened via a floating hamburger button (`toggleSidebar()`, bottom-left, fixed) with a tap-to-close overlay. This was fixed after users reported the layout being "too large"/squeezed on phones — the sidebar previously had zero responsive treatment and permanently ate ~256px of a ~375px screen.

### 1. Mobile-first grids

Always specify a `grid-cols-1` base, then scale up:

```html
<!-- Good -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

<!-- Bad — crushes content on a 375px phone -->
<div class="grid grid-cols-3 gap-4">
```

Any grid cell containing a KPI number (`text-3xl`/`text-4xl`/`text-5xl` etc.) must start at `grid-cols-1` on mobile, never `grid-cols-2` or higher — the number gets crushed otherwise.

### 2. Tables always scroll, never squeeze

Every `<table>` must be wrapped:

```html
<div class="overflow-x-auto">
  <table class="w-full text-sm">...</table>
</div>
```

This project has no JS framework for a card-view fallback — horizontal scroll inside a bounded container is the accepted mobile pattern here. Add the wrapper unconditionally, even if the table looks small today (columns get added later).

### 3. Form inputs stack full-width on mobile

Inside a `flex flex-wrap` filter/form bar, give each input/select wrapper a responsive width so fields stack cleanly instead of sizing to content:

```html
<div class="w-full sm:w-auto">
  <label class="...">...</label>
  <select class="w-full sm:w-auto border ...">...</select>
</div>
```

### 4. Sidebar / navigation

The sidebar drawer, hamburger button, and overlay live in `base.html` and are inherited automatically by every page that extends it — do not reimplement navigation per-template. When adding a new module's nav link (Step 8 below), just add the `<li>` inside the existing `<ul>` in `base.html`; the responsive drawer behavior applies to it for free.

Pages that do **not** extend `base.html` (self-contained `<!DOCTYPE html>` documents) do not get this drawer — avoid this pattern for anything a user browses on a phone; it's only acceptable for print-only views.

### 5. Button/action rows

Any row of action buttons (`flex items-center gap-2`) in a header must include `flex-wrap` so buttons wrap to a new line instead of overflowing on narrow screens. Pair it with `min-h-*` instead of a fixed `h-*` on the containing header, so wrapped content isn't clipped.

### 6. `<select>` needs `appearance-none` + a custom chevron to match `<input>` height

A `<select>` renders at a **different native height than `<input>`/`<textarea>` even with a byte-identical Tailwind class string** — confirmed by measurement (Playwright `boundingBox()`): with the shared `_TW_TASK`-style class (`p-2.5`, `border`, `text-sm`), `<input type="text">` measured **42px** tall while `<select>` measured **47px**. The browser's native OS "menulist" control (`appearance: auto` / `-webkit-appearance: auto`) boxes itself differently regardless of declared padding — this is a browser default, not a copy-paste mistake, and it affects every `<select>` in the project (the original Task Manager's status dropdown has the same 5px mismatch; it just went unnoticed).

The fix, applied per `<select>` (both `ModelForm`-rendered and raw hand-written ones):
```python
# forms.py — derive a select-only variant from the module's shared input class:
_TW_TASK_SELECT = _TW_TASK + ' appearance-none pr-8'
# ... 'status': forms.Select(attrs={'class': _TW_TASK_SELECT}),
```
```html
<!-- template — appearance-none removes the native arrow, so draw one back with Lucide -->
<div class="relative">
  {{ form.status }}
  <i data-lucide="chevron-down" class="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"></i>
</div>
```
Rules:
- Every `<select>` gets `appearance-none pr-8` (the `pr-8` reserves room for the chevron so option text doesn't run under it) and is wrapped in its own `relative` div with the chevron `<i>` — wrap the `<select>` alone, not the label+select block, or the icon won't center on the control.
- This applies to raw hand-written `<select>` elements too (cascading process→equipment dropdowns), not just `ModelForm` widgets — the native-appearance issue is on the `<select>` element itself, independent of how it was rendered.
- Separately, every `<input>`/`<select>`/`<textarea>` in one form should still share one Tailwind class string apart from this select-specific addition (don't invent a new class from memory or copy a different template's convention) — verify with `grep -n 'class="w-full'` before shipping.
- `<input type="date">`/`<input type="time">` are ~2px taller than `<input type="text">` for the same reason (native picker-icon chrome); this is barely visible and is not worth risking `appearance-none` on, since it can suppress the clickable calendar icon in some browsers — leave date/time inputs alone.
- Verify with real pixel measurements, not eyeballing a screenshot — a 5px `<select>` vs `<input>` gap is easy to miss visually. If Playwright/Chromium is available, measure `boundingBox().height` for one of each control type in the form and confirm they match.

### 7. Verification

No automated visual testing exists in this project. Manually check every new/edited template in browser devtools responsive mode at minimum: **375px** (small phone), **768px** (tablet/`md:` breakpoint boundary — sidebar switches from drawer to static exactly here), and **1280px** (desktop). Confirm: no horizontal page scroll (only inside `overflow-x-auto` table wrappers), no clipped/overlapping text, hamburger opens/closes the drawer cleanly with tap-outside-to-close working below 768px, and all form fields in the same form are visually the same size (see item 6).

### Note on Tailwind vs Bootstrap classes

Tailwind (CDN) is the standard for page layout, grids, and containers — use it for all new markup per the rules above. Some `ModelForm` widgets independently render Bootstrap classes (`form-control`, `mb-3`, etc., see Step 6 of "How to Add a New Module") via widget `attrs` — that's a separate, pre-existing convention for form-field styling only, not something to unify with Tailwind. Don't add Bootstrap layout classes (`row`/`col`/`container`) to new templates, only Tailwind utility classes.

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
- Follow the [Responsive / Mobile Layout Standard](#responsive--mobile-layout-standard) above for all grids, tables, and multi-field forms in the new template.

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
- **Do not** introduce React, Vue, Angular, Svelte, or any component framework — not even via CDN. This caused a production outage (blank black screen) because Babel standalone requires `eval()` which is blocked in some environments. Use Django template tags + vanilla JS instead.
- **Do not** load Babel standalone (`@babel/standalone`) or write JSX in templates. There is no transpilation step in this project.
- **Do not** use `json_script` + client-side JSON parsing as a replacement for Django template rendering. Render data with `{{ var }}` and `{% for %}` / `{% if %}` tags.
- **Do not** load more than the CDN libraries already in `base.html` (Tailwind CSS, Lucide icons, Google Fonts). If a new library is genuinely needed, add it to `base.html` after discussion — not per-template.
- **Do not** use `DateTimeField` for shift-based log entries — use `DateField` + `TimeField` separately.
- **Do not** make fields non-nullable without a default value — operators skip fields frequently.
- **Do not** hardcode the `SECRET_KEY` in `settings.py` for production. Use `.env`.
- **Do not** commit `db.sqlite3` or `.env` — both are in `.gitignore`.
- **Do not** edit migration files manually. Always use `makemigrations`.
- **Do not** add a `grid-cols-N` (N≥2) class without a `grid-cols-1` mobile base, and **do not** add a `<table>` without wrapping it in `<div class="overflow-x-auto">` — see [Responsive / Mobile Layout Standard](#responsive--mobile-layout-standard).
- **Do not** style a `<select>` with the same Tailwind class as `<input>`/`<textarea>` and expect matching height — it needs `appearance-none pr-8` plus a custom chevron icon, or it renders taller due to native OS control styling. See item 6 of [Responsive / Mobile Layout Standard](#responsive--mobile-layout-standard).

### Dashboard view pattern — pre-compute alert flags in the view

Django templates cannot do arithmetic comparisons (`value > 1.01`). When a template needs per-field alert colours, add boolean flags in the view's context dict instead of offloading logic to JavaScript:

```python
boiler_data = {
    'downtime_a': float(kpi.downtime_a),
    'downtime_a_alert': bool(kpi.downtime_a > 1.01),  # ← pre-computed flag
    ...
}
```

Then in the template:
```html
{% if boiler.downtime_a_alert %}
  <div class="border-orange-400 text-orange-600">...</div>
{% else %}
  <div class="border-slate-200 text-slate-800">...</div>
{% endif %}
```

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
