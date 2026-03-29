# DAL (Python/FastAPI) — Αναλυτική εξήγηση για μελέτη

Αυτό το κείμενο εξηγεί **τι κάνει** το Data Abstraction Layer και **γιατί** μπήκαν συγκεκριμένες τεχνικές λύσεις (tests, asyncio, `metadata`, coverage).

---

## 1. Τι είναι το DAL

Το **DAL** (Data Abstraction Layer) είναι η υπηρεσία που αποθηκεύει και εκθέτει μέσω REST τα δεδομένα πειραμάτων: experiments, workflows, metrics (και σχετικές εγγραφές). Υλοποιείται με **FastAPI** και **PostgreSQL**, με **ασύγχρονη** πρόσβαση στη βάση (`asyncpg` μέσω SQLAlchemy async).

Το **Experimentation Engine** (ή άλλα clients) καλεί το DAL με HTTP (π.χ. `PUT /api/experiments`, `POST /api/experiments-query`) και συχνά στέλνει header **`access-token`**.

---

## 2. Πώς τρέχουν τα tests

### Ροή σε μία γραμμή

```mermaid
flowchart LR
  pytest[pytest_asyncio] --> conftest[conftest.py]
  conftest --> env[DATABASE_URL από TEST_DATABASE_URL]
  conftest --> override[override get_db]
  conftest --> client[httpx AsyncClient plus ASGITransport]
  client --> app[FastAPI app]
  app --> router[routers]
  router --> db[(PostgreSQL)]
```

### Λεπτομέρειες

1. **`tests/conftest.py`** τρέχει **πριν** φορτωθεί η εφαρμογή και ορίζει:
   - `ACCESS_TOKEN` για dev/test.
   - `DATABASE_URL` από τη μεταβλητή περιβάλλοντος **`TEST_DATABASE_URL`** (ή default αν το έχεις ρυθμίσει).

2. **Ίδιο app, πραγματική βάση:** δεν σηκώνουμε ξεχωριστό server. Το **httpx** μιλάει στην εφαρμογή μέσω **`ASGITransport(app=app)`**, δηλαδή in-process κλήσεις όπως στο production routing.

3. **Dependency override:** το `get_db` αντικαθίσταται ώστε κάθε test να χρησιμοποιεί **test engine / sessionmaker**, όχι την παραγωγική ρύθμιση.

4. **Καθαρισμός δεδομένων:** πριν από κάθε test γίνεται `TRUNCATE` στους πίνακες DAL (με `CASCADE`), ώστε τα tests να είναι **ανεξάρτητα** μεταξύ τους.

5. **Schema:** σε session fixture δημιουργούνται οι πίνακες (`create_all`) αν χρειάζεται.

Άρα: τα tests ελέγχουν **πραγματικό SQL**, πραγματικά endpoints και πραγματική σειρά HTTP status / JSON.

---

## 3. Γιατί «έσκαγε» το event loop (asyncio)

Με **pytest-asyncio** νεότερων εκδόσεων, τα **async tests** μπορεί να τρέχουν σε **διαφορετικό** event loop από τα **session-scoped** async fixtures (π.χ. το engine που ανοίγει συνδέσεις asyncpg).

Τότε εμφανίζονται σφάλματα όπως: *Task got Future attached to a different loop*.

**Λύση:** στο `pytest.ini` ορίζουμε και για fixtures και για tests το **ίδιο** loop scope σε επίπεδο session, π.χ.:

- `asyncio_default_fixture_loop_scope = session`
- `asyncio_default_test_loop_scope = session`

Έτσι οι συνδέσεις και τα async endpoints μοιράζονται **ένα** loop για όλη τη συνεδρία pytest.

---

## 4. Το πρόβλημα με το όνομα `metadata`

### Δύο διαφορετικά «metadata»

| Τι | Σημαίνει |
|----|----------|
| **`metadata` στο JSON API** | Ένα πεδίο **δεδομένων** του experiment/workflow/metric (λέξεις-κλειδιά που αποθηκεύονται σε JSONB). |
| **`Base.metadata` στο SQLAlchemy** | Το **σχήμα** όλων των πινάκων του ORM (αντικείμενο τύπου `MetaData`), όχι JSON του πελάτη. |

Κάθε κλάση μοντέλου που κληρονομεί το `DeclarativeBase` έχει **ιδιότητα** `.metadata` που δείχνει σε αυτό το αντικείμενο.

### Τι πήγαινε στραβά με το Pydantic

