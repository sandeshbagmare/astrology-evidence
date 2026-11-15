# Local development runbook

This package is for local synthetic-data development. The Compose configuration binds services to loopback, uses PostgreSQL 16 and Qdrant 1.20.0, runs migrations before the web process and privacy worker, and preserves service data in named volumes. AI and embeddings remain disabled by default. Readiness means the database can answer a query; it does not certify source rights, Google login, AI, or retrieval availability.

## Windows setup

Install uv through an approved installation method, then from the repository root run:

```powershell
./scripts/bootstrap.ps1
$env:DEV_LOGIN_ENABLED = 'true'
./.venv/Scripts/python.exe -m uvicorn astrology_evidence.main:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and select **Use local synthetic demo** on the sign-in page. This creates a local demo account; it is not Google authentication. Use invented birth data only. Start the durable privacy executor in another terminal:

```powershell
./.venv/Scripts/python.exe -m astrology_evidence.jobs.worker
```

The local SQLite database is created automatically for development. Python 3.12 or 3.13 is required for the native calculation engine. The package also supports Python 3.14 for non-calculation work, but 3.14 does not install pysweph and is not a complete calculation runtime. On this laptop native Python execution may be blocked by Windows application policy. Pass an explicitly approved interpreter to `./scripts/bootstrap.ps1 -Python C:/approved/path/python.exe`; if no approved interpreter is available, use an approved Docker environment or CI. Do not disable Windows policy or treat a partial fallback runtime as a complete build. The existing `scripts/dev.ps1` is a machine-specific fallback, not the standard bootstrap path.

## Docker Compose

Docker Desktop with Linux containers and Compose is required. Generate a URL-safe local database password in your shell (do not commit it):

```powershell
$env:POSTGRES_PASSWORD = python -c 'import secrets; print(secrets.token_hex(24))'
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs migrate web worker
```

Keep that password available for later Compose commands; named volumes retain the original database password. The database password must be URL-safe because it is included in `DATABASE_URL`. Open the same loopback URL and synthetic sign-in flow. `docker compose stop` preserves data. Schema migrations are a separate `migrate` service. After changing migrations, rerun `docker compose run --rm migrate` before restarting web and worker. Do not use `down -v` unless you intend to erase the local database and index. Take a PostgreSQL backup and Qdrant snapshot before upgrading persisted services.

## Verification

```powershell
./.venv/Scripts/python.exe -m pytest
./.venv/Scripts/python.exe -m ruff check .
./.venv/Scripts/python.exe -m mypy src
./scripts/test-calculations.ps1
node scripts/check-docs.mjs
node --test scripts/check-docs.test.mjs
```

CI installs the frozen uv lock with Python 3.12 and supplies disposable PostgreSQL/Qdrant services. To exercise the same delivery checks locally, start those services and set the test URLs:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://astrology:$($env:POSTGRES_PASSWORD)@127.0.0.1:5432/astrology"
$env:TEST_QDRANT_URL = 'http://127.0.0.1:6333'
./.venv/Scripts/python.exe -m pytest tests/test_delivery.py
```

These checks create a unique PostgreSQL schema and Qdrant collection, then remove only those test resources. Use a disposable test database. Without the URLs they are explicitly skipped. The migration check compares the upgraded PostgreSQL schema to application models; the Qdrant check builds and queries an actual remote dense/sparse index using a synthetic encoder.

## Source and launch gates

`examples/synthetic-corpus.json` is a labeled test fixture, not a licensed astrology collection. Do not grant real content rights by copying its permission flags. Corpus import/publication requires an authorized administrator, edition-specific ingestion/display/transmission rights, and a configured pinned embedding model. No production content is automatically seeded.

Google sign-in needs runtime `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` and the matching `/auth/google/callback` redirect URL. Real-user deployment additionally needs HTTPS, secure cookies, disabled development login, reviewed ephemeris licensing/files, an operating privacy worker, backups/restoration checks, and review of the actual provider/data transfer. Set `OPENAI_API_KEY` only in the runtime secret store after provider review; no credential is included here. Optional embedding dependencies/models must be installed and pinned separately. Do not enable production merely to bypass these gates.

Docker build/start and live PostgreSQL/Qdrant delivery tests have not been executed on this Windows host because Docker is unavailable. CI is configured to perform the service tests; a workflow file is not evidence of a completed CI run.
