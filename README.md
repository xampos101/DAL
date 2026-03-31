# ExtremeXP DAL (Data Abstraction Layer)

Υπηρεσία **REST** σε **Python 3.12+** με **FastAPI** και **PostgreSQL** (async μέσω **SQLAlchemy 2** και **asyncpg**). Αποθηκεύει μεταδεδομένα πειραμάτων, workflows και metrics, με συμβατότητα προς το **ExtremeXP Experimentation Engine** (header `access-token`, legacy διαδρομές όπως `executed-experiments` και `*-query`).

Για **ευρετήριο ελληνικής τεκμηρίωσης** δες [docs/README_EL.md](docs/README_EL.md).
Για πλήρες τεχνικό πακέτο **NEW DAL only** (architecture, flowcharts, ERD, installation, Docker), δες [docs/NEW_DAL_DOCUMENTATION.md](docs/NEW_DAL_DOCUMENTATION.md).

---

## Απαιτήσεις

- Python 3.12 ή νεότερο (δοκιμασμένο με 3.12)
- PostgreSQL με υποστήριξη **UUID**, **JSONB**, **ARRAY(UUID)** (όπως η παραγωγική βάση DAL)

---

## Γρήγορη εκκίνηση

### 1. Κλώνος και εικονικό περιβάλλον

```bash
git clone <repository-url>
cd <φάκελος-του-repo>
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
source .venv/bin/activate
```

### 2. Εξαρτήσεις

```bash
pip install -r requirements-test.txt
pip install "uvicorn[standard]"
```

Το αρχείο `requirements-test.txt` περιλαμβάνει τις βιβλιοθήκες εφαρμογής και τις βιβλιοθήκες δοκιμών. Το **uvicorn** χρειάζεται για εκτέλεση του API server και δεν περιλαμβάνεται στο ίδιο αρχείο.

### 3. Μεταβλητές περιβάλλοντος

Αντίγραψε το `.env.example` σε `.env` και συμπλήρωσε τιμές (μην ανεβάζεις το `.env` στο Git):

| Μεταβλητή       | Περιγραφή |
|-----------------|-----------|
| `DATABASE_URL`  | `postgresql+asyncpg://user:password@host:5432/dbname` |
| `ACCESS_TOKEN`  | Κοινό μυστικό για header `access-token` (λειτουργία εξαρτάται από `dal_service/deps.py`) |

### 4. Εκτέλεση API

Από τον **ρίζα** του project (εκεί που βρίσκονται οι φάκελοι `dal_service/` και `tests/`):

```bash
uvicorn dal_service.main:app --reload --host 0.0.0.0 --port 8000
```

Αντιμετώπιση προβλημάτων με reload σε Windows: περιόρισε την παρακολούθηση αρχείων ώστε να μην σαρώνει το `.venv`.

- Διαδραστική τεκμηρίωση: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

Όλα τα routers του DAL είναι κάτω από prefix **`/api`**.

---

## Docker Compose (NEW DAL + PostgreSQL)

1. Αντέγραψε το `.env.example` σε `.env` και βάλε πραγματικές τιμές.
2. Εκκίνηση stack:

```bash
docker compose up -d --build
```

3. Έλεγχος services:

```bash
docker compose ps
docker compose logs -f dal
```

4. Γρήγορος έλεγχος API:

```bash
curl -H "access-token: <DAL_ACCESS_TOKEN>" http://127.0.0.1:8000/api/health
```

5. Τερματισμός:

```bash
docker compose down
```

6. Καθαρό reset βάσης (destructive):

```bash
docker compose down -v
```

---

## Δομή αποθετηρίου

| Διαδρομή | Ρόλος |
|----------|--------|
| `dal_service/main.py` | Σημείο εισόδου FastAPI, εγγραφή routers |
| `dal_service/routers/` | HTTP handlers (experiments, workflows, metrics, queries, health) |
| `dal_service/models/` | SQLAlchemy ORM |
| `dal_service/schemas/` | Pydantic request/response |
| `dal_service/db/` | Async engine και `get_db` |
| `dal_service/deps.py` | Auth dependency |
| `dal_service/utils/` | Βοηθητικά (π.χ. `orm_columns_dict` για ασφαλές `model_validate` από στήλες ORM) |
| `tests/` | Pytest suite, `conftest.py` |
| `docs/` | Αρχιτεκτονική, πρόοδος, τεχνικές εξηγήσεις (πολλά στα ελληνικά) |
| `pytest.ini` | Ρυθμίσεις pytest και asyncio (session-scoped loops) |
| `.coveragerc` | `concurrency = greenlet` για ρεαλιστικό coverage με SQLAlchemy async |

---

## Δοκιμές (pytest)

Χρειάζεσαι **τρέχουσα PostgreSQL** και URL asyncpg. Προτείνεται **ξεχωριστή** βάση για tests (π.χ. `dal_test`), επειδή το suite κάνει `TRUNCATE` σε πίνακες DAL πριν από κάθε test.

PowerShell (παράδειγμα με πλήρες path στο project):

```powershell
cd "C:\Users\<user>\...\extremexp-experimentation-engine-main\extremexp-experimentation-engine-main\extremexp-experimentation-engine-main"
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:YOUR_PASSWORD@127.0.0.1:5432/dal_test"
py -3.12 -m pytest tests/ -v --cov=dal_service.routers --cov-report=term-missing --cov-fail-under=80
```

Σημαντικό: το `cd` πρέπει να δείχνει στον φάκελο που περιέχει `pytest.ini`. Αν τρέξεις pytest από άλλο directory, δεν φορτώνονται οι ρυθμίσεις asyncio και εμφανίζονται λάθη τύπου διαφορετικού event loop.

Λεπτομέρειες: [tests/README.md](tests/README.md).

---

## Αρχιτεκτονική

Διαγράμματα Mermaid και επίπεδα συστήματος: [docs/DAL_ARCHITECTURE.md](docs/DAL_ARCHITECTURE.md).

---

## Άδεια

Δες το αρχείο `LICENSE` στο αποθετήριο (αν υπάρχει).

---

## Συνεισφορά

Pull requests κατά προτίμηση από ξεχωριστό branch. Πριν το push: `pytest` με ενεργό `TEST_DATABASE_URL`, χωρίς να συμπεριλαμβάνονται μυστικά στο commit (`.gitignore` για `.env`, `.venv`, coverage artifacts).
