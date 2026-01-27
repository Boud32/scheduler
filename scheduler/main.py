import datetime
from datetime import date, timedelta
import sys

# Ensure we can import from local package
import os
sys.path.append(os.getcwd())

from scheduler import ai, gcal, solver, models

def run_scheduler_loop():
    print("🤖 --- AI Accountability Scheduler --- 🤖")
    
    # 1. Scope: Today
    today = date.today()
    print(f"📅 Scheduling for: {today.strftime('%A, %B %d')}")
    
    # 2. Get Constraints (Existing Events)
    print("⏳ Fetching your calendar...")
    try:
        # Define day window (00:00 to 23:59) for constraints
        day_start = datetime.datetime.combine(today, datetime.time.min)
        day_end = datetime.datetime.combine(today, datetime.time.max)
        
        # GCal expects ISO format with Z or offset
        existing_events = gcal.list_events(time_min=day_start, time_max=day_end, limit=50)
        print(f"✅ Found {len(existing_events)} existing events/meetings.")
    except Exception as e:
        print(f"❌ Error fetching GCal events: {e}")
        return

    # 3. User Input
    print("\n💬 What do you want to accomplish today?")
    try:
        user_input = input("   (e.g., 'Draft project proposal for 2 hours'): ")
    except KeyboardInterrupt:
        return

    if not user_input.strip():
        print("👋 Exiting.")
        return

    # 4. AI Parse
    print("\n🧠 Analyzing your request...")
    try:
        tasks = ai.parse_user_input(user_input, reference_date=today)
        if not tasks:
            print("🤔 Could not understand tasks. Please try again.")
            return
        
        print(f"   Parsed {len(tasks)} tasks:")
        for t in tasks:
            priority_icon = "🔴" if "CRITICAL" in t.priority.name else "🔵"
            print(f"   - {priority_icon} {t.title} ({t.duration_minutes}m) [{t.category.value}]")
            
    except Exception as e:
        print(f"❌ Error parsing input: {e}")
        return

    # 5. Solve
    print("\n🧩 Optimizing schedule...")
    # Default work hours: 07:00 to 22:00 for flexibility
    constraint = models.ScheduleConstraint(
        work_start_hour=7, 
        work_end_hour=22
    )
    sched = solver.AppointmentScheduler(today, constraint)
    
    # Add existing events as hard constraints
    for evt in existing_events:
        start_str = evt.get('start', {}).get('dateTime') or evt.get('start', {}).get('date')
        end_str = evt.get('end', {}).get('dateTime') or evt.get('end', {}).get('date')
        
        # We only care about timed events for now (skip all-day events if they are just dates)
        if 'T' in str(start_str): 
            try:
                # Basic ISO parsing. Replace Z with +00:00 for python < 3.11 compatibility if needed
                if str(start_str).endswith('Z'):
                    start_str = str(start_str).replace('Z', '+00:00')
                if str(end_str).endswith('Z'):
                    end_str = str(end_str).replace('Z', '+00:00')
                    
                s = datetime.datetime.fromisoformat(start_str)
                e = datetime.datetime.fromisoformat(end_str)
                
                # Make timezone naive if needed or handle aware. 
                # Our solver uses minutes from midnight local time essentially (since we pass date).
                # Ideally we normalize to local time. For now, assume simplified local handling.
                # If s has tzinfo, convert to local or strip if we match 'today' local.
                
                # Simplification: stripping tzinfo for OR-Tools minute calc 
                # (Assuming 'today' is in same timezone as User)
                if s.tzinfo is not None:
                    s = s.replace(tzinfo=None) # Start time in local wall clock
                if e.tzinfo is not None:
                    e = e.replace(tzinfo=None)
                    
                sched.add_existing_event(s, e)
            except Exception as parse_err:
                 print(f"   Warning: skipped event due to parse error: {parse_err}")

    # Add desired tasks
    for t in tasks:
        sched.add_task(t)
        
    schedule_state = sched.solve(current_dt=datetime.datetime.now())
    
    # 6. Display
    print("\n📝 Proposed Schedule:")
    if not schedule_state.scheduled_tasks:
        print("   ❌ No tasks could be scheduled. (Too many constraints?)")
    else:
        sorted_tasks = sorted(schedule_state.scheduled_tasks, key=lambda x: x.start_time)
        for slot in sorted_tasks:
            fmt_start = slot.start_time.strftime("%H:%M")
            fmt_end = slot.end_time.strftime("%H:%M")
            print(f"   👉 {fmt_start} - {fmt_end}: {slot.description}")
            
    if schedule_state.pending_tasks:
        print("\n⚠️  Could not schedule (Time/Priority Conflicts):")
        for t in schedule_state.pending_tasks:
             print(f"   - {t.title}")

    # 7. Push to GCal
    if schedule_state.scheduled_tasks:
        try:
            confirm = input("\n🚀 Push to Google Calendar? (y/N): ")
        except KeyboardInterrupt:
            return
            
        if confirm.lower() == 'y':
            print("   Uploading...")
            count = 0
            for slot in schedule_state.scheduled_tasks:
                res = gcal.create_event(
                    summary=slot.description,
                    start_time=slot.start_time, # Should ideally be aware, but gcal module handles mapping
                    end_time=slot.end_time,
                    description=f"Generated by AI Scheduler. Category: {slot.category.value}"
                )
                if res:
                    count += 1
            print(f"   ✅ Done! {count} events created.")
        else:
            print("   Cancelled.")

if __name__ == "__main__":
    run_scheduler_loop()
