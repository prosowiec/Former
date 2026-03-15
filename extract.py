from extractors.extractGoogle import GOOGLE_EXTRACTORS
from extractors.extractMS import MS_EXTRACTORS

def remove_aria_hidden_children(q):
    """
    Removes all child elements with aria-hidden='true' from the element.
    Returns the cleaned element.
    """
    # Find all children with aria-hidden="true" and remove them
    hidden_elements = q.query_selector_all("[aria-hidden='true']")
    for elem in hidden_elements:
        elem.evaluate("el => el.remove()")
    
    return q

def extract_options(q, qtype, platform):
    """
    Dispatch extractor based on detected question type
    Returns structured extraction dict or None
    """
    
    if platform == "MS":
        extractor = MS_EXTRACTORS.get(qtype)
    else:  # GOOGLE
        # Remove all aria-hidden children
        q = remove_aria_hidden_children(q)
        extractor = GOOGLE_EXTRACTORS.get(qtype)
        
    if not extractor:
        return []
    
    return extractor(q)

def extract_question_items(page, platform):
    """
    Docstring for extract_question_items
    
    :param page: Description
    :param platform: Description
    """
    if platform == "MS":
        question_items = page.query_selector_all("div[data-automation-id='questionItem']")
    else:  # GOOGLE
        question_items = page.query_selector_all("div[role='listitem']")
        
    return question_items

def extract_title(q, platform):
    if platform == "MS":
        title_el = q.query_selector("span[data-automation-id='questionTitle']")
        return title_el.inner_text().strip() if title_el else ""
    else:  # GOOGLE
        title_el = q.query_selector("div[role='heading']")
        return title_el.inner_text().strip() if title_el else ""