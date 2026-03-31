# Docker Deployment (Default: Single Compose)

This page documents the default local deployment path:

- NEW DAL service
- PostgreSQL service
- one Docker Compose file

## Recommended project files

Create:

- `docker-compose.yml`
- `.env` (local only, never committed)
- `.env.example` (committed placeholders only)

Ensure `.env` is listed in `.gitignore`.

## `.env.example` template

```env
POSTGRES_DB=<POSTGRES_DB>
POSTGRES_USER=<POSTGRES_USER>
POSTGRES_PASSWORD=<POSTGRES_PASSWORD>
DATABASE_URL=postgresql+asyncpg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@postgres:5432/<POSTGRES_DB>
DAL_ACCESS_TOKEN=<DAL_ACCESS_TOKEN>
```

## Single-compose template

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  new_dal:
    image: <NEW_DAL_IMAGE_OR_BUILD>
    environment:
      DATABASE_URL: ${DATABASE_URL}
      ACCESS_TOKEN: ${DAL_ACCESS_TOKEN}
    depends_on:
      - postgres
    ports:
      - "8000:8000"

volumes:
  postgres_data:
```

## Runbook commands

Start:

```bash
docker compose up -d --build
```

First-time startup checks:

```bash
docker compose ps
docker compose logs --no-log-prefix new_dal
```

Inspect:

```bash
docker compose ps
docker compose logs -f new_dal
```

Verify API:

```bash
curl -H "access-token: <DAL_ACCESS_TOKEN>" http://127.0.0.1:8000/api/experiments
```

Stop:

```bash
docker compose down
```

Stop and remove volumes (destructive):

```bash
docker compose down -v
```

## Persistence and reset

- PostgreSQL data persists in `postgres_data` volume.
- Use `down -v` only when you intentionally want a clean database state.

## Security requirements

- Never commit `.env` with real values.
- Use `.env.example` with placeholders only.
- Rotate tokens if exposed.
