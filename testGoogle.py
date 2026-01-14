import time, random
from browser import launch_browser
from form_filler import fill_form
# from exporters import export_json, export_csv
from config import FORM_URL

def main():
    pw, browser, page = launch_browser()
    page.goto(FORM_URL, wait_until="networkidle")

    extracted = fill_form(page)

    # export_json(extracted)
    # export_csv(extracted)

    browser.close()
    pw.stop()
    
if __name__ == "__main__":
    main()