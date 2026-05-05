import os
import random
from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task

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
            "run_id": dag_run.run_id if dag_run else None,
        }

    # 2. Build execution plan — each item carries its own index for logging
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
                "delay_minutes": delay,
                "execution_index": i,
                "num_executions": num,
                "run_id": conf["run_id"],
            })
        return plan

    # 3. Run form filler then immediately log — single mapped task guarantees
    #    log fires right after its own execution, not after all siblings finish.
    @task
    def run_and_log(form_url: str, delay_minutes: float, execution_index: int, num_executions: int, run_id: str):
        import time
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.backend.models import AirflowProgress
        from former.fillWorkflow.config import OPENAI_API_KEY
        from former.LLM_interface.ChatgptFormFiller import chatgptFormFiller
        from former.fillWorkflow.formFiller import run_form_pipeline

        # --- run ---
        if delay_minutes > 0:
            print(f"[{execution_index + 1}/{num_executions}] Sleeping {delay_minutes:.2f} min before execution")
            time.sleep(delay_minutes * 60)

        filler = chatgptFormFiller(OPENAI_API_KEY)
        run_form_pipeline(form_url, filler)

        # --- log (runs immediately after, in the same task instance) ---
        db_url = os.environ["DATABASE_URL"]
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            execution: AirflowProgress = (
                session.query(AirflowProgress).filter_by(dag_id=run_id).first()
            )
            if execution:
                execution.numberOfSuccessfulRuns += 1
            else:
                execution = AirflowProgress(
                    dag_id=run_id,
                    numberOfSuccessfulRuns=1,
                    hasFailedRuns=False,
                    expectedTotalRuns=num_executions,
                )
                session.add(execution)
            session.commit()
            print(f"[{execution_index + 1}/{num_executions}] Logged successful run.")
        finally:
            session.close()

    # 4. DAG flow — N independent mapped tasks, each runs then logs immediately
    conf = get_conf()
    execution_plan = build_execution_plan(conf)
    run_and_log.expand_kwargs(execution_plan)