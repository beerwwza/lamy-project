---
name: implement
description: "Implement an approved LAMY Django spec or set of tickets."
disable-model-invocation: true
---

Implement only the approved work described by the spec or tickets. If the
requirements are unclear, stop and route back to `/grill-with-docs`, `/to-spec`,
or `/to-tickets` instead of inventing scope.

# LAMY implementation workflow

Before editing:

- Read `AGENTS.md` and the relevant sections of `CLAUDE.md`.
- Identify the owning Django model, form, function-based view, URL, template,
	admin registration, and nearby tests.
- Preserve the single `myapp/` architecture, Django templates, Tailwind,
	vanilla JavaScript, and Lucide icons. Do not introduce React, Vue, REST
	framework, or another Django app.
- If the work changes a model, plan a generated migration and a README update.

During implementation:

- Prefer the smallest vertical slice that delivers a user-visible behavior.
- Add or update focused Django tests at the highest useful behavior seam.
- After model changes, run `python manage.py makemigrations` and inspect the
	generated migration; never edit migrations by hand.
- Run focused tests and `python manage.py check` as soon as the touched slice
	is runnable.
- Keep POST handlers validated and redirect after success; keep protected views
	behind `@login_required`.

Before handing work to review, run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test myapp
```

If model, URL, or dependency behavior changed, verify that `README.md` was
updated as required by `CLAUDE.md`. Report any unavailable command or unrelated
pre-existing failure separately.

Run focused tests regularly and the full Django test suite once at the end.

Once implementation and checks are complete, hand the changes to `/code-review`.
Do not commit, push, deploy, or modify git history from this skill. Those actions
belong to the explicitly requested git workflow and require the user's intent.
