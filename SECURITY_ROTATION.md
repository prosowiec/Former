# Production secret rotation

The repository and deployment manifests contain only environment-variable or
Key Vault references. Never generate `app.yaml` by merging a local `.env` file.

Before the next deployment, an operator must rotate every value that has ever
appeared in repository history or a generated deployment artifact:

1. Rotate OpenAI, Gemini, Stripe, Google OAuth, SMTP, Airflow,
   database, application-session, and JWT credentials at their issuers.
2. Write the replacements directly to Azure Key Vault under the names referenced
   by `app.yaml`; do not stage them in a tracked JSON or YAML file.
3. Revoke old key versions after the new Container App revision is healthy.
4. Purge exposed values from Git history if this repository has been shared.
5. Run a secret scanner over the full history before declaring rotation complete.

Secret rotation is an external operation and cannot be completed by a source
change alone. The ignored `azure-key-vault-secrets.production.json` workflow is
deprecated; use direct Key Vault writes from an approved operator environment.
