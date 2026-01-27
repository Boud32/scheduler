from scheduler.models import Task, Priority, TaskCategory, ScheduleState, TimeSlot
from datetime import datetime, date, timedelta
from uuid import uuid4

def test_models():
    print("Testing Models...")
    
    # Test Task Creation
    try:
        t = Task(
            title="Deep Work Session",
            duration_minutes=60,
            priority=Priority.P0_CRITICAL,
            category=TaskCategory.DEEP_WORK
        )
        print(f"✅ Task created: {t.title} [Score: {t.priority_score}]")
        assert t.priority_score == 100
    except Exception as e:
        print(f"❌ Task creation failed: {e}")

    # Test Defaults
    t_default = Task(title="Simple Task", duration_minutes=30)
    print(f"✅ Default Priority: {t_default.priority}")
    assert t_default.priority == Priority.P2_MEDIUM

    # Test ScheduleState
    try:
        state = ScheduleState(
            date_val=date.today(),
            scheduled_tasks=[
                TimeSlot(
                    start_time=datetime.now(), 
                    end_time=datetime.now() + timedelta(hours=1),
                    description="Meeting"
                )
            ]
        )
        print(f"✅ ScheduleState created with {len(state.scheduled_tasks)} task")
    except Exception as e:
        print(f"❌ ScheduleState failed: {e}")

if __name__ == "__main__":
    test_models()
