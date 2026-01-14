import time

def fill_time(q):
    time_input = q.query_selector_all("input[maxlength='2']")
    
    if len(time_input) < 2: 
        print("⚠️ Time inputs not found") 
        return # Order is always: hour, minute 
    hour_input = time_input[0] 
    minute_input = time_input[1] 
    hour_input.click() 
    hour_input.fill("15") 
    time.sleep(0.2) 
    minute_input.click() 
    minute_input.fill("30")