def fill_date(q):
    date_input = q.query_selector("input[type='date']")
    if date_input:
        date_input.click()
        date_input.fill("2023-06-15")  