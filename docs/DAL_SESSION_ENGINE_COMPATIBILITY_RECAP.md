# DAL Session Recap - Engine Compatibility

## Scope of this session

This session focused on making the Python DAL implementation compatible with the current ExtremeXP Engine client behavior and with legacy DAL request/response expectations where needed.

## What was implemented

### 1) Query endpoints aligned to Engine/legacy behavior

- Updated query endpoints:
  - `POST /api/experiments-query`
  - `POST /api/workflows-query`
  - `POST /api/metrics-query`
- Response shape changed to bare list `[...]` (no wrapper object) for compatibility.
- Legacy filter behavior implemented:
  - plain body dict
  - scalar equality filters
  - JSONB contains for nested objects (e.g. `creator`, `metadata`)
  - unknown keys ignored (no 400)
  - empty body returns all

### 2) Engine compatibility endpoint added

- Added `GET /api/executed-experiments`
- Response shape:
  - `{ "executed_experiments": [ ... ] }`

### 3) CamelCase request compatibility

- Added compatibility for Engine-style request keys:
  - `experimentId` alias for workflow create payloads
  - `producedByTask` alias for metric payloads

### 4) Metrics data ingestion endpoint added

- Added `PUT /api/metrics-data/{metric_id}`
- Accepts:
  - `{ "records": [ { "value": <number> }, ... ] }`
- Inserts records into `metric_records`
- Returns:
  - `{ "message": "ok", "inserted": <n> }`

### 5) Critical metric creation fix

The Engine creates metrics without `experiment_id`. This was fixed by:

- Making `experiment_id` optional in `MetricCreate`
- In `PUT /api/metrics`, resolving `experiment_id` when missing:
  - if `parent_type == "workflow"`: lookup workflow by `parent_id` and use `workflow.experiment_id`
  - if `parent_type == "experiment"`: use `parent_id` as `experiment_id`
  - if still unresolved: return `422`

## Manual verification completed in this session

- `PUT /api/metrics` with Engine-style payload (without `experiment_id`) returned `201 Created`
- `PUT /api/metrics-data/{metric_id}` returned `200 OK` with `inserted: 2`
- `GET /api/metrics/{metric_id}/records` returned inserted records (values `0.1`, `0.2`)
- `POST /api/experiments-query` returned bare list format as expected

## Files changed in this session

- `dal_service/routers/queries.py`
- `dal_service/routers/experiments.py`
- `dal_service/routers/metrics.py`
- `dal_service/schemas/workflow.py`
- `dal_service/schemas/metric.py`
- `dal_service/main.py`

## Current status

- Core DAL API is now in good shape for Engine integration on experiments/workflows/metrics paths tested in this session.
- Query behavior and metric creation are aligned with Engine client expectations tested during this session.

## Suggested starting point for next phase

1. Define the exact scope of the next phase (sorting endpoint, hardening, or tests).
2. Add automated tests for:
   - query response shapes
   - metric create without `experiment_id`
   - metrics-data ingestion/readback
3. Run a full end-to-end Engine smoke test against this DAL build.
