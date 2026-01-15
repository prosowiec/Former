from playwright.sync_api import sync_playwright
import json
import csv
import time
import random
from browser import launch_browser

ANSWERS = [
    "Good experience overall",
    "It was fine",
    "No major issues",
    "Pretty straightforward",
]

FORM_URL = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=W0Pa0OendE2krvcs-POy23esuPnlaW5LjSJAQ8hH3ThUN0hQSTg1WDc2Qk1FWFZKRVFKVEg0RzBDOC4u"

OUTPUT_JSON = "form_data.json"
OUTPUT_CSV = "form_data.csv"

def is_likert(q):
    return (
        q.query_selector("table") is not None and
        q.query_selector("input[type='radio']") is not None
    )

def detect_question_type(q):
    if is_likert(q):
        return "likert"
    if q.query_selector("div[role='radiogroup'] span[role='radio']"):
        return "star_rating"
    if q.query_selector("input[type='text']"):
        return "short_text"
    if q.query_selector("textarea"):
        return "paragraph"
    if q.query_selector("div[data-automation-id='choiceItem']"):
        return "multiple_choice"
    if q.query_selector("select"):
        return "dropdown"
    return "unknown"

def extract_options(q):
    options = []
    choice_items = q.query_selector_all("div[data-automation-id='choiceItem']")
    for c in choice_items:
        options.append(c.inner_text().strip())
    return options

def is_star_rating(q):
    return q.query_selector('div[role="radiogroup"] span[role="radio"]') is not None

def extract_star_count(q):
    stars = q.query_selector_all('span[role="radio"]')
    return len(stars)

def extract_star_labels(q):
    stars = q.query_selector_all('span[role="radio"]')
    return [s.get_attribute("aria-label") for s in stars]

def extract_likert_options(page):
    headers = page.locator('th[data-automation-id="likerTableTh"] span')
    header_texts = [header.text_content().strip() for header in headers.all()]
    
    instructions = page.locator('th[data-automation-id="likerStatementTd"] span')
    instructions_texts = [instruction.text_content().strip() for instruction in instructions.all()]

    return header_texts, instructions_texts

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

def go_next_or_submit(page):
    # If already on thank-you page → STOP
    if "ThankYou" in page.url:
        print("🎉 Submission confirmed")
        return "submitted"

    submit = page.locator("button[data-automation-id='submitButton']")
    if submit.count() > 0:
        if submit.first.is_enabled():
            submit.first.click()
            print("✅ Submit clicked")
            return "submitted"
        else:
            print("⏳ Submit in progress, waiting...")
            page.wait_for_url("**ThankYou**", timeout=15000)
            return "submitted"

    next_btn = page.locator("button[data-automation-id='nextButton']")
    if next_btn.count() > 0 and next_btn.first.is_enabled():
        next_btn.first.click()
        print("➡️ Next section")
        page.wait_for_load_state("networkidle")
        return "next"

    return "none"

    
def human_scroll(page):
    """Realistic scrolling behavior"""
    scroll_amount = random.randint(100, 400)
    page.evaluate(f"""
        window.scrollBy({{
            top: {scroll_amount},
            behavior: 'smooth'
        }});
    """)
    time.sleep(random.uniform(0.3, 0.8))

def human_mouse_move(page):
    """Random mouse movements"""
    page.mouse.move(
        random.randint(200, 1200),
        random.randint(200, 800),
        steps=random.randint(10, 30)
    )

def human_type(el, text):
    """Human-like typing with mistakes"""
    for i, char in enumerate(text):
        # 5% chance of typo
        if random.random() < 0.05 and i < len(text) - 1:
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            el.type(wrong_char, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.1, 0.3))
            el.press('Backspace')
            time.sleep(random.uniform(0.05, 0.15))
        
        el.type(char, delay=random.randint(60, 180))
        
        # Random pauses (thinking)
        if random.random() < 0.1:
            time.sleep(random.uniform(0.5, 2.0))

def human_pause(a=1.5, b=4.5):
    """Longer, more realistic pauses"""
    time.sleep(random.uniform(a, b))

def main():
    with sync_playwright() as p:
        # Use persistent context instead of regular browser
        pw, browser, page = launch_browser()
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
                
                q_type = detect_question_type(q)
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
                human_mouse_move(page)
                human_pause(0.8, 2.0)
                
                # Scroll question into view naturally
                q.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.3, 0.7))
                
                # Text input
                text_input = q.query_selector("input[type='text']")
                if text_input:
                    text_input.click()
                    time.sleep(random.uniform(0.2, 0.5))
                    human_type(text_input, random.choice(ANSWERS))
                
                # Textarea
                textarea = q.query_selector("textarea")
                if textarea:
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
                if is_likert(q):
                    fill_likert(q)
                
                # Occasional scroll
                if random.random() < 0.3:
                    human_scroll(page)
            
            human_pause(1.5, 3.0)
            
            # Navigate or submit
            result = go_next_or_submit(page)
            if result == "submitted":
                time.sleep(3)
                break
        
        # Export data
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)
        
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "question", "type", "options"])
            for q in extracted:
                writer.writerow([
                    q["id"],
                    q["question"],
                    q["type"],
                    "; ".join(q["options"])
                ])
        
        browser.close()
        pw.stop()


if __name__ == "__main__":
    for e in range(250):
        print(f"\n🔄 Submission {e+1}/250")
        main()
        # CRITICAL: Add delay between submissions
        wait_time = random.uniform(30, 90)  # 30-90 seconds between forms
        print(f"⏳ Waiting {wait_time:.1f}s before next submission...")
        time.sleep(wait_time)