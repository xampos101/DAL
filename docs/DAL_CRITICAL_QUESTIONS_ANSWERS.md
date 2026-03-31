# Απαντήσεις στα Cursor Prompts – DAL & Engine

Οι απαντήσεις βασίζονται στην ανάλυση των αρχείων:

- [DAL/extremexp-dal-main/server/routes/api/experiments.js](../../DAL/extremexp-dal-main/server/routes/api/experiments.js)
- [DAL/extremexp-dal-main/server/routes/api/workflows.js](../../DAL/extremexp-dal-main/server/routes/api/workflows.js)
- [DAL/extremexp-dal-main/server/routes/api/metrics.js](../../DAL/extremexp-dal-main/server/routes/api/metrics.js)
- [DAL/extremexp-dal-main/server/routes/api/util.js](../../DAL/extremexp-dal-main/server/routes/api/util.js)
- [exp_engine/.../data_abstraction_api.py](../exp_engine/src/eexp_engine/data_abstraction_layer/data_abstraction_api.py)

---

## PROMPT SET 1: DATABASE SCHEMA

### 1A: Nullable fields

**Validation in code:** Το DAL χρησιμοποιεί μόνο `validateSchema(body, SCHEMA)` από util.js. Η `validateSchema` ελέγχει μόνο **τι υπάρχει στο body**: αν ένα key υπάρχει, ελέγχει το type. Δεν απαιτεί την παρουσία συγκεκριμένων keys. Το `REQUIRED_FIELDS` στα experiments (name, intent) και workflows (name, start, end) **δεν καλείται πουθενά** στα route handlers.

| Field                  | Required in route? | Evidence                                                                                                   | PostgreSQL suggestion                                                             |
| ---------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **experiments.intent** | NO                 | Μόνο `validateSchema(body, EXPERIMENTS_SCHEMA)`· δεν καλείται `validateRequiredFields`.                    | `NULL` allowed                                                                    |
| **experiments.start**  | NO                 | Ίδιο.                                                                                                      | `NULL` allowed                                                                    |
| **experiments.end**    | NO                 | Ίδιο.                                                                                                      | `NULL` allowed                                                                    |
| **experiments.model**  | NO                 | Ίδιο.                                                                                                      | `NULL` allowed                                                                    |
| **PUT /experiments**   | -                  | Body μπορεί να έχει id (χρησιμοποιείται ως `elasticsearch.index(..., id: body.id)`). Τα υπόλοιπα optional. | Όλα nullable εκτός αν το Engine πάντα στέλνει name/intent                         |
| **workflows.start**    | NO                 | `validatePayload(body)` = `validateSchema(body, WORKFLOW_SCHEMA)`. Δεν καλείται `validateRequiredFields`.  | `NULL` allowed (αν θέλεις strict: NOT NULL για create)                            |
| **workflows.end**      | NO                 | Ίδιο.                                                                                                      | `NULL` allowed                                                                    |
| **PUT /workflows**     | -                  | Schema έχει name, start, end· κανένα required check.                                                       | name NOT NULL λογικό· start/end nullable ή NOT NULL αν το Engine πάντα τα στέλνει |

**Συμπέρασμα:** Για ακριβή συμβατότητα με το τρέχον DAL, όλα τα παραπάνω μπορούν nullable. Για πιο strict API, το νέο DAL μπορεί να απαιτεί `name` (+ `intent` για experiments) και να κάνει `start`/`end` NOT NULL μόνο αν το contract το ορίζει.

---

### 1B: Embedded vs separate data (workflows)

**Parameters, tasks, input_datasets, output_datasets:** Ενσωματωμένα (embedded) στο workflow document.

- workflows.js γραμμές 136–139:

```javascript
const response = await elasticsearch.index({
    index: 'workflows',
    body   // body περιέχει tasks, parameters, input_datasets, output_datasets, metrics, ...
});
```

- Το `body` έρχεται από το request και γράφεται ολόκληρο στο index `workflows`. Δεν υπάρχει `elasticsearch.index({ index: 'parameters', ... })` ή ξεχωριστό index για tasks/datasets.

