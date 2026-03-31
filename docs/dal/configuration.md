# DAL Configuration (NEW DAL Focus)

## Minimal NEW DAL configuration

Use NEW DAL as the default path:

```python
DAL_VERSION = "NEW"
DATA_ABSTRACTION_BASE_URL = "<NEW_DAL_URL>"
DATA_ABSTRACTION_ACCESS_TOKEN = "<DAL_ACCESS_TOKEN>"
```

Common local value for NEW DAL URL:

```text
http://127.0.0.1:8000/api
```

## `eexp_config.py` alignment

When using `DAL_VERSION`, keep URL/token mapping explicit:

```python
DAL_VERSION = "NEW"

if DAL_VERSION == "NEW":
    DATA_ABSTRACTION_BASE_URL = "<NEW_DAL_URL>"
    DATA_ABSTRACTION_ACCESS_TOKEN = "<DAL_ACCESS_TOKEN>"
else:
    raise ValueError("This deployment path documents NEW DAL only.")
```

## Environment-variable driven configuration

Prefer env vars over hardcoded values:

```python
import os

DATA_ABSTRACTION_BASE_URL = os.getenv("DATA_ABSTRACTION_BASE_URL", "http://127.0.0.1:8000/api")
DATA_ABSTRACTION_ACCESS_TOKEN = os.getenv("DATA_ABSTRACTION_ACCESS_TOKEN", "")
```

Example shell setup:

```bash
export DATA_ABSTRACTION_BASE_URL="<NEW_DAL_URL>"
export DATA_ABSTRACTION_ACCESS_TOKEN="<DAL_ACCESS_TOKEN>"
```

## Secrets handling

- Do not commit real tokens to the repository.
- Do not place secrets in Markdown pages.
- Use `.env` for local development and `.env.example` with placeholders for sharing.
- Rotate access tokens if accidentally exposed.
