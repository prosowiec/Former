from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from former.formFiller import main, run_form_pipeline


default_args = {
    "owner": "you",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def run_google_form():
    from former.config import FORM_URL_GOOGLE, OPENAI_API_KEY
    from former.LLM_interface.ChatgptFormFiller import chatgptFormFiller

    filler = chatgptFormFiller(OPENAI_API_KEY)
    run_form_pipeline(FORM_URL_GOOGLE, filler)



with DAG(
    dag_id="form_filler_pipeline",
    default_args=default_args,
    description="Auto fill forms using LLM",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["forms", "automation"],
) as dag:

    google_task = PythonOperator(
        task_id="fill_google_form",
        python_callable=run_google_form,
    )


    # Run sequentially
    google_task