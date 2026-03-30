from former.LLM_interface.ChatInterface import chatInterface
from former.LLM_interface.Gemini import geminiFormFiller
from former.LLM_interface.ChatgptFormFiller import chatgptFormFiller
from former.browser import launch_browser

from former.detectors import detect_question_type, detect_platform
from former.extract import extract_options, extract_title, extract_question_items
from former.fill import fill_question
from former.navigation import go_next_or_submit
from former.human import human_pause, human_before_question
import former.config as config
import json



def go_through_form(page, chat_filler: chatInterface, platform="GOOGLE"):
    qid = 1
    
    while True:
        questions = extract_question_items(page, platform)
        processed_qestions = []
        extracted = []
        seen = set()
        
        
        for q in questions:

            title = extract_title(q, platform)
            qtype = detect_question_type(q, platform)
            if qtype == 'section_title':
                continue
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
        
        try:
            answered_form = chat_filler.get_selection(extracted)

        except Exception as e:
            print(f"Error occurred while getting ChatGPT selection: {e}")
            raise

        print("Answered form:", answered_form)
        
        for (q, qtype), answer in zip(processed_qestions, answered_form):
            human_before_question(page, q)
            fill_question(page, q, platform, qtype, answer)

        human_pause(1.5, 3.0)

        if go_next_or_submit(page, platform) == "submitted":
            human_pause(1.5, 3.0)

            break
        
        
def run_form_pipeline(form_url, chat_filler):
    playwright, browser, page = launch_browser()
    try:
        platform = detect_platform(form_url)
        page.goto(form_url, wait_until="networkidle")
        go_through_form(page, chat_filler, platform)
    finally:
        browser.close()
        playwright.stop()

        
def main():
    FORM_URL = config.FORM_URL_GOOGLE
    chat_filler = chatgptFormFiller(config.OPENAI_API_KEY)
    run_form_pipeline(FORM_URL, chat_filler)
        
if __name__ == "__main__":
    main()