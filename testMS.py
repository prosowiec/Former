from playwright.sync_api import sync_playwright
import json
import csv
import time
import random
from browser import launch_browser
from detectors import detect_MS_question_type
from extractors.extractMS import *
from human import human_type, human_pause, human_mouse_move, human_scroll
from navigation import go_next_or_submit_MS
from fillers.fillMS import fill_likert
ANSWERS = [
    "Good experience overall",
    "It was fine",
    "No major issues",
    "Pretty straightforward",
]

FORM_URL = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u"

OUTPUT_JSON = "form_data.json"
OUTPUT_CSV = "form_data.csv"



    

def main(pw, browser, page):
    
    # Use persistent context instead of regular browser
    page.goto(FORM_URL, wait_until="networkidle")
    
    # Random initial interactions
    human_pause(2, 4)
    human_mouse_move(page)
    human_scroll(page)
    
    extracted = []
    question_ID = 1
    
    while True:
        page.wait_for_selector("div[data-automation-id='questionItem']", timeout=10000)
        questions = page.query_selector_all("div[data-automation-id='questionItem']")
        
        # Extract question data
        for i, q in enumerate(questions, 1):
            title_el = q.query_selector("div[data-automation-id='questionTitle']")
            title = title_el.inner_text().strip() if title_el else f"Question {i}"
            
            q_type = detect_MS_question_type(q)
            options = []
            instructions = []
            
            if q_type in ["multiple_choice", "dropdown"]:
                options = extract_options(q)
            if q_type == "star_rating":
                stars = q.query_selector_all("span[role='radio']")
                options = [s.get_attribute("aria-label") for s in stars]
            elif q_type == "likert":
                options, instructions = extract_likert_options(page)
            
            if instructions:
                for instr in instructions:
                    extracted.append({
                        "id": question_ID,
                        "question": instr,
                        "type": q_type,
                        "options": options
                    })
                    question_ID += 1
            else:
                extracted.append({
                    "id": question_ID,
                    "question": title,
                    "type": q_type,
                    "options": options
                })
                question_ID += 1
        
        # Fill out form with realistic behavior
        for idx, q in enumerate(questions):
            # Random mouse movement before each question
            info = extracted[idx]
            qtype = info["type"]
            human_mouse_move(page)
            human_pause(0.8, 2.0)
            
            # Scroll question into view naturally
            q.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.3, 0.7))
            
            # Text input
            if qtype == "text":
                text_input = q.query_selector("input[type='text']")

                text_input.click()
                time.sleep(random.uniform(0.2, 0.5))
                human_type(text_input, random.choice(ANSWERS))
            
            # Textarea
            
            if qtype == "paragraph":
                textarea = q.query_selector("textarea")
                textarea.click()
                time.sleep(random.uniform(0.3, 0.6))
                human_type(textarea, random.choice(ANSWERS))
            
            # Multiple choice
            choices = q.query_selector_all("div[data-automation-id='choiceItem']")
            if choices:
                choice_idx = random.randint(0, min(2, len(choices)-1))  # Vary selection
                time.sleep(random.uniform(0.2, 0.6))
                choices[choice_idx].click()
            
            # Dropdown
            dropdown = q.query_selector("select")
            if dropdown:
                time.sleep(random.uniform(0.3, 0.7))
                dropdown.select_option(index=random.randint(0, 1))
            
            # Star rating
            star_rating = q.query_selector("div[role='radiogroup'] span[role='radio']")
            if star_rating:
                stars = q.query_selector_all("span[role='radio']")
                star_idx = random.randint(max(0, len(stars)-3), len(stars)-1)
                time.sleep(random.uniform(0.2, 0.5))
                stars[star_idx].click()
            
            # Likert
            if qtype == "likert":
                fill_likert(q)
            
            # Occasional scroll
            if random.random() < 0.3:
                human_scroll(page)
        
        human_pause(1.5, 3.0)
        
        # Navigate or submit
        result = go_next_or_submit_MS(page)
        if result == "submitted":
            time.sleep(3)
            break
    


if __name__ == "__main__":
    for e in range(250):
        pw, browser, page = launch_browser()
        print(f"\n🔄 Submission {e+1}/250")
        main(pw, browser, page)
        # CRITICAL: Add delay between submissions
        wait_time = random.uniform(30, 90)  # 30-90 seconds between forms
        print(f"⏳ Waiting {wait_time:.1f}s before next submission...")
        time.sleep(wait_time)
        browser.close()
        pw.stop()
