import datetime
from scheduler.models import Task, Priority, ScheduleConstraint, TaskCategory, TimeRange, ConstraintType
from scheduler.solver import AppointmentScheduler

def test_past_scheduling_prevention():
    print("Testing Past Scheduling Prevention...")
    today = datetime.date.today()
    
    # Work day 8am - 10pm
    constraint = ScheduleConstraint(work_start_hour=8, work_end_hour=22)
    scheduler = AppointmentScheduler(today, constraint)
    
    # Current time is 3 PM (15:00)
    now = datetime.datetime.combine(today, datetime.time(15, 0))
    
    # Generic Task
    t1 = Task(title="Late Task", duration_minutes=60, priority=Priority.P2_MEDIUM)
    scheduler.add_task(t1)
    
    state = scheduler.solve(current_dt=now)
    
    if state.scheduled_tasks:
        start_hour = state.scheduled_tasks[0].start_time.hour
        print(f"✅ Generic Task scheduled at hour: {start_hour}")
        # Should be >= 15
        assert start_hour >= 15
    else:
        print("❌ Failed to schedule generic task")

def test_fixed_time_constraint():
    print("Testing Fixed Time Constraint...")
    today = datetime.date.today()
    constraint = ScheduleConstraint(work_start_hour=8, work_end_hour=22)
    scheduler = AppointmentScheduler(today, constraint)
    
    # Fixed Task: Volleyball at 6 PM (18:00)
    start_dt = datetime.datetime.combine(today, datetime.time(18, 0))
    end_dt = start_dt + datetime.timedelta(minutes=120)
    
    t_fixed = Task(
        title="Volleyball", 
        duration_minutes=120, 
        priority=Priority.P0_CRITICAL,
        preferred_time_windows=[TimeRange(start_time=start_dt, end_time=end_dt)],
        constraint_type=ConstraintType.HARD
    )
    
    scheduler.add_task(t_fixed)
    
    # Solve with current time 3 PM
    now = datetime.datetime.combine(today, datetime.time(15, 0))
    state = scheduler.solve(current_dt=now)
    
    if state.scheduled_tasks:
        slot = state.scheduled_tasks[0]
        print(f"✅ Fixed Task scheduled at: {slot.start_time.strftime('%H:%M')}")
        assert slot.start_time.hour == 18
    else:
        print("❌ Failed to schedule fixed task")

if __name__ == "__main__":
    test_past_scheduling_prevention()
    test_fixed_time_constraint()
