# ExtremeXP DAL (Data Abstraction Layer)

REST service in **Python 3.12+** using **FastAPI** and **PostgreSQL** (async with **SQLAlchemy 2** + **asyncpg**).
It stores experiment, workflow, and metric metadata with compatibility for the
ExtremeXP Experimentation Engine (`access-token` header and legacy routes such as
`/executed-experiments` and `*-query`).

For full NEW-DAL technical documentation, see `docs/NEW_DAL_DOCUMENTATION.md`.
For architecture diagrams and presentation material, see files under `docs/`.

---

## Requirements

- Python 3.12+
- PostgreSQL (UUID, JSONB, ARRAY support)
- Docker Desktop + Docker Compose (recommended for local setup)

---

## Quick Start

### 1) Clone and create a virtual environment

```bash
git clone <repository-url>
cd <repository-folder>
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements-test.txt
pip install "uvicorn[standard]"
```

### 3) Configure environment

Copy `.env.example` to `.env` and set real values:

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:password@host:5432/dbname` |
| `ACCESS_TOKEN` | Shared token expected in `access-token` header |

### 4) Run the API

```bash
uvicorn dal_service.main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

All DAL routers are mounted under `/api`.

---

## Docker Compose (NEW DAL + PostgreSQL)

1. Copy `.env.example` to `.env` and fill in real values.
2. Start:

```bash
docker compose up -d --build
```

3. Inspect:

```bash
docker compose ps
docker compose logs -f dal
```

4. Health check:

```bash
curl -H "access-token: <DAL_ACCESS_TOKEN>" http://127.0.0.1:8000/api/health
```

5. Stop:

```bash
docker compose down
```

6. Reset database volume (destructive):

```bash
docker compose down -v
```

---

## Repository Structure

| Path | Purpose |
|---|---|
| `dal_service/main.py` | FastAPI app entry point |
| `dal_service/routers/` | HTTP endpoints (experiments, workflows, metrics, queries, health) |
| `dal_service/models/` | SQLAlchemy models |
| `dal_service/schemas/` | Pydantic request/response models |
| `dal_service/db/` | Async engine/session handling |
| `dal_service/deps.py` | Auth dependency |
| `dal_service/utils/` | Utility helpers |
| `tests/` | Pytest suite |
| `docs/` | Architecture and supporting documentation |

---

## Testing

Set `TEST_DATABASE_URL` before running tests:

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:YOUR_PASSWORD@127.0.0.1:5432/dal_test"
py -3.12 -m pytest tests/ -v --cov=dal_service.routers --cov-report=term-missing --cov-fail-under=80
```

Run tests from the repository root (where `pytest.ini` lives).
More details: `tests/README.md`.

---

## Contributing

- Use feature branches for changes.
- Run tests before pushing.
- Never commit secrets (`.env`, tokens, DB credentials).
