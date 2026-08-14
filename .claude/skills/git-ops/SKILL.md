---
name: git-ops
description: Manage git for the LAMY project — add/commit/push/pull/merge, undo or revert mistakes (staged, committed, or already-pushed), and deploy to the production VPS. Use whenever the user wants to commit changes, push/pull, fix a bad commit or merge, roll back a broken deploy, or ship the current branch to lamy23.cloud.
argument-hint: "[commit | push | pull | undo | deploy | rollback]"
license: MIT
metadata:
  author: lamy-project
  version: "1.0.0"
---

# git-ops — LAMY git & VPS deploy skill

Local git for `D:\lamy\lamy-project` (GitHub remote `origin` → `beerwwza/lamy-project.git`, branch `main`, no feature branches — commits land on `main` directly), plus generating deploy/rollback commands for the production VPS (Hostinger, `root@lamy23.cloud`, project at `/app/lamy-project`, Docker Compose services `web` + `nginx`).

**Always state which scope (범위) an action applies to before doing it: local-only, or "this will also touch the VPS/production."**

## 0. Scope check (always ask, every session)

Before doing anything, confirm with the user what they actually want this run:
- Local git only (commit/push/pull/undo), or
- Local git **and** a VPS deploy, or
- A VPS-only action (rollback, redeploy, check status)

Don't assume a `commit` request also means "and deploy it" — ask.

## 1. Local git — autonomy tiers

Run these **without asking** (reversible, low blast radius):
`git status`, `git diff`, `git log`, `git add <files>`, `git commit`, `git fetch`, `git pull` (fast-forward or clean merge only), `git merge` (only if it resolves with no conflicts), `git branch` (list/create, never delete).

**Always ask for explicit confirmation before running**, and say exactly what will happen first:
`git push` / `git push --force` / `git push --force-with-lease`, `git reset --hard`, `git branch -D`, `git checkout -- <file>` or `git restore` (discards uncommitted changes), `git clean -fd`, anything that rewrites history already pushed to `origin`.

This mirrors the project's standing rule: pushing code and destructive/hard-to-reverse operations always need a yes from the user, in this session, for this specific action.

### Commit messages

Format (always, no exceptions): `<description>_<DDMMYY>`

- `<description>` — short English/Thai phrase for what changed, ask the user or infer from the diff and confirm with them before committing. No spaces (use `_` between words, matching existing history like `edit_toolandinventory`).
- `<DDMMYY>` — today's date, **plain Gregorian (AD) calendar**, no Buddhist-year conversion. 2-digit day, 2-digit month, 2-digit AD year, always as a suffix. Compute it from the current date at commit time — never ask the user for it. Example: 14 Aug 2026 → `140826`.
- Full example: a fix to the inventory edit view committed on 14 Aug 2026 → `edit_inventory_fix_140826`.

This standardizes the repo's previous inconsistent style (dates sometimes prefixed, sometimes suffixed, sometimes YYMMDD order, sometimes missing entirely for infra commits) into one fixed suffix format going forward. Don't apply it retroactively to old commits.

Never use `git commit -am` blindly — check `git status`/`git diff` first so nothing unintended gets staged.

### Merge conflicts
**Never resolve a conflict by guessing intent.** When `git merge`/`git pull` reports a conflict:
1. Stop immediately, don't attempt an automatic resolution.
2. List the conflicted files (`git status`) and show the conflicting hunks.
3. Ask the user which side to keep for each conflict, or how to combine them.
4. Only after the user decides: apply their choice, `git add` the resolved files, and let them confirm before `git commit`.

## 2. README.md sync check (before every commit)

Per `CLAUDE.md`'s checklist: before running `git commit`, check `git diff --staged` (or `git status`) for changes to `myapp/models.py`, `myapp/urls.py`, or `requirements.txt`. If any of those changed and `README.md` was **not** also staged/modified in this change, warn the user:

> "แก้ `<file>` แล้ว แต่ยังไม่เห็นแก้ README.md — ต้องการให้ผมอัปเดต README ส่วนที่เกี่ยวข้องก่อน commit ไหม?"