Όταν κάναμε `SomeRead.model_validate(orm_instance)` και το schema είχε πεδίο με όνομα που οδηγούσε το Pydantic να διαβάσει `getattr(orm, "metadata")`, έπαιρνε το **SQLAlchemy MetaData**, όχι το JSONB — εξ ου και σφάλμα *Input should be a valid dictionary*.

Γι’ αυτό **δεν** χρησιμοποιούμε ως Python όνομα πεδίου απλά `metadata` για ανάγνωση από ORM, όταν το μοντέλο είναι SQLAlchemy mapped class.

---

## 5. Η λύση που εφαρμόστηκε

### Schemas

- **`experiment_metadata`**, **`workflow_metadata`**, **`metric_metadata`**: ονόματα πεδίων που **ταιριάζουν** με τις ιδιότητες του ORM (ή με τα κλειδιά που βγαίνουν από τις στήλες).
- **`validation_alias=AliasChoices("metadata", "..._metadata")`**: το API μπορεί να στέλνει **`metadata`** στο JSON εισόδου.
- **`serialization_alias="metadata"`**: στην **έξοδο** JSON (με `by_alias` όπως κάνει το FastAPI) ο client βλέπει πάλι το κλειδί **`metadata`**.

### Routers (create / update)

Το `model_dump()` δίνει τα **ονόματα πεδίων** του μοντέλου (π.χ. `experiment_metadata`). Ο κώδικας κάνει `pop` αυτού του κλειδιού και περνάει την τιμή στον κατασκευαστή ORM ως `experiment_metadata` / `workflow_metadata` / `metric_metadata`.

### `orm_columns_dict`

Για **ανάγνωση** από DB, αντί να περνάμε απευθείας το ORM instance στο Pydantic, καλούμε `orm_columns_dict(instance)` που χτίζει dict **μόνο από τις mapped στήλες** (μέσω SQLAlchemy `inspect(...).mapper.column_attrs`). Έτσι **ποτέ** δεν «βλέπουμε» το `.metadata` του Declarative API.

---

## 6. Γιατί χρειάζεται `greenlet` στο coverage

Το SQLAlchemy async εκτελεί μέρος του ORM κώδικα μέσα σε **greenlets** (γέφυρα sync/async). Το πρότυπο tracer του `coverage` δεν μετράει αυτόματα όλες αυτές τις γραμμές.

Με **`concurrency = greenlet`** στο `.coveragerc`, το coverage ξέρει να παρακολουθεί και αυτό το νήμα εκτέλεσης. Χωρίς αυτό, φαίνεται λάθος χαμηλή κάλυψη (π.χ. ολόκληρα routers «ακάλυπτα» ενώ τα tests τα καλούν κανονικά).

---

## 7. Εντολές (σωστό path, χωρίς `...`)

Αντικατέστησε το path αν το project σου είναι αλλού:

```powershell
cd "C:\Users\xampo\Downloads\extremexp-experimentation-engine-main\extremexp-experimentation-engine-main\extremexp-experimentation-engine-main"
$env:TEST_DATABASE_URL = "postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/ONOMA_VASHS"
py -3.12 -m pytest tests/ -v --cov=dal_service.routers --cov-report=term-missing --cov-fail-under=80
```

- Το `cd` **πρέπει** να δείχνει στον φάκελο που περιέχει `pytest.ini`, `dal_service/`, `tests/`.
- Το `rootdir` στο output του pytest πρέπει να είναι αυτός ο φάκελος (όχι `C:\Users\xampo`).

---

## Σύνοψη

1. **DAL** = REST + PostgreSQL + async ORM για δεδομένα πειραμάτων.  
2. **Tests** = πραγματική εφαρμογή + πραγματική βάση + httpx ASGI + καθαρισμό πινάκων.  
3. **Ίδιο event loop** = απαραίτητο για σταθερό asyncpg/SQLAlchemy async κάτω από pytest-asyncio.  
4. **`metadata` στο API ≠ `Base.metadata`** — χρειάστηκαν σωστά ονόματα πεδίων, aliases και `orm_columns_dict`.  
5. **Coverage + greenlet** = ρεαλιστική μέτρηση κάλυψης για async SQLAlchemy.

Αν κάτι από τα παραπάνω «δεν κάθεται», διάβασε το αντίστοιχο αρχείο στο repo (`tests/conftest.py`, `pytest.ini`, `.coveragerc`, `dal_service/utils/orm_columns.py`, schemas και routers) παράλληλα με αυτό το κείμενο.
