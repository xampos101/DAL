# DAL service tests

## Database

Tests require **PostgreSQL** (same dialect as production: JSONB, ARRAY, UUID).

Set a dedicated database URL before running pytest:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/dal_test"
```

If unset, the default is `postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/dal_test`.

The suite creates tables with SQLAlchemy `create_all` on first run and **truncates** all DAL tables before each test.

## Run

From this directory (parent of `dal_service/` and `tests/`):

```bash
pip install -r requirements-test.txt
pytest tests/ -v --cov=dal_service.routers --cov-report=term-missing --cov-fail-under=80
```

`ACCESS_TOKEN` is forced to `test-token` by `conftest.py` for the test process.
