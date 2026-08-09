import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.sdk import task

from dags.utils import extract_answers, record_task_failure


default_args = {
    "owner": "former",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "on_failure_callback": record_task_failure,
}


with DAG(
    dag_id="form_filler_dag",
    default_args=default_args,
    description="Single form fill run. Triggered by form_filler_plan.",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["forms", "automation"],
) as dag:

    @task
    def read_conf() -> dict:
        from airflow.operators.python import get_current_context

        dag_run = get_current_context().get("dag_run")
        conf = (dag_run.conf if dag_run else {}) or {}
        return {
            "form_url": conf["form_url"],
            "delay_minutes": float(conf.get("delay_minutes", 0)),
            "execution_index": int(conf.get("execution_index", 0)),
            "num_executions": int(conf.get("num_executions", 1)),
            "run_id": conf["run_id"],
            "user_id": conf["user_id"],
        }

    @task
    def generate_personality(conf: dict) -> dict:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.backend.models import AirflowTriggerInternalRequest
        from former.LLM_interface.personalityBuilder import PersonalityBuilder

        engine = create_engine(os.environ["DATABASE_URL"])
        session = sessionmaker(bind=engine)()
        try:
            trigger = session.query(AirflowTriggerInternalRequest).filter_by(
                run_id=conf["run_id"]
            ).first()
            if not trigger:
                raise RuntimeError(f"Trigger {conf['run_id']} does not exist")
            return PersonalityBuilder().build_personality(trigger)
        finally:
            session.close()
            engine.dispose()

    @task
    def run_form(conf: dict, personality: dict) -> dict:
        import time
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.fillWorkflow.browser import launch_browser
        from former.fillWorkflow.detectors import detect_platform
        from former.fillWorkflow.fill import fill_question
        from former.fillWorkflow.navigation import go_next_or_submit
        from former.fillWorkflow.human import human_pause, human_before_question
        from dags.utils import get_or_create_page_answers

        idx, total = conf["execution_index"], conf["num_executions"]
        if conf["delay_minutes"] > 0:
            time.sleep(conf["delay_minutes"] * 60)

        engine = create_engine(os.environ["DATABASE_URL"])
        session = sessionmaker(bind=engine)()
        playwright = browser = None
        all_questions, all_answers = [], []
        try:
            playwright, browser, page = launch_browser()
            platform = detect_platform(conf["form_url"])
            page.goto(conf["form_url"], wait_until="networkidle")
            page_idx = 0
            while True:
                extracted, page_elements = extract_answers(page, platform, page_idx)
                answers = get_or_create_page_answers(
                    session,
                    page_idx,
                    extracted,
                    personality,
                    conf["form_url"],
                    conf["user_id"],
                )
                for (question, qtype), answer in zip(page_elements, answers):
                    human_before_question(page, question)
                    fill_question(page, question, platform, qtype, answer)
                all_questions.extend(extracted)
                all_answers.extend(answers)
                human_pause(1.5, 3.0)
                if go_next_or_submit(page, platform) == "submitted":
                    human_pause(1.5, 3.0)
                    break
                page_idx += 1
            return {"success": True, "error": None, "questions": all_questions, "answers": all_answers}
        except Exception as exc:
            return {"success": False, "error": str(exc), "questions": all_questions, "answers": all_answers}
        finally:
            if browser is not None:
                browser.close()
            if playwright is not None:
                playwright.stop()
            session.close()
            engine.dispose()
            print(f"Child {idx + 1}/{total} finished")

    @task
    def update_status(conf: dict, fill_result: dict) -> None:
        from dags.utils import record_terminal_child

        record_terminal_child(conf, fill_result)

    child_conf = read_conf()
    child_personality = generate_personality(child_conf)
    child_result = run_form(child_conf, child_personality)
    update_status(child_conf, child_result)
