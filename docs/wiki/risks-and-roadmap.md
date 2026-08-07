# Risks and roadmap

## Completed P0/P1 remediation

- Deployment manifests contain Key Vault/secret references only. Plaintext
  env-to-YAML and JSON-upload helpers were removed.
- Billing credit is derived from server pricing and a Stripe-retrieved,
  succeeded PaymentIntent whose metadata and customer belong to the caller.
  Transaction uniqueness provides idempotency; client-written billing routes
  were removed.
- `/airflow/trigger` locks the billing row, reserves the entire request, and
  commits a durable outbox row before Airflow dispatch. Stable run IDs and the
  dispatcher sidecar reconcile lost responses and failed dispatches.
- Child outcomes are unique per run/execution and atomically settle or refund
  reservations. Browser/LLM cleanup and Airflow failure callbacks record failed
  terminal children.
- Only HTTPS Google Forms and Microsoft Forms destinations on the configured
  exact-host allowlist are accepted.
- Authentication uses Secure HttpOnly SameSite cookies, trusted hosts/proxy
  settings, and no browser token storage or token-export endpoint.
- Answer caching is isolated per user and keyed by normalized URL, page,
  question hash, and personality hash. Legacy unsafe cache entries are purged
  by migration.
- Alembic owns application schema evolution; the web process no longer mutates
  schema at startup. Production manifests use a managed database URL and a
  dedicated migration job rather than a database sidecar.
- The password-change client sends the backend's `old_password` field and the
  contract has regression coverage.

External secret rotation and revocation still require an operator; follow
`SECURITY_ROTATION.md` before the next production release.

## Remaining work

- Pin and split backend, Airflow, migration, and development dependency sets.
- Separate live browser e2e tests from unit/integration CI and provision an
  isolated PostgreSQL integration database for locking/concurrency tests.
- Centralize frontend auth state to avoid duplicate `/auth/me` requests.
- Add bounded run polling or server-pushed progress updates.
- Add readiness probes, metrics, structured logs, correlation IDs, and alerts.
- Replace direct Airflow metadata reads during cancellation with supported API
  calls or an application-owned parent/child mapping.
- Validate LLM answer count/type before filling and report unsupported question
  types explicitly.
- Reconcile inconsistent initial quota defaults for password and OAuth signup.
