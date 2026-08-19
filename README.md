# TenderFlow — Tender Status Tracking Service

FastAPI microservice for managing tenders with CRUD operations, manual status changes, and an auditable status history.

## Test task #6
The service implements:
- tender creation;
- tender editing and deletion;
- tender status changes: `draft` / `active` / `won` / `lost`;
- status change audit: who, when and why;
- separate `tender_status_history` table;
- REST API + responsive web UI;
- SQLite by default for a zero-infrastructure local run;
- PostgreSQL supported through `DATABASE_URL`;
- Alembic migrations;
- automated tests.

## Architecture

```text
Browser / REST client
        |
        v
     FastAPI
        |
        v
 Service layer
        |
        v
 SQLAlchemy ORM
        |
   +----+----+
   |         |
 tenders  tender_status_history
   |         |
   +----+----+
        |
        v
   SQLite / PostgreSQL
```

Status changes and audit records are committed in a single database transaction.

Authentication is intentionally outside the test task. `changed_by` is supplied by the API client; a production system can replace it with the authenticated user identity.

## API

- `GET /api/v1/tenders`
- `POST /api/v1/tenders`
- `GET /api/v1/tenders/{id}`
- `PUT /api/v1/tenders/{id}`
- `DELETE /api/v1/tenders/{id}`
- `PATCH /api/v1/tenders/{id}/status`
- `GET /api/v1/tenders/{id}/history`

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

The UI supports create, edit, delete, search/filter, manual status changes, audit timeline, and refresh.

## PostgreSQL

Set for example:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/tender_status
```

Then run:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

## Docker

Docker configuration is included for users who want a PostgreSQL container, but Docker is not required for the default local SQLite run.

```powershell
docker compose up --build
```

## Tests

The test suite covers creation/default draft status, full CRUD, manual status changes, audit history with who/when/why, invalid same-status changes, 404 handling, and UI/static assets.

## License

MIT
