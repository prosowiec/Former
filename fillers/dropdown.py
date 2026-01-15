import random
import time

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
