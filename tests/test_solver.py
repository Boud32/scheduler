import pytest
from datetime import date, datetime, timedelta
from scheduler.models import Task, Priority, ScheduleConstraint, TaskCategory
from scheduler.solver import AppointmentScheduler

def test_solver_simple_fit():
    today = date.today()
    constraint = ScheduleConstraint(work_start_hour=8, work_end_hour=18)
    scheduler = AppointmentScheduler(today, constraint)
    
    t1 = Task(title="Morning Routine", duration_minutes=60, priority=Priority.P1_HIGH)
    scheduler.add_task(t1)
    
    state = scheduler.solve()
    
    assert len(state.scheduled_tasks) == 1
    scheduled = state.scheduled_tasks[0]
    assert scheduled.description == "Morning Routine"
    # Should start at 8:00 AM (480 mins)
    assert scheduled.start_time.hour == 8 

def test_solver_priority_conflict():
    """Verify that higher priority task wins if there isn't enough time."""
    today = date.today()
    # Very short work day: 8am - 9am (60 mins)
    constraint = ScheduleConstraint(work_start_hour=8, work_end_hour=9)
    scheduler = AppointmentScheduler(today, constraint)
    
    # Two 60 min tasks
    t_high = Task(title="Critical", duration_minutes=60, priority=Priority.P0_CRITICAL)
    t_low = Task(title="Optional", duration_minutes=60, priority=Priority.P4_OPTIONAL)
    
    scheduler.add_task(t_high)
    scheduler.add_task(t_low)
    
    state = scheduler.solve()
    
    assert len(state.scheduled_tasks) == 1
    assert state.scheduled_tasks[0].description == "Critical"
    assert len(state.pending_tasks) == 1
    assert state.pending_tasks[0].title == "Optional"

def test_solver_with_hard_constraints():
    """Verify tasks are scheduled around existing meetings."""
    today = date.today()
    # 8am - 12pm
    constraint = ScheduleConstraint(work_start_hour=8, work_end_hour=12) 
    scheduler = AppointmentScheduler(today, constraint)
    
    # Existing meeting 8:00 - 9:00
    base_time = datetime.combine(today, datetime.min.time())
    meeting_start = base_time + timedelta(hours=8)
    meeting_end = base_time + timedelta(hours=9)
    
    scheduler.add_existing_event(meeting_start, meeting_end)
    
    # Task needs 2 hours
    t1 = Task(title="Deep Work", duration_minutes=120, priority=Priority.P1_HIGH)
    scheduler.add_task(t1)
    
    state = scheduler.solve()
    
    assert len(state.scheduled_tasks) == 1
    scheduled = state.scheduled_tasks[0]
    
    # Should start at 9:00 because 8-9 is blocked
    assert scheduled.start_time.hour == 9
    assert scheduled.end_time.hour == 11

if __name__ == "__main__":
    test_solver_simple_fit()
    test_solver_priority_conflict()
    test_solver_with_hard_constraints()
    print("All tests passed!")
