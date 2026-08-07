# Backend API

## Service entry point

`former/backend/api.py` creates the FastAPI application, installs middleware,
and registers domain routers from `former/backend/routers`. Versioned Alembic
migrations run as a dedicated release step. OpenAPI documentation remains at
`/docs` and `/redoc` under normal FastAPI defaults.

Authentication uses Secure HttpOnly cookies. Access and refresh JWTs contain
the user's email in `sub`; refresh tokens also carry `type=refresh`.

## Endpoint catalog

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | Public | Process health probe |
| POST | `/auth/login` | Public | Password login and session-cookie creation |
| POST | `/auth/register` | Public | Create user/billing rows and session cookies |
| GET | `/auth/google` | Public | Start Google OAuth with session state |
| GET | `/auth/callback` | OAuth callback | Exchange Google code and set token cookies |
| POST | `/auth/refresh` | Refresh cookie | Rotate access and refresh cookies |
| POST | `/auth/logout` | Public | Clear authentication cookies |
| GET | `/auth/me` | Access token | Return current user profile |
| POST | `/auth/verify-email/send` | Public | Issue and email a verification token |
| POST | `/auth/verify-email` | Public | Consume verification token |
| POST | `/auth/change-password` | Verified session | Verify old password and set a new hash |
| POST | `/auth/password-reset/request` | Public | Issue password-reset token and email |
| POST | `/auth/password-reset/confirm` | Public | Consume reset token and change password |
| GET | `/airflow/runs` | Access token | List caller-owned runs and derived progress |
| POST | `/airflow/trigger` | Verified session | Reserve quota and persist/dispatch an outbox row |
| POST | `/airflow/runs/{id}/cancel` | Access token | Cancel caller-owned parent and child runs |
| GET | `/billing/info` | Access token | Get quota and payment aggregates |
| GET | `/billing/transactions` | Session cookie | List caller-owned transactions |
| POST | `/billing/create-payment-intent` | Access token | Create Stripe PaymentIntent |
| POST | `/billing/confirm-payment` | Session cookie | Verify caller-owned intent and credit quota idempotently |

## Trigger request

`POST /airflow/trigger` accepts:

```json
{
  "form_url": "https://docs.google.com/forms/...",
  "run_name": "Spring survey",
  "dag_id": "form_filler_plan",
  "run_id": "spring_survey__abc123",
  "num_executions": 5,
  "base_interval_minutes": 10,
  "conf_personality": {
    "age_profile": "mid_career",
    "political_leaning": "centrist",
    "risk_tolerance": "moderate",
    "verbosity": "balanced",
    "formality": "professional"
  }
}
```

Pydantic validates an HTTPS Google/Microsoft Forms hostname, at least one execution, and a base interval of at
least five minutes, enforcing a maximum of 12 fills per hour. The UI expresses
that interval as forms per hour or day and caps the visible pace value at 12.
Jitter is derived by the backend from `SCHEDULER_JITTER_RATIO` and capped by
`SCHEDULER_MAX_JITTER_MINUTES`; clients cannot configure it.
The trigger response and run-list response include `expected_end_at` as a UTC
ISO 8601 timestamp. The frontend converts it to the browser's local timezone.

## Backend modules

| Module | Responsibility |
| --- | --- |
| `api.py` | HTTP endpoints, dependencies, CORS/session middleware, orchestration |
| `auth.py` | Google OAuth calls, JWT creation/verification, random tokens |
| `users.py` | User CRUD, password hashing, verification/reset workflows |
| `db.py` | SQLAlchemy engine and session dependency |
| `models.py` | ORM table declarations |
| `schemas.py` | Request and response validation models |
| `mailService.py` | SMTP configuration, Jinja templates, sync/async send wrappers |
| `airflowInterface/trigger_run.py` | Airflow token acquisition and DAG-run POST |
| `airflowInterface/cancel_run.py` | Parent/child cancellation orchestration |
| `airflowInterface/airflow_utils.py` | Airflow auth and child-run database lookup |

## Security boundaries

- `get_current_user` validates JWT type, subject, and current database user.
- `get_verified_user` additionally requires `users.email_verified`.
- Run list/cancel operations scope records to the caller's email.
- Billing operations scope rows to the caller's UUID.
- CORS allows configured frontend origin plus local development origins.
- Starlette session cookies protect Google OAuth state.

See [Risks and roadmap](risks-and-roadmap.md) for remaining hardening work.
