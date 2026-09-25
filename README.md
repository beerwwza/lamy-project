# LAMY — Industrial Monitoring & Maintenance System

A comprehensive Django-based industrial monitoring platform designed for sugar mill operations. The system covers boiler operation logging, equipment condition-based monitoring (CBM), maintenance management, mill production reporting, and lathe job tracking — all in one integrated web application.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Commands](#3-commands)
4. [Project Structure](#4-project-structure)
5. [Code Style](#5-code-style)
6. [Testing and Validation](#6-testing-and-validation)
7. [Boundaries](#7-boundaries)
8. [Key Modules](#8-key-modules)
9. [Database Models](#9-database-models)
10. [API Endpoints](#10-api-endpoints)
11. [Deployment](#11-deployment)
12. [Environment Variables](#12-environment-variables)

---

## 1. Project Overview

LAMY is a web-based industrial operations management system built for a large-scale sugar mill facility. It provides:

- **Boiler Operations Monitoring** — Real-time data logging for 6 boiler units (JT/Jetshin, Yoshimine, Banpong 1 & 2, Chengchen, Takuma), each with 25–100+ parameters per shift entry (steam flow, pressure, temperature, water quality, emissions).
- **Condition-Based Monitoring (CBM)** — Equipment health data collected via 5 inspection types: Visual, Vibration, Thermoscan (infrared), Oil Analysis, and Acoustic monitoring.
- **Maintenance Management** — Failure logging, root cause analysis, downtime categorization, spare parts tracking, and KPI scoring.
- **Mill Production Reporting** — Daily production KPIs for Line A/B covering extraction rates, purity, bagasse moisture, and throughput.
- **Equipment Registry** — Master inventory of all plant equipment with technical specifications, maintenance history, spare parts (BOM), criticality levels, and image storage.
- **Lathe Job Tracking** — Machining job management with job requirements, quality control records, and status tracking.
- **Tools Module** — Dedicated hand-tool tracking (`/tools/`) separate from general Inventory, with per-physical-unit status (so identical tools like 5 impact wrenches are tracked individually), borrow/return history with due dates, and an integrated tool-readiness checklist.
- **Manual Library** (`/manuals/`) — Structured machine operation & maintenance manuals (cover info, safety precautions, part names, pre-use checklist, operating steps, daily/periodic maintenance, troubleshooting, specifications), built via a multi-section form with dynamic add/remove rows.
- **Task Manager** (`/tasks/`) — A hub page linking to 4 equipment-readiness test types, each its own sub-module with its own list/form pages: **Rotating/Electrical/Control** (`/tasks/rotating/`) — pick equipment from the registry, track a task through Todo → Doing → Done, and record a full vibration measurement set (Amp, DE/NDE, Temp) for both the no-load and loaded run phases, compared side by side (each phase reading is also written into `CBMVibration` so it shows in the equipment's normal CBM history); **Water System Test (CIP)** (`/watercip/`) — pick a process, a start equipment and an end equipment along the tested water path, then log an unlimited number of pH readings (time + value); **Steam System Test (Leak Inspection)** (`/steamleak/`) — pick a process and a single piece of equipment, then work through a repeatable checklist (topic → item → standard → normal/abnormal; if abnormal, cause → corrective action → fix-due date); **Flushing Test** (`/flushing/`) — pick a process and a pipe/equipment, log unlimited blow rounds (round number, start/end time, blow pressure in bar, whether a copper plate was inserted, and — only when a plate was used — the count of spots larger than 0.3mm found), with pass/fail per round computed automatically (≤ 3 oversized spots/cm² passes). All 4 share the same task shell (title/assignee/status/note).
- **Energy Tracking — Electricity** (`/electricity/`, Phase 1 of a broader Energy module; steam usage is a planned Phase 2) — Daily cumulative electricity-meter readings per plant (ESC-A / ESC-B), with each meter optionally linked to multiple pieces of equipment to auto-calculate a daily kWh(Max) target from their `power_kw`. Dashboards at plant level and per-meter/process level show actual vs. target kWh, a daily trend chart, a 6-month summary table, and month-over-month/year-over-year % comparisons.

The system is primarily operated by plant engineers and maintenance teams, with data used for production optimization and equipment health trend analysis.

---

## 2. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend Framework | Django | >= 5.2 |
| Language | Python | 3.10 |
| Database | SQLite3 | — |
| Web Server | Gunicorn / Django dev server | — |
| Reverse Proxy | Nginx | (via Docker) |
| Containerization | Docker + Docker Compose | — |
| Data Processing | Pandas, NumPy | — |
| Excel / CSV | OpenPyXL | — |
| Image Processing | Pillow | — |
| Frontend Styling | Bootstrap (custom CSS) | — |
| File Storage | Google Drive API (optional) | — |

### Python Dependencies (`requirements.txt`)

```
Django>=4.2
pandas
numpy
openpyxl
Pillow
```

---

## 3. Commands

### Local Development

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create superuser (admin access)
python manage.py createsuperuser

# Run development server
python manage.py runserver
# Server runs at http://127.0.0.1:8000
```

### Database Management

```bash
# Create new migrations after model changes
python manage.py makemigrations

# Apply pending migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Open Django shell (ORM access)
python manage.py shell
```

### Static Files

```bash
# Collect static files to staticfiles/ (required for production)
python manage.py collectstatic
```

### Docker

```bash
# Build and start all services (web + nginx)
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d

# Stop all services
docker-compose down

# View running container logs
docker-compose logs -f web

# Run Django commands inside container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Utility Scripts

```bash
# Check and debug mill data
python check_mill_data.py
python debug_mill_data.py

# Verify data tags
python check_tags.py
python check_tags2.py

# Fix incorrect tags
python fix_tags.py

# Test Google Drive upload integration
python test_gdrive_upload.py

# Test CBM template binding
python bind_cbm.py
```

---

## 4. Project Structure

```
lamy-project/
├── manage.py                       # Django CLI entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker image (Python 3.10-slim)
├── docker-compose.yml              # Multi-service orchestration
├── db.sqlite3                      # SQLite database (gitignored)
├── .env                            # Environment variables (gitignored)
├── .gitignore
│
├── learning/                       # Django project configuration
│   ├── settings.py                 # App settings, database, middleware
│   ├── urls.py                     # Root URL dispatcher
│   └── wsgi.py                     # WSGI entry point
│
├── myapp/                          # Main application
│   ├── models.py                   # All database models (~815 lines)
│   ├── views.py                    # View functions / controllers
│   ├── urls.py                     # App URL routing
│   ├── forms.py                    # Django ModelForms (all modules)
│   ├── admin.py                    # Django Admin configuration
│   ├── migrations/                 # 81 database migration files
│   └── templates/
│       └── myapp/
│           ├── base.html           # Master layout with navigation
│           ├── login.html
│           ├── register.html
│           ├── dashboard.html
│           ├── boiler.html
│           ├── boiler_operation.html
│           ├── boiler_operation_form.html
│           ├── banpong1_form.html
│           ├── banpong2_form.html
│           ├── chengchen_form.html
│           ├── yoshimine_form.html
│           ├── takuma_form.html
│           ├── boiler_kpi_form.html
│           ├── maintenance_dashboard.html
│           ├── maintenance_log_form.html
│           ├── maintenance_kpi_metric_form.html
│           ├── mill.html
│           ├── mill_report.html
│           ├── lathe.html
│           ├── equipment_list.html
│           ├── equipment_form.html
│           ├── equipment_data.html
│           ├── equipment_bom.html
│           ├── tableemployee.html
│           └── css/                # Custom Bootstrap-based stylesheets
│
├── staticfiles/                    # Collected static files (production)
├── media/                          # User-uploaded files (equipment images)
├── nginx/                          # Nginx configuration files
│
└── (utility scripts)
    ├── bind_cbm.py
    ├── check_mill_data.py
    ├── debug_mill.py
    ├── check_tags.py
    ├── fix_tags.py
    ├── test_gdrive_upload.py
    ├── test_lathe.py
    ├── test_form.py
    └── test_view.py
```

---

## 5. Code Style

### Django Conventions

- **Views** — Function-based views (FBVs) throughout; no class-based views used.
- **Forms** — All forms extend `ModelForm` with Bootstrap styling applied via widget `attrs`.
- **Authentication** — `@login_required` decorator applied on all protected views; login redirects to `/`.
- **URL naming** — URL patterns follow resource-oriented naming: `/equipment/<eq_id>/`, `/boiler/operation/add/`, etc.
- **Imports** — Standard Django imports at the top, then third-party (Pandas, NumPy), then local models/forms.

### Data Model Conventions

- Primary keys use Django's default auto-incrementing `id`.
- Equipment uses a custom `eq_id` CharField as a human-readable identifier.
- Boolean fields for active/inactive states use `is_active` naming.
- Timestamps use `DateField` and `TimeField` separately (not `DateTimeField`).
- Thai-language field `verbose_name` labels throughout models and forms for operator-facing UI.
- Nullable fields use `null=True, blank=True` to accommodate partial data entry.

### Frontend Conventions

- All pages extend `base.html` via `{% extends %}`.
- Bootstrap grid and utility classes for layout.
- Form rendering uses custom Bootstrap-styled form widgets.
- JavaScript inline in templates for dynamic behavior (chart rendering, AJAX calls to API endpoints).

### Naming

- Models: `PascalCase` (e.g., `BoilerOperationLog`, `CBMVibration`)
- Views: `snake_case` functions (e.g., `equipment_data`, `add_boiler_operation`)
- URL names: `snake_case` kebab-style paths (e.g., `/boiler/operation/add/`)
- Templates: `snake_case` filenames matching their view (e.g., `equipment_form.html`)

---

## 6. Testing and Validation

### Test Files

```
test_lathe.py     — Lathe job module tests
test_form.py      — Form validation tests
test_view.py      — View response tests
```

Run tests with:

```bash
python manage.py test myapp
# or run specific test scripts directly
python test_view.py
python test_form.py
```

### Data Validation

- Django ModelForms provide field-level validation on all form submissions.
- Numeric parameters on boiler and CBM forms are bounded by `DecimalField` precision/max_digits constraints.
- CSV/Excel imports are processed through Pandas with error handling before writing to the database.
- Debug/check scripts (`check_mill_data.py`, `check_tags.py`) can be run manually to audit data integrity.

### Admin Interface Validation

The Django Admin (`/admin/`) provides a second layer for reviewing and correcting data:
- All models registered with custom `list_display`, `search_fields`, and `list_filter`.
- Direct record editing available to superusers.

---

## 7. Boundaries

### What This System Does NOT Handle

- **Real-time sensor data ingestion** — All data is manually entered by operators via web forms; there is no automated OPC-UA, MQTT, or PLC integration.
- **Alerting / Notifications** — No automated email, SMS, or push alert system for threshold breaches.
- **Reporting / PDF Export** — No built-in report generation to PDF; data export is via CSV/Excel import utilities only.
- **Multi-tenancy** — Single-site deployment; no multi-plant or organization separation.
- **Role-based Access Control (RBAC)** — Module-level *write* access is enforced (see [Access Control](#8-key-modules) in Key Modules), using Django's built-in Groups/Permissions; there is still no field-level or per-record permission granularity, and read access is not separately restricted by module.
- **Audit Logs** — No automatic record of who changed what and when (beyond Django's admin history).

### Infrastructure Boundaries

- **Database** — SQLite3 only; not suitable for high-concurrency writes beyond a single plant deployment. Migration to PostgreSQL would be required for scaling.
- **File Storage** — Media files stored locally in `media/`; Google Drive integration exists for equipment images but is optional and not enforced.
- **SSL/HTTPS** — Provided via Nginx + Let's Encrypt in the Docker Compose setup; the Django app itself runs over HTTP.
- **Deployment Target** — Designed for single-server deployment (VPS or on-premises industrial PC); not architected for Kubernetes or horizontal scaling.

### Security Considerations

- `DEBUG = True` and `ALLOWED_HOSTS = ['*']` in `settings.py` are development defaults — **must be changed for production**.
- `SECRET_KEY` is hardcoded in `settings.py` — **must be moved to `.env`** before any public deployment.
- CSRF protection is enabled; `CSRF_TRUSTED_ORIGINS` is configured for `https://lamy23.cloud`.
- All views require login (`@login_required`); no public-facing data endpoints.

---

## 8. Key Modules

### Boiler Operations

Six boiler units, each with its own data model and form:

| Unit | Model | Key Parameters |
|---|---|---|
| JT / Jetshin | `BoilerOperationLog` | 30+ fields: steam flow/pressure/temp, feedwater, furnace, gas, pH, TDS, CEM |
| Yoshimine | `YoshimineLog` | 100+ fields including ESP (electrostatic precipitator) monitoring |
| Banpong 1 | `Banpong1Log` | High-capacity unit, 25+ parameters |
| Banpong 2 | `Banpong2Log` | High-capacity unit, 25+ parameters |
| Chengchen | `ChengchenLog` | Standardized 25+ parameters |
| Takuma | `TakumaLog` | Standardized 25+ parameters |

Daily KPIs are separately recorded in `BoilerDailyKPI` (13 metrics including downtime %, steam production, consumption rates).

### Condition-Based Monitoring (CBM)

Each equipment item can have multiple CBM records of 5 types:

| Type | Model | Metrics |
|---|---|---|
| Visual Inspection | `CBMVisualTest` | Condition rating (good/fair/poor), observations |
| Vibration Analysis | `CBMVibration` | Velocity (mm/s), acceleration (g), bearing temp, ISO status |
| Infrared Thermoscan | `CBMThermoscan` | Max temp, ambient temp, delta T |
| Oil Analysis | `CBMOilAnalysis` | Viscosity, water content %, wear particle level |
| Acoustic Monitoring | `CBMAcoustic` | Sound level (dB), pattern classification |

### Maintenance Management

`MaintenanceLog` captures:
- Equipment ID, failure category, description
- Downtime duration, lost production
- Root cause, corrective action, spare parts used
- Reporter and resolver personnel
- Status tracking (open → closed)

`KPIMetric` scores maintenance performance across weighted categories (1–4 scale).

### Equipment Registry

`Equipment` model tracks 30+ attributes per asset:
- Identification: ID, name, location, process area, manufacturer, model
- Technical specs: capacity, RPM, serial number, installation date
- Drive system: motor nameplate, panel, starter, breaker, drive type
- Maintenance KPIs: MTBF, MTTR, accumulated cost
- Priority level: 1-CRITICAL / 2-IMPORTANT / 3-GENERAL
- Image: local file or Google Drive file ID

### Tools Module (เครื่องมือ)

Standalone module at `/tools/`, separated from the general Inventory module (`InventoryItem` category `tools` is excluded from `/inventory/` views). Solves per-unit tracking for identical tools (e.g. 5 impact wrenches of the same SKU):

- `ToolUnit` — one row per physical tool (unit code, status: available/checked_out/maintenance/lost/retired), FK to `InventoryItem` (the "tool type")
- `ToolCheckout` — per-unit borrow/return history (borrower name as free text, optional due date, `return_date IS NULL` = still checked out; overdue = `due_date` in the past and not yet returned)
- `ToolReadinessCheck` — the tool-readiness checklist now records against a specific `ToolUnit` (in addition to the legacy item-level `item` FK); the checkout flow shows a soft warning (not a hard block) if the unit's latest check is "not ready"
- Checkout/return also writes an `InventoryTransaction` (linked via `tool_unit`) so the shared Inventory transaction ledger still reflects tool movement

### Manual Library

Standalone module at `/manuals/`, not linked to `Equipment` (machine name is free text) or to `RepairDocument`/`doc_repository` (which is a separate uploaded-file library). Categorized by department (`DEPARTMENT_CHOICES`).

- `Manual` — cover info (machine name, model, department, prepared by, doc no., revision, date) with 8 repeating child sections, each its own model + inline formset: `ManualSafetyItem`, `ManualPartItem`, `ManualPrecheckItem`, `ManualOperatingStep`, `ManualMaintenanceDailyItem`, `ManualMaintenancePeriodicItem`, `ManualTroubleshootItem`, `ManualSpecItem` (all `on_delete=CASCADE` from `Manual`). Editor page (`manual_form.html`) uses a tabbed single-page form with vanilla-JS dynamic add/remove rows (formset `cloneNode` + prefix renumbering — no React). Preview/print page (`manual_detail.html`) supports Export to PDF via `window.print()`. List page (`manual_list.html`) is a plain table of all manuals with a single "สร้างคู่มือใหม่" create button.

### Task Manager

`/tasks/` is a **hub page** (`task_manager_hub` view, `task_manager_hub.html`) showing 4 shortcut cards
(one per test type below, each with a live total/pending-count badge computed from that model's `status`
field) — it does not merge or query across the 4 models beyond those counts. Each test type is otherwise
a fully independent sub-module with its own model(s), form(s), list page and add/edit page; the hub is
purely a navigation layer sitting in front of them, added after the 4 types accumulated 4 separate flat
sidebar links that no longer read as one module. The sidebar now has a single "Task Manager" nav entry
(`base.html`) that links to the hub, and each sub-module's list page has a back-arrow to return to it.

- **Rotating / Electrical / Control** at `/tasks/rotating/` (originally `/tasks/`, moved when the hub took
  over that path — the URL *name* `machine_task_list` is unchanged, so every `{% url %}` reference
  elsewhere in the codebase kept working without edits) — linked to `Equipment` via FK, lets an operator
  pick a machine from the registry and track a readiness/trial-run task through a staged workflow instead
  of one big form:
  - `MachineTask` — equipment, title, assignee, status (`todo`/`doing`/`done`), note. Created via a modal on the list page (`machine_task_list.html`), which shows each equipment's `power_kw`/`rpm_input`/`rpm` as reference info on selection (plain `<option data-*>` attributes + vanilla JS, no extra endpoint).
  - `MachineTaskVibration` — child of `MachineTask`, one row per `phase` (`no_load`/`loaded`, enforced unique together), duplicating all 14 `CBMVibration` measurement fields (Amp, DE/NDE gE/V/H/A/M, Temp DE/FRAME/NDE). Submitting a phase's form on the task detail page (`machine_task_detail.html`) also creates a real `CBMVibration` row for that equipment (tagged `[Task Manager] <phase> - <title>` in `measurement_point`, no schema change to `CBMVibration`) and auto-advances the task status (`todo`→`doing` on the no-load reading, →`done` on the loaded reading). The detail page renders both phases as a 14-row comparison table (no-load vs loaded side by side) rather than as extra columns on the main list.

Three further test types were added as separate sub-modules with the same task shell (title/assignee/status/note), each with its own list + combined add/edit page (no separate detail page — editing happens on the same page as the child-row formset, following the Manual Library's inline-formset scaffold rather than the rotating test's own modal+detail-page split):

- **Water System Test (CIP)** at `/watercip/` — `WaterCIPTest` (start/end equipment FK, test date, start/end time) + `WaterCIPPhReading` (child, unlimited add/remove rows: reading time, pH value, optional point label).
- **Steam System Test (Leak Inspection)** at `/steamleak/` — `SteamLeakTest` (single equipment FK, inspection date) + `SteamLeakCheckItem` (child, unlimited add/remove rows: check topic, check item, standard, result normal/abnormal, and — shown only when abnormal — cause, corrective action, fix-due date).
- **Flushing Test** at `/flushing/` — `FlushingTest` (single equipment/pipe FK, test date, measured pipe surface temperature) + `FlushingRound` (child, unlimited add/remove rows: round number, start/end time, blow pressure in bar, whether a copper plate was inserted, and — only relevant when a plate was used — the count of spots larger than 0.3mm found). `FlushingRound.passed` is a model `@property` (not a view/template calculation) that returns `None` when there's no plate or no count yet, else `True`/`False` against the fixed `OVERSIZED_SPOT_LIMIT = 3`/cm² threshold — the same "pre-compute the flag, never compare numbers in the template" convention used by `ElectricityReading.usage_kwh`.

All 4 reuse the existing `api_equipment_by_process` cascade endpoint and the `_process_equipment_options()`/`_scoped_equipment_for()` helpers (factored out of `machine_task_list` for reuse) for the process→equipment dropdown, and none stores a `process` field on its own model (process is only a UI filter, matching `MachineTask`'s existing convention).

### Energy Tracking — Electricity (Phase 1)

Standalone module at `/electricity/`, first slice of a broader Energy module (steam usage is a planned Phase 2, sharing the same `write_energy` permission and the `PLANT_CHOICES` constant).

- `ElectricityMeter` — master data per physical meter: `meter_code`, `name`, `plant` (`ESC-A`/`ESC-B`, via module-level `PLANT_CHOICES`), `location` (free text), `equipment` (M2M to `Equipment`, used to auto-calculate a target), `assumed_operating_hours` (default 24/day), `target_kwh_override` (manual override). Property `target_kwh_auto` = `sum(power_kw of linked equipment) × assumed_operating_hours`; property `target_kwh_effective` returns the override if set, else the auto value — every view reads this one property rather than re-implementing the precedence check.
- `ElectricityReading` — one row per meter per day (`UniqueConstraint(meter, date)`), storing the **cumulative** meter reading (`reading_kwh`) as physically read off the dial. Property `usage_kwh` computes that day's consumption as the delta from the previous day's reading; returns `None` for the first-ever reading of a meter or when `is_meter_reset` is ticked (meter physically swapped/reset that day, so no delta is computed against the old meter's value). A negative delta without the reset flag ticked is kept (not hidden) and flagged via `is_anomalous` so a likely data-entry error surfaces in the UI instead of silently corrupting a chart. The module-level `electricity_usage_series(meters_qs, start, end)` function computes usage for many meters/days in one query pass (avoids N+1 queries in the dashboards).
- Two dashboards: `electricity_plant_dashboard` (select `ESC-A`/`ESC-B`, aggregates target vs. actual kWh across all meters in that plant) and `electricity_meter_dashboard/<id>/` (same, scoped to one meter/process). Both share a `_electricity_period_comparison()` helper for the 6-month summary table and month-over-month/year-over-year % comparison, and follow the `boiler` view's existing `days`/`start`/`end` GET-param convention for the trend chart's date range. Alert/comparison booleans (e.g. `over_target`) are pre-computed in the view (Django templates can't do `>` comparisons), not in the template.

### Access Control (Module-level Write Permissions)

Staff-level write access is scoped per module using Django's built-in Groups/Permissions, replacing the earlier all-or-nothing `is_staff` check:

- 11 synthetic permissions (`write_boiler`, `write_equipment`, `write_cbm`, `write_maintenance`, `write_mill`, `write_docs`, `write_inventory`, `write_tools`, `write_training`, `write_general`, `write_energy`) are declared on `Profile.Meta.permissions` and auto-created in `auth_permission` on `migrate`.
- A matching Group per module (e.g. "Boiler Staff", "CBM Staff", "Energy Staff") is seeded by data migrations (`0095_seed_module_groups.py`, plus `0097_seed_energy_group.py` for the Energy module added later), which also grandfather all pre-existing `is_staff` users into every Group so no one loses access on deploy. New staff accounts start in zero Groups and must be assigned via Django Admin → Groups.
- The `module_required('<key>')` decorator (`myapp/views.py`, replaces the old `staff_required`) gates each module's add/edit views: requires `is_staff` **and** the matching `write_<key>` permission, or `is_superuser` (which bypasses all module checks). The separate `superuser_required` decorator for destructive/admin-only actions is unchanged.
- Templates hide nav links and dashboard shortcut cards for modules a user can't write to via `{% if perms.myapp.write_<key> %}` (`base.html`, `dashboard.html`, and the CBM tab in `equipment_data.html`) — this affects visibility of the entry point, not read access to the underlying views, most of which remain open to any logged-in user.

---

## 9. Database Models

```
User / Personnel
├── Job
├── employee
└── Profile (extends Django User)

Boiler
├── BoilerOperationLog     (JT boiler)
├── YoshimineLog
├── Banpong1Log
├── Banpong2Log
├── ChengchenLog
├── TakumaLog
└── BoilerDailyKPI

Production
├── MillReport

Maintenance
├── MaintenanceLog
└── KPIMetric

Equipment
├── Equipment
├── EquipmentBOM           (spare parts)
├── EquipmentLink          (linked equipment, e.g. driving motor)
├── CBMVisualTest
├── CBMVibration
├── CBMThermoscan
├── CBMOilAnalysis
├── CBMAcoustic
├── PMPlan                 (preventive maintenance schedule)
│   └── PMPlanItem         (checklist tasks per PM cycle)
└── WorkOrder              (repair job history, linked to Equipment)

Shop
└── LatheJob

Inventory
├── InventoryItem          (stock item: tools/spares/consumables/lubricants; soft-delete via is_active; optional image)
├── InventoryTransaction   (receive/issue/return/adjust; auto-updates item.stock; optional tool_unit FK)
└── ToolReadinessCheck     (readiness checklist for tools before checkout; optional tool_unit FK)

Tools (แยกจาก Inventory ทั่วไป — /tools/)
├── ToolUnit               (per-unit tracking for identical tools; FK to InventoryItem category='tools')
└── ToolCheckout           (per-unit borrow/return history; borrower_name, due_date, return_date)

Training / Knowledge Center (คลังหลักสูตร)
├── TrainingSkill
├── EmployeeSkillLevel
├── TrainingCourse
│   └── TrainingCourseMaterial   (เอกสาร/วิดีโอ — เก็บที่ local disk ผ่าน `file`, media เสิร์ฟผ่าน nginx `/media/`)
├── TrainingRecord
├── TrainingExamScore
├── TrainingQuizQuestion / TrainingQuizChoice
└── TrainingCourseExamAttempt / TrainingCourseExamAnswer

Documents
└── RepairDocument         (เอกสารงานซ่อม — เชื่อมโยง Equipment/PO, ไฟล์เก็บบน Google Drive ผ่าน `drive_file_id`)

Manuals (คู่มือปฏิบัติงานเครื่องจักร — /manuals/, ไม่ผูก Equipment)
└── Manual
    ├── ManualSafetyItem
    ├── ManualPartItem
    ├── ManualPrecheckItem
    ├── ManualOperatingStep
    ├── ManualMaintenanceDailyItem
    ├── ManualMaintenancePeriodicItem
    ├── ManualTroubleshootItem
    └── ManualSpecItem

Task Manager (งานเตรียมความพร้อม/ทดลองเดินเครื่อง — /tasks/, ผูก Equipment)
└── MachineTask            (title, assignee, status: todo/doing/done, note)
    └── MachineTaskVibration   (phase: no_load/loaded; 14 measurement fields mirroring CBMVibration; unique per task+phase)

Task Manager — ทดสอบระบบน้ำ (CIP) (/watercip/, ผูก Equipment 2 จุด)
└── WaterCIPTest           (start_equipment FK, end_equipment FK, title, assignee, status, note, test_date, start_time, end_time)
    └── WaterCIPPhReading  (child, แถวเพิ่ม/ลบได้ไม่จำกัด: reading_time, ph_value, point_label)

Task Manager — ทดสอบระบบไอน้ำ ตรวจรอยรั่ว (/steamleak/, ผูก Equipment 1 ตัวต่อใบบันทึก)
└── SteamLeakTest          (equipment FK, title, assignee, status, note, inspection_date)
    └── SteamLeakCheckItem (child, แถวเพิ่ม/ลบได้ไม่จำกัด: check_topic, check_item, standard, result: normal/abnormal, cause, corrective_action, fix_due_date)

Task Manager — ทดสอบเป่าแป๊ป Flushing (/flushing/, ผูก Equipment/ท่อ 1 ตัวต่อใบบันทึก)
└── FlushingTest           (equipment FK, title, assignee, status, note, test_date, pipe_surface_temp_c)
    └── FlushingRound      (child, แถวเพิ่ม/ลบได้ไม่จำกัด: round_no, has_copper_plate, start_time, end_time,
                             blow_pressure_bar, oversized_spot_count; property `passed` เทียบกับ OVERSIZED_SPOT_LIMIT=3)

Energy Tracking — Electricity (Phase 1) (ระบบติดตามการใช้พลังงาน — /electricity/, plant: ESC-A/ESC-B ผ่าน PLANT_CHOICES)
└── ElectricityMeter       (meter_code, name, plant, location, equipment: M2M→Equipment, assumed_operating_hours, target_kwh_override)
    └── ElectricityReading (meter FK, date, reading_kwh: เลขมิเตอร์สะสม, is_meter_reset, note; unique per meter+date)

```

Google Drive uploads (`RepairDocument` only) ไม่ใช้ Google API SDK โดยตรง — ส่งไฟล์ผ่าน Google Apps Script Web App (`gas_webapp_script.js`, ตั้งค่า URL ที่ `GAS_WEBAPP_URL` ใน `.env`). ไฟล์ที่อัปโหลดสำเร็จจะถูกตั้งสิทธิ์เป็น "Anyone with the link — Viewer" อัตโนมัติ.

Database migrations: **100 migration files** in `myapp/migrations/`.

---

## 10. API Endpoints

### Authentication

| Method | URL | Description |
|---|---|---|
| GET/POST | `/` | Login page |
| POST | `/register/` | User registration |
| POST | `/logout/` | Logout |

### Dashboard

| Method | URL | Description |
|---|---|---|
| GET | `/dashboard/` | Main dashboard |
| GET | `/dashboard/api/` | Dashboard data (JSON) |

### Boiler Operations

| Method | URL | Description |
|---|---|---|
| GET | `/boiler/` | Boiler overview |
| GET | `/boiler/operation/` | Operation dashboard with history |
| POST | `/boiler/operation/add/` | Add JT boiler log |
| POST | `/boiler/yoshimine/add/` | Add Yoshimine log |
| POST | `/boiler/banpong1/add/` | Add Banpong 1 log |
| POST | `/boiler/banpong2/add/` | Add Banpong 2 log |
| POST | `/boiler/chengchen/add/` | Add Chengchen log |
| POST | `/boiler/takuma/add/` | Add Takuma log |
| GET | `/boiler/api/history/` | Boiler history (JSON) |
| POST | `/boiler/kpi/add/` | Add daily KPI record |

### Maintenance

| Method | URL | Description |
|---|---|---|
| GET | `/maintenance/` | Maintenance dashboard |
| POST | `/maintenance/add/` | Add maintenance log |
| POST | `/maintenance/edit/<log_id>/` | Edit maintenance log |
| POST | `/maintenance/kpi/add/` | Add KPI metric |
| POST | `/maintenance/import_csv/` | Bulk import via CSV |

### Mill Operations

| Method | URL | Description |
|---|---|---|
| GET | `/mill/` | Mill dashboard |
| GET | `/mill/report/` | Production report |
| POST | `/mill/import/` | Import mill data |
| GET | `/mill/api/history/` | Mill history (JSON) |

### Equipment & CBM

| Method | URL | Description |
|---|---|---|
| GET | `/equipment/list/` | Equipment inventory |
| GET | `/equipment/` | Equipment details |
| GET/POST | `/equipment/form/` | Add new equipment |
| GET/POST | `/equipment/form/<eq_id>/` | Edit equipment |
| GET | `/equipment/<eq_id>/` | Equipment details |
| POST | `/equipment/<eq_id>/toggle_status/` | Activate/deactivate |
| GET | `/equipment/cbm/<eq_id>/` | CBM dashboard |
| POST | `/equipment/upload_image/<eq_id>/` | Upload equipment image |
| GET/POST | `/equipment/bom/` | BOM management |
| POST | `/equipment/<eq_id>/bom/add/` | Add spare part |
| POST | `/equipment/bom/delete/<bom_id>/` | Delete spare part |
| POST | `/equipment/<eq_id>/pm/add/` | Add PM plan |
| POST | `/equipment/pm/edit/<plan_id>/` | Edit PM plan |
| POST | `/equipment/pm/delete/<plan_id>/` | Delete PM plan |
| POST | `/equipment/pm/<plan_id>/complete/` | Mark PM cycle complete (recalculates next due date) |
| POST | `/equipment/pm/<plan_id>/item/add/` | Add PM checklist item |
| POST | `/equipment/pm/item/delete/<item_id>/` | Delete PM checklist item |
| POST | `/equipment/<eq_id>/wo/add/` | Create work order (auto-generates `WO-YYMM-####`) |
| POST | `/equipment/wo/edit/<wo_id>/` | Update work order status/mechanic/progress |
| POST | `/equipment/wo/delete/<wo_id>/` | Delete work order |

### Lathe / Shop

| Method | URL | Description |
|---|---|---|
| GET | `/lathe/` | Lathe job dashboard |
| GET | `/api/lathe/` | Lathe job data (JSON) |

### Inventory

| Method | URL | Description |
|---|---|---|
| GET | `/inventory/` | Inventory dashboard (KPIs, low stock, recent tx, dept summary) |
| GET | `/inventory/list/` | Filterable item list (category/department/search) |
| GET | `/inventory/item/<pk>/` | Stock card — item detail + transaction history |
| GET | `/inventory/departments/` | Department summary cards |
| GET | `/inventory/department/<key>/` | Department drill-down |
| GET | `/inventory/transactions/` | Full transaction history (filterable) |
| GET | `/inventory/checkout/` | เบิก-คืน เครื่องมือ — item picker + checkout/return modal |
| GET | `/inventory/receive/` | รับสินค้าเข้า — item picker + receive-with-PO modal |
| GET | `/inventory/readiness/` | ตรวจสอบความพร้อมเครื่องมือ — readiness checklist history |
| GET/POST | `/inventory/readiness/add/` | Record a new tool readiness check |
| POST | `/api/inventory/checkout/` | JSON API: issue/return a transaction |
| POST | `/api/inventory/receive/` | JSON API: receive stock with PO |
| POST | `/api/inventory/add-item/` | JSON API: create new inventory item |
| POST | `/api/inventory/item/<pk>/delete/` | JSON API: soft-delete item (sets `is_active=False`) |
| POST | `/api/inventory/item/<pk>/upload-image/` | Multipart API: upload/replace item image |

### Tools (เครื่องมือ — แยกจาก Inventory ทั่วไป)

| Method | URL | Description |
|---|---|---|
| GET | `/tools/` | Tools dashboard (unit status KPIs, overdue checkouts, recent activity) |
| GET | `/tools/types/` | List of tool types with per-status unit counts |
| GET | `/tools/types/<pk>/` | Tool type detail — unit grid, checkout/return/status actions |
| GET | `/tools/unit/<pk>/` | Single unit detail — checkout history + readiness check history |
| GET | `/tools/overdue/` | Checkouts past `due_date` and not yet returned |
| GET/POST | `/tools/readiness/add/` | Record a readiness check against a specific tool unit |
| POST | `/api/tools/checkout/` | JSON API: check out a unit (soft-warns if last readiness check was "not ready") |
| POST | `/api/tools/return/` | JSON API: return a checked-out unit |
| POST | `/api/tools/type/add/` | JSON API: create a new tool type (`InventoryItem` category `tools`) |
| POST | `/api/tools/unit/add/` | JSON API: add a new physical unit to a tool type |
| POST | `/api/tools/unit/<pk>/edit/` | JSON API: change unit status/location/condition note |

### Manual Library

| Method | URL | Description |
|---|---|---|
| GET | `/manuals/` | Manual list |
| GET/POST | `/manuals/add/` | Create a new manual (tabbed form, 8 sections) |
| GET | `/manuals/<manual_id>/` | Manual preview / print view (Export PDF) |
| GET/POST | `/manuals/<manual_id>/edit/` | Edit an existing manual |
| POST | `/manuals/<manual_id>/delete/` | Delete a manual (cascades to all child sections) |

### Task Manager

| Method | URL | Description |
|---|---|---|
| GET | `/tasks/` | Hub page: 4 cards linking to the sub-modules below, each with a total/pending count |
| GET | `/tasks/rotating/` | Rotating/electrical/control task list (filter by `?equipment=` / `?status=`), add-task modal — this is the path that used to be bare `/tasks/` before the hub was added; the URL *name* `machine_task_list` didn't change |
| POST | `/tasks/add/` | Create a new task (status starts at `todo`) |
| POST | `/tasks/edit/<task_id>/` | Edit task title/assignee/status/note/equipment |
| POST | `/tasks/delete/<task_id>/` | Delete a task (cascades to its vibration readings) |
| GET | `/tasks/<task_id>/` | Task detail: equipment reference info, comparison table, phase entry forms |
| POST | `/tasks/<task_id>/vibration/<phase>/` | Save a `no_load`/`loaded` vibration reading; also writes a `CBMVibration` row and advances task status |

### Task Manager — Water System Test (CIP)

| Method | URL | Description |
|---|---|---|
| GET | `/watercip/` | Test list (filter by `?title=` / `?status=`) |
| GET/POST | `/watercip/add/` | Create a test: task shell + start/end equipment + pH readings formset |
| GET/POST | `/watercip/edit/<test_id>/` | Edit an existing test and its pH readings |
| POST | `/watercip/delete/<test_id>/` | Delete a test (cascades to its pH readings) |

### Task Manager — Steam System Test (Leak Inspection)

| Method | URL | Description |
|---|---|---|
| GET | `/steamleak/` | Test list (filter by `?title=` / `?status=`) |
| GET/POST | `/steamleak/add/` | Create a test: task shell + equipment + checklist formset |
| GET/POST | `/steamleak/edit/<test_id>/` | Edit an existing test and its checklist items |
| POST | `/steamleak/delete/<test_id>/` | Delete a test (cascades to its checklist items) |

### Task Manager — Flushing Test

| Method | URL | Description |
|---|---|---|
| GET | `/flushing/` | Test list (filter by `?title=` / `?status=`) |
| GET/POST | `/flushing/add/` | Create a test: task shell + equipment/pipe + blow-round formset |
| GET/POST | `/flushing/edit/<test_id>/` | Edit an existing test and its blow rounds |
| POST | `/flushing/delete/<test_id>/` | Delete a test (cascades to its blow rounds) |

### Energy Tracking — Electricity

| Method | URL | Description |
|---|---|---|
| GET | `/electricity/` | Plant-level dashboard (`?plant=ESC-A\|ESC-B`, `?days=`/`?start=`&`?end=`) |
| GET | `/electricity/meter/<meter_id>/` | Single meter/process dashboard |
| GET | `/electricity/meters/` | Meter list (`?plant=`) |
| GET/POST | `/electricity/meters/add/` | Add a meter |
| GET/POST | `/electricity/meters/<meter_id>/edit/` | Edit a meter |
| POST | `/electricity/meters/<meter_id>/toggle-active/` | Activate/deactivate a meter |
| GET/POST | `/electricity/reading/add/` | Add a daily reading (meter chosen in the form) |
| GET/POST | `/electricity/reading/add/<meter_id>/` | Add a daily reading for a specific meter |
| GET | `/electricity/readings/` | Reading history (`?meter=`) |

### Admin

| URL | Description |
|---|---|
| `/admin/` | Django Admin interface (superuser only) |

---

## 11. Deployment

### Docker Compose (Recommended)

The `docker-compose.yml` defines two services:

```yaml
services:
  web:    # Django app on port 8000
  nginx:  # Reverse proxy on ports 80 / 443
```

**Steps:**

1. Copy `.env.example` to `.env` and fill in production values (see [Environment Variables](#12-environment-variables)).
2. Place SSL certificates in the path referenced by `nginx/` config (Let's Encrypt recommended).
3. Build and start:
   ```bash
   docker-compose up --build -d
   ```
4. Run initial setup:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py collectstatic --noinput
   docker-compose exec web python manage.py createsuperuser
   ```

### Production Checklist

- [ ] Set `DEBUG = False` in `settings.py` or via `.env`
- [ ] Set `SECRET_KEY` to a strong random value via `.env`
- [ ] Restrict `ALLOWED_HOSTS` to actual domain(s)
- [ ] Run `collectstatic` for static file serving via Nginx
- [ ] Configure Nginx SSL certificate paths
- [ ] Verify media file volume is persisted (not ephemeral in Docker)
- [ ] Consider migrating from SQLite to PostgreSQL for production reliability

---

## 12. Environment Variables

Create a `.env` file in the project root (never commit this file):

```env
# Django core
SECRET_KEY=your-strong-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=lamy23.cloud,www.lamy23.cloud

# Database (if migrating to PostgreSQL)
DATABASE_URL=postgres://user:password@host:5432/dbname

# Google Drive integration (optional)
GOOGLE_DRIVE_CREDENTIALS_JSON=path/to/credentials.json
```

> The `.env` file is listed in `.gitignore` and will not be committed to version control.
