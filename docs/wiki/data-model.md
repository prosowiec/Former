# Data model

## Entity overview

```mermaid
erDiagram
    USERS ||--|| USER_BILLING_INFO : has
    USERS ||--o{ STRIPE_TRANSACTIONS : owns
    USERS ||--o{ AIRFLOW_TRIGGER_REQUESTS : "identified by email"
    AIRFLOW_TRIGGER_REQUESTS ||--o| AIRFLOW_PROGRESS : "run_id"
    AIRFLOW_TRIGGER_REQUESTS ||--o{ FORM_RUN_ANSWERS : "run_id"
    FORM_PAGE_ANSWERS_CACHE ||--o{ FORM_RUN_ANSWERS : "logical cache reference"

    USERS {
      string id PK
      string email UK
      string password_hash
      string google_id
      boolean email_verified
      datetime created_at
    }
    USER_BILLING_INFO {
      string id PK
      string user_id FK_UK
      float total_amount_paid
      int form_fills_remaining
      int form_fills_used
      string stripe_customer_id
    }
    STRIPE_TRANSACTIONS {
      string id PK
      string user_id FK
      string stripe_transaction_id UK
      float amount
      string currency
      int form_fills_purchased
      string status
    }
    AIRFLOW_TRIGGER_REQUESTS {
      string id PK
      string user_email
      string run_id
      string form_url
      int num_executions
      datetime expected_end_at
      string state
    }
    AIRFLOW_PROGRESS {
      string run_id PK
      int numberOfSuccessfulRuns
      boolean hasFailedRuns
      int expectedTotalRuns
    }
    FORM_PAGE_ANSWERS_CACHE {
      int id PK
      string form_url
      int page_index
      json questions
      json answers
    }
    FORM_RUN_ANSWERS {
      string id PK
      string run_id
      int execution_index
      json questions
      json answers
      boolean success
    }
```

The diagram includes logical relationships that are not all enforced with
foreign keys. Only billing and Stripe tables have database-level foreign keys
to `users`.

## Application tables

### `users`

Stores password and Google identities, verification/reset tokens, profile
names, activation state, and timestamps. Passwords are Argon2 hashes. OAuth
users may have no password hash and are considered email-verified.

### `user_billing_info`

One row per user. Tracks aggregate paid amount, remaining/used form fills, and
Stripe customer/subscription ids. Password registrations currently receive 20
initial fills; OAuth registrations receive 10, despite the model default of 10.

### `stripe_transactions`

Immutable-style payment history keyed by the unique Stripe PaymentIntent id.
The JSON metadata column keeps provider details.

### `airflow_trigger_requests`

Application-owned audit record for every accepted parent DAG run. It stores
the user email, scheduling parameters, timezone-aware expected completion,
display name, five personality axes, and application state. `run_id` is not
declared unique or a foreign key. `expected_end_at` is persisted as PostgreSQL
`TIMESTAMP WITH TIME ZONE` and returned by the API as UTC ISO 8601.

### `airflow_progress`

One aggregate row per parent run id. Child completions increment success count
or set the failure flag. The API uses it to derive displayed run state.

### `form_page_answers_cache`

Caches extracted questions and generated answers under the unique pair
`(form_url, page_index)`. Personality, question revision, and execution id are
not part of the key.

### `form_run_answers`

Stores the exact questions and answers used by one execution, plus success and
error fields. `cache_id` is a string without a foreign-key constraint and is
not populated by the current DAG.

## Airflow metadata

Airflow creates and migrates its own tables in the same database. Former reads
the Airflow `dag_run` table directly only when locating child runs for
cancellation. All other orchestration calls use the Airflow REST API.

## Schema lifecycle

- `airflow-init` runs `airflow db migrate` at Compose startup.
- FastAPI startup calls `Base.metadata.create_all()` for application tables.
- There is no application Alembic revision history despite Alembic being a
  dependency; `create_all()` cannot evolve existing columns safely.
- `scripts/migrate_mssql_to_postgresql.py` performs a one-time, ordered copy
  from MSSQL into an empty PostgreSQL target.

## Ownership and transactional notes

- User creation commits the user before creating billing info, so a billing
  failure can leave a user without billing state.
- Triggering Airflow happens before inserting the application trigger record;
  a later database failure can leave an untracked Airflow run.
- Payment confirmation records the transaction and credits quota in one
  database commit.
- Child status and billing are separate Airflow tasks and separate database
  transactions.
