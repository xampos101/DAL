# DAL Study Guide – Τι κάνουμε και γιατί

Αυτό το έγγραφο είναι για επανάληψη: να διαβάζεις σε 10–15 λεπτά και να καταλαβαίνεις τι είναι το DAL, τι αποφάσεις έχουμε πάρει, και πώς συνδέονται API, Engine, DAL και βάση PostgreSQL.

**Σχετικά docs:** [critical_findings.md](critical_findings.md), [DAL_DATA_FLOW.md](DAL_DATA_FLOW.md), [database_schema.sql](database_schema.sql), [DAL_POSTGRESQL_SCHEMA.md](DAL_POSTGRESQL_SCHEMA.md), [implementation_plan.md](implementation_plan.md).

---

## 1. High-level εικόνα

### ExtremeXP Experimentation Engine

- Framework που εκτελεί **πειράματα** (experiments) οργανωμένα σε **workflows** και **tasks**.
- Κατά την εκτέλεση παράγει **μετρικές** (metrics) και αποτελέσματα που αποθηκεύονται στο DAL.

### Τι είναι το DAL;

- **DAL (Data Abstraction Layer):** REST API που αποθηκεύει και εξυπηρετεί:
  - metadata πειραμάτων (**experiments**),
  - πληροφορίες εκτελέσεων (**workflows**, με tasks, parameters, datasets),
  - μετρήσεις αποτελεσμάτων (**metrics**, records, aggregations).
- Το Engine μιλάει **μόνο** με το DAL μέσω HTTP· δεν βλέπει απευθείας τη βάση.

### Πώς μιλάνε μεταξύ τους (Engine → DAL → DB)

1. Το Engine στέλνει HTTP request στο DAL (π.χ. `PUT /api/experiments`) με header **`access-token`**.
2. Το DAL: ελέγχει token (auth), τρέχει λογική (CRUD, validation), γράφει/διαβάζει από **PostgreSQL**.
3. Το DAL επιστρέφει JSON (π.χ. `{ "message": { "experimentId": "<uuid>" } }`).
4. Το Engine χρησιμοποιεί τα IDs για τα επόμενα βήματα.

**Διάγραμμα ροής:** Βλ. [DAL_DATA_FLOW.md](DAL_DATA_FLOW.md). Σύντομα: Engine → API → Auth → CRUD → DB → CRUD → API → Engine.

---

## 2. Critical findings (περίληψη)

### 2.1 Missing endpoint `/executed-experiments` (CRITICAL)

- Το Engine καλεί **GET /executed-experiments** και περιμένει key **`executed_experiments`**.
- Το παλιό Node.js DAL έχει μόνο **GET /experiments** (key `experiments`, paginated).
- **Απόφαση:** Το νέο DAL **πρέπει** να έχει `GET /api/executed-experiments` που επιστρέφει `{"executed_experiments": [...]}`.

### 2.2 Workflow sorting bug

- Στο παλιό DAL το sort endpoint διαβάζει από **`workflow_ids`** αλλά γράφει στο **`workflows`**.
- Τα υπόλοιπα endpoints χρησιμοποιούν μόνο `workflow_ids`.
- **Απόφαση:** Στο νέο DAL χρησιμοποιούμε **ένα** field (`workflow_ids`) για read και write.

### 2.3 Nullable fields

- Το Node.js DAL δεν απαιτεί παρουσία συγκεκριμένων keys (μόνο type check για keys που υπάρχουν).
- **Απόφαση:** Στο PostgreSQL όλα τα πεδία experiments είναι nullable· στα workflows μόνο `name` NOT NULL.

### 2.4 Embedded data (JSONB-only για workflows)

- Στο Elasticsearch τα workflows έχουν parameters, tasks, input_datasets, output_datasets **embedded**.
- **Απόφαση:** Στο νέο schema αυτά είναι **JSONB** columns στο πίνακα `workflows` (όχι ξεχωριστά tables).

### 2.5 Authentication

- Το Engine στέλνει μόνο header **`access-token`**.
- **Απόφαση:** Το νέο DAL πρέπει να δέχεται και να επαληθεύει το `access-token`.

### 2.6 Response formats (create endpoints)

- `PUT /experiments` → `201`, `{ "message": { "experimentId": "<uuid>" } }`
- `PUT /workflows` → `201`, `{ "workflow_id": "<uuid>" }`
- `PUT /metrics` → `201`, `{ "metric_id": "<uuid>" }`

Τα response shapes πρέπει να ταιριάζουν ακριβώς με το Engine client.

### 2.7 Metrics: records & aggregations

- Records: array μέσα στο metric document. Στο νέο schema: `metrics.records` JSONB + optional `metric_records` table.
- Aggregations: υπολογίζονται on read (count, sum, min, max, average, median). Στο νέο DAL: on-the-fly ή cached πίνακας `metric_aggregations`.

