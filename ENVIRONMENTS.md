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

```sh
docker compose up --build
```

## Production

- The deployment must set `APP_ENV=production`.
- Use `.env.production.example` as the variable contract only; inject real
  values through the deployment platform's secret/configuration system.
- Production must not define legacy `LOCAL_*`, `ENV`, or `AIRFLOW_MODE`
  variables.

The canonical variables are `DATABASE_URL`, `AIRFLOW_DB_URI`, `AIRFLOW_HOST`,
`AIRFLOW_BASE_URL`, `FRONTEND_URL`, and the corresponding credential/secret
variables listed in the templates.
