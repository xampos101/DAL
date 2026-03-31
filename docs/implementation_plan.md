# DAL Implementation Plan – Python/FastAPI/PostgreSQL

Roadmap για την υλοποίηση του νέου Data Abstraction Layer (DAL) σε Python, FastAPI και PostgreSQL, με πλήρη συμβατότητα API με το υπάρχον Node.js DAL και το Experimentation Engine.

---

## Phase 1: Schema and first migration (Priority: Critical)

**Στόχος:** Έτοιμη βάση και δομή project.

| Task | Λεπτομέρειες |
|------|--------------|
| 1.1 | Δημιουργία project structure (`dal-service/`, `app/`, `alembic/`, `tests/`) σύμφωνα με [.cursor/rules/DAL.mdc](../.cursor/rules/DAL.mdc) |
| 1.2 | Πρώτο Alembic migration βασισμένο στο [database_schema.sql](database_schema.sql) |
| 1.3 | Ρύθμιση σύνδεσης DB (config από env, `DATABASE_URL`), validation on startup |
| 1.4 | Έλεγχος ότι το schema εφαρμόζεται με `alembic upgrade head` |

**Deliverables:** Repository structure, migration που τρέχει χωρίς σφάλματα, `.env.example` με απαιτούμενα vars.

---

## Phase 2: Core CRUD and authentication (Priority: Critical)

**Στόχος:** Βασικά endpoints experiments/workflows και προστασία με auth.

| Task | Λεπτομέρειες |
|------|--------------|
| 2.1 | SQLAlchemy models για experiments, workflows, metrics (ευθυγραμμισμένα με [database_schema.sql](database_schema.sql)) |
| 2.2 | Pydantic v2 schemas (request/response) για experiments, workflows, metrics |
| 2.3 | CRUD layer με transactions (rollback on error), βλ. DAL rules |
| 2.4 | **GET /api/executed-experiments** → `{"executed_experiments": [...]}` (κρίσιμο για Engine) |
| 2.5 | PUT /api/experiments, GET /api/experiments, GET /api/experiments/{id}, POST /api/experiments/{id} |
| 2.6 | PUT /api/workflows, GET /api/workflows/{id}, POST /api/workflows/{id} |
| 2.7 | Auth: dependency για `access-token` header (και optional Bearer), validation, 401 on missing/invalid |
| 2.8 | Response formats ακριβώς όπως το Engine περιμένει (`message.experimentId`, `workflow_id`, `experiment`, `workflow`) |

**Deliverables:** Engine μπορεί να καλεί base URL + token και να παίρνει executed_experiments, create/read/update experiments και workflows.

---

## Phase 3: Metrics and aggregations (Priority: High)

**Στόχος:** Πλήρης υποστήριξη metrics και metric data.

| Task | Λεπτομέρειες |
|------|--------------|
| 3.1 | PUT /api/metrics, GET /api/metrics/{id}, POST /api/metrics/{id} |
| 3.2 | PUT /api/metrics-data/{id} με body `{"records": [{"value": ...}]}` · append στο `metrics.records` JSONB και optional sync σε `metric_records` |
| 3.3 | Υπολογισμός aggregations (count, sum, min, max, average, median) on read από records ή από `metric_aggregations` αν materialized |
| 3.4 | Σύνδεση metrics με workflows (parent_type/parent_id), ενημέρωση workflow.metric_ids και workflow.metrics όταν προστίθενται metrics |

**Deliverables:** Create/read/update metrics, append records, aggregations σε GET metric/workflow.

---

## Phase 4: Query endpoints, sorting, and hardening (Priority: Medium)

**Στόχος:** Query endpoints και διορθώσεις συμβατότητας.

| Task | Λεπτομέρειες |
|------|--------------|
| 4.1 | POST /api/experiments-query (filter by creator, metadata, κ.λπ.) |
| 4.2 | POST /api/workflows-query, POST /api/metrics-query |
| 4.3 | POST /api/experiments-sort-workflows/{experimentId} · **fix bug:** read και write στο ίδιο field `workflow_ids` (όχι `workflows`) |
| 4.4 | POST /api/experiments-metrics (όλα τα metrics ενός experiment) |
| 4.5 | Rate limiting (SlowAPI) σε write endpoints |
| 4.6 | Health checks: `/health`, `/ready` (optional DB check) |
| 4.7 | Structured logging, error handling σύμφωνα με DAL rules (no bare except, log + re-raise or HTTPException) |

**Deliverables:** Query/sort endpoints, rate limiting, health checks, consistent error handling.

---

## Phase 5: Testing and deployment (Priority: High)

**Στόχος:** Test coverage και deployment-ready setup.

| Task | Λεπτομέρειες |
|------|--------------|
| 5.1 | Pytest fixtures (DB session, test client, sample data), deterministic tests |
| 5.2 | Contract tests: endpoints ακολουθούν OpenAPI / engine client expectations |
| 5.3 | Coverage ≥80% (`pytest --cov=app --cov-fail-under=80`) |
| 5.4 | Dockerfile και docker-compose (PostgreSQL + DAL service) |
| 5.5 | CI (optional): run tests + migrations on push |

**Deliverables:** Test suite που περνάει, Docker image, docker-compose για τοπικό run.

---

## Timeline (indicative)

| Phase | Εκτίμηση | Εξαρτήσεις |
|-------|----------|------------|
| Phase 1 | 0.5–1 ημέρα | - |
| Phase 2 | 1–2 ημέρες | Phase 1 |
| Phase 3 | 1 ημέρα | Phase 2 |
| Phase 4 | 1–2 ημέρες | Phase 2, 3 |
| Phase 5 | 1–2 ημέρες | Phase 4 |

---

## Environment variables (.env.example)

Να περιλαμβάνονται (χωρίς πραγματικές τιμές):

- `DATABASE_URL` – PostgreSQL connection string
- `SECRET_KEY` / `JWT_SECRET` – για token validation
- `ACCESS_TOKEN` ή αντίστοιχο – για απλό access-token validation (MVP)
- `LOG_LEVEL` – π.χ. INFO
- `CORS_ORIGINS` – για frontend αν χρειάζεται

Όλα τα secrets από env· `.env` στο `.gitignore`.

---

## References

- [DAL_POSTGRESQL_SCHEMA.md](DAL_POSTGRESQL_SCHEMA.md) – schema documentation
- [database_schema.sql](database_schema.sql) – executable DDL
- [DAL_CRITICAL_QUESTIONS_ANSWERS.md](DAL_CRITICAL_QUESTIONS_ANSWERS.md) – λεπτομέρειες API και συμπεριφορά
- [DAL_OVERVIEW_AND_API_CONTRACT.md](DAL_OVERVIEW_AND_API_CONTRACT.md) – architecture και API contract
- [.cursor/rules/DAL.mdc](../.cursor/rules/DAL.mdc) – mandatory rules (security, transactions, testing, deployment)
