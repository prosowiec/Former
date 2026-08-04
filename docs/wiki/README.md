# Former codebase wiki

This wiki documents the system as implemented in the repository. It is the
starting point for maintainers, reviewers, and operators.

## What Former does

Former is a web application that schedules repeated submissions of Google
Forms and Microsoft Forms. A user supplies a form URL, scheduling parameters,
and a personality profile. The backend creates an Airflow plan; child DAG runs
open the form with Playwright, extract its questions, ask an LLM for structured
answers, fill and submit the form, and persist progress and billing usage.

## Wiki map

| Page | Purpose |
| --- | --- |
| [System architecture](architecture.md) | Containers, boundaries, dependencies, and design rationale |
| [Runtime flows](runtime-flows.md) | Authentication, trigger, execution, cancellation, and payment sequences |
| [Backend API](backend-api.md) | FastAPI endpoints, auth requirements, and service modules |
| [Data model](data-model.md) | PostgreSQL tables, ownership, and lifecycle |
| [Airflow and automation](airflow-automation.md) | DAG topology, browser pipeline, LLM integration, and supported form controls |
| [Frontend](frontend.md) | Routes, API client, hooks, major components, and state flow |
| [Deployment and operations](deployment-operations.md) | Local/production environments, containers, startup, and troubleshooting |
| [Code index](code-index.md) | Directory-by-directory source map |
| [Risks and roadmap](risks-and-roadmap.md) | Known gaps, inconsistencies, and recommended improvements |

## Fast orientation

- Backend entry point: `former.backend.api:app`
- Local UI: `http://localhost`
- Local API: `http://localhost:8000`
- Local Airflow UI/API: `http://localhost:9090`
- Parent DAG: `form_filler_plan`
- Child DAG: `form_filler_dag`
- Shared database: PostgreSQL database `former`
- Local orchestration: `docker-compose.yml`
- Production container definition: `app.yaml`
- Environment contract: `.env.example` and `.env.production.example`

## Repository conventions

- Runtime Python package: `former/`
- Airflow DAG definitions: `dags/`
- React application: `former/front/`
- Operational scripts: `scripts/`
- Tests: `former/tests/`
- Wiki: `docs/wiki/`

The source currently uses both application and Airflow tables in one
PostgreSQL database. Airflow owns its metadata tables; Former owns the tables
listed in [Data model](data-model.md).
