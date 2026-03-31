# DAL service tests

English technical notes for the pytest suite. For project setup and Greek documentation index see the root [README.md](../README.md) and [docs/README_EL.md](../docs/README_EL.md).

## Requirements

Tests require **PostgreSQL** (same dialect as production: JSONB, ARRAY, UUID).

Set a dedicated database URL before running pytest:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/dal_test"
```

Windows PowerShell:

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/dal_test"
```

If unset, the default in `tests/conftest.py` is `postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/dal_test`. Create that database and user, or override with a real URL.

The suite creates tables with SQLAlchemy `create_all` on first run and **truncates** all DAL tables before each test. Prefer a database used only for tests.

## Working directory

Run pytest from the **repository root** (parent of `dal_service/` and `tests/`), the directory that contains `pytest.ini`. Otherwise pytest may not load `asyncio_default_test_loop_scope = session` and asyncpg can fail with a wrong event loop.

Do not use a literal `...` placeholder in `cd` paths; use the full path to the project folder.

## Run

```bash
pip install -r requirements-test.txt
pytest tests/ -v --cov=dal_service.routers --cov-report=term-missing --cov-fail-under=80
```

Coverage reads [`.coveragerc`](../.coveragerc) (`concurrency = greenlet`) so SQLAlchemy async code is measured correctly.

`ACCESS_TOKEN` is forced to `test-token` by `conftest.py` for the test process.
