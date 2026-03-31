# PostgreSQL Database Schema – Python DAL

Αυτό το έγγραφο περιγράφει το πλήρες σχήμα βάσης PostgreSQL για το νέο Python DAL (Data Abstraction Layer), ευθυγραμμισμένο με τη δομή των εγγράφων Elasticsearch του υπάρχοντος Node.js DAL ώστε να μην χαθούν δεδομένα σε μελλοντική μετάβαση.

**Production-ready executable schema:** Το πλήρες DDL script βρίσκεται στο [database_schema.sql](database_schema.sql). Χρησιμοποιείται για `psql -f` ή ως πηγή για το πρώτο Alembic migration.

---

## 1. Core entities – CREATE TABLE

Production schema: όλα nullable στα experiments (σύμφωνα με validation του τρέχοντος DAL)· workflows με μόνο `name` NOT NULL· `tasks` ως JSONB (embedded, όχι ξεχωριστός πίνακας). Reserved keyword `end` ως `"end"`.

### 1.1 Experiments

```sql
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    intent TEXT,
    start TIMESTAMPTZ,
    "end" TIMESTAMPTZ,
    model TEXT,
    comment TEXT,
    status TEXT DEFAULT 'new',
    metadata JSONB DEFAULT '{}',
    creator JSONB DEFAULT '{}',
    workflow_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
-- Indexes: status, created_at DESC, GIN(metadata), GIN(creator)
```

### 1.2 Workflows

```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    start TIMESTAMPTZ,
    "end" TIMESTAMPTZ,
    comment TEXT,
    status TEXT DEFAULT 'scheduled',
    parameters JSONB DEFAULT '[]',
    tasks JSONB DEFAULT '[]',
    input_datasets JSONB DEFAULT '[]',
    output_datasets JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    metric_ids UUID[] DEFAULT '{}',
    metrics JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
-- Indexes: experiment_id, status, created_at, (start, "end"), GIN(metadata)
```

### 1.3 Metrics

`parent_id` μπορεί να δείχνει σε `workflows(id)` ή `experiments(id)`. Η referential integrity επιβάλλεται από την εφαρμογή (ή με trigger).

```sql
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    parent_type TEXT NOT NULL CHECK (parent_type IN ('workflow', 'experiment')),
    parent_id UUID NOT NULL,
    name TEXT,
    kind TEXT,
    type TEXT,
    semantic_type TEXT,
    value TEXT,
    produced_by_task TEXT,
    date TIMESTAMPTZ,
    records JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
-- Indexes: experiment_id, (parent_type, parent_id), kind, name, semantic_type
```

---

## 2. Column mapping (Elasticsearch → PostgreSQL)

### Experiments

| Elasticsearch field | PostgreSQL column | Σημειώσεις |
|---------------------|-------------------|------------|
| `_id` | `id` | UUID; το client μπορεί να στείλει `id` στο body → χρήση ως PK στο insert |
| `name` | `name` | TEXT |
| `intent` | `intent` | TEXT |
| `start` | `start` | ISO string → TIMESTAMPTZ |
| `end` | `end` | TIMESTAMPTZ |
| `status` | `status` | default `'new'` |
| `comment` | `comment` | TEXT |
| `model` | `model` | TEXT |
| `metadata` | `metadata` | object → JSONB |
| `creator` | `creator` | object → JSONB |
| `workflow_ids` | `workflow_ids` | array of strings → UUID[] |

### Workflows

| Elasticsearch field | PostgreSQL column | Σημειώσεις |
|---------------------|-------------------|------------|
| `_id` | `id` | UUID (API επιστρέφει ως `workflow_id`) |
| `experimentId` | `experiment_id` | FK → experiments(id) |
| `name`, `start`, `end` | id. | start/end → TIMESTAMPTZ |
| `status` | `status` | default `'scheduled'` |
| `comment`, `metadata` | id. | metadata → JSONB |
| `parameters` | `parameters` | array of objects → JSONB |
| `input_datasets` | `input_datasets` | array → JSONB |
| `output_datasets` | `output_datasets` | array → JSONB |
| `tasks` | `tasks` | array of task objects → JSONB (embedded, no separate table) |
| `metric_ids` | `metric_ids` | array → UUID[] |
| `metrics` | `metrics` | denormalized metric objects → JSONB (προαιρετικό cache) |

