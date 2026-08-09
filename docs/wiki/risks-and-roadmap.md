# Risks and roadmap

## P0 operational work

- Rotate and revoke every credential that appeared in repository history or a
  generated deployment artifact. Update Key Vault and follow
  `SECURITY_ROTATION.md` before the next production release.
- Confirm the production PostgreSQL service has automated backups,
  point-in-time recovery, monitoring, and a tested restore procedure.

## Engineering roadmap

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
