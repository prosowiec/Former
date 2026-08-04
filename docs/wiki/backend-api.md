# Backend API

## Service entry point

`former/backend/api.py` creates the FastAPI application. On startup it calls
`Base.metadata.create_all()` and exposes OpenAPI documentation at `/docs` and
`/redoc` under normal FastAPI defaults.

Authentication uses `Authorization: Bearer <access-token>`. Access and refresh
tokens are HS256 JWTs with the user's email in `sub`; refresh tokens also carry
`type=refresh`.

## Endpoint catalog

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | Public | Process health probe |
| POST | `/auth/login` | Public | Password login and JWT pair creation |
| POST | `/auth/register` | Public | Create user/billing rows and JWT pair |
| GET | `/auth/google` | Public | Start Google OAuth with session state |
| GET | `/auth/callback` | OAuth callback | Exchange Google code and set token cookies |
| GET | `/auth/tokens` | Token cookies | Exchange OAuth cookies for JSON tokens |
| POST | `/auth/refresh` | Refresh token body | Rotate access and refresh tokens |
| POST | `/auth/logout` | Public | Clear authentication cookies |
| GET | `/auth/me` | Access token | Return current user profile |
| POST | `/auth/verify-email/send` | Public | Issue and email a verification token |
| POST | `/auth/verify-email` | Public | Consume verification token |
| POST | `/auth/change-password` | Verified access token | Verify old password and set a new hash |
| POST | `/auth/password-reset/request` | Public | Issue password-reset token and email |
| POST | `/auth/password-reset/confirm` | Public | Consume reset token and change password |
| GET | `/airflow/runs` | Access token | List caller-owned runs and derived progress |
| POST | `/airflow/trigger` | Verified access token | Trigger the parent DAG and store audit row |
| POST | `/airflow/runs/{id}/cancel` | Access token | Cancel caller-owned parent and child runs |
| GET | `/billing/info` | Access token | Get quota and payment aggregates |
| GET | `/billing/transactions` | Access token | List caller-owned transactions |
| POST | `/billing/transaction` | Access token | Record a transaction supplied by the client |
| POST | `/billing/deduct-form-fills` | Access token | Manually deduct quota |
| POST | `/billing/create-payment-intent` | Access token | Create Stripe PaymentIntent |
| POST | `/billing/confirm-payment` | Access token | Verify intent, record it, and credit quota |

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
  "interval_jitter_minutes": 2,
  "conf_personality": {
    "age_profile": "mid_career",
    "political_leaning": "centrist",
    "risk_tolerance": "moderate",
    "verbosity": "balanced",
    "formality": "professional"
  }
}
```

Pydantic validates a URL, at least one execution, a base interval of at least
0.1 minute, and non-negative jitter.

## Backend modules

| Module | Responsibility |
| --- | --- |
| `api.py` | HTTP endpoints, dependencies, CORS/session middleware, orchestration |
| `auth.py` | Google OAuth calls, JWT creation/verification, random tokens |
| `users.py` | User CRUD, password hashing, verification/reset workflows |
| `db.py` | SQLAlchemy engine, session dependency, application table creation |
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

See [Risks and roadmap](risks-and-roadmap.md) for public email endpoints,
cookie flags, client-submitted transaction recording, and token-storage issues.
