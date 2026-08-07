import random
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import PokeReturnValue, get_current_context, task, task_group


default_args = {
    "owner": "former",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="form_filler_plan",
    default_args=default_args,
    description="Schedule and trigger one form_filler_dag per reserved fill",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["forms", "automation"],
) as dag:

    @task
    def get_conf() -> dict:
        dag_run = get_current_context().get("dag_run")
        conf = (dag_run.conf if dag_run else {}) or {}
        return {
            "form_url": conf["form_url"],
            "num_executions": int(conf.get("num_executions", 1)),
            "base_interval_minutes": float(conf.get("base_interval_minutes", 10.0)),
            "interval_jitter_minutes": float(conf.get("interval_jitter_minutes", 2.0)),
            "run_id": dag_run.run_id,
            "user_id": conf["user_id"],
        }

    @task
    def build_items(conf: dict) -> list[dict]:
        import logging
        from tzlocal import get_localzone

        now = datetime.now(get_localzone())
        items = []
        cumulative_delay = 2.0
        for execution_index in range(conf["num_executions"]):
            if execution_index > 0:
                cumulative_delay += random.uniform(
                    max(
                        0.1,
                        conf["base_interval_minutes"]
                        - conf["interval_jitter_minutes"],
                    ),
                    conf["base_interval_minutes"]
                    + conf["interval_jitter_minutes"],
                )
            scheduled_time = now + timedelta(minutes=cumulative_delay)
            logging.info(
                "Execution %s scheduled for %s (in %.2f minutes)",
                execution_index,
                scheduled_time.isoformat(),
                cumulative_delay,
            )
            items.append({
                "scheduled_time": scheduled_time.isoformat(),
                "trigger_run_id": f"{conf['run_id']}__item_{execution_index}",
                "child_conf": {
                    "form_url": conf["form_url"],
                    "run_id": conf["run_id"],
                    "user_id": conf["user_id"],
                    "execution_index": execution_index,
                    "num_executions": conf["num_executions"],
                },
            })
        return items

    @task.sensor(poke_interval=10, mode="reschedule")
    def wait_until(scheduled_time: str) -> PokeReturnValue:
        target = datetime.fromisoformat(scheduled_time)
        now = datetime.now(target.tzinfo)
        return PokeReturnValue(is_done=now >= target)

    @task_group(group_id="scheduled_fill")
    def schedule_fill(
        scheduled_time: str,
        trigger_run_id: str,
        child_conf: dict,
    ) -> None:
        # Mapping the group creates a depth-first dependency for every item:
        # scheduled_fill[i].wait -> scheduled_fill[i].trigger. A later sensor
        # therefore cannot block an earlier form submission.
        wait = wait_until.override(task_id="wait")(scheduled_time)
        trigger = TriggerDagRunOperator(
            task_id="trigger",
            trigger_dag_id="form_filler_dag",
            trigger_run_id=trigger_run_id,
            conf=child_conf,
            wait_for_completion=False,
            reset_dag_run=True,
        )
        wait >> trigger

    planner_conf = get_conf()
    planned_items = build_items(planner_conf)
    schedule_fill.expand_kwargs(planned_items)
