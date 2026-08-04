# PostgreSQL migration

Airflow metadata and Former application tables now share the PostgreSQL
database running on the local machine. Docker Compose reaches it through
`host.docker.internal`; it does not create another PostgreSQL container.

## Start with an empty database

Create the `former` database and user in your local PostgreSQL installation.
Copy `.env.example` to `.env`, replace `change-me`, then run:

```sh
docker compose up --build
```

Airflow creates its metadata tables during `airflow-init`. The backend creates
the Former application tables during startup. PostgreSQL must accept TCP
connections from Docker Desktop on the configured port (5432 by default).

## Copy existing MSSQL application data

Stop application writes before starting the copy. The target Former tables must
be empty. Airflow metadata tables may already exist in the target database.

The one-time migration environment needs `pyodbc`, an installed SQL Server ODBC
driver, SQLAlchemy, and the PostgreSQL driver. Runtime containers do not need
ODBC.

```sh
pip install pyodbc
set SOURCE_DATABASE_URL=mssql+pyodbc://...
set DATABASE_URL=postgresql+psycopg2://former:password@localhost:5432/former
python scripts/migrate_mssql_to_postgresql.py
```

Use `$env:NAME = "value"` instead of `set` in PowerShell. The script creates
missing application tables, rejects a non-empty target, copies data in foreign
key order, and updates the PostgreSQL integer sequence.
