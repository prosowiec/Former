from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta
import random
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook

default_args = {
    "owner": "you",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="form_filler_pipeline",
    default_args=default_args,
    description="Auto fill forms using LLM",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["forms", "automation"],
) as dag:


    # 1. Read config safely (runtime only)
    @task
    def get_conf():
        from airflow.operators.python import get_current_context
        context = get_current_context()
        dag_run = context.get("dag_run")
        conf = (dag_run.conf if dag_run else {}) or {}

        return {
            "form_url": conf.get("form_url"),
            "num_executions": int(conf.get("num_executions", 1)),
            "base_interval_minutes": float(conf.get("base_interval_minutes", 10.0)),
            "interval_jitter_minutes": float(conf.get("interval_jitter_minutes", 2.0)),
        }


    # 2. Build execution plan (ALL runtime safe)
    @task
    def build_execution_plan(conf: dict):
        num = conf["num_executions"]
        base = conf["base_interval_minutes"]
        jitter = conf["interval_jitter_minutes"]

        plan = []

        for i in range(num):
            delay = 0 if i == 0 else random.uniform(
                max(0.1, base - jitter),
                base + jitter,
            )

            plan.append({
                "form_url": conf["form_url"],
                "delay_minutes": delay
            })

        return plan
    
    @task
    def log_execution(conf):
        from former.backend.models import AirflowProgress
        from sqlalchemy.orm import sessionmaker
        hook = MsSqlHook(mssql_conn_id="mssql_default")
        engine = hook.get_sqlalchemy_engine()

        Session = sessionmaker(bind=engine)
        session = Session()

        execution : AirflowProgress = session.query(AirflowProgress).filter_by(dag_id=dag.dag_id).first()
        if execution:
            execution.numberOfSuccessfulRuns += 1
            session.add(execution)
        else:
            execution = AirflowProgress(
                dag_id=dag.dag_id,
                numberOfSuccessfulRuns=1,
                hasFailedRuns=False,
                expectedTotalRuns=conf["num_executions"]
            )
            session.add(execution)
            
        session.commit()
        session.close()

    @task
    def run_single_execution(form_url: str, delay_minutes: float):
        import time
        from former.fillWorkflow.config import OPENAI_API_KEY
        from former.LLM_interface.ChatgptFormFiller import chatgptFormFiller
        from former.fillWorkflow.formFiller import run_form_pipeline

        if delay_minutes > 0:
            print(f"Sleeping {delay_minutes:.2f} minutes before execution")
            time.sleep(delay_minutes * 60)

        filler = chatgptFormFiller(OPENAI_API_KEY)
        run_form_pipeline(form_url, filler)


    # 4. DAG flow
    conf = get_conf()

    execution_plan = build_execution_plan(conf)

    executions = run_single_execution.expand_kwargs(execution_plan)
    logs = log_execution(conf)

    executions >> logs