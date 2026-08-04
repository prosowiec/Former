# Runtime flows

## Registration and email verification

1. React posts name, surname, email, and password to `POST /auth/register`.
2. The backend hashes the password with Argon2 and inserts `users`.
3. A `user_billing_info` row is created with an initial fill allowance.
4. The backend returns JWT access and refresh tokens.
5. The frontend may request `POST /auth/verify-email/send`.
6. The backend stores a random verification token and expiry, then sends an
   SMTP email containing `EMAIL_VERIFY_URL?token=...`.
7. `POST /auth/verify-email` marks the user verified.
8. Verified email is required to trigger a form run.

## Password or Google login

Password login verifies an Argon2 hash and returns an access/refresh pair.
Google login stores an OAuth state in the signed Starlette session, exchanges
the callback code with Google, creates or updates the user, and redirects to
the frontend with short-lived HTTP-only token cookies. The OAuth success page
exchanges those cookies through `GET /auth/tokens`; the API client then keeps
tokens in browser session storage and navigates directly to `/home`. The
private-route guard waits for `/auth/me` before rendering or redirecting.

## Form-run trigger

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI
    participant DB as PostgreSQL
    participant AF as Airflow API

    User->>UI: URL, run count, hourly/daily pace, personality
    UI->>API: POST /airflow/trigger + access token
    API->>DB: Validate user and verified email
    API->>AF: POST form_filler_plan DAG run
    AF-->>API: Accepted DAG run
    API->>DB: Insert airflow_trigger_requests
    API-->>UI: queued run response
    UI->>UI: Optimistically prepend run
```

The backend appends the user UUID to a supplied run id. Overlong identifiers
are truncated and suffixed with a SHA-1 fragment to fit 255 characters.

## Scheduled execution

```mermaid
sequenceDiagram
    participant Plan as form_filler_plan
    participant Triggerer as Airflow triggerer
    participant Child as form_filler_dag
    participant DB as PostgreSQL
    participant Browser as Playwright
    participant LLM as OpenAI
    participant Form as Google/MS Form

    Plan->>Plan: Build jittered execution timestamps
    Plan->>Triggerer: Defer until each timestamp
    Triggerer->>Child: Trigger mapped child run
    Child->>DB: Load personality selections
    Child->>Browser: Open form and extract page
    Child->>DB: Look up cached page answers
    alt cache miss
        Child->>LLM: Questions + generated personality
        LLM-->>Child: Structured ANSWERS values
        Child->>DB: Cache page answers
    end
    Child->>Browser: Fill controls and submit
    Browser->>Form: Form submission
    Child->>DB: Insert run answers and update progress
    Child->>DB: Deduct one successful fill
```

The first planned execution is scheduled approximately two minutes ahead.
The UI converts the selected hourly or daily pace into a base interval. Later
executions add scheduler-controlled jitter; users do not configure it directly.

## Run status

`GET /airflow/runs` joins application trigger records with `airflow_progress`
in application code. State is derived as:

1. `cancelled` when the trigger record was cancelled.
2. `failed` when any child recorded failure.
3. `success` when successful runs reach the expected total.
4. `running` after at least one success but before the total.
5. `queued` when no progress row or success exists.

The frontend fetches this list on mount and computes dashboard statistics. It
does not currently poll automatically after the initial fetch.

## Cancellation

1. The backend verifies the trigger record belongs to the caller.
2. It patches the parent Airflow run state to `failed`.
3. For `form_filler_plan`, it queries Airflow's `dag_run` table for child ids
   matching `<parent>__item_%` and patches each child concurrently.
4. It marks the application trigger record `cancelled`.

Cancellation is therefore represented differently in the two systems:
`failed` inside Airflow and `cancelled` in the Former application table.

## Billing and payment

- Successful child runs decrement `form_fills_remaining` and increment
  `form_fills_used`.
- The UI prevents submission when its locally fetched balance is insufficient.
- Stripe payment intents use EUR cents and include user/fill metadata.
- Payment confirmation retrieves the intent from Stripe, records an idempotent
  `stripe_transactions` row, and credits the purchased fills.

The backend trigger endpoint does not currently reserve or validate the full
requested quota before scheduling; see [Risks and roadmap](risks-and-roadmap.md).
