# Code index

## Root and infrastructure

| Path | Role |
| --- | --- |
| `docker-compose.yml` | Local multi-container topology and service wiring |
| `Dockerfile.front` | Vite build and Nginx runtime image |
| `Dockerfile.backend` | FastAPI runtime image |
| `Dockerfile.airflow` | Airflow, browser dependencies, Chromium, DAG package |
| `.dockerignore` | Excludes secrets, Git data, caches, builds, and node modules |
| `.env.example` | Local canonical environment template |
| `.env.production.example` | Production canonical environment template |
| `ENVIRONMENTS.md` | Environment-selection rules |
| `app.yaml` | Current production-oriented Azure multi-container definition |
| `requirements.txt` | Shared Python dependency list |
| `pyproject.toml` | Python package metadata |
| `pytest.ini` | Pytest e2e marker declaration |
| `POSTGRESQL_MIGRATION.md` | PostgreSQL and Alembic deployment guide |

## Backend package

| Path | Role |
| --- | --- |
| `former/config.py` | Canonical runtime configuration and environment validation |
| `former/backend/api.py` | FastAPI lifecycle, middleware, and router registration |
| `former/backend/dependencies.py` | Shared current-user and verified-user dependencies |
| `former/backend/routers/auth.py` | Login, OAuth, tokens, verification, and passwords |
| `former/backend/routers/airflow.py` | Run listing, triggering, pacing, and cancellation |
| `former/backend/routers/billing.py` | Billing balance, Stripe, and transaction endpoints |
| `former/backend/routers/health.py` | Public process health endpoint |
| `former/backend/auth.py` | JWT and Google OAuth primitives |
| `former/backend/users.py` | User, verification, and password operations |
| `former/backend/db.py` | SQLAlchemy engine/session/base |
| `former/backend/models.py` | Seven application ORM models |
| `former/backend/schemas.py` | Pydantic API request/response models |
| `former/backend/mailService.py` | SMTP and templated email sending |
| `former/backend/templates/verification_mail.html` | Verification email template |
| `former/backend/templates/reset_password_mail.html` | Password reset email template |
| `former/backend/airflowInterface/airflow_utils.py` | Airflow access token and child lookup |
| `former/backend/airflowInterface/trigger_run.py` | Parent DAG request builder/client |
| `former/backend/airflowInterface/cancel_run.py` | Parent and child run cancellation |

## Airflow DAGs

| Path | Role |
| --- | --- |
| `dags/form_filler_plan.py` | Parent scheduling and mapped child triggers |
| `dags/form_filler_dag.py` | Single browser execution, persistence, progress, billing |
| `dags/utils.py` | Question normalization and page-answer cache |

## Browser automation

| Path | Role |
| --- | --- |
| `former/fillWorkflow/browser.py` | Chromium launch/context and stealth scripts |
| `former/fillWorkflow/detectors.py` | Platform and question-type detection |
| `former/fillWorkflow/extract.py` | Platform-neutral extraction dispatcher |
| `former/fillWorkflow/extractors/extractGoogle.py` | Google DOM extractors |
| `former/fillWorkflow/extractors/extractMS.py` | Microsoft DOM extractors |
| `former/fillWorkflow/fill.py` | Platform-neutral filler dispatcher |
| `former/fillWorkflow/fillers/fillGoogle.py` | Google control fillers |
| `former/fillWorkflow/fillers/fillMS.py` | Microsoft control fillers |
| `former/fillWorkflow/navigation.py` | Next/submit detection and clicks |
| `former/fillWorkflow/human.py` | Randomized human-like interactions |
| `former/fillWorkflow/formFiller.py` | Standalone, non-Airflow pipeline entry point |
| `former/fillWorkflow/exporters.py` | JSON/CSV export helpers; not on active DAG path |

## LLM layer

| Path | Role |
| --- | --- |
| `former/LLM_interface/ChatInterface.py` | Abstract prompt and provider contract |
| `former/LLM_interface/ChatgptFormFiller.py` | OpenAI structured-output implementation |
| `former/LLM_interface/Gemini.py` | Gemini implementation; not active in DAG |
| `former/LLM_interface/personalityBuilder.py` | Personality trait generation |
| `former/LLM_interface/PERSONAS.json` | Axis labels, values, and trait catalogs |

## Frontend

| Path | Role |
| --- | --- |
| `former/front/src/main.jsx` | React root and browser router |
| `former/front/src/App.jsx` | Route table and guards |
| `former/front/src/api/client.js` | Token-aware fetch wrapper and endpoint methods |
| `former/front/src/hooks/useAuth.js` | Authentication state/actions |
| `former/front/src/hooks/useRuns.js` | Run retrieval and derived statistics |
| `former/front/src/hooks/useBilling.js` | Billing/transaction retrieval |
| `former/front/src/hooks/useDashboard.js` | Dashboard filters and optimistic updates |
| `former/front/src/hooks/runsUtils.js` | Run-response normalization |
| `former/front/src/components/Landingpage.jsx` | Marketing page |
| `former/front/src/components/LoginPage.jsx` | Login, registration, Google, forgot password |
| `former/front/src/components/OAuthSuccess.jsx` | OAuth cookie-to-token exchange |
| `former/front/src/components/PrivateRoute.jsx` | Auth and verification guard |
| `former/front/src/components/PublicRoute.jsx` | Logged-out-only guard |
| `former/front/src/components/Unverifiedpage.jsx` | Verification-required screen |
| `former/front/src/components/VerifyEmail.jsx` | Verification token screen |
| `former/front/src/components/Resetpassword.jsx` | Password reset screen |
| `former/front/src/components/Dashboard.jsx` | Main authenticated composition |
| `former/front/src/components/TriggerForm.jsx` | Trigger/schedule/personality form |
| `former/front/src/components/RunsTable.jsx` | Run list, details, cancellation |
| `former/front/src/components/RunResult.jsx` | Near-duplicate run table implementation |
| `former/front/src/components/RunStageIndicator.jsx` | Visual run-state stages |
| `former/front/src/components/Billingmodal.jsx` | Stripe checkout and transaction history |
| `former/front/src/components/Changepasswordmodal.jsx` | Password-change form |
| `former/front/src/components/HealthBadge.jsx` | Backend health indicator |
| `former/front/src/components/StatsBar.jsx` | Standalone run stats component |
| `former/front/src/index.css` | Global/component styling |
| `former/front/nginx.conf` | SPA serving and reverse proxy paths |
| `former/front/vite.config.js` | Vite plugin, development proxy, allowed hosts |
| `former/front/package.json` | Frontend scripts and dependencies |

## Scripts and tests

| Path | Role |
| --- | --- |
| `scripts/dispatch_pending_airflow.py` | Durable Airflow-outbox reconciliation |
| `former/tests/test_trigger_run.py` | Airflow trigger payload/client tests |
| `former/tests/test_api.py` | API surface and orchestration utility tests |
| `former/tests/test_auth.py` | HttpOnly-cookie authentication tests |
| `former/tests/test_backend_and_schema.py` | Backend/schema validation tests |
| `former/tests/test_e2e_forms.py` | Live form automation tests |
| `former/tests/TestResponses.py` | LLM/form response fixtures or experiments |

## Generated and local-only paths

- `former/front/node_modules/`: installed frontend dependencies
- `former/front/dist/`: Vite build output
- `__pycache__/`, `.pytest_cache/`: generated Python caches
- `.env`: local secrets/configuration
- `simple_auth_manager_passwords.json.generated`: local Airflow simple-auth data
- `browser_data/` when persistent browser context is used