### Metrics

| Elasticsearch field | PostgreSQL column | Σημειώσεις |
|---------------------|-------------------|------------|
| `_id` | `id` | UUID (API: `metric_id`) |
| `experimentId` | `experiment_id` | FK, resolved από parent |
| `parent_type`, `parent_id` | `parent_type`, `parent_id` | parent_id = workflow ή experiment id |
| `name`, `semantic_type`, `kind`, `type`, `value` | id. | value TEXT |
| `producedByTask` | `produced_by_task` | snake_case |
| `date` | `date` | TIMESTAMPTZ |
| `records` | `records` | array of `{value}` → JSONB; ή πίνακας `metric_records` |

---

## 3. Supporting tables

Στο production schema χρησιμοποιούνται μόνο οι πίνακες `metric_records` και `metric_aggregations`. Τα parameters, tasks, input_datasets, output_datasets είναι embedded ως JSONB στο `workflows` (όπως στο Elasticsearch).

### 3.1 metric_records (series/timeseries)

Για μεγάλα series ή analytics: normalize εγγραφών από το `metrics.records` JSONB.

```sql
CREATE TABLE metric_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_id UUID NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
    value DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
-- Indexes: metric_id, (metric_id, created_at), (metric_id, timestamp)
```

### 3.2 metric_aggregations (computed)

Αντιστοιχεί στα aggregations του `util.js` (count, sum, min, max, average, median). Cached on write.