**Metrics:** Ξεχωριστά documents στο index `metrics`, και το workflow ενημερώνεται με `metric_ids` + embedded array `metrics`.

- Γραμμές 168–202: αν το body έχει `metrics`, για κάθε metric γίνεται `createSubIndex(metric, 'metrics', 'workflow', response._id, ...)` που κάνει `elasticsearch.index({ index: 'metrics', body: {...} })`. Στη συνέχεια `elasticsearch.update` στο workflow με `doc: { metric_ids: metricIDs, metrics: metrics }`.

**Συμπέρασμα για PostgreSQL:** Για workflow document equivalence: **parameters, tasks, input_datasets, output_datasets** = JSONB (ή πίνακες) μέσα στο `workflows` row. **Metrics** = ξεχωριστό πίνακας `metrics` με FK στο workflow, και optional denormalized snapshot (π.χ. `metric_ids`, `metrics` JSONB) στο workflow αν χρειάζεται ίδιο response shape με το ES.

---

### 1C: Metric records & aggregations

**1–2. Πού αποθηκεύονται τα records; Μορφή;**

- metrics.js γραμμές 176–202 (PUT /metrics-data/:metricId):

```javascript
const data = (existingMetric._source.hasOwnProperty("records")) ? existingMetric._source.records : [];
for (let dataObject of body.records) {
    data.push(dataObject);
}
const response = await elasticsearch.update({
    index: 'metrics',
    id: metricId,
    body: { doc: { records: data } }
});
```

- Records = **array μέσα στο metric document** (όχι ξεχωριστό index). Στο PostgreSQL: `records JSONB` στο `metrics` table ή ξεχωριστό `metric_records` αν θέλεις normalize.

**3. Όριο αριθμού records;** Δεν υπάρχει check στο code.

**4–5. Aggregations:** util.js γραμμές 72–131.

- `calculateMedian`: sort array by `item.value`, μέσο (ή average των δύο μεσαίων).
- `calculateSum`, `calculateMin`, `calculateMax`, `calculateAverage`, `calculateCount`: απλά reduce/map πάνω στο `metricResponse._source.records`.
- `aggregatieMetric(metricResponse)` επιστρέφει `{ count, average, sum, min, max, median }` **μόνο αν** το document έχει `records`.
- Κλήση: **on read** — σε GET /metrics/:id (metrics.js 111–115) και GET workflow (workflows.js 322–324) όταν φορτώνονται τα metrics. Δεν γίνονται on write ούτε cache. Στο PostgreSQL: είτε υπολογισμός on-the-fly από `records`, είτε materialized/cached πίνακας `metric_aggregations` που ενημερώνεται on write ή με job.

---

## PROMPT SET 2: ENGINE CLIENT

### 2A: Endpoints που καλεί το Engine

| Method              | HTTP | Endpoint              | Request body                                               | Expected response                               |
| ------------------- | ---- | --------------------- | ---------------------------------------------------------- | ----------------------------------------------- |
| get_all_experiments | GET  | /executed-experiments | -                                                          | `r.json().get('executed_experiments', [])`      |
| create_experiment   | PUT  | /experiments          | {name, intent, ...}                                        | `201`, `message.experimentId`                   |
| get_experiment      | GET  | /experiments/{id}     | -                                                          | `experiment`                                    |
| update_experiment   | POST | /experiments/{id}     | body                                                       | -                                               |
| query_experiments   | POST | /experiments-query    | e.g. {creator: {name: username}}                           | array (current Engine uses as experiments list) |
| create_workflow     | PUT  | /workflows            | {experimentId, name, start, end, tasks, ...}               | `201`, `workflow_id`                            |
| get_workflow        | GET  | /workflows/{id}       | -                                                          | `workflow` (full doc + metrics με aggregation)  |
| update_workflow     | POST | /workflows/{id}       | body                                                       | -                                               |
| create_metric       | PUT  | /metrics              | {name, producedByTask, type, kind, parent_id, parent_type} | `201`                                           |
| update_metric       | POST | /metrics/{id}         | e.g. {value}                                               | -                                               |
| add_value_to_metric | -    | (uses update_metric)  | {value}                                                    | -                                               |
| add_data_to_metric  | PUT  | /metrics-data/{id}    | {records: [{value: d}, ...]}                                | -                                               |

