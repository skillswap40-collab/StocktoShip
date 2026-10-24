# StocktoShip

Warehouse, POS and invoicing system for a B2B grocery wholesaler.

| Part | Status |
| --- | --- |
| `backend/` | FastAPI + PostgreSQL API — skeleton in progress |
| Web app (back office + POS) | Not started |
| Mobile app | Phase 2 |

## Backend build progress

| Step | What | Status |
| --- | --- | --- |
| 1 | Scaffold, settings, `/health` with DB check | Done |
| 2 | SQLAlchemy base, Alembic migrations, isolated test DB | Done |
| 3 | Staff users, roles, login (JWT), create-admin command | Done |
| 4 | Customers: staff registration, tax ID masked for non-admins | Next |
| 5 | Products, barcodes, CSV import | — |
| 6 | Inventory ledger, receive and adjust | — |
| 7 | POS sale → invoice under customer | — |
| 8 | Payments, customer balance and history | — |
| 9 | CSV import of existing data | — |

## Run it locally (macOS)

Requirements: Python 3.12+, Docker Desktop (or a local PostgreSQL 16).

```bash
# 1. Start PostgreSQL (creates stocktoship and stocktoship_test databases)
docker compose up -d

# 2. Set up the backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env

# 3. Create the tables
alembic upgrade head

# 4. Create the first admin (asks for a password)
python -m app.cli create-admin --email you@example.com --name "Your Name"

# 5. Run the API
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API, or check http://localhost:8000/health.

> If you already have PostgreSQL running on port 5432, stop it or change the port in
> `docker-compose.yml` and both URLs in `.env`.

## Tests and lint

```bash
cd backend
source .venv/bin/activate
pytest            # uses the stocktoship_test database; wipes and re-migrates it each run
ruff check . && ruff format --check .
```

GitHub Actions runs the same checks on every push that touches `backend/`.

## Adding a database change

1. Edit or add a model under `app/modules/<module>/models.py` and import it in `app/db/models.py`.
2. `alembic revision --autogenerate -m "short description"` and read the generated file.
3. `alembic upgrade head`, then `pytest`. `test_models_match_migrations` fails if a model
   change has no migration.

## Backend layout

```
backend/
  app/
    main.py              FastAPI app and router registration
    cli.py               admin commands (create-admin)
    core/                settings, password hashing, JWT
    db/                  engine/session, declarative base, model registry
    api/deps.py          current user + role checks
    api/routes/          HTTP endpoints (health, auth, users)
    modules/<name>/      models, schemas, service logic per business area
  alembic/versions/      migrations
  tests/                 pytest suite (runs against real PostgreSQL)
```

## Roles

| Role | Can do now |
| --- | --- |
| admin | Everything, including managing staff accounts |
| manager | View staff list |
| sales_rep, cashier, warehouse | Sign in; feature access arrives with later steps |
