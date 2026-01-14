from detectors import detect_question_type
from extract import extract_options
from fillers import text, choice, dropdown, matrix, date, time
from navigation import next_or_submit
import random
FILLERS = {
    "short_text": text.fill_short_text,
    "paragraph": text.fill_paragraph,
    "multiple_choice": choice.fill_multiple_choice,
    "checkboxes": choice.fill_checkboxes,
    "dropdown": dropdown.fill_dropdown,
    "matrix_radio": matrix.fill_matrix,
    "date": date.fill_date,
    "time": time.fill_time,
    'matrix_checkbox': matrix.fill_matrix_checkbox,
}

def fill_form(page):
    extracted = []
    seen = set()
    qid = 1

    while True:
        questions = page.query_selector_all("div[role='listitem']")

        for q in questions:
            title_el = q.query_selector("div[role='heading']")
            if not title_el:
                continue

            title = title_el.inner_text().strip()
            qtype = detect_question_type(q)
            options = extract_options(q, qtype)
            print(f"Detected question: {title} | Type: {qtype} | Options: {options}")
            signature = (title.lower(), qtype, tuple(options))
            if signature in seen:
                continue
            seen.add(signature)

            extracted.append({
                "id": qid,
                "question": title,
                "type": qtype,
                "options": options
            })
            qid += 1

            filler = FILLERS.get(qtype)
            if filler:
                filler(q, page) if qtype == "dropdown" else filler(q)

        result = next_or_submit(page)

        if result == "next":
            time.sleep(random.uniform(1.5, 3.0))  # 👈 important
            continue
        elif result == "submitted":
            print("Form submitted successfully.")
            break

    return extracted
