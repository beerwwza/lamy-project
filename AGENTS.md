# AGENTS.md

For full development guide, architecture patterns, naming conventions, and rules → see **CLAUDE.md**

## Quick Reference

**Tech Stack:** Python / Django 5.2 · Tailwind CSS · vanilla JavaScript · SQLite3 · Docker + Nginx

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
- No JavaScript framework — vanilla JS + Tailwind CSS only
- Never edit migration files manually
- Never change models without running `makemigrations`
- When unsure → ask or propose a plan before making changes

### Skill Workflow

Use these five skills as the project workflow:

```text
grill-with-docs (when ambiguous)
				↓
to-spec → to-tickets → implement → code-review
```

- `to-spec` and `to-tickets` publish only after user approval.
- `implement` does not commit, push, deploy, or rewrite git history.
- Every implementation that can run Django checks `python manage.py check`,
	`python manage.py makemigrations --check --dry-run`, and `python manage.py test myapp`.
- Git and deployment actions require explicit user intent and are outside this
	five-skill implementation chain.
