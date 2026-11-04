# StocktoShip

Warehouse, POS and invoicing system for a B2B grocery wholesaler.

| Part | Status |
| --- | --- |
| `backend/` | FastAPI + PostgreSQL API — skeleton in progress |
| `frontend/` | React + Vite web app (back office + POS) — skeleton |
| Mobile app | Phase 2 |

## Web app (`frontend/`)

React 18 + TypeScript + Vite. The screen layout follows the client's current QuickBooks POS
(top menu, left action rail, dense grids) so staff recognise it, restyled.

| Screen | Route | Data |
| --- | --- | --- |
| Sign in | — | Live (`/auth/login`) |
| Navigator (home) | `/` | Workflow map; unbuilt tiles show the step that delivers them |
| Make a Sale | `/sale` | Live customer picker; items, tax and saving are sample data until steps 5 and 7 |
| Customers | `/customers` | Live: search, register, edit, admin-only tax ID reveal |
| Sales History / Held Receipts | `/sales`, `/held` | Sample data until step 7 |
| End of Day | dialog from Navigator | Placeholder until step 8 |
| Employees | `/staff` | Live (`/users`), admin and manager only |
| Reward Manager | `/rewards` | Read-only placeholder: not in the build plan |

```bash
# with the API running on :8000
cd frontend
npm install
npm run dev        # http://localhost:5173 (matches the API's default CORS_ORIGINS)
npm run build      # typecheck + production build
```

Set `VITE_API_URL` in `frontend/.env.local` if the API is not on `http://localhost:8000`.
The UI hides actions a role can't use, but the API is what enforces permissions.

## Backend build progress

| Step | What | Status |
| --- | --- | --- |
| 1 | Scaffold, settings, `/health` with DB check | Done |
| 2 | SQLAlchemy base, Alembic migrations, isolated test DB | Done |
| 3 | Staff users, roles, login (JWT), create-admin command | Done |
| 4 | Customers: staff registration, tax ID encrypted and masked for non-admins | Done |
| 5 | Products, barcodes, CSV import | Next |
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
    core/                settings, password hashing, JWT, field encryption (crypto.py)
    db/                  engine/session, declarative base, model registry
    api/deps.py          current user + role checks
    api/routes/          HTTP endpoints (health, auth, users, customers)
    modules/<name>/      models, schemas, service logic per business area
  alembic/versions/      migrations
  tests/                 pytest suite (runs against real PostgreSQL)
```

## Permissions

| Action | admin | manager | sales_rep | cashier | warehouse |
| --- | :-: | :-: | :-: | :-: | :-: |
| Manage staff accounts | ✓ | | | | |
| View staff list | ✓ | ✓ | | | |
| Register customers | ✓ | ✓ | ✓ | ✓ | |
| Search and view customers (tax ID masked) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Edit customers (incl. status) | ✓ | ✓ | | | |
| Change a customer's tax ID | ✓ | | | | |
| Reveal a full tax ID (audit-logged) | ✓ | | | | |

## Customer endpoints

| Method | Path | Who | Notes |
| --- | --- | --- | --- |
| POST | `/customers` | admin, manager, sales_rep, cashier | 409 if the tax ID is already registered (names the existing account) |
| GET | `/customers?q=&status=&limit=50&offset=0` | all staff | Searches name, owner, account number, phone |
| GET | `/customers/{id}` | all staff | Tax ID shown as `•••••6789` |
| GET | `/customers/{id}/tax-id` | admin | Full EIN; every call is audit-logged |
| PATCH | `/customers/{id}` | admin, manager | Only admins may include `tax_id` |

Account numbers (`C-000001`, …) are generated by the database. Customers are registered by
staff on site; there is no self-registration.

## How tax IDs are protected

- Stored **encrypted** (Fernet, key `DATA_ENCRYPTION_KEY`), never in plain text.
- A keyed **HMAC fingerprint** (`DATA_HASH_KEY`) with a unique constraint catches duplicates in
  any format (`12-3456789` = `123456789`) without decrypting.
- API responses only ever carry the last four digits. Admins get the full value from a separate
  endpoint, so each disclosure is deliberate and written to `audit_log`.
- Audit entries record field names, never tax ID values.
- Production refuses to start with the development keys. Generate real keys as described in
  `backend/.env.example`, **back them up**, and never change `DATA_HASH_KEY` once real data exists.
  `DATA_ENCRYPTION_KEY` accepts a comma-separated list for key rotation (first key encrypts).
