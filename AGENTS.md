# AGENTS.md

For full development guide, architecture patterns, naming conventions, and rules → see **CLAUDE.md**

## Quick Reference

**Tech Stack:** Python / Django 4.2+ · Bootstrap · SQLite3 · Docker + Nginx

### Essential Commands

```bash
# Backend
python manage.py runserver
python manage.py makemigrations && python manage.py migrate
python manage.py test myapp

# Docker
docker-compose up --build -d
docker-compose exec web python manage.py migrate
```

### Key Rules

- Single Django app (`myapp/`) — do not create additional apps
- Function-based views only — no class-based views
- No JavaScript framework — vanilla JS + Bootstrap only
- Never edit migration files manually
- Never change models without running `makemigrations`
- When unsure → ask or propose a plan before making changes
