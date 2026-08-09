# PostgreSQL and application migrations

Former application tables and Airflow metadata may share a PostgreSQL service,
but production must use managed PostgreSQL (or equivalent persistent storage)
with automated backups, point-in-time recovery, and tested restores. PostgreSQL
must not run as an application sidecar or on container-local storage.

## Schema deployment

Schema changes are managed by Alembic and never by web-process startup.
Former records its revision in `former_alembic_version`, leaving Airflow's
separate `alembic_version` table untouched when both use the same database.

- Fresh database: `alembic upgrade head`.
- Existing database created by the former `create_all()` startup: back it up,
  run `alembic stamp 20260807_0001`, then `alembic upgrade head`.
- Production: execute `app-migrate-job.yaml` as a dedicated release step before
  updating the application revision.

## Local development

Create the PostgreSQL database and user, copy `.env.example` to `.env`, replace
the placeholder credentials, run `alembic upgrade head`, then start Compose.

```sh
alembic upgrade head
pwsh -File scripts/init_local_secrets.ps1
docker compose up --build
```
