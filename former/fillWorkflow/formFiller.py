import os
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
    dag_id="form_filler_execution",
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
        Mirrors go_through_form / run_form_pipeline exactly.
        Per page: extract → check cache → (miss) LLM → store → fill → next.
        Browser stays open the whole time.
        """
        import time
        import json
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from former.backend.models import FormPageAnswersCache, FormRunAnswers
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
            """
            Returns answers for this page from cache if available,
            otherwise calls LLM and stores result.
            Cache key: (form_url, page_idx).
            """
            cached = (
                session.query(FormPageAnswersCache)
                .filter_by(form_url=form_url, page_index=page_idx)
                .first()
            )
            if cached:
                print(f"  Page {page_idx}: cache hit")
                return cached.answers

            print(f"  Page {page_idx}: cache miss — calling LLM")
            chat_filler = chatgptFormFiller(OPENAI_API_KEY)
            answers = chat_filler.get_selection(extracted)

            session.add(FormPageAnswersCache(
                form_url=form_url,
                page_index=page_idx,
                questions=extracted,
                answers=answers,
            ))
            session.commit()
            print(f"  Page {page_idx}: answers stored")
            return answers

        playwright, browser, page = launch_browser()
        try:
            platform = detect_platform(form_url)
            page.goto(form_url, wait_until="networkidle")

            page_idx = 0
            session = Session()
            try:
                while True:
                    # ── Extract ──────────────────────────────────────────────
                    seen = set()
                    extracted = []
                    page_questions = []  # (element, qtype) pairs — needed for filling
                    qid = 1

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
                        extracted.append({"id": qid, "question": title, "type": qtype, "options": options})
                        page_questions.append((q, qtype))
                        qid += 1

                    print(f"[{idx + 1}/{total}] Page {page_idx}: {len(extracted)} questions")

                    # ── Cache check / LLM call ────────────────────────────────
                    answers = get_or_create_page_answers(session, page_idx, extracted)

                    # ── Fill ──────────────────────────────────────────────────
                    for (q, qtype), answer in zip(page_questions, answers):
                        human_before_question(page, q)
                        fill_question(page, q, platform, qtype, answer)

                    human_pause(1.5, 3.0)

                    # ── Navigate ──────────────────────────────────────────────
                    if go_next_or_submit(page, platform) == "submitted":
                        human_pause(1.5, 3.0)
                        print(f"[{idx + 1}/{total}] Submitted after {page_idx + 1} page(s)")
                        break

                    page_idx += 1
            finally:
                session.close()

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            browser.close()
            playwright.stop()

        return {"success": True, "error": None}

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
                success=success,
                error_message=fill_result.get("error"),
            ))

            progress = session.query(AirflowProgress).filter_by(dag_id=conf["run_id"]).first()
            if progress:
                if success:
                    progress.numberOfSuccessfulRuns += 1
                else:
                    progress.hasFailedRuns = True
            else:
                session.add(AirflowProgress(
                    dag_id=conf["run_id"],
                    numberOfSuccessfulRuns=1 if success else 0,
                    hasFailedRuns=not success,
                    expectedTotalRuns=total,
                ))

            session.commit()
            print(f"{'✓' if success else '✗'} [{idx + 1}/{total}] {'Success' if success else 'Failed: ' + str(fill_result.get('error'))}")
        finally:
            session.close()

    conf = read_conf()
    fill_result = run_form(conf)
    update_status(conf, fill_result)