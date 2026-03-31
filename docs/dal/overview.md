# DAL Overview (NEW DAL)

## Purpose

The NEW Data Abstraction Layer (DAL) is the persistence and query API used by ExpEngine for:

- experiment metadata
- workflow metadata and execution statuses
- metrics and metric records

It provides a consistent API surface over a PostgreSQL backend so downstream consumers can read stable execution results.

## Architecture

```mermaid
flowchart LR
  ExpEngine[ExpEngine]
  ExecutionWare[ExecutionWare]
  ProActive[ProActive]
  DalApi[DAL API FastAPI]
  PostgreSQL[(PostgreSQL)]

  ExpEngine -->|"PUT/GET/POST /api/*"| DalApi
  ExpEngine --> ExecutionWare
  ExecutionWare --> ProActive
  DalApi -->|"SQLAlchemy"| PostgreSQL
```

## Runtime flow

```mermaid
flowchart TD
  Start[Experiment starts]
  CreateExperiment["Create experiment (PUT /api/experiments)"]
  CreateWorkflow["Create workflows (PUT /api/workflows)"]
  RunTasks[ExecutionWare runs tasks]
  CreateMetric["Create metrics (PUT /api/metrics)"]
  WriteMetricData["Write records (PUT /api/metrics-data/{metricId})"]
  FinalizeStatus["Update final workflow/experiment status"]
  QueryResults["Read results (GET/POST query endpoints)"]

  Start --> CreateExperiment
  CreateExperiment --> CreateWorkflow
  CreateWorkflow --> RunTasks
  RunTasks --> CreateMetric
  CreateMetric --> WriteMetricData
  WriteMetricData --> FinalizeStatus
  FinalizeStatus --> QueryResults
```

## Core ER Diagram

```mermaid
erDiagram
  EXPERIMENT ||--o{ WORKFLOW : contains
  EXPERIMENT ||--o{ METRIC : has
  WORKFLOW ||--o{ METRIC : has
  METRIC ||--o{ METRIC_RECORD : stores

  EXPERIMENT {
    uuid id PK
    string name
    string status
    datetime created_at
    datetime updated_at
  }

  WORKFLOW {
    uuid id PK
    uuid experiment_id FK
    string status
    datetime created_at
    datetime updated_at
  }

  METRIC {
    uuid id PK
    uuid experiment_id FK
    uuid workflow_id FK
    string name
    string metric_type
    datetime created_at
  }

  METRIC_RECORD {
    uuid id PK
    uuid metric_id FK
    float value
    datetime timestamp
  }
```
