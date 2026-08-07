# Frontend

## Stack and build

The UI is React 18 with React Router 6 and Vite 5. Stripe Elements provides
payment input. A multi-stage image runs `npm ci`, builds the Vite bundle, and
serves it from Nginx on port 80.

## Routes

| Route | Guard | Screen |
| --- | --- | --- |
| `/` | Dynamic redirect | `/home` when authenticated, otherwise `/landing` |
| `/landing` | Public-only | Marketing/FAQ page |
| `/login` | Public-only | Password, registration, Google, forgot password |
| `/register` | Public-only | Registration mode of login page |
| `/oauth-success` | Public | Compatibility redirect to `/home` |
| `/verify-email` | Public | Consumes verification token from query string |
| `/reset-password` | Public | Consumes reset token and new password |
| `/home` | Authenticated and verified | Dashboard |

`PrivateRoute` renders an unverified-email screen instead of the dashboard
when the user exists but has not verified email.

## API client

`src/api/client.js` centralizes requests. It:

- reads `VITE_API_BASE_URL`, defaulting to same-origin requests;
- sends server-managed cookies with requests;
- retries once after a 401;
- normalizes FastAPI validation errors;
- exposes grouped auth, billing, and Airflow methods.

JavaScript never receives or persists access or refresh tokens.

## State hooks

| Hook | State and behavior |
| --- | --- |
| `useAuth` | Current user, loading state, login/logout, profile refresh |
| `useRuns` | Initial run fetch, optimistic add/update, derived counts |
| `useBilling` | Parallel billing-info and transaction fetch |
| `useDashboard` | Run filters, success banner, cancellation state updates |

These hooks are instantiated independently by route guards and screens; there
is no shared context/store. Multiple `useAuth()` calls can issue duplicate
`/auth/me` requests and hold separate user state.

## Dashboard composition

`Dashboard` combines:

- header and account actions;
- `TriggerForm` for URL, schedule, and personality axes;
- remaining/used quota visualization;
- run statistics and filters;
- `RunsTable` with detail/cancellation modals;
- `Billingmodal` with fixed/custom fill packages and Stripe Elements;
- password-change modal;
- Stripe redirect confirmation handling.

After a trigger, the run is inserted optimistically. Server state is fetched
on mount but is not periodically polled.

## Frontend environment

Vite variables are compile-time values:

- `VITE_API_BASE_URL`
- `VITE_STRIPE_PUBLISHABLE_KEY`
- `VITE_DEFAULT_DAG_ID` (optional; defaults to `form_filler_plan`)

Root backend environment files and frontend Vite environment files are
separate contracts. Local Compose passes explicit Docker build arguments so a
production `.env.production` file cannot leak its URL into a local bundle.
Production frontend values must likewise be passed as image build arguments;
setting them only on the runtime Nginx container cannot change compiled code.

## Nginx

Nginx serves the SPA and falls back to `index.html` for client routes. It also
defines `/auth/`, `/airflow/`, `/billing/`, `/api/`, and `/health` reverse
proxies to `localhost:8000`. In local Compose the browser currently calls port
8000 directly through `VITE_API_BASE_URL`; `localhost` proxying only works when
Nginx and backend share a network namespace, as intended by the current
production sidecar layout.
