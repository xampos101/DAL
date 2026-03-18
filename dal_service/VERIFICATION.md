# DAL Phase 2 – Manual verification

After starting the server from the project root (where `dal_service` lives) with venv activated:

```bash
uvicorn dal_service.main:app --reload
```

Ensure PostgreSQL is running and `.env` has `DATABASE_URL` (e.g. `postgresql+asyncpg://user:pass@localhost:5432/dbname`) and `ACCESS_TOKEN`. Then:

1. **Create experiment**  
   `PUT /api/experiments` with header `access-token: <your ACCESS_TOKEN>` and body e.g. `{"name": "test-exp"}`.  
   Expect `201` and `message.experimentId`.

2. **Get experiment**  
   `GET /api/experiments/{experimentId}` with `access-token`.  
   Expect `200` and `experiment` object.

3. **List experiments**  
   `GET /api/experiments` with `access-token`.  
   Expect `200` and `experiments` array.

4. **Create workflow**  
   `PUT /api/workflows` with body `{"experiment_id": "<experimentId>", "name": "wf1"}` and `access-token`.  
   Expect `201` and `workflow_id`.

5. **Get workflow**  
   `GET /api/workflows/{workflow_id}` with `access-token`.  
   Expect `200` and `workflow` object.

Example (replace `YOUR_TOKEN` and base URL):

```bash
curl -X PUT http://127.0.0.1:8000/api/experiments -H "access-token: YOUR_TOKEN" -H "Content-Type: application/json" -d '{"name":"test-exp"}'
```
