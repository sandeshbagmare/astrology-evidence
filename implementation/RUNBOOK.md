# Local development runbook

This package is for local synthetic-data development. The app opens directly into a separate anonymous browser workspace, without sign-in. Authentication is future scope and disabled by default. Compose binds services to loopback, uses PostgreSQL 16/Qdrant 1.20.0, runs migrations before web/worker and preserves service data in named volumes. AI/embeddings remain disabled by default. Readiness means the database can answer a query, not that source rights, AI or retrieval have been validated.

## Windows setup

Install uv through an approved installation method, then from the repository root run:

```powershell
./scripts/bootstrap.ps1
$env:AUTHENTICATION_ENABLED = 'false'
./.venv/Scripts/python.exe -m uvicorn astrology_evidence.main:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. No login or Google credentials are needed. Each browser receives its own opaque workspace cookie; another browser has separate records. Clearing cookies or session expiry loses access, with no recovery or cross-device sync yet. Use invented birth data only. Start the durable privacy executor in another terminal:

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

Keep that password available for later Compose commands; named volumes retain the original database password. The database password must be URL-safe because it is included in `DATABASE_URL`. Open the same loopback URL and start directly in the anonymous workspace. `docker compose stop` preserves data. Schema migrations are a separate `migrate` service. After changing migrations, rerun `docker compose run --rm migrate` before restarting web/worker. Do not use `down -v` unless you intend to erase the local database/index. Take a PostgreSQL backup and Qdrant snapshot before upgrading services.

## Verification

```powershell
./.venv/Scripts/python.exe -m pytest
./.venv/Scripts/python.exe -m ruff check .
./.venv/Scripts/python.exe -m mypy src
./scripts/test-calculations.ps1
node scripts/check-docs.mjs
node --test scripts/check-docs.test.mjs
node --test tests/ui_app_js.test.mjs tests/browser_cleanup.test.mjs
```

CI installs the frozen uv lock with Python 3.12 and supplies disposable PostgreSQL/Qdrant services. To exercise the same delivery checks locally, start those services and set the test URLs:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://astrology:$($env:POSTGRES_PASSWORD)@127.0.0.1:5432/astrology"
$env:TEST_QDRANT_URL = 'http://127.0.0.1:6333'
./.venv/Scripts/python.exe -m pytest tests/test_delivery.py
```

These checks create a unique PostgreSQL schema and Qdrant collection, then remove only those test resources. Use a disposable test database. Without the URLs they are explicitly skipped. The migration check compares the upgraded PostgreSQL schema to application models; the Qdrant check builds and queries an actual remote dense/sparse index using a synthetic encoder.

## Automated browser journey

The Python CI job pins Ubuntu 24.04 and Playwright 1.58.2, installs Chromium outside the checkout, starts a disposable synthetic SQLite app and privacy worker, then executes `scripts/run-browser-check.mjs`. It reuses `tests/browser/verify-app.js`: 24 screen/width combinations, separate-workspace denials, DST input, native chart, chart-bound abstention, confirmed reading/profile deletion, JavaScript-disabled keyboard forms, completed owner-only export and workspace deletion. The runner closes Chromium and the workflow stops both Python processes. No provider credentials or real source material are used.

Locally, start the app and worker above, then open its actual port in Playwright CLI and run `tests/browser/verify-app.js`. A failed browser action is not a passing smoke test; the cleanup harness preserves its original error. This laptop's Edge stopped delivering animation frames during the later quality pass; Linux CI supplies the fresh browser evidence rather than using forced clicks. See [the verification report](E2E-AND-DEMO-REPORT.md) for tested commits and outcomes.

## Source and launch gates

`examples/synthetic-corpus.json` is a labeled test fixture, not a licensed astrology collection. Do not grant real content rights by copying its permission flags. Corpus import/publication requires an authorized administrator, edition-specific ingestion/display/transmission rights, and a configured pinned embedding model. No production content is automatically seeded.

Real-user deployment still needs HTTPS, secure cookies, disabled development login, reviewed ephemeris licensing/files, a reliable privacy worker, anonymous-workspace abuse limits, backups/restoration checks, and provider/data-transfer review. Set `OPENAI_API_KEY` only in a runtime secret store after provider review. Optional embedding dependencies/models must be installed and pinned separately. Do not enable production merely to bypass these gates. Google credentials are unnecessary in the current mode. The retained future authentication path is enabled only with `AUTHENTICATION_ENABLED=true`, configured Google client/callback and separate live validation; account linking/recovery is not implemented.

Docker build/start and live PostgreSQL/Qdrant delivery tests have not been executed on this Windows host because Docker is unavailable. CI is configured to perform the service tests; a workflow file is not evidence of a completed CI run.

## Curator and model setup

After creating your account, a local operator can list opaque account IDs and grant a curator role:

```text
./.venv/Scripts/python.exe -m astrology_evidence.manage users
./.venv/Scripts/python.exe -m astrology_evidence.manage grant-curator USER_ID
./.venv/Scripts/python.exe -m astrology_evidence.manage import-edition examples/synthetic-corpus.json
```

These commands require direct database access and are not public endpoints. The synthetic edition is original test material, not an astrology reference. Curators can import reviewed edition JSON and publish/withdraw it from `/admin/corpus`.

For semantic retrieval, install `uv sync --extra embeddings`, fetch the model through an approved process and pin its 40-character revision in `EMBEDDING_REVISION`. Set `EMBEDDING_ENABLED=true` only after the weights are cached, then publish through the curator page. E5 does not download automatically at application import. `uv sync --extra pdf` enables optional native PDF text extraction. OCR requires separately installed Tesseract and an operator-isolated worker; no books or OCR binaries are bundled.

The optional `CALCULATION_PYTHON` plus `CALCULATION_PYTHONPATH` settings run the native calculator through an explicitly configured local interpreter, with JSON input and a minimal environment that excludes provider/session secrets. This supports the verified Windows two-runtime setup; ordinary Python3.12 deployments need neither setting.

