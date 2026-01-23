import time


def next_or_submit_GOOGLE(page): 
    """Handle Next/Submit buttons""" # SUBMIT (last page) 
    submit = page.locator("div[role='button'][jsname='M2UYVd']") 
    if submit.count() > 0 and submit.first.is_visible(): 
        submit.first.scroll_into_view_if_needed() 
        submit.first.click() 
        print("✅ Submit clicked") 
        time.sleep(1) # Try to detect submission confirmation with multiple fallbacks 
        try: 
            page.wait_for_selector( "div.freebirdFormviewerViewResponseConfirmationMessage", timeout=5000 ) 
            print("✓ Confirmation message found") 
            return "submitted" 
        except: # Fallback: check if form elements are gone (page changed) 
            try: 
                page.wait_for_selector("div[role='listitem']", timeout=2000) 
                print("⚠️ Still on form page") 
                return "error" 
            except: # Form elements gone = likely submitted 
                print("✓ Form cleared (likely submitted)") 
                return "submitted"
    next_btn = page.locator("div[role='button'][jsname='OCpkoe']") 
    if next_btn.count() > 0 and next_btn.first.is_visible(): 
        next_btn.first.scroll_into_view_if_needed() 
        next_btn.first.click() 
        print("➡️ Next clicked") 
        try: 
            page.wait_for_selector("div[role='listitem']", timeout=8000) 
        except:
            print("⚠️ Next button timeout, but continuing") 
            return "next" 
        
    return "none"

def go_next_or_submit_MS(page):
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


def go_next_or_submit(page, platform="GOOGLE"):
    if platform == "MS":
        return go_next_or_submit_MS(page)
    else:  # GOOGLE
        return next_or_submit_GOOGLE(page)