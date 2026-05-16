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
