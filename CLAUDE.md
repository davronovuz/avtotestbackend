# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**Avtotest** — a Django REST Framework backend for a mobile app that helps Uzbekistan users prepare for the driving license exam. Users register with a phone number, take randomized or section-based tests, track mistakes, and monitor progress.

## Running locally (Docker)

All services run through Docker Compose. The stack is: **Nginx (8080) → Gunicorn (8000) → PostgreSQL**.

```bash
# Copy and edit env vars before first run
cp .env.example .env

# Build and start everything (runs migrations + collectstatic automatically via entrypoint.sh)
docker compose up --build

# Stop
docker compose down
```

The API is available at `http://localhost:8080/api/v1/`.
Swagger UI: `http://localhost:8080/swagger/`
ReDoc: `http://localhost:8080/redoc/`

## Common management commands (inside the container)

```bash
docker compose exec web python manage.py makemigrations users
docker compose exec web python manage.py makemigrations tests
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
```

Django admin: `http://localhost:8080/admin/`

## Environment variables

All config is read by `python-decouple` from `.env`. Required keys (see `.env.example`):

| Key | Purpose |
|-----|---------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `DB_NAME/USER/PASSWORD/HOST/PORT` | PostgreSQL connection |

`DB_HOST` defaults to `db` (the Docker service name). When running outside Docker, point it to `localhost` and ensure the port is exposed.

## Architecture

### Apps

All Django apps live under `apps/`:

- **`apps.users`** — custom `User` model (phone as `USERNAME_FIELD`), register/login/profile views, `PhoneBackend` auth backend.
- **`apps.tests`** — all exam logic: sections, questions, answers, test sessions, answer submission, mistake tracking, and section progress.

### URL layout

```
/admin/
/swagger/   /redoc/   /swagger.json
/api/v1/
    (root)                         → api_root listing
    users/register/                → RegisterView
    users/login/                   → LoginView
    users/token/refresh/           → SimpleJWT TokenRefreshView
    users/profile/                 → ProfileView
    tests/home/                    → HomeDashboardView
    tests/sections/                → SectionListView
    tests/sections/<id>/questions/ → SectionQuestionsView
    tests/start/                   → StartTestView
    tests/sessions/<id>/answer/    → SubmitAnswerView
    tests/sessions/<id>/finish/    → FinishTestView
    tests/history/                 → TestHistoryView
    tests/mistakes/                → MistakeListView
```

### Authentication

- Phone number (`+998XXXXXXXXX` format) is the login identifier.
- `PhoneBackend` (`apps/users/backends.py`) handles `authenticate(phone=..., password=...)`.
- JWT via `djangorestframework-simplejwt`: access token valid 7 days, refresh 30 days, refresh rotation enabled.
- All API endpoints require `IsAuthenticated` by default; register/login are `AllowAny`.

### Test flow (key business logic)

1. **Start** (`POST /tests/start/`) — client chooses `mode` (`random` / `section` / `mistakes`) and optional `section_id` + `limit`. Server shuffles matching questions and creates a `TestSession` with `question_ids` (JSON list preserving order).
2. **Answer** (`POST /tests/sessions/<id>/answer/`) — client sends `question_id`, `answer_id`, `skipped`. Server:
   - Records `UserAnswer`
   - Updates `UserSectionProgress` (mastered question IDs stored as JSON)
   - Creates/updates `MistakeLog` (wrong/skipped → `resolved=False`; correct → `resolved=True`)
3. **Finish** (`POST /tests/sessions/<id>/finish/`) — calls `session.finish()` which aggregates counts and `score_percent`, sets `status=finished`.

### Key model relationships

```
User
 ├── TestSession (many) — has question_ids JSON + UserAnswer children
 ├── UserSectionProgress (one per section) — mastered_question_ids JSON
 └── MistakeLog (one per question) — resolved flag
Section → Question → Answer (FK chain)
TestSession → UserAnswer → Question + Answer
```

### Settings structure

`config/settings.py` splits `INSTALLED_APPS` into `DJANGO_APPS`, `THIRD_PARTY_APPS`, and `LOCAL_APPS`. Key non-obvious settings:

- `AUTH_USER_MODEL = 'users.User'`
- `CORS_ALLOW_ALL_ORIGINS = True` (IP-based mobile client)
- Language `uz`, timezone `Asia/Tashkent`
- Pagination default: 20 items per page

### Migrations

`entrypoint.sh` runs `makemigrations` for each app explicitly (`users`, `tests`) then `migrate`. When adding models, always run `makemigrations <app>` per app — not `makemigrations` without arguments.
