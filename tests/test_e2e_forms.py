import pytest
from former.formFiller import run_form_pipeline
from TestResponses import testResponses

FORM_URL_GOOGLE = "https://docs.google.com/forms/d/e/1FAIpQLSf6uyAWNw1p4NL-Q4Q4o5M4avpsQZ0or7iL4PLHraAXculZEw/viewform?usp=dialog"
FORM_URL_MS = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u" # - REAL FORM

@pytest.mark.e2e
@pytest.mark.parametrize("form_url", [
    FORM_URL_GOOGLE,
    FORM_URL_MS])
def test_e2e_form_submission(form_url):
    assert form_url is not None, "Form URL must be set"

    filler = testResponses()

    # run full pipeline
    run_form_pipeline(form_url, filler)

    # If no exception → success
    
    
test_e2e_form_submission(FORM_URL_GOOGLE)