- **/executed-experiments:** Το Engine καλεί **GET /executed-experiments** και περιμένει key **`executed_experiments`**. Στο τρέχον DAL **δεν υπάρχει** αυτό το endpoint· υπάρχει μόνο GET /experiments (paginated, key `experiments`). Το νέο Python DAL **πρέπει** να εκθέτει GET /executed-experiments που επιστρέφει `{ executed_experiments: [...] }` (ή ισοδύναμο) για συμβατότητα.

---

### 2B: Authentication

- data_abstraction_api.py γραμμή 14:

```python
self._headers = {'access-token': config.DATA_ABSTRACTION_ACCESS_TOKEN}
```

- Όλες οι κλήσεις περνούν το ίδιο header. **Μόνο `access-token`**· όχι `Authorization: Bearer`. Το νέο DAL πρέπει να δέχεται και να επαληθεύει το `access-token` header.

---

### 2C: Query patterns (αναζήτηση workflows/tasks/datasets)

- **Workflows by parameter values:** Δεν υπάρχει κλήση. Το Engine παίρνει workflow by ID και διασχίζει embedded data.
- **Tasks ανεξάρτητα (by name/status):** Δεν υπάρχει. Tasks έρχονται μέσα στο `workflow.tasks`.
- **Datasets by title/checksum:** Δεν υπάρχει. Datasets έρχονται μέσα στα tasks (input_datasets, output_datasets).

Το Engine κάνει μόνο: create experiment/workflow/metric, get experiment/workflow by ID (full doc), update experiment/workflow status/body, update metric / add metric data. **Normalized πίνακες για search tasks/datasets/parameters δεν απαιτούνται για το Engine.** JSONB (ή arrays) μέσα στο workflow document είναι αρκετά.

---

## PROMPT SET 3: API CONTRACT

### 3A: Response formats (create endpoints)

- **PUT /experiments:** experiments.js:47 — `res.status(201).json({ message: { experimentId: response._id } })` (Σημ.: στο code είναι `response._id`· αν στέλνεται `body.id`, το ES μπορεί να χρησιμοποιεί αυτό.)
- **PUT /workflows:** workflows.js:210 — `res.status(201).json({ workflow_id: response._id })`
- **PUT /metrics:** metrics.js:88 — `res.status(201).json({ metric_id: response._id })`

Άρα: `experimentId` μέσα σε `message`, `workflow_id` και `metric_id` top-level. Το Engine περιμένει ακριβώς αυτά (message.experimentId, workflow_id)· για metric δεν διαβάζει το response id από create.

---

### 3B: Missing endpoint /executed-experiments

- **Υπάρχει /executed-experiments στο DAL;** Όχι. Στο experiments.js υπάρχει μόνο GET /experiments (paginated, key `experiments`).
- **Γιατί το Engine καλεί /executed-experiments;** Το contract του Engine (και πιθανόν η τεκμηρίωση) ορίζει λίστα "executed experiments" με ένα endpoint. Το τρέχον DAL το εξυπηρετεί με άλλο path/format.
- **Προτεινόμενο για νέο DAL:** Νέο endpoint GET /executed-experiments που επιστρέφει `{ executed_experiments: [ ... ] }` (π.χ. όλα τα experiments χωρίς pagination ή με ίδιο format που χρειάζεται το Engine), ώστε το Engine να δουλεύει χωρίς αλλαγές.

---

## PROMPT SET 4: BUSINESS LOGIC

### 4A: DSL parsing (DMS)

