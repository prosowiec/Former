import random
import time

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