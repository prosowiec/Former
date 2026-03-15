import random
import dotenv
import os
from datetime import datetime, timedelta

dotenv.load_dotenv()

FORM_URL_GOOGLE = "https://docs.google.com/forms/d/e/1FAIpQLSftl5wRWwtjEhbeecNjaO880pn5vr3-25hqq7K06eEdjLY2nw/viewform?usp=header"
FORM_URL_MS = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u" # - REAL FORM

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

OUTPUT_JSON = "data/form_data.json"
OUTPUT_CSV = "data/form_data.csv"

MAX_SUBMISSIONS = 250
WAIT_BETWEEN = (30, 90)