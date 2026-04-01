# ExtremeXP DAL (Data Abstraction Layer)

REST API service in **Python 3.12+** with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2** (async), and **asyncpg**. It stores **experiments**, **workflows**, and **metrics** metadata and is shaped to work with the **ExtremeXP Experimentation Engine** (same route patterns and response shapes where compatibility is required).

---

## Table of contents

- [Features](#features)
- [Documentation](#documentation)
- [Requirements](#requirements)
- [Quick start (local)](#quick-start-local)
- [Configuration](#configuration)
- [Run with Docker Compose](#run-with-docker-compose)
- [API overview](#api-overview)
- [Authentication](#authentication)
- [Project layout](#project-layout)
- [Tests](#tests)
- [Documentation site (MkDocs)](#documentation-site-mkdocs)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Features

- Async SQLAlchemy models and CRUD-style routers for experiments, workflows, and metrics.
- **Engine compatibility:** e.g. `GET /api/executed-experiments` with `{ "executed_experiments": [...] }`.
- **Query endpoints:** `POST /api/experiments-query`, `/api/workflows-query`, `/api/metrics-query`.
- **Metrics data:** `PUT /api/metrics-data/{metric_id}` for appending records.
- **Health check:** `GET /api/health` — **no** `access-token` required.
- OpenAPI / Swagger at `/docs` when running the app.
- Pytest suite with coverage targets for routers.
- Optional **GitHub Pages** build for the MkDocs site (see [Documentation site](#documentation-site-mkdocs)).

---

## Documentation

- **Published (GitHub Pages):** [https://xampos101.github.io/DAL/](https://xampos101.github.io/DAL/)
- **In this repo:** operational guides under [`docs/dal/`](docs/dal/) (overview, installation, configuration, Docker, troubleshooting).

---

## Requirements

| Component | Notes |
|-----------|--------|
| Python | 3.12+ |
| PostgreSQL | 15+ recommended; UUID, JSONB, arrays as used by models |
| Docker (optional) | Docker Desktop + Compose for the bundled stack |

---

## Quick start (local)

### 1. Clone and virtual environment

```bash
git clone https://github.com/xampos101/DAL.git
cd DAL
python -m venv .venv
```

**PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements-test.txt
pip install "uvicorn[standard]"
```

### 3. Configure environment

Copy [`.env.example`](.env.example) to `.env` and set real values (see [Configuration](#configuration)).

### 4. Start PostgreSQL

Use your own instance or [Docker Compose](#run-with-docker-compose) for Postgres only / full stack.

### 5. Run the API

```bash
uvicorn dal_service.main:app --reload --host 0.0.0.0 --port 8000
```

| URL | Purpose |
|-----|---------|
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | OpenAPI JSON |

All business routes are under the **`/api`** prefix (see [API overview](#api-overview)).

---

## Configuration

Create `.env` in the repository root (never commit it). Variables used by Compose and/or the app:

| Variable | Description |
|----------|-------------|
| `POSTGRES_DB` | Database name (Compose `postgres` service) |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `DATABASE_URL` | Async URL for the app, e.g. `postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB` — under Compose, host is `postgres` |
| `ACCESS_TOKEN` | Shared secret; clients must send header **`access-token: <token>`** on protected routes |

See [`.env.example`](.env.example) for a template.

---

## Run with Docker Compose

From the repo root (after `.env` exists):

```bash
docker compose up -d --build
```

Useful commands:

```bash
docker compose ps
docker compose logs -f dal
```

**Health (no token):**

```bash
curl http://127.0.0.1:8000/api/health
```

**Stop**

```bash
docker compose down
```

**Reset database volume (destructive)**

```bash
docker compose down -v
```

The Compose file ([`docker-compose.yml`](docker-compose.yml)) runs **PostgreSQL 15** and the **DAL** service on port **8000**, with the app code bind-mounted for development.

---

## API overview

Base path: **`/api`**.

| Area | Examples |
|------|----------|
| Health | `GET /api/health` |
| Experiments | `PUT /api/experiments`, `GET /api/experiments`, `GET/POST /api/experiments/{id}`, `GET /api/experiments/{id}/metrics` |
| Engine legacy | `GET /api/executed-experiments` |
| Workflows | `PUT /api/workflows`, `GET/POST /api/workflows/{id}`, … |
| Metrics | `PUT /api/metrics`, `GET/POST /api/metrics/{id}`, `GET /api/metrics/{id}/records`, `PUT /api/metrics-data/{metric_id}` |
| Queries | `POST /api/experiments-query`, `POST /api/workflows-query`, `POST /api/metrics-query` |

Exact bodies and status codes are defined in OpenAPI (`/docs`).

---

## Authentication

Protected routes expect the header:

```http
access-token: <your ACCESS_TOKEN value>
```

`/api/health` is **unauthenticated** so load balancers and Compose health checks can use it without a token.

---

## Project layout

| Path | Purpose |
|------|---------|
| [`dal_service/main.py`](dal_service/main.py) | FastAPI app and router registration |
| [`dal_service/routers/`](dal_service/routers/) | HTTP routes (experiments, workflows, metrics, queries, health) |
| [`dal_service/models/`](dal_service/models/) | SQLAlchemy ORM models |
| [`dal_service/schemas/`](dal_service/schemas/) | Pydantic request/response models |
| [`dal_service/db/`](dal_service/db/) | Async engine and session |
| [`dal_service/deps.py`](dal_service/deps.py) | Auth dependency (`access-token`) |
| [`dal_service/core/`](dal_service/core/) | Settings / config |
| [`tests/`](tests/) | Pytest suite ([`tests/README.md`](tests/README.md)) |
| [`docs/`](docs/) | MkDocs source (User Guide, DSL, ExecutionWare, DAL section, …) |
| [`.github/workflows/docs-pages.yml`](.github/workflows/docs-pages.yml) | Build and deploy docs to GitHub Pages |

---

## Tests

Point `TEST_DATABASE_URL` at a **real PostgreSQL** database (create an empty DB first, e.g. `dal_test`).

**PowerShell**

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:YOUR_PASSWORD@127.0.0.1:5432/dal_test"
py -3.12 -m pytest tests/ -v --cov=dal_service.routers --cov-report=term-missing --cov-fail-under=80
```

Run from the repository root (where [`pytest.ini`](pytest.ini) lives). The test app may set `ACCESS_TOKEN` for the suite; see [`tests/conftest.py`](tests/conftest.py) and [`tests/README.md`](tests/README.md).

---

## Documentation site (MkDocs)

**Local preview**

```bash
pip install mkdocs mkdocs-material pymdown-extensions mkdocs-render-swagger-plugin
mkdocs serve
```

Then open the URL printed in the terminal (dev server uses the `site_url` path from [`mkdocs.yml`](mkdocs.yml)).

**Publish**

Pushes to `main` trigger [GitHub Actions](.github/workflows/docs-pages.yml) when **Pages → Build and deployment → Source** is set to **GitHub Actions** in the repository settings.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `401` on API calls | Header `access-token` present and equal to `ACCESS_TOKEN` in `.env` |
| DB connection errors | `DATABASE_URL` host/port/user/password; under Docker, DB host is `postgres` |
| Tests fail with wrong token | Shell `ACCESS_TOKEN` vs test fixture — see `tests/conftest.py` |
| Docs workflow fails on GitHub | Workflow logs; ensure `guide.md` exists with **lowercase** name (Linux is case-sensitive) |
| Empty or missing tables | Migrations / schema: align DB with models (Alembic or equivalent in your deployment) |

---

## Contributing

- Use feature branches and open PRs against `main`.
- Run tests and `mkdocs build` when changing code or docs.
- **Never** commit `.env`, real tokens, or database passwords.

Questions about contract alignment with the Experimentation Engine should be checked against the engine client and any project OpenAPI / DAL rules your team uses.
