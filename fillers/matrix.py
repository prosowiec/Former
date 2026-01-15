import random
import time

def fill_matrix_radio(q, answer):
    rows = q.query_selector_all("div[role='radiogroup']")

    for row in rows:
        radios = row.query_selector_all("div[role='radio']")
        if not radios:
            continue

        row_name_el = row.query_selector("div[class='V4d7Ke wzWPxe OIC90c']")
        if not row_name_el:
            continue

        row_name = row_name_el.inner_text().strip()
        selected_answer = answer.get(row_name)

        if not selected_answer:
            continue

        for radio in radios:
            radio_value = radio.get_attribute("data-answer-value")
            if radio_value and radio_value.strip() == selected_answer:
                time.sleep(random.uniform(0.2, 0.4))
                radio.scroll_into_view_if_needed()
                radio.click()
                break
            
            
def fill_matrix_checkbox(q, answer):
    rows = q.query_selector_all("div[role='group']")

    for row_idx, row in enumerate(rows):
        checkboxes = row.query_selector_all("div[role='checkbox']")
        row_name = row.query_selector("div[class='V4d7Ke wzWPxe OIC90c']").inner_text().strip()
        if not checkboxes:
            continue
        
        selected_answers = answer.get(row_name, [])
        for box in checkboxes:
            box_value = box.get_attribute("data-answer-value")
            if box_value and box_value.strip() in selected_answers:
                time.sleep(random.uniform(0.2, 0.4))
                box.scroll_into_view_if_needed()
                box.click()
