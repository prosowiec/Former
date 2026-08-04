# Deployment and operations

## Local prerequisites

- Docker Desktop with Linux containers
- PostgreSQL 17 running on the host on port 5432
- A `former` login role and `former` database
- Valid local `.env` values for database, JWT/session, Airflow, LLM, OAuth,
  Stripe, and mail features that will be exercised

Example database bootstrap from an administrator `psql` session:

```sql
CREATE ROLE former WITH LOGIN PASSWORD 'choose-a-local-password';
CREATE DATABASE former OWNER former;
```

Copy `.env.example` to `.env` and use a URL whose host is
`host.docker.internal` for container access to host PostgreSQL.

## Local lifecycle

```powershell
# Build and start
docker compose up --build -d

# Service state
docker compose ps -a

# Follow logs
docker compose logs -f backend airflow-api-server airflow-scheduler

# Stop containers without deleting data
docker compose stop

# Remove current Compose containers/network
docker compose down
```

`airflow-init` should exit with code 0. That is successful one-shot behavior,
not a crash.

## Health checks

| Surface | URL | Expected result |
| --- | --- | --- |
| Frontend | `http://localhost/` | HTTP 200, SPA HTML |
| Backend | `http://localhost:8000/health` | `{"status":"ok"}` |
| Airflow API | `http://localhost:9090/api/v2/version` | HTTP 200 and version JSON |

Useful database-path check from the Airflow container:

```powershell
docker compose exec -T airflow-init pg_isready -h host.docker.internal -p 5432
```

## Startup order

1. Compose runs `airflow-init` and waits for a zero exit code.
2. API server, scheduler, DAG processor, and triggerer start.
3. Backend starts after the Airflow API container has started.
4. Frontend starts after backend.

The dependencies express process ordering, not full application readiness.
There are no Compose healthchecks on backend or Airflow services.

## Local environment contract

`.env` is ignored by Git and represents only local development. Compose
explicitly injects `APP_ENV=local`. The most important network values are:

```dotenv
APP_ENV=local
DATABASE_URL=postgresql+psycopg2://former:...@host.docker.internal:5432/former
FRONTEND_URL=http://localhost
AIRFLOW_HOST=http://localhost:9090
AIRFLOW_BASE_URL=http://localhost:9090/api/v2
```

Compose overrides `AIRFLOW_HOST` and `AIRFLOW_BASE_URL` inside the backend to
use `http://airflow-api-server:8080`, while native host-side tools can use port
9090.

See the canonical definitions in `.env.example` and `ENVIRONMENTS.md`.

## Production contract

Production must set `APP_ENV=production` and inject the canonical variables
listed in `.env.production.example`. Real secrets should be supplied through
the platform secret store rather than committed YAML or image layers.

The current `app.yaml` is an Azure Container Apps-style multi-container
definition. Before production use, address the security and persistence items
in [Risks and roadmap](risks-and-roadmap.md), especially plaintext secrets and
the PostgreSQL sidecar without declared persistent storage.

## Images

### Frontend

Node Alpine builds the Vite bundle; Nginx Alpine serves it. The build context is
`former/front`, so Dockerfile copy paths are relative to that directory.

### Backend

Python 3.10 slim installs the shared `requirements.txt` and starts Uvicorn.
Because requirements are shared, the backend currently installs Airflow,
Playwright, and LLM packages it does not need directly.

### Airflow

Extends `apache/airflow:3.1.8-python3.10`, installs browser system libraries,
Python requirements, Chromium, DAGs, application code, and the simple-auth
password file. Local Compose overrides the image command for each Airflow role.

## Database migration and backup

- Airflow schema: `airflow db migrate` through `airflow-init`.
- Application schema: SQLAlchemy `create_all()` at backend startup.
- Legacy MSSQL data: `scripts/migrate_mssql_to_postgresql.py`; the target
  application tables must be empty.

Back up the host PostgreSQL database as one unit because it contains both
Airflow metadata and application state. Restore testing should verify DAG run
metadata, user/billing rows, answer caches, and run results together.

## Troubleshooting

### `password authentication failed for user "former"`

Network routing is working. Verify the role exists and `.env` credentials match
the local PostgreSQL role. PostgreSQL logs may add `Role "former" does not
exist.` Keep `pg_hba.conf` on `scram-sha-256`; do not solve this with `trust`.

### Frontend connection closes immediately

The Nginx container listens on port 80. Compose must map `80:80`, not
`80:5173` (5173 is the Vite development-server port).

### Frontend Docker `COPY ... not found`

The frontend build context is already `former/front`; Dockerfile paths must be
`package.json`, `.`, and `nginx.conf`, not `former/front/...`.

### Airflow init waits then reaches maximum retries

Inspect `docker compose logs airflow-init`. The entrypoint waits for the
metadata database before executing `airflow db migrate`; routing, role,
password, database existence, and PostgreSQL listen/auth rules are the usual
causes.

### Orphan `former-postgres-1`

This is a stopped container from the older Compose topology. Inspect its
mounts/data before intentionally removing it. The current stack uses the host
PostgreSQL service.

## Observability

Current observability is container logs, Airflow UI/task logs, and database
records. There are no declared metrics, tracing, structured application-log
pipeline, alert rules, or service healthchecks. Avoid logging raw LLM payloads
or tokens because forms may contain sensitive data.
