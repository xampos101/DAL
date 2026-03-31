# DAL Installation (NEW DAL + PostgreSQL)

This guide covers installation for the NEW DAL stack only.

## Prerequisites

Install the following:

- Python 3.11+ (for ExpEngine runtime)
- Docker and Docker Compose plugin
- Git
- Java runtime (required when using ProActive execution backend)

Quick verification:

```bash
python --version
docker --version
docker compose version
```

You also need:

- a NEW DAL API base URL (local or remote)
- a NEW DAL access token

Use placeholders in docs/scripts:

- `<NEW_DAL_URL>`
- `<DAL_ACCESS_TOKEN>`

## Install ExpEngine dependencies

From project root:

```bash
py -3 -m pip install -e exp_engine
py -3 -m pip install mkdocs mkdocs-material mkdocs-render-swagger-plugin pymdown-extensions
```

## Install NEW DAL stack locally

Use the single-compose workflow from [Docker Deployment](docker-deployment.md).

If your DAL image requires migrations, run them before smoke testing:

```bash
docker compose exec new_dal alembic upgrade head
```

After startup, verify DAL is reachable:

```bash
curl -H "access-token: <DAL_ACCESS_TOKEN>" http://127.0.0.1:8000/api/experiments
```

If your deployment exposes health endpoint:

```bash
curl -H "access-token: <DAL_ACCESS_TOKEN>" http://127.0.0.1:8000/api/health
```

## Configure ExpEngine for NEW DAL

In `eexp_config.py` (or env-based equivalent), set DAL selection to NEW and point to NEW DAL URL/token. See [Configuration](configuration.md).

## Smoke verification flow

1. Start DAL + PostgreSQL containers.
2. Confirm DAL API responds.
3. Run one known small experiment.
4. Confirm:
   - experiment creation succeeded
   - workflow execution status updates succeeded
   - metric writes succeeded

## Troubleshooting pointers

- If API calls timeout, check container status and port mapping.
- If `401` occurs, verify token and `access-token` header.
- If ProActive jobs fail due to Java module access, apply the compatibility flags listed in [Troubleshooting](troubleshooting.md).