Don't block the commit — just flag it and let the user decide (update now, later, or skip).

## 3. Undo / revert playbook

Before any **destructive** step below (marked ⚠️), create a safety backup branch first: `git branch backup/<short-desc>-<date>` pointing at the current HEAD, and tell the user it's there and how to get back to it.

| Situation | Command(s) | Confirm first? |
|---|---|---|
| Unstage a file | `git restore --staged <file>` | No |
| Discard uncommitted changes to a file | ⚠️ `git restore <file>` | Yes |
| Undo last commit, keep changes staged | `git reset --soft HEAD~1` | No |
| Undo last commit, keep changes unstaged | `git reset HEAD~1` | No |
| Undo last commit, discard the changes entirely | ⚠️ `git reset --hard HEAD~1` | Yes (backup branch first) |
| Undo a commit that's already been pushed | `git revert <commit>` then confirm before `git push` | Yes on the push |
| Recover a bad merge before it's committed | `git merge --abort` | No |
| Recover a bad merge already committed/pushed | `git revert -m 1 <merge-commit>` then confirm before push | Yes on the push |
| Go back to how a branch looked at a specific point | ⚠️ `git reset --hard <commit>` | Yes (backup branch first) |
| Find a commit that "disappeared" | `git reflog` | No |

Always explain in plain terms what will happen to the user's files before running anything marked ⚠️.

## 4. VPS deploy — command generation only

**Never run `ssh` or any remote-executing command against the VPS via Bash.** This machine has no SSH config to the VPS, and it's a production system real mill operators depend on. Instead, always **output the exact shell commands in a fenced bash block** for the user to copy and run themselves in their own VPS terminal session. Say so explicitly: "รันคำสั่งนี้บน VPS เอง (SSH เข้าไปก่อน)".

### 4.1 Pre-flight (run locally, before generating deploy commands)

1. Confirm the local branch is pushed and clean: `git status`, `git log origin/main..HEAD` should be empty.
2. Check for missing migrations: `python manage.py makemigrations --check --dry-run`. If it reports missing migrations, stop and tell the user — do not generate deploy commands until migrations are created and committed.

### 4.2 Standard deploy sequence (generate as one block)

```bash
ssh root@lamy23.cloud
cd /app/lamy-project
bash scripts/backup_db.sh
git pull origin main
docker-compose up --build -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

Backup always comes first, every time — no exceptions, even for "small" changes. If the user says they already backed up recently, still include the step; it's cheap and the rule is unconditional per project decision.

### 4.3 Emergency rollback (bad deploy already live)

1. Locally: identify the last good commit (`git log`), then `git revert <bad-commit>` (or a range) and confirm with the user before pushing.
2. Push the revert: confirm, then `git push origin main`.
3. Generate the redeploy block (same shape as 4.2) so the user re-pulls and rebuilds with the reverted code:

```bash
ssh root@lamy23.cloud
cd /app/lamy-project
bash scripts/backup_db.sh
git pull origin main
docker-compose up --build -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

If the DB also needs restoring to a pre-incident backup (not just code), point the user at `scripts/restore_db.sh <backup-filename>` — that script already prompts for confirmation and backs up the current DB before overwriting, run it interactively on the VPS, don't try to script the y/N prompt away.

### 4.4 Read-only checks (safe to hand over, no confirmation needed)

```bash
ssh root@lamy23.cloud "cd /app/lamy-project && docker-compose ps"
ssh root@lamy23.cloud "cd /app/lamy-project && docker-compose logs --tail=100 web"
```

These are still commands for the *user* to run — this skill generates them, it does not execute them.

## 5. Hostinger MCP (future, not currently available)

The VPS is hosted on Hostinger, and a `hostinger-mcp` connector exists in this environment but is **not authenticated**. Once the user authorizes it (via their Claude connector settings), read-only VPS operations — checking container status, pulling logs, restarting a service — could go through `mcp__hostinger-mcp__VPS_*` tools directly instead of generated SSH commands. Until then, stick to section 4's copy-paste model. Do not attempt to call the Hostinger MCP tools while they're unauthenticated.
