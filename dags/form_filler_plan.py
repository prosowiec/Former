import random
from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.standard.sensors.date_time import DateTimeSensorAsync

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
    def build_items(conf: dict) -> list:
        import logging
        from tzlocal import get_localzone
        local_tz = get_localzone()
        now = datetime.now(local_tz)
        logging.info("Local timezone: %s | now: %s", local_tz, now.isoformat())

        items = []
        cumulative_delay = 2.0  # minimum buffer so item 0 is always in the future
        for i in range(conf["num_executions"]):
            if i > 0:
                cumulative_delay += random.uniform(
                    max(0.1, conf["base_interval_minutes"] - conf["interval_jitter_minutes"]),
                    conf["base_interval_minutes"] + conf["interval_jitter_minutes"],
                )
            scheduled_time = now + timedelta(minutes=cumulative_delay)
            logging.info("[ITEM %s] scheduled_time=%s (in %.1f min)", i, scheduled_time.isoformat(), cumulative_delay)
            items.append({
                "scheduled_time": scheduled_time.isoformat(),
                "trigger_run_id": f"{conf['run_id']}__item_{i}",
                "conf": {
                    "form_url": conf["form_url"],
                    "user_id": conf["user_id"],
                    "execution_index": i,
                    "num_executions": conf["num_executions"],
                },
            })
        return items

    @task
    def extract_scheduled_times(items: list) -> list:
        import logging
        from tzlocal import get_localzone
        from datetime import datetime
        local_tz = get_localzone()
        now = datetime.now(local_tz)
        times = []
        for item in items:
            t = datetime.fromisoformat(item["scheduled_time"])
            # Safety guard: ensure target is always at least 10s in the future
            if t <= now:
                from datetime import timedelta
                t = now + timedelta(seconds=10)
                logging.warning("Scheduled time was in the past, bumped to %s", t.isoformat())
            times.append(t.isoformat())
        return times

    @task
    def extract_confs(items: list) -> list:
        return [item["conf"] for item in items]

    @task
    def extract_run_ids(items: list) -> list:
        return [item["trigger_run_id"] for item in items]

    @task
    def zip_trigger_inputs(items: list) -> list:
        return [
            {"conf": item["conf"], "trigger_run_id": item["trigger_run_id"]}
            for item in items
        ]

    conf = get_conf()
    items = build_items(conf)

    wait = DateTimeSensorAsync.partial(
        task_id="wait_for_schedule",
        poke_interval=30,
    ).expand(
        target_time=extract_scheduled_times(items),
    )

    trigger = TriggerDagRunOperator.partial(
        task_id="trigger_execution",
        trigger_dag_id="form_filler_dag",
        wait_for_completion=False,
        reset_dag_run=True,
    ).expand_kwargs(zip_trigger_inputs(items))

    wait >> trigger