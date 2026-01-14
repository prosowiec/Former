import time
# def next_or_submit(page):
#     submit = page.locator("div[jsname='M2UYVd'][role='button']")
#     if submit.count() and submit.first.is_visible():
#         submit.first.click()
#         return "submitted"

#     next_btn = page.locator("div[jsname='OCpkoe'][role='button']")
#     if next_btn.count() and next_btn.first.is_visible():
#         next_btn.first.click()
#         return "next"

#     return "none"


def next_or_submit(page): 
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