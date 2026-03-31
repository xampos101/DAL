# DAL Architecture Diagrams

Architecture reference for the ExtremeXP Data Abstraction Layer (FastAPI + PostgreSQL).
All diagrams are Mermaid-compatible and can be rendered in GitHub/Cursor.

---

## A. System Context

```mermaid
flowchart TB
  subgraph external [External Clients]
    ExpEngine[ExperimentationEngine]
    Scripts[ScriptsAndOtherClients]
  end

  subgraph dalSvc [DAL Service]
    FastAPI[FastAPIUvicorn]
  end

  subgraph persistence [Persistence]
    Postgres[(PostgreSQL)]
  end

  ExpEngine -->|"REST JSON + access-token"| FastAPI
  Scripts -->|"REST JSON"| FastAPI
  FastAPI -->|"asyncpg over TCP 5432"| Postgres
```

## B. Runtime Container View

```mermaid
flowchart LR
  subgraph app [DAL Runtime]
    Uvicorn[UvicornASGIServer]
    ApiApp[FastAPIApp]
    Uvicorn --> ApiApp
  end

  Client[HttpClients] <-->|HTTP| Uvicorn
  ApiApp <-->|Async SQLAlchemy| DB[(PostgreSQLCluster)]
```

## C. Internal Components

```mermaid
flowchart TB
  Main[main.py] --> ExpRouter[routers/experiments.py]
  Main --> WfRouter[routers/workflows.py]
  Main --> MetricRouter[routers/metrics.py]
  Main --> QueryRouter[routers/queries.py]
  Main --> HealthRouter[routers/health.py]

  ExpRouter --> Deps[deps.py]
  WfRouter --> Deps
  MetricRouter --> Deps
  QueryRouter --> Deps

  ExpRouter --> Session[db/session.py]
  WfRouter --> Session
  MetricRouter --> Session
  QueryRouter --> Session

  ExpRouter --> Models[models/*]
  WfRouter --> Models
  MetricRouter --> Models
  QueryRouter --> Models

  ExpRouter --> Schemas[schemas/*]
  WfRouter --> Schemas
  MetricRouter --> Schemas
  QueryRouter --> Schemas
```

## D. API Registration (`/api` prefix)

```mermaid
flowchart TB
  App[FastAPIApp]
  App -->|"include health router"| R1[health]
  App -->|"include experiments router"| R2[experiments]
  App -->|"include executed experiments router"| R3[executed_experiments]
  App -->|"include workflows router"| R4[workflows]
  App -->|"include metrics router"| R5[metrics]
  App -->|"include metrics data router"| R6[metrics_data]
  App -->|"include queries router"| R7[queries]
```

## E. Logical Entity Model

```mermaid
erDiagram
  EXPERIMENTS ||--o{ WORKFLOWS : contains
  EXPERIMENTS ||--o{ METRICS : scopes
  WORKFLOWS ||--o{ METRICS : scopes
  METRICS ||--o{ METRIC_RECORDS : has
  METRICS ||--o| METRIC_AGGREGATIONS : has
```

## F. Write Sequence (Create Endpoint)

```mermaid
sequenceDiagram
  actor Client
  participant Router
  participant Auth as AccessTokenDependency
  participant Session as AsyncSession
  participant DB as PostgreSQL

  Client->>Router: PUT JSON request
  Router->>Auth: validate access-token
  Auth-->>Router: allow or 401
  Router->>Session: create or update entity
  Session->>DB: SQL statements
  DB-->>Session: rows
  Session-->>Router: ORM objects
  Router-->>Client: JSON response
```

## G. Read Sequence (Safe Model Validation)

```mermaid
sequenceDiagram
  participant Client
  participant Router
  participant Session as AsyncSession
  participant ORMRow as ORMInstance
  participant Mapper as orm_columns_dict
  participant Pydantic as PydanticModel

  Client->>Router: GET with access-token
  Router->>Session: SELECT query
  Session-->>ORMRow: ORM instance
  Router->>Mapper: extract mapped columns
  Mapper-->>Pydantic: plain dict
  Pydantic-->>Router: validated response model
  Router-->>Client: JSON response
```
