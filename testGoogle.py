import time, random
from browser import launch_browser
from form_filler import fill_form
from exporters import export_json, export_csv
from config import FORM_URL
from gemini import GeminiFormFiller
import dotenv
import os

dotenv.load_dotenv()


def main():
    pw, browser, page = launch_browser()
    page.goto(FORM_URL, wait_until="networkidle")
    API_KEY = os.getenv("GEMINI_API_KEY")
    filler = GeminiFormFiller(api_key=API_KEY)
    extracted = fill_form(page, filler)

    export_json(extracted, "data/extracted_data.json")
    export_csv(extracted, "data/extracted_data.csv")

    browser.close()
    pw.stop()
    
if __name__ == "__main__":
    main()