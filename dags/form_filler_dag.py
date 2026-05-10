import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.sdk import task

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
        }

    @task
    def run_form(conf: dict) -> dict:
        """
        Per-page loop: extract → cache check → (miss) LLM → store → fill → next.
        Browser stays open across all pages.
        Collects all questions+answers per page for the run record.
        """
        import time
        import json
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.backend.models import FormPageAnswersCache
        from former.fillWorkflow.browser import launch_browser
        from former.fillWorkflow.detectors import detect_question_type, detect_platform
        from former.fillWorkflow.extract import extract_options, extract_title, extract_question_items
        from former.fillWorkflow.fill import fill_question
        from former.fillWorkflow.navigation import go_next_or_submit
        from former.fillWorkflow.human import human_pause, human_before_question
        from former.fillWorkflow.config import OPENAI_API_KEY
        from former.LLM_interface.ChatgptFormFiller import chatgptFormFiller

        idx, total = conf["execution_index"], conf["num_executions"]
        form_url = conf["form_url"]

        if conf["delay_minutes"] > 0:
            print(f"[{idx + 1}/{total}] Sleeping {conf['delay_minutes']:.2f} min")
            time.sleep(conf["delay_minutes"] * 60)

        engine = create_engine(os.environ["DATABASE_URL"])
        Session = sessionmaker(bind=engine)

        def get_or_create_page_answers(session, page_idx: int, extracted: list) -> list:
            cached = (
                session.query(FormPageAnswersCache)
                .filter_by(form_url=form_url, page_index=page_idx)
                .first()
            )
            if cached:
                print(f"  Page {page_idx}: cache hit")
                return cached.answers

            print(f"  Page {page_idx}: cache miss — calling LLM")
            answers = chatgptFormFiller(OPENAI_API_KEY).get_selection(extracted)
            session.add(FormPageAnswersCache(
                form_url=form_url,
                page_index=page_idx,
                questions=extracted,
                answers=answers,
            ))
            session.commit()
            print(f"  Page {page_idx}: answers stored")
            return answers

        all_questions = []
        all_answers = []

        playwright, browser, page = launch_browser()
        try:
            platform = detect_platform(form_url)
            page.goto(form_url, wait_until="networkidle")
            page_idx = 0
            session = Session()
            try:
                while True:
                    seen = set()
                    extracted = []
                    page_elements = []

                    for q in extract_question_items(page, platform):
                        title = extract_title(q, platform)
                        qtype = detect_question_type(q, platform)
                        if qtype == "section_title":
                            continue
                        options = extract_options(q, qtype, platform)
                        sig = (title.lower(), qtype, json.dumps(options, sort_keys=True, default=str))
                        if sig in seen:
                            continue
                        seen.add(sig)
                        extracted.append({"id": page_idx * 100 + len(extracted) + 1,
                                          "question": title, "type": qtype, "options": options})
                        page_elements.append((q, qtype))

                    print(f"[{idx + 1}/{total}] Page {page_idx}: {len(extracted)} questions")
                    answers = get_or_create_page_answers(session, page_idx, extracted)

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
            finally:
                session.close()

        except Exception as e:
            return {"success": False, "error": str(e),
                    "questions": all_questions, "answers": all_answers}
        finally:
            browser.close()
            playwright.stop()

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
            # FormRunAnswers.answers + questions are non-nullable — always pass them
            session.add(FormRunAnswers(
                run_id=conf["run_id"],
                execution_index=idx,
                form_url=conf["form_url"],
                answers=fill_result["answers"],
                questions=fill_result["questions"],
                success=success,
                error_message=fill_result.get("error"),
            ))

            # AirflowProgress uses run_id as primary key (not dag_id)
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

    conf = read_conf()
    fill_result = run_form(conf)
    update_status(conf, fill_result)