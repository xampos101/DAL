# Τι κάναμε σήμερα (12 Μαρτίου 2026) – DAL Phase 2

## Σύνοψη

Ολοκληρώσαμε το **Phase 2** του νέου DAL: Core CRUD για **experiments** και **workflows** (FastAPI + PostgreSQL). Όλα τα βασικά endpoints δοκιμάστηκαν με success και η σύνδεση WSL → PostgreSQL (Windows) ρυθμίστηκε.

---

## 1. Υλοποίηση (κώδικας)

- **SQLAlchemy models:** `Experiment`, `Workflow` (με `experiment_metadata` / `workflow_metadata` αντί για `metadata` λόγω reserved attribute στο Declarative API).
- **Pydantic schemas:** ExperimentCreate/Update/Read/ListItem, WorkflowCreate/Update/Read (με `validation_alias` για τα metadata πεδία).
- **Routers:**
  - **Experiments:** `PUT /api/experiments`, `GET /api/experiments`, `GET /api/experiments/{id}`, `POST /api/experiments/{id}`.
  - **Workflows:** `PUT /api/workflows`, `GET /api/workflows/{id}`, `POST /api/workflows/{id}`.
- **Auth:** Όλα τα endpoints (εκτός health) απαιτούν header `access-token`.
- **Σύνδεση:** Routers wired στο `dal_service/main.py` με prefix `/api`.

---

## 2. Διορθώσεις που κάναμε

- **Reserved `metadata`:** Στα ORM models το attribute ονομάστηκε `experiment_metadata` / `workflow_metadata` με column name `"metadata"` στη βάση· στα schemas χρησιμοποιήθηκε `Field(validation_alias=...)` ώστε το API να συνεχίζει να δέχεται/επιστρέφει `metadata`.
- **Σύνδεση WSL → PostgreSQL (Windows):** Το `localhost` από WSL δεν δείχνει στο Windows. Χρησιμοποιήσαμε την IP του Windows από το WSL (`ip route show default` → gateway **172.22.240.1**) στο `DATABASE_URL`.
- **PostgreSQL:** Ενεργοποιήσαμε σύνδεση από δίκτυο: `pg_hba.conf` με γραμμή `host all all 0.0.0.0/0 scram-sha-256`, και Windows Firewall inbound rule για TCP port **5432**.
- **Schema βάσης:** Εκτελέσαμε το `database_schema.sql` στη βάση **DAL** ώστε να υπάρχουν οι πίνακες `experiments` και `workflows`.

---

## 3. Verification (manual)

Δοκιμάσαμε από **PowerShell** με `Invoke-WebRequest` (ισοδύναμο με Postman):

| Βήμα | Endpoint | Αποτέλεσμα |
|------|----------|------------|
| 1 | `PUT /api/experiments` (body: `{"name":"test-exp"}`) | **201** – `message.experimentId` |
| 2 | `GET /api/experiments` | **200** – `experiments` array |
| 3 | `GET /api/experiments/{id}` | **200** – `experiment` object |
| 4 | `PUT /api/workflows` (body: `experiment_id` + `name`) | **201** – `workflow_id` |
| 5 | `GET /api/workflows/{id}` | **200** – `workflow` object |

Όλα πέρασαν με το αναμενόμενο status και JSON.

---

## 4. Περιβάλλον

- **Uvicorn** τρέχει στο **WSL**, από το φάκελο που περιέχει `dal_service` και το `.env` (triple-nested `extremexp-experimentation-engine-main`).
- **PostgreSQL 18** τρέχει στο **Windows** (pgAdmin). Βάση: **DAL**, user: **postgres**, σύνδεση από WSL via **172.22.240.1:5432**.
- **`.env`** (στον ίδιο φάκελο με το `dal_service`): `DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@172.22.240.1:5432/DAL`, `ACCESS_TOKEN=dev-token`.

---

## 5. Τι δεν κάναμε σήμερα (μένει για μελλοντική συνεδρία)

- **Metrics:** πίνακες + endpoints (Phase 3).
- **Query / filter / sorting:** φίλτρα στη λίστα experiments, endpoint sort workflows (Phase 4).
- **Tests:** pytest για routers.
- **Έλεγχος με το Engine:** να τρέχει πραγματικό experiment με base URL το νέο DAL.

---

## 6. Χρήσιμα αρχεία

- `dal_service/routers/experiments.py` – experiments API
- `dal_service/routers/workflows.py` – workflows API
- `dal_service/models/experiment.py`, `workflow.py` – ORM
- `dal_service/schemas/experiment.py`, `workflow.py` – Pydantic
- `dal_service/VERIFICATION.md` – βήματα manual verification
- `docs/database_schema.sql` – PostgreSQL schema
