from detectors import detect_GOOGLE_question_type
from extract import extract_options
from fillers import text, choice, dropdown, matrix, date, time
from navigation import next_or_submit
import random
from gemini import GeminiFormFiller

FILLERS = {
    "short_text": text.fill_short_text,
    "paragraph": text.fill_paragraph,
    "linear_scale_radio": choice.fill_linear_scale_radio,
    "checkboxes": choice.fill_checkboxes,
    "dropdown": dropdown.fill_dropdown,
    "matrix_radio": matrix.fill_matrix_radio,
    'multiple_choice': choice.fill_checkboxes,
    "date": date.fill_date,
    "time": time.fill_time,
    'matrix_checkbox': matrix.fill_matrix_checkbox,
}

def fill_form(page, chat_filler: GeminiFormFiller):
    qid = 1

    while True:
        questions = page.query_selector_all("div[role='listitem']")
        processed_qestions = []
        extracted = []
        seen = set()

        for q in questions:
            title_el = q.query_selector("div[role='heading']")
            if not title_el:
                continue

            title = title_el.inner_text().strip()
            qtype = detect_GOOGLE_question_type(q)
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
            processed_qestions.append((q, qtype))
            qid += 1

        # TODO : Make responos
        answered_form = chat_filler.selector_test(extracted)
        print("Answered form:", answered_form)
        
        for (q, qtype), answer in zip(processed_qestions, answered_form):
            filler = FILLERS.get(qtype)
            if filler:
                filler(q, page, answer['ANSWERS']) if qtype == "dropdown" else filler(q, answer['ANSWERS'])

        result = next_or_submit(page)

        if result == "next":
            time.sleep(random.uniform(1.5, 3.0))  # 👈 important
            continue
        elif result == "submitted":
            print("Form submitted successfully.")
            break

    return extracted
