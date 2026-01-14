import random
import time

def fill_matrix(q):
    for row in q.query_selector_all("div[role='radiogroup']"):
        radios = row.query_selector_all("div[role='radio']")
        if radios:
            time.sleep(random.uniform(0.2, 0.4))
            random.choice(radios).click()
            
            
def fill_matrix_checkbox(q, min_per_row=1, max_per_row=2):
    rows = q.query_selector_all("div[role='group']")

    for row_idx, row in enumerate(rows):
        checkboxes = row.query_selector_all("div[role='checkbox']")

        if not checkboxes:
            continue
        count = random.randint(
            min_per_row,
            min(max_per_row, len(checkboxes))
        )
        selected = random.sample(checkboxes, count)

        for box in selected:
            time.sleep(random.uniform(0.2, 0.4))
            box.scroll_into_view_if_needed()
            box.click()
