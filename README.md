# TenderFlow — Tender Status Tracking Service

FastAPI microservice for creating tenders, editing and deleting them, changing tender status, and keeping a separate audit history of status changes.

## Scope
This repository contains the complete implementation of test task #6 only.

## Stack
- Python 3.12+
- FastAPI
- SQLAlchemy 2
- SQLite by default for zero-infrastructure local runs
- PostgreSQL supported via `DATABASE_URL`
- Alembic migrations
- pytest
- Responsive web UI + Swagger/OpenAPI

## Statuses
- `draft` — Черновик
- `active` — Активен
- `won` — Выигран
- `lost` — Проигран

## Core API
- `GET /api/v1/tenders` — list tenders, optional status filter
- `POST /api/v1/tenders` — create tender
- `GET /api/v1/tenders/{id}` — get tender details + history
- `PUT /api/v1/tenders/{id}` — edit tender fields
- `DELETE /api/v1/tenders/{id}` — delete tender
- `PATCH /api/v1/tenders/{id}/status` — change status and write audit record
- `GET /api/v1/tenders/{id}/history` — status history

## Audit history
Every status change stores:
- previous status;
- new status;
- who changed it;
- when it was changed;
- why it was changed.

The status update and history record are committed atomically.

## Local Windows run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
pytest -q
python -m uvicorn app.main:app --reload
```

Open:
- http://127.0.0.1:8000 — web UI
- http://127.0.0.1:8000/docs — Swagger

SQLite database: `data/tender_status.db`

## PostgreSQL
Set, for example:
```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/tender_status
```
Then run `alembic upgrade head` and start the app.

## Tests
The repository includes API/service tests covering creation, CRUD, status transitions, audit history, invalid transitions and terminal states.
