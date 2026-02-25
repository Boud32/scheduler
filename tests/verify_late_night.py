import sys
import os
import datetime
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from scheduler import ai, solver, models

def test_late_night_scheduling():
    print("Testing late night scheduling...")
    
    # User Input
    user_input = "I have volleyball from 9-11 tongiht, but want to do a leetcode before then."
    print(f"Input: {user_input}")
    
    # Parse
    today = date.today()
    tasks = ai.parse_user_input(user_input, reference_date=today)
    
    print(f"Parsed {len(tasks)} tasks.")
    for t in tasks:
        print(f" - {t.title}: {t.duration_minutes}m, Priority: {t.priority}")

    # Solve
    # Ensure our modified constraints are used (which are default now in models.py, or set in main.py)
    # But since we are importing models, let's use the defaults from models.py which we updated.
    constraint = models.ScheduleConstraint() # Should be 5-24
    print(f"Constraints: Start={constraint.work_start_hour}, End={constraint.work_end_hour}")
    
    sched = solver.AppointmentScheduler(today, constraint)
    for t in tasks:
        sched.add_task(t)
        
    # Solve relative to now (or simulate "now" as earlier in the day to allow scheduling)
    # If we run this now (5pm), 9pm is in the future, so it should work.
    current_dt = datetime.datetime.now()
    if current_dt.hour >= 21:
        # If running late at night, simulate earlier time so test passes
        print("Simulating earlier time (17:00) for test stability.")
        current_dt = datetime.datetime.combine(today, datetime.time(17, 0))
        
    state = sched.solve(current_dt=current_dt)
    
    # Check results
    volleyball = next((t for t in state.scheduled_tasks if "Volleyball" in t.description), None)
    
    if volleyball:
        print(f"SUCCESS: Volleyball scheduled at {volleyball.start_time.strftime('%H:%M')} - {volleyball.end_time.strftime('%H:%M')}")
    else:
        print("FAILURE: Volleyball NOT scheduled.")
        if state.pending_tasks:
            print("Pending tasks:")
            for t in state.pending_tasks:
                print(f" - {t.title}")

if __name__ == "__main__":
    test_late_night_scheduling()
