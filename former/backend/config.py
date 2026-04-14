import os

AIRFLOW_HOST = os.getenv("AIRFLOW_HOST", "http://localhost:9090")
AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", f"{AIRFLOW_HOST}/api/v2")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")
DEFAULT_DAG_ID = os.getenv("AIRFLOW_DAG_ID", "form_filler_pipeline")

