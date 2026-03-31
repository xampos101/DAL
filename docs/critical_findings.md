# Critical findings – DAL re-implementation

Σύντομη σύνοψη κρίσιμων ευρημάτων και αποφάσεων για το νέο Python DAL. Λεπτομέρειες και evidence: [DAL_CRITICAL_QUESTIONS_ANSWERS.md](DAL_CRITICAL_QUESTIONS_ANSWERS.md).

---

## 1. Missing endpoint (CRITICAL)

- **Πρόβλημα:** Το Experimentation Engine καλεί **GET /executed-experiments** και περιμένει response key **`executed_experiments`** (array). Το τρέχον Node.js DAL εκθέτει μόνο **GET /experiments** (paginated, key `experiments`).
- **Επιπτώσεις:** Χωρίς αυτό το endpoint το Engine δεν μπορεί να λάβει τη λίστα experiments όπως την περιμένει.
- **Λύση:** Το νέο DAL **πρέπει** να έχει endpoint **GET /api/executed-experiments** που επιστρέφει `{"executed_experiments": [...]}` (π.χ. όλα τα experiments ή ίδιο format με το Engine).

---

## 2. Workflow sorting bug

- **Πρόβλημα:** Στο τρέχον DAL, το endpoint **POST /experiments-sort-workflows/{experimentId}** διαβάζει από **`workflow_ids`** αλλά γράφει την ταξινομημένη λίστα στο field **`workflows`**. Τα υπόλοιπα endpoints (π.χ. create workflow) ενημερώνουν το **`workflow_ids`**. Αποτέλεσμα: ασυνέπεια· η σειρά δεν αντικατοπτίζεται στο field που χρησιμοποιείται παντού.
- **Λύση:** Στο νέο DAL να χρησιμοποιείται **ένα** field (**`workflow_ids`**) και για read και για write στο sort endpoint.

---

## 3. Nullable fields (evidence-based)

- **Evidence:** Στο Node.js DAL δεν καλείται `validateRequiredFields`· μόνο `validateSchema(body, SCHEMA)` που ελέγχει τύπους για keys που **υπάρχουν**. Δεν απαιτείται παρουσία συγκεκριμένων keys.
- **Απόφαση:** Στο production PostgreSQL schema όλα τα πεδία experiments (name, intent, start, end, model, κ.λπ.) είναι **nullable**. Στα workflows μόνο **`name`** NOT NULL· start/end nullable. Ακριβής συμβατότητα με τρέχον DAL.

---

## 4. Embedded data (JSONB-only για workflows)

- **Evidence:** Στο Elasticsearch το workflow document περιέχει parameters, tasks, input_datasets, output_datasets ως **embedded** arrays/objects. Δεν υπάρχουν ξεχωριστά indices για αυτά.
- **Απόφαση:** Στο νέο schema τα **parameters, tasks, input_datasets, output_datasets** είναι **JSONB** columns στο πίνακα **workflows** (όχι ξεχωριστά tables). Metrics παραμένουν ξεχωριστός πίνακας με FK και optional denormalized cache στο workflow (`metric_ids`, `metrics` JSONB).

---

## 5. Authentication

- **Evidence:** Το Engine στέλνει header **`access-token`** σε όλες τις κλήσεις (data_abstraction_api.py). Δεν χρησιμοποιεί `Authorization: Bearer`.
- **Απόφαση:** Το νέο DAL **πρέπει** να δέχεται και να επαληθεύει το **`access-token`** header. Optional: υποστήριξη και για `Authorization: Bearer` για συμβατότητα με τεκμηρίωση/OpenAPI.

---

## 6. Response formats (create endpoints)

- **PUT /experiments:** `201`, body **`{ "message": { "experimentId": "<uuid>" } }`**
- **PUT /workflows:** `201`, body **`{ "workflow_id": "<uuid>" }`**
- **PUT /metrics:** `201`, body **`{ "metric_id": "<uuid>" }`**

Το Engine βασίζεται σε `message.experimentId` και `workflow_id`. Τα response shapes πρέπει να ταιριάζουν ακριβώς.

---

## 7. Metric records and aggregations

- **Records:** Στο τρέχον DAL αποθηκεύονται ως array **μέσα** στο metric document. Στο νέο schema: **metrics.records** JSONB + optional πίνακας **metric_records** για μεγάλα series (performance).
- **Aggregations:** Υπολογίζονται **on read** (count, sum, min, max, average, median). Στο νέο DAL: είτε on-the-fly από records είτε materialized/cached πίνακας **metric_aggregations** που ενημερώνεται on write.

---

## 8. DSL / modelJSON (low priority)

- **Evidence:** Το Engine δεν χρησιμοποιεί το `modelJSON` (αναζήτηση στο code). Το τρέχον DAL καλεί DMS script για να μετατρέψει το DSL (`model`) σε JSON όταν υπάρχει `DMS_PATH`.
- **Απόφαση:** Phase 1 μπορεί να επιστρέφει **modelJSON: null**. Phase 2+: optional υλοποίηση DSL→JSON αν χρειάζεται για visualization/IDE.

---

## References

- [DAL_CRITICAL_QUESTIONS_ANSWERS.md](DAL_CRITICAL_QUESTIONS_ANSWERS.md) – πλήρης ανάλυση και πίνακες
- [DAL_OVERVIEW_AND_API_CONTRACT.md](DAL_OVERVIEW_AND_API_CONTRACT.md) – architecture και API contract
- [database_schema.sql](database_schema.sql) – production schema που αντικατοπτρίζει τις παραπάνω αποφάσεις
