from gemini import GeminiFormFiller
from detectors import detect_question_type, detect_platform
from extract import extract_options, extract_title, extract_question_items
from fill import fill_question
from navigation import go_next_or_submit
from human import human_pause
import config
import json



def go_through_form(page, chat_filler: GeminiFormFiller, platform="GOOGLE"):
    qid = 1
    
    while True:
        questions = extract_question_items(page, platform)
        processed_qestions = []
        extracted = []
        seen = set()
        
        
        for q in questions:

            title = extract_title(q, platform)
            qtype = detect_question_type(q, platform)
            options = extract_options(q, qtype, platform)
            
            print(f"Detected question: {title} | Type: {qtype} | Options: {options}")
            
            # Convert options to JSON string for hashable signature
            options_hash = json.dumps(options, sort_keys=True, default=str)
            signature = (title.lower(), qtype, options_hash)
            
            if signature in seen:
                continue
            seen.add(signature)

            extracted.append({
                "id": qid,
                "question": title,
                "type": qtype,
                "options": options
            })
            processed_qestions.append((q, qtype))
            qid += 1

        
        print("Extracted questions:", extracted)
        answered_form = chat_filler.selector_test(extracted)
        answered_form = config.MS_ANSWERS if platform == "MS" else config.GOOGLE_ANSWERS
        print("Answered form:", answered_form)
        
        for (q, qtype), answer in zip(processed_qestions, answered_form):
            fill_question(page, q, platform, qtype, answer)

        human_pause(1.5, 3.0)

        if go_next_or_submit(page) == "submitted":
            human_pause(1.5, 3.0)

            break


        
def main():
    from browser import launch_browser
    playwright, browser, page = launch_browser()
    API_KEY = config.GEMINI_API_KEY
    
    chat_filler = GeminiFormFiller(API_KEY)

    try:
        FORM_URL = config.FORM_URL_MS
        platform = detect_platform(FORM_URL)
        page.goto(FORM_URL, wait_until="networkidle")

        go_through_form(page, chat_filler, platform=platform)


        print("Form submitted successfully!")

    finally:
        browser.close()
        playwright.stop()
        
if __name__ == "__main__":
    main()