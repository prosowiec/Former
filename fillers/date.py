def fill_date(q, answer):
    date_input = q.query_selector("input[type='date']")
    if date_input:
        date_input.click()
        date_input.fill(answer)