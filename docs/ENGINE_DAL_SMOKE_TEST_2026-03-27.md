# Engine-to-DAL Smoke Test Report (LOCAL)

## Scope

Run one real experiment from Engine (LOCAL executionware) against local DAL and verify core DAL compatibility paths before automated tests.

## Environment

- Engine repo: `extremexp-experimentation-engine-main`
- DAL service: `extremexp-experimentation-engine-main/extremexp-experimentation-engine-main/dal_service`
- DAL URL: `http://127.0.0.1:8000/api`
- Auth header: `access-token: dev-token`

## Smoke assets used

- New experiment spec: `playground/experiments/tests/smoke/dal_engine_smoke.xxp`
- New runner: `run_smoke_experiment.py`

## Execution command

From Engine repo root:

```bash
python run_smoke_experiment.py
```

## DAL access-log evidence (key calls)

- `PUT /api/experiments` -> `201 Created`
- `POST /api/experiments/{experiment_id}` -> `200 OK`
- `PUT /api/workflows` -> `201 Created`
- `PUT /api/metrics` -> `201 Created`
- `POST /api/workflows/{workflow_id}` -> `200 OK`
- `POST /api/experiments-query` -> `200 OK`
- `POST /api/metrics-query` -> `200 OK`
- `PUT /api/metrics-data/{metric_id}` -> `200 OK`
- `GET /api/metrics/{metric_id}/records` -> `200 OK`

Observed IDs:
- `experiment_id`: `a5949bae-3ed7-4f3d-9ca6-e58dd9a4c786`
- `workflow_id`: `a25d41f4-4a6f-4f68-84c1-a2ecf40a091c`
- `metric_id`: `fb64f88f-3f50-400c-b075-c33e4a5de9b6`

## Post-run checks

- `GET /api/experiments/{experiment_id}` -> 200 and contains `workflow_ids` with the created workflow.
- `POST /api/experiments-query` with creator filter -> 200 and bare list response.
- `POST /api/workflows-query` with `experimentId` (camelCase) -> 200 and bare list response.
- `POST /api/metrics-query` with `producedByTask` (camelCase) -> 200 and bare list response.
- `PUT /api/metrics-data/{metric_id}` inserted records.
- `GET /api/metrics/{metric_id}/records` returned inserted records (`0.11`, `0.22`).

## Compatibility verdict

- DAL contract paths exercised by Engine in this smoke run are compatible.
- Critical fix validated: metric creation without explicit `experiment_id` works and resolves experiment from parent.

## Remaining gaps before automated tests

1. Engine LOCAL task subprocess environment showed shell/runtime issues (`python`/`source` not found for task execution scripts).  
   - This did not block DAL contract validation but can affect workflow task success semantics.
2. Add automated API tests for:
   - `POST /experiments-query` bare list shape
   - `PUT /metrics` without `experiment_id`
   - `PUT /metrics-data` + `GET /metrics/{id}/records`

