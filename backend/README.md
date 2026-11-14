# Trend Detective backend (Member 3)

FastAPI service over the verified cubes and the frozen statistics pipeline.
Ingestion is never triggered by a user request; the API only reads verified
data and `method_revision m2-1.0.0`.

## Run

```bash
cd backend
python -m pip install -r requirements.txt
python -m pip install -r ../data/nasa/requirements.txt
python run.py                 # http://127.0.0.1:8000  (docs at /docs)
```

## Test

```bash
python -m pytest tests/test_api.py -q      # 14 contract tests
python bench.py                            # performance numbers
python warm_cache.py                       # pre-warm demo presets
```

## Layout

```
app/config.py       paths, compute limits, software revision (no secrets)
app/db.py           SQLite: jobs, results, receipts, catalog snapshot
app/canonical.py    geometry validation + canonical request hashing
app/registry.py     runtime catalog built from Roles 01/02 JSON artifacts
app/analysis_runner.py  adapter to data/nasa/analysis/trend.py
app/worker.py       background worker, stale-job recovery
app/receipts.py     receipt builder + secret redaction
app/main.py         routes and error codes
```

## Behaviour worth knowing

- **Idempotent:** one job per canonical request hash (unique constraint). A
  duplicate submission returns the same job.
- **Canonical geometry:** ring rotation, orientation and precision are
  normalized before hashing, so the same area always maps to the same job.
- **Cache:** a result is reused only for the same `data_revision` and
  `method_revision`. Changing either invalidates it by construction.
- **Failed jobs:** a failed job has no result and no receipt. Result and
  receipt rows are written in a single transaction.
- **Crash recovery:** jobs left `running` at startup become `failed` with
  `INTERRUPTED`; success is never inferred from a partial file.
- **Secrets:** nothing sensitive is read, stored or returned; receipt keys that
  look like credentials are stripped before hashing.

Environment overrides: `TD_DB_PATH`, `TD_VAR_DIR`, `TD_DATA_DIR`,
`TD_MAX_CELLS`, `TD_MAX_VARIABLES`, `TD_WORKER_POLL`.