- experiments.js:182–189: Στο GET /experiments/:id, αν υπάρχει `experiment._source.model` και `process.env.DMS_PATH`, καλείται `execSync(\`bash ${process.env.DMS_PATH}/run.sh '${experiment._source.model}'\`)` και το stdout parse-άρεται ως JSON → `modelJSON`. Αυτό επιστρέφεται στο response ως `modelJSON`.
- Αν DMS_PATH δεν είναι set: δεν καλείται script· `modelJSON` μένει undefined (στο response απλά δεν υπάρχει ή null).
- Το Engine: δεν βρέθηκε χρήση του `modelJSON` στο code (αναζήτηση "modelJSON"). Επομένως για το Engine δεν είναι κρίσιμο· για visualization/IDE μπορεί να χρησιμοποιείται.

---

### 4B: Aggregation logic

- Όπως 1C: στο util.js — `calculateMedian` (sort + middle), `calculateSum/Min/Max/Average/Count`, `aggregatieMetric` που επιστρέφει count, average, sum, min, max, median. Κλήση **on read** (GET metric, GET workflow). Σύγχρονο. Median = ακριβές (sort, pick middle).

---

### 4C: Workflow sorting (experiments-sort-workflows)

- experiments.js:251–265:
  - **Read:** `experimentResponse._source.workflow_ids`
  - **Write:** `doc: { "workflows": workflowIdList }`  
  Δηλαδή η ταξινομημένη λίστα γράφεται στο field **`workflows`**, ενώ το rest του συστήματος (π.χ. PUT /workflows που προσθέτει workflow στο experiment) χρησιμοποιεί **`workflow_ids`**. Αποτέλεσμα: το sort αλλάζει άλλο field και η "κανονική" λίστα παραμένει στο `workflow_ids`. **Bug:** read από `workflow_ids`, write στο `workflows`.
- **Συμβατότητα για νέο DAL:** Να χρησιμοποιείται **ένα** field (π.χ. `workflow_ids`) και για read και για write στο sort endpoint, ώστε η σειρά να είναι συνεπής.

---

## PROMPT SET 5: DEPLOYMENT & OPERATIONS

### 5A: Authentication (τρέχον DAL)

- Η αναζήτηση στα routes (experiments/workflows/metrics) δεν έδειξε middleware που να ελέγχει access-token. Το authentication πιθανόν γίνεται σε επίπεδο ivis-core ή reverse proxy. Για το νέο Python DAL, το DAL.mdc ορίζει access-token/Bearer και JWT validation· αυτό πρέπει να υλοποιηθεί στο νέο service.

### 5B: Test data

- Δεν ελέχθηκαν συστηματικά fixtures· συνήθως demo data θα έρχεται από το Engine (run experiment) ή από υπαρκτά repositories (playground, examples). Χρήσιμο να οριστεί ένα minimal experiment/workflow/metric JSON σύμφωνα με τα schemas των routes για tests.

### 5C: Configuration

- DAL: config από env (π.χ. DMS_PATH, ES, DB). Docker Compose: services (expvis, mariadb, elasticsearch), ports, env.
- Engine: eexp_config_TEMPLATE.py — `DATA_ABSTRACTION_BASE_URL`, `DATA_ABSTRACTION_ACCESS_TOKEN`. Το νέο DAL πρέπει να δέχεται τα ίδια env για URL και token.

---

## Σύνοψη για implementation

1. **Schema (PostgreSQL):** Experiments/workflows με nullable πεδία όπως πάνω· workflows με embedded parameters/tasks/input_datasets/output_datasets (JSONB/arrays). Metrics ξεχωριστά πίνακας· records είτε JSONB στο metric είτε πίνακας metric_records. Aggregations on read (ή cached table).
2. **API contract:** Υλοποίηση GET /executed-experiments → `{ executed_experiments: [...] }`· response keys για create: message.experimentId, workflow_id, metric_id.
3. **Auth:** Header `access-token` υποχρεωτικό για συμβατότητα με Engine.
4. **Fix:** experiments-sort-workflows να γράφει (και να διαβάζει) το ίδιο field με το υπόλοιπο σύστημα (workflow_ids).