```sql
CREATE TABLE metric_aggregations (
    metric_id UUID PRIMARY KEY REFERENCES metrics(id) ON DELETE CASCADE,
    count BIGINT NOT NULL DEFAULT 0,
    sum DOUBLE PRECISION,
    min DOUBLE PRECISION,
    max DOUBLE PRECISION,
    average DOUBLE PRECISION,
    median DOUBLE PRECISION,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### Εναλλακτική: κανονικοποιημένα tables (optional)

Για μελλοντική χρήση μπορεί να προστεθούν ξεχωριστά tables `tasks`, `parameters`, `input_datasets`, `output_datasets` με FK στο workflow. Το τρέχον production schema τα κρατά embedded ως JSONB ώστε να ταιριάζει ακριβώς με τη δομή Elasticsearch.

---

## 4. Relationships και DELETE behavior

| Σχέση | Τύπος | FK | ON DELETE |
|-------|--------|-----|-----------|
| experiments → workflows | 1-to-many | `workflows.experiment_id` | CASCADE |
| experiments → metrics | 1-to-many | `metrics.experiment_id` | CASCADE |
| workflows → metrics | 1-to-many | `metrics.parent_id` (όταν parent_type='workflow') | (application-enforced) |
| metrics → metric_records | 1-to-many | `metric_records.metric_id` | CASCADE |
| metrics → metric_aggregations | 1-to-1 | `metric_aggregations.metric_id` | CASCADE |

Διαγραφή experiment → CASCADE διαγράφονται workflows και metrics. Διαγραφή workflow → τα metrics με parent_type='workflow' και parent_id το workflow πρέπει να διαχειριστούν από την εφαρμογή (ή trigger). Parameters, tasks, input/output datasets είναι JSONB μέσα στο workflow και διαγράφονται με το workflow.

---

## 5. Index strategy

| Πίνακας | Index | Λόγος |
|---------|--------|--------|
| experiments | `status` | Φιλτράρισμα κατά status |
| experiments | `created_at DESC` | Σελιδοποίηση / listing |
| experiments | `metadata` GIN | experiments-query κατά metadata |
| experiments | `creator` GIN | experiments-query κατά creator |
| workflows | `experiment_id` | workflows-query κατά experimentId |
| workflows | `status` | workflows-query κατά status |
| workflows | `(start, "end")` | workflows-query range |
| workflows | `metadata` GIN | workflows-query metadata |
| workflows | `created_at DESC` | listing |
| metrics | `experiment_id` | metrics-query, experiments-metrics |
| metrics | `(parent_type, parent_id)` | Ανάκτηση metrics κατά parent |
| metrics | `kind`, `name`, `semantic_type` | metrics-query |
| metric_records | `metric_id`, `(metric_id, created_at)`, `(metric_id, timestamp)` | Series/aggregation ανά metric |
| metric_aggregations | (PK only) | Lookup by metric_id |

---

## 6. Executable SQL (Alembic-ready)

Το πλήρες production-ready script βρίσκεται στο **[database_schema.sql](database_schema.sql)**. Μπορεί να εκτελεστεί με `psql -f database_schema.sql` ή να αντιγραφεί στο πρώτο Alembic migration.

**Triggers:** PostgreSQL 11+ χρησιμοποιεί `EXECUTE FUNCTION update_updated_at();`. Για PostgreSQL &lt; 11 αντικαταστήστε με `EXECUTE PROCEDURE update_updated_at();`.

---

## 7. Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    experiments ||--o{ workflows : "has many"
    experiments ||--o{ metrics : "has many"
    workflows ||--o{ metrics : "parent_id"
    metrics ||--o{ metric_records : "series"
    metrics ||--o| metric_aggregations : "computed"

    experiments {
        uuid id PK
        text name
        text intent
        timestamptz start
        timestamptz end_ts "end"
        text status
        jsonb metadata
        jsonb creator
        uuid_array workflow_ids
        timestamptz created_at
        timestamptz updated_at
    }

    workflows {
        uuid id PK
        uuid experiment_id FK
        text name
        timestamptz start
        timestamptz end_ts "end"
        text status
        jsonb parameters
        jsonb tasks
        jsonb input_datasets
        jsonb output_datasets
        uuid_array metric_ids
        jsonb metrics
        timestamptz created_at
        timestamptz updated_at
    }

    metrics {
        uuid id PK
        uuid experiment_id FK
        text parent_type
        uuid parent_id
        text name
        text kind
        text type
        text value
        jsonb records
        timestamptz created_at
        timestamptz updated_at
    }

    metric_records {
        uuid id PK
        uuid metric_id FK
        double value
        timestamptz timestamp
        timestamptz created_at
    }

    metric_aggregations {
        uuid metric_id PK_FK
        bigint count
        double sum
        double min
        double max
        double average
        double median
        timestamptz updated_at
    }
```

---

## 8. Migration notes (no data loss)

- **Client-provided IDs:** Τα experiments επιτρέπουν `body.id`· στο insert χρησιμοποιήστε αυτό το UUID αν δίνεται ώστε το API να επιστρέφει το ίδιο `experimentId`. Αντίστοιχα για workflows και metrics.
- **workflow_ids:** Κατά τη δημιουργία workflow, προσάρτηση του `id` του στο `experiments.workflow_ids` στην ίδια transaction.
- **metric_ids:** Κατά τη δημιουργία metric, προσάρτηση του `id` στο parent (`workflows.metric_ids` ή experiments αν υπάρχει αντίστοιχο πεδίο) στην ίδια transaction.
- **records:** Το πεδίο `metrics.records` παραμένει JSONB· στο `PUT /metrics-data/:id` γίνεται append (concat) του νέου array. Προαιρετικά μπορεί να γίνεται συγχρονισμός και στο `metric_records` για analytics.
- **Aggregations:** Οι τιμές count/sum/min/max/avg/median υπολογίζονται από `metrics.records` (ή από `metric_records`) κατά το GET metric ή POST experiments-metrics· ή να materialize στο `metric_aggregations` με trigger ή periodic job.
