# Former

Former schedules and executes LLM-assisted Google Forms and Microsoft Forms
submissions through a React, FastAPI, Airflow, Playwright, and PostgreSQL stack.

## Documentation

Start with the [codebase wiki](docs/wiki/README.md). It includes:

- system architecture and runtime diagrams;
- authentication, scheduling, automation, cancellation, and payment flows;
- API and database references;
- frontend and Airflow internals;
- local and production operations;
- a complete code index;
- known risks and a recommended target architecture.

Environment setup is documented in [ENVIRONMENTS.md](ENVIRONMENTS.md). Local
PostgreSQL migration notes are in
[POSTGRESQL_MIGRATION.md](POSTGRESQL_MIGRATION.md).

## Local start

Create the local PostgreSQL role/database, copy `.env.example` to `.env`, fill
in the required values, then run:

```powershell
docker compose up --build -d
```

Open:

- Frontend: `http://localhost`
- Backend API docs: `http://localhost:8000/docs`
- Airflow: `http://localhost:9090`
