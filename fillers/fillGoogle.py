import random
import time
from human import human_type, human_pause


def fill_linear_scale_radio(q, answer):
    radios = q.query_selector_all("div[role='radio']")
    answer = int(answer)
    if answer >= 1 and answer <= len(radios):
        radios[answer-1].click()

def fill_checkboxes(q, answers):
    boxes = q.query_selector_all("div[data-value]")
    for box in boxes:
        text = box.get_attribute("data-value").strip()
        if text in answers:
            time.sleep(random.uniform(0.2, 0.5))
            box.click()

def fill_date(q, answer):
    date_input = q.query_selector("input[type='date']")
    if date_input:
        date_input.click()
        date_input.fill(answer)
        
def fill_dropdown(q, page, answer):
    dropdown = q.query_selector("div[role='listbox']")
    if not dropdown:
        return

    dropdown.click()
    time.sleep(1)

    options = page.query_selector_all("div[role='option'][aria-selected='false']")
    valid = [o for o in options if o.get_attribute("data-value")]

    for o in valid:
        if o.get_attribute("data-value").strip().lower() == answer.lower():
            o.click()
            return

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

def fill_short_text(q, answer):
    input_el = q.query_selector("input[type='text']")
    if input_el:
        input_el.click()
        human_type(input_el, answer)

def fill_paragraph(q, answer):
    textarea = q.query_selector("textarea")
    if textarea:
        textarea.click()
        human_type(textarea, answer)
        
def fill_time(q, answer):
    time_input = q.query_selector_all("input[maxlength='2']")
    answer = answer.strip()
    answer = answer.split(":")
    if len(time_input) < 2: 
        print("⚠️ Time inputs not found") 
        return # Order is always: hour, minute 
    hour_input = time_input[0] 
    minute_input = time_input[1] 
    hour_input.click() 
    hour_input.fill(answer[0]) 
    human_pause(0.2, 0.5)
    minute_input.click() 
    minute_input.fill(answer[0])