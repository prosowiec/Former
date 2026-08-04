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
| `/oauth-success` | Public | Exchanges OAuth cookies for tokens |
| `/verify-email` | Public | Consumes verification token from query string |
| `/reset-password` | Public | Consumes reset token and new password |
| `/home` | Authenticated and verified | Dashboard |

`PrivateRoute` renders an unverified-email screen instead of the dashboard
when the user exists but has not verified email.

## API client

`src/api/client.js` centralizes requests. It:

- reads `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`;
- attaches an access bearer token;
- refreshes proactively within 60 seconds of expiry;
- retries once after a 401;
- normalizes FastAPI validation errors;
- exposes grouped auth, billing, and Airflow methods.

The module stores tokens in `sessionStorage`. `useAuth` still attempts to read
`localStorage` on mount, an inconsistency recorded in the roadmap.

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
separate contracts. Production frontend values must exist at image build time,
not merely as runtime container variables.

## Nginx

Nginx serves the SPA and falls back to `index.html` for client routes. It also
defines `/auth/`, `/airflow/`, `/billing/`, `/api/`, and `/health` reverse
proxies to `localhost:8000`. In local Compose the browser currently calls port
8000 directly through `VITE_API_BASE_URL`; `localhost` proxying only works when
Nginx and backend share a network namespace, as intended by the current
production sidecar layout.