---

## 3. Database schema – PostgreSQL (5 πίνακες)

### 3.1 `experiments`

**Τι μοντελοποιεί:** Ένα πείραμα (όνομα, σκοπός, status, χρονικά όρια, creator, metadata).

**Σημαντικά πεδία:** `id`, `name`, `intent`, `status`, `workflow_ids` (UUID[]), `metadata`, `creator` (JSONB), `created_at`, `updated_at`.

**Σύνδεση με Engine:** `PUT /experiments` δημιουργεί row· `workflow_ids` ενημερώνεται όταν δημιουργούμε workflows ή κάνουμε sort.

### 3.2 `workflows`

**Τι μοντελοποιεί:** Μια εκτέλεση/ροή εργασιών για ένα experiment.

**Σημαντικά πεδία:** `id`, `experiment_id` (FK), `name` (NOT NULL), `status`, `parameters`, `tasks`, `input_datasets`, `output_datasets` (JSONB), `metric_ids`, `metrics` (JSONB cache), timestamps.

**Σύνδεση με Engine:** `PUT /workflows` δημιουργεί row· `GET /workflows/{id}` επιστρέφει full document με embedded data.

### 3.3 `metrics`

**Τι μοντελοποιεί:** Μια μετρική (π.χ. accuracy, loss, runtime).

**Σημαντικά πεδία:** `id`, `experiment_id`, `parent_type`, `parent_id`, `name`, `kind` (scalar/series/timeseries), `type`, `value`, `records` (JSONB), timestamps.

**Σύνδεση με Engine:** `PUT /metrics` δημιουργεί metric· `PUT /metrics-data/{id}` προσθέτει records.

### 3.4 `metric_records`

**Τι μοντελοποιεί:** Normalized records για μεγάλα series (performance).

**Πεδία:** `id`, `metric_id`, `value`, `timestamp`, `created_at`.

### 3.5 `metric_aggregations`

**Τι μοντελοποιεί:** Cached aggregations (count, sum, min, max, average, median) ανά metric.

**Πεδία:** `metric_id` (PK), `count`, `sum`, `min`, `max`, `average`, `median`, `updated_at`.

---

## 4. JSONB & Embedded data

Γιατί workflows έχουν `parameters`, `tasks`, `input_datasets`, `output_datasets` ως JSONB;

- Το παλιό DAL αποθηκεύει ολόκληρο το workflow document σε ένα Elasticsearch document.
- Δεν υπάρχουν ξεχωριστά indices για αυτά.
- Με JSONB: 1:1 mapping με Elasticsearch, ευελιξία, GIN indexes για queries.

---

## 5. Metrics & aggregations (συνοπτικά)

- **Scalar metric:** π.χ. `accuracy = 0.95` (χρησιμοποιεί `value TEXT`).
- **Series metric:** λίστα από values (stored στο `records JSONB`).
- **Timeseries metric:** series με timestamps (`metric_records.timestamp`).

**Aggregations:** Στο παλιό DAL on-the-fly από `records`. Στο νέο: είτε on-the-fly είτε materialized στο `metric_aggregations`.

---

## 6. API contract (συνοπτικά)

**Experiments:** `PUT /api/experiments`, `GET /api/experiments/{id}`, `POST /api/experiments/{id}`, `POST /api/experiments-query`, **`GET /api/executed-experiments`**, `POST /api/experiments-sort-workflows/{id}`.

**Workflows:** `PUT /api/workflows`, `GET /api/workflows/{id}`, `POST /api/workflows/{id}`.

**Metrics:** `PUT /api/metrics`, `GET /api/metrics/{id}`, `POST /api/metrics/{id}`, `PUT /api/metrics-data/{id}`.

Λεπτομέρειες: [DAL_OVERVIEW_AND_API_CONTRACT.md](DAL_OVERVIEW_AND_API_CONTRACT.md), [DAL_CRITICAL_QUESTIONS_ANSWERS.md](DAL_CRITICAL_QUESTIONS_ANSWERS.md).

---

## 7. Πώς δένουν όλα μαζί (τυπικό flow)

1. **PUT /api/experiments** → row σε `experiments` → γυρνά `experimentId`.
2. **PUT /api/workflows** με `experimentId` → row σε `workflows` → ενημέρωση `workflow_ids` στο experiment.
3. Κατά την εκτέλεση: **PUT /api/metrics**, **PUT /api/metrics-data/{id}** για records.
4. Για ανάγνωση: **GET /api/executed-experiments**, **GET /api/workflows/{id}** (με metrics + aggregations).

Αν μπορώ να περιγράψω αυτό το flow προφορικά, έχω καταλάβει το DAL αρκετά καλά για την υλοποίηση.
