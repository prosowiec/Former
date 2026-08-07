# Environments

The application uses the same variable names everywhere. Environment-specific
selection belongs to the deployment layer, not to Python code.

## Local development

- `docker-compose.yml` always sets `APP_ENV=local`.
- `.env` contains local secrets and connection values and is ignored by Git.
- Copy `.env.example` when creating a new local configuration.
- Containers reach PostgreSQL on the host through `host.docker.internal`.
- The backend reaches Airflow through the Compose service name
  `airflow-api-server`.

Start locally with:

```powershell
Copy-Item .env.example .env  # only when .env does not exist yet
.\scripts\init_local_secrets.ps1
docker compose up --build
```

## Production

- The deployment must set `APP_ENV=production`.
- Use `.env.production.example` as the variable contract only; inject real
  values through the deployment platform's secret/configuration system.
- Production must not define legacy `LOCAL_*`, `ENV`, or `AIRFLOW_MODE`
  variables.

### Azure Key Vault

`azure-key-vault-secrets.example.json` documents production secret names only.
Write rotated values directly to Key Vault from an approved operator session;
do not create a plaintext production JSON file. `app.yaml` contains only Key
Vault/`secretRef` mappings and non-secret configuration.

Key Vault names use hyphens because Azure Key Vault does not allow underscores.
Map container environment variables such as `DATABASE_URL` to the corresponding
Key Vault secret such as `database-url`. Production database URLs include
`sslmode=require`; local `.env` values are unaffected.

The canonical variables are `DATABASE_URL`, `AIRFLOW_DB_URI`, `AIRFLOW_HOST`,
`AIRFLOW_BASE_URL`, `FRONTEND_URL`, and the corresponding credential/secret
variables listed in the templates.

Run `app-migrate-job.yaml` before deploying a new application revision.
Production database URLs must point to durable managed PostgreSQL.
