import random
from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

default_args = {
    "owner": "you",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="form_filler_plan",
    default_args=default_args,
    description="Builds execution plan and triggers form_filler_execution per item",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["forms", "automation"],
) as dag:

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
            "user_id": conf.get("user_id"),
        }

    @task
    def build_confs(conf: dict) -> list:
        """One conf dict per triggered execution."""
        num = conf["num_executions"]
        base = conf["base_interval_minutes"]
        jitter = conf["interval_jitter_minutes"]
        confs = []
        for i in range(num):
            delay = 0 if i == 0 else random.uniform(
                max(0.1, base - jitter),
                base + jitter,
            )
            confs.append({
                "form_url": conf["form_url"],
                "delay_minutes": delay,
                "execution_index": i,
                "num_executions": num,
                "run_id": conf["run_id"],
                "user_id": conf["user_id"],
            })
        return confs

    @task
    def build_run_ids(conf: dict) -> list:
        """Matching list of unique trigger_run_ids — must align by index with build_confs."""
        return [
            f"{conf['run_id']}__item_{i}"
            for i in range(conf["num_executions"])
        ]

    conf = get_conf()

    # expand() fans out by index: conf[i] paired with trigger_run_id[i]
    TriggerDagRunOperator.partial(
        task_id="trigger_execution",
        trigger_dag_id="form_filler_dag",
        wait_for_completion=False,
        reset_dag_run=True,
    ).expand(
        conf=build_confs(conf),
        trigger_run_id=build_run_ids(conf),
    )