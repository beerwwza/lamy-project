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
- **Manual Library** (`/manuals/`) — Structured machine operation & maintenance manuals (cover info, safety precautions, part names, pre-use checklist, operating steps, daily/periodic maintenance, troubleshooting, specifications), built via a multi-section form with dynamic add/remove rows. **Safety Manuals** (`/safety-manuals/add/`) are a separate, standalone JSA & SSOP (Job Safety Analysis / Standard Safe Operating Procedure) document type, not tied to a specific machine manual.

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
│   ├── migrations/                 # 74 database migration files
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
- **Role-based Access Control (RBAC)** — Authentication is present but fine-grained permission roles per module are not implemented.
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

### Manual & Safety Manual Library

Standalone module at `/manuals/`, not linked to `Equipment` (machine name is free text) or to `RepairDocument`/`doc_repository` (which is a separate uploaded-file library). Categorized by department (`DEPARTMENT_CHOICES`).

- `Manual` — cover info (machine name, model, department, prepared by, doc no., revision, date) with 8 repeating child sections, each its own model + inline formset: `ManualSafetyItem`, `ManualPartItem`, `ManualPrecheckItem`, `ManualOperatingStep`, `ManualMaintenanceDailyItem`, `ManualMaintenancePeriodicItem`, `ManualTroubleshootItem`, `ManualSpecItem` (all `on_delete=CASCADE` from `Manual`). Editor page (`manual_form.html`) uses a tabbed single-page form with vanilla-JS dynamic add/remove rows (formset `cloneNode` + prefix renumbering — no React). Preview/print page (`manual_detail.html`) supports Export to PDF via `window.print()`.
- `SafetyManual` — **independent** JSA & SSOP document, not tied to a specific `Manual`. Cover is `job_name` + `prepared_by`. JSA and SSOP are kept as two clearly separate sections/tables (not merged per-row), shown JSA first: `SafetyManualJsaItem` (phase, step title, hazard, prevention — the hazard analysis) and `SafetyManualSsopStep` (phase, step title, action, tools — the standard operating procedure), each its own model + inline formset under `SafetyManual`. Create-only for now (`safety_manual_add`) — no dedicated list/edit page yet.

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

Safety Manuals (คู่มือความปลอดภัย — /safety-manuals/add/, เอกสารอิสระ ไม่ผูกกับ Manual, แยก JSA/SSOP ชัดเจน)
└── SafetyManual              (job_name, prepared_by)
    ├── SafetyManualJsaItem   (JSA — การวิเคราะห์งานเพื่อความปลอดภัย)
    └── SafetyManualSsopStep  (SSOP — วิธีปฏิบัติงานมาตรฐาน)
```

Google Drive uploads (`RepairDocument` only) ไม่ใช้ Google API SDK โดยตรง — ส่งไฟล์ผ่าน Google Apps Script Web App (`gas_webapp_script.js`, ตั้งค่า URL ที่ `GAS_WEBAPP_URL` ใน `.env`). ไฟล์ที่อัปโหลดสำเร็จจะถูกตั้งสิทธิ์เป็น "Anyone with the link — Viewer" อัตโนมัติ.

Database migrations: **74 migration files** in `myapp/migrations/`.

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

### Manual & Safety Manual Library

| Method | URL | Description |
|---|---|---|
| GET | `/manuals/` | Manual list (search, filter by department) |
| GET/POST | `/manuals/add/` | Create a new manual (tabbed form, 8 sections) |
| GET | `/manuals/<manual_id>/` | Manual preview / print view (Export PDF) |
| GET/POST | `/manuals/<manual_id>/edit/` | Edit an existing manual |
| POST | `/manuals/<manual_id>/delete/` | Delete a manual (cascades to all child sections) |
| GET/POST | `/safety-manuals/add/` | Create a new safety manual (JSA & SSOP, independent document) |

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
