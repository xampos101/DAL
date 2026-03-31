# DAL Production readiness checklist

Checklist ευθυγραμμισμένο με τα [.cursor/rules/DAL.mdc](../.cursor/rules/DAL.mdc). Χρησιμοποιήστε για review και για meetings (Done / To do).

---

## Schema and database

| Item | Status | Σημειώσεις |
|------|--------|------------|
| UUID primary keys (όχι auto-increment) | To do | [database_schema.sql](database_schema.sql) |
| JSONB για metadata, parameters, embedded data | To do | workflows: parameters, tasks, input_datasets, output_datasets |
| TIMESTAMPTZ για όλα τα timestamps | To do | created_at, updated_at |
| Indexes σε FKs και status / created_at | To do | Βλ. DAL_POSTGRESQL_SCHEMA.md §5 |
| Triggers για updated_at (EXECUTE FUNCTION, PG 11+) | To do | update_updated_at() |
| Migrations μόνο μέσω Alembic (όχι manual DDL) | To do | Πρώτο migration από database_schema.sql |

---

## Security

| Item | Status | Σημειώσεις |
|------|--------|------------|
| Όλα τα /api/* endpoints προστατεύονται | To do | Auth dependency |
| Αποδοχή access-token header (Engine) | To do | Υποχρεωτικό για συμβατότητα |
| Optional: Bearer token (OpenAPI) | To do | |
| Validation token (signature, exp, iss/aud) | To do | JWT ή απλό token check |
| Rate limiting σε write endpoints | To do | SlowAPI, π.χ. 60/min |
| Secrets μόνο από env (όχι hardcode) | To do | DATABASE_URL, SECRET_KEY, κ.λπ. |
| .env στο .gitignore, .env.example χωρίς τιμές | To do | |

---

## API contract

| Item | Status | Σημειώσεις |
|------|--------|------------|
| GET /executed-experiments → executed_experiments | To do | Κρίσιμο για Engine |
| PUT /experiments → 201, message.experimentId | To do | |
| PUT /workflows → 201, workflow_id | To do | |
| PUT /metrics → 201, metric_id | To do | |
| GET responses: experiment, workflow (keys) | To do | |
| OpenAPI / engine client paths και shapes | To do | Βλ. critical_findings.md |

---

## Transactions and error handling

| Item | Status | Σημειώσεις |
|------|--------|------------|
| Mutable ops σε transactions με rollback on error | To do | try/except SQLAlchemyError, db.rollback() |
| Multi-table ops σε μία transaction | To do | π.χ. workflow + metrics |
| Όχι bare except χωρίς log + re-raise ή HTTPException | To do | |
| Log για όλα τα non-2xx (operation, error, exc_info) | To do | |
| Μην log tokens/passwords/secrets | To do | |

---

## Testing

| Item | Status | Σημειώσεις |
|------|--------|------------|
| Contract tests (OpenAPI / engine client) | To do | |
| Coverage ≥ 80% (--cov-fail-under=80) | To do | |
| Deterministic fixtures, test isolation | To do | |
| Tests για CRUD, 404, 400, 401, 500 | To do | |

---

## Deployment and operations

| Item | Status | Σημειώσεις |
|------|--------|------------|
| Health check endpoint (π.χ. /health, /ready) | To do | |
| Config από env, validation on startup | To do | Fail fast αν λείπουν απαραίτητα |
| Dockerfile για DAL service | To do | |
| docker-compose (PostgreSQL + DAL) | To do | |
| API versioning (αν απαιτείται) | To do | |

---

## Documentation

| Item | Status | Σημειώσεις |
|------|--------|------------|
| database_schema.sql (production DDL) | Done | docs/database_schema.sql |
| DAL_POSTGRESQL_SCHEMA.md (schema docs + ERD) | Done | |
| implementation_plan.md | Done | |
| critical_findings.md | Done | |
| DAL_PRESENTATION_NOTES.md | Done | |
| DAL_DATA_FLOW.md (Mermaid flow) | Done | |
| .env.example με λίστα variables | To do | Στο dal-service repo |

---

**How to use:** Ενημερώστε το Status σε "Done" όταν ολοκληρωθεί το αντίστοιχο task. Χρήσιμο για sync με mentor και για code review.
