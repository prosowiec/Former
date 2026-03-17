# tests/test_e2e_forms.py

import os
import pytest
import sys
print(sys.path)


from former.formFiller import main
from TestResponses import testResponses

FORM_URL_GOOGLE = "https://docs.google.com/forms/d/e/1FAIpQLSftl5wRWwtjEhbeecNjaO880pn5vr3-25hqq7K06eEdjLY2nw/viewform?usp=header"
FORM_URL_MS = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u" # - REAL FORM

@pytest.mark.e2e
@pytest.mark.parametrize("form_url", [
    FORM_URL_GOOGLE,
    FORM_URL_MS])
def test_e2e_form_submission(form_url):
    assert form_url is not None, "Form URL must be set"

    filler = testResponses()

    # run full pipeline
    main(FORM_URL=form_url, chat_filler=filler)

    # If no exception → success