def fill_star_rating(q, value):
    stars = q.query_selector_all('span[role="radio"]')
    if 1 <= value <= len(stars):
        stars[1].click()

def fill_likert(q):
    rows = q.query_selector_all("tr")
    for row in rows:
        radios = row.query_selector_all("input[type='radio']")
        if radios:
            radios[0].check()
