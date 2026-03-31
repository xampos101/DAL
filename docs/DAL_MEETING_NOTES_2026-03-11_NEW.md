# DAL – Meeting notes (2026-03-11)

Σκονάκι για το meeting με τον καθηγητή (Dr. Ilias Gerostathopoulos): τι έχω κάνει, τι σκοπεύω να κάνω, τι ερωτήσεις να κάνω.

---

## 1. Opening – Τι έχω κάνει μέχρι τώρα (2–3 προτάσεις)

Έκανα **ανάλυση** του υπάρχοντος Node.js DAL (routes + Elasticsearch documents) και του Engine client. Σχεδίασα και τεκμηρίωσα το **PostgreSQL schema** (5 πίνακες, JSONB, indexes, triggers). Συγκέντρωσα τα **critical findings** και έφτιαξα docs για data flow, implementation plan και production checklist.

---

## 2. Τι έχω κάνει μέχρι τώρα (bullets)

- Ανάλυση Node.js DAL: experiments.js, workflows.js, metrics.js, util.js
- Ανάλυση Engine client (`data_abstraction_api.py`) και των endpoints που χρησιμοποιεί
- Καταγραφή critical findings: missing `/executed-experiments`, bug στο sort workflows, nullable fields, JSONB-only workflows, auth με `access-token`, response formats
- Σχεδιασμός PostgreSQL schema: `experiments`, `workflows`, `metrics`, `metric_records`, `metric_aggregations` (βλ. [database_schema.sql](database_schema.sql))
- Δημιουργία documentation:
  - [DAL_POSTGRESQL_SCHEMA.md](DAL_POSTGRESQL_SCHEMA.md) (schema + ERD)
  - [critical_findings.md](critical_findings.md)
  - [DAL_DATA_FLOW.md](DAL_DATA_FLOW.md) (request lifecycle)
  - [implementation_plan.md](implementation_plan.md)
  - [DAL_PRODUCTION_CHECKLIST.md](DAL_PRODUCTION_CHECKLIST.md)
  - [DAL_STUDY_GUIDE.md](DAL_STUDY_GUIDE.md) (επανάληψη)

---

## 3. Τι σκοπεύω να κάνω στη συνέχεια (plan)

(Βασισμένο στο [implementation_plan.md](implementation_plan.md))

**Phase 1 – Setup & migrations**
- Δημιουργία project (`dal-service/`) με FastAPI, SQLAlchemy, Alembic
- Πρώτο Alembic migration από [database_schema.sql](database_schema.sql)
- Σύνδεση σε τοπική PostgreSQL (DATABASE_URL από env), έλεγχος `alembic upgrade head`

**Phase 2 – Core API για experiments/workflows**
- SQLAlchemy models + Pydantic schemas
- Endpoints: PUT/GET/POST experiments, **GET /executed-experiments**, PUT/GET/POST workflows
- Auth dependency για `access-token`
- Response formats ακριβώς όπως το Engine

**Phase 3 – Metrics**
- PUT/GET/POST metrics, PUT /metrics-data/{id}
- Aggregations (on read ή metric_aggregations)

**Phase 4 – Query & hardening**
- POST /experiments-query, /workflows-query, /metrics-query
- POST /experiments-sort-workflows (fix bug: read/write στο ίδιο field `workflow_ids`)
- Rate limiting, health checks, logging

**Phase 5 – Testing & deployment**
- Pytest, contract tests, coverage ≥80%
- Dockerfile + docker-compose (PostgreSQL + DAL)

---

## 4. Ρίσκα / δυσκολίες που βλέπω

- Ο όγκος των endpoints είναι μεγάλος· χρειάζεται προτεραιοποίηση (πρώτα experiments/workflows + executed-experiments)
- Λεπτομέρειες στο auth (απλό access-token τώρα, ίσως JWT αργότερα)
- Αν χρειαστεί migration από υπαρκτά ES δεδομένα σε PostgreSQL, θα χρειαστεί extra χρόνος

---

## 5. Ερωτήσεις προς τον καθηγητή

- Για πρώτο **milestone**, είναι αρκετό ένα working prototype με create/get experiments, workflows και `/executed-experiments`; ή θέλετε και βασικά metrics από την αρχή;
- Υπάρχει προτίμηση για δομή repo (ξεχωριστό repo vs φάκελος δίπλα στο Engine);
- Τι θεωρείτε πιο σημαντικό στη φάση αυτή: metrics & aggregations ή query endpoints;
- Κάθε πότε θα θέλατε updates (weekly / bi-weekly meeting ή async);

---

## 6. Closing – Τι θα πω στο τέλος

«Αν συμφωνείτε με αυτό το πλάνο και την προτεραιοποίηση, θα ξεκινήσω με το project structure, το πρώτο migration και τα βασικά endpoints για experiments/workflows και `/executed-experiments`, ώστε στο επόμενο meeting να έχουμε ήδη κάτι που μιλάει με το Engine. Είμαι ανοιχτός σε αλλαγές προτεραιοτήτων αν θέλετε να δώσετε έμφαση σε κάποιο κομμάτι.»
