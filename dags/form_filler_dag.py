import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.sdk import task
from dags.utils import extract_answers

default_args = {
    "owner": "you",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
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
        context = get_current_context()
        dag_run = context.get("dag_run")
        conf = (dag_run.conf if dag_run else {}) or {}
        return {
            "form_url": conf["form_url"],
            "delay_minutes": float(conf.get("delay_minutes", 0)),
            "execution_index": int(conf.get("execution_index", 0)),
            "num_executions": int(conf.get("num_executions", 1)),
            "run_id": conf.get("run_id"),
            "user_id": conf.get("user_id"),
        }
    
    @task
    def generate_personality(conf: dict) -> dict:
        from former.backend.models import AirflowTriggerInternalRequest
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.LLM_interface.personalityBuilder import PersonalityBuilder

        
        engine = create_engine(os.environ["DATABASE_URL"])
        Session = sessionmaker(bind=engine)
        session = Session()
        fromData = session.query(AirflowTriggerInternalRequest).filter_by(run_id=conf["run_id"]).first()

        personality = PersonalityBuilder().build_personality(fromData)
        print(f"Generated personality for run_id {conf['run_id']}: {personality}")
        
        return personality


    @task
    def run_form(conf: dict, personality: dict) -> dict:
        """
        Per-page loop: extract → cache check → (miss) LLM → store → fill → next.
        Browser stays open across all pages.
        Collects all questions+answers per page for the run record.
        """
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
        form_url = conf["form_url"]

        if conf["delay_minutes"] > 0:
            print(f"[{idx + 1}/{total}] Sleeping {conf['delay_minutes']:.2f} min")
            time.sleep(conf["delay_minutes"] * 60)

        engine = create_engine(os.environ["DATABASE_URL"])
        Session = sessionmaker(bind=engine)
        session = Session()


        all_questions = []
        all_answers = []

        playwright, browser, page = launch_browser()
        platform = detect_platform(form_url)
        page.goto(form_url, wait_until="networkidle")
        page_idx = 0
        while True:
            
            extracted, page_elements = extract_answers(page, platform, page_idx)

            print(f"[{idx + 1}/{total}] Page {page_idx}: {len(extracted)} questions")
            answers = get_or_create_page_answers(session, page_idx, extracted, personality, form_url)

            for (q, qtype), answer in zip(page_elements, answers):
                human_before_question(page, q)
                fill_question(page, q, platform, qtype, answer)

            all_questions.extend(extracted)
            all_answers.extend(answers)

            human_pause(1.5, 3.0)
            if go_next_or_submit(page, platform) == "submitted":
                human_pause(1.5, 3.0)
                print(f"[{idx + 1}/{total}] Submitted after {page_idx + 1} page(s)")
                break
            
            page_idx += 1

        browser.close()
        playwright.stop()
        session.close()

        return {"success": True, "error": None,
                "questions": all_questions, "answers": all_answers}

    @task
    def update_status(conf: dict, fill_result: dict) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.backend.models import FormRunAnswers, AirflowProgress

        success = fill_result["success"]
        idx, total = conf["execution_index"], conf["num_executions"]

        engine = create_engine(os.environ["DATABASE_URL"])
        session = sessionmaker(bind=engine)()
        try:

            session.add(FormRunAnswers(
                run_id=conf["run_id"],
                execution_index=idx,
                form_url=conf["form_url"],
                answers=fill_result["answers"],
                questions=fill_result["questions"],
                success=success,
                error_message=fill_result.get("error"),
            ))


            progress = session.query(AirflowProgress).filter_by(run_id=conf["run_id"]).first()
            if progress:
                if success:
                    progress.numberOfSuccessfulRuns += 1
                else:
                    progress.hasFailedRuns = True
            else:
                session.add(AirflowProgress(
                    run_id=conf["run_id"],
                    numberOfSuccessfulRuns=1 if success else 0,
                    hasFailedRuns=not success,
                    expectedTotalRuns=total,
                ))

            session.commit()
            print(f"{'✓' if success else '✗'} [{idx + 1}/{total}] "
                  f"{'Success' if success else 'Failed: ' + str(fill_result.get('error'))}")
        finally:
            session.close()
            
    @task
    def update_billing(conf: dict, fill_result: dict) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.backend.models import UserBillingInfo

        if not fill_result["success"]:
            return

        engine = create_engine(os.environ["DATABASE_URL"])
        session = sessionmaker(bind=engine)()

        try:
            billing = (
                session.query(UserBillingInfo)
                .filter(UserBillingInfo.user_id == conf["user_id"])
                .first()
            )

            if billing:
                billing.form_fills_remaining = max(
                    0,
                    billing.form_fills_remaining - 1
                )
                billing.form_fills_used += 1

                session.commit()

                print(
                    f"Billing updated for user {conf['user_id']}: "
                    f"remaining={billing.form_fills_remaining}, "
                    f"used={billing.form_fills_used}"
                )
            else:
                print(f"No billing record found for user {conf['user_id']}")

        finally:
            session.close()

    conf = read_conf()
    personality = generate_personality(conf)
    fill_result = run_form(conf, personality)

    status_task = update_status(conf, fill_result)
    billing_task = update_billing(conf, fill_result)

    status_task >> billing_task