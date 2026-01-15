import time
import human

def fill_time(q, answer):
    time_input = q.query_selector_all("input[maxlength='2']")
    answer = answer.strip()
    answer = answer.split(":")
    if len(time_input) < 2: 
        print("⚠️ Time inputs not found") 
        return # Order is always: hour, minute 
    hour_input = time_input[0] 
    minute_input = time_input[1] 
    hour_input.click() 
    hour_input.fill(answer[0]) 
    human.human_pause(0.2, 0.5)
    minute_input.click() 
    minute_input.fill(answer[0])