import random
import time

def fill_multiple_choice(q):
    radios = q.query_selector_all("div[role='radio']")
    if radios:
        random.choice(radios).click()

def fill_checkboxes(q):
    boxes = q.query_selector_all("div[data-answer-value]")
    for box in random.sample(boxes, random.randint(1, min(2, len(boxes)))):
        time.sleep(random.uniform(0.2, 0.5))
        box.click()