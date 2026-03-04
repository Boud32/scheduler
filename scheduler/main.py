import datetime
from datetime import date
from collections import defaultdict
import sys
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Ensure we can import from local package
import os
sys.path.append(os.getcwd())

from scheduler import ai, gcal, solver, models, tracker, journal


def get_input(prompt):
    while True:
        try:
            val = input(prompt).strip()
            if val:
                return val
            print("Input cannot be empty. Please try again.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            exit(0)


def run_scheduler_loop():
    print("🤖 --- AI Accountability Scheduler --- 🤖")
    print("\n[1] Schedule tasks    [2] Recruitment Tracker    [3] Daily Journal")
    try:
        mode = input("Select mode: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        return

    if mode == "2":
        tracker.run_tracker()
        return

    if mode == "3":
        journal.run_journal()
        return
    
    today = date.today()

    # 1. User Input
    print("\n💬 What do you want to accomplish? (Enter to exit)")
    try:
        user_input = input("   (e.g., 'Volleyball 7-9am this Saturday, deep work 2hrs today'): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        return

    if not user_input or user_input.lower() in ("q", "quit", "exit", "nothing", "n"):
        print("👋 Exiting.")
        return

    # 2. AI Parse
    print("\n🧠 Analyzing your request...")
    try:
        tasks = ai.parse_user_input(user_input, reference_date=today)
        if not tasks:
            print("🤔 Could not understand tasks. Please try again.")
            return

        print(f"   Parsed {len(tasks)} tasks:")
        for t in tasks:
            priority_icon = "🔴" if "CRITICAL" in t.priority.name else "🔵"
            date_label = t.target_date.strftime("%a %b %d") if t.target_date and t.target_date != today else "today"
            print(f"   - {priority_icon} {t.title} ({t.duration_minutes}m) [{t.category.value}] → {date_label}")

    except Exception as e:
        print(f"❌ Error parsing input: {e}")
        return

    # 3. Group tasks by target date
    tasks_by_date = defaultdict(list)
    for t in tasks:
        tasks_by_date[t.target_date or today].append(t)

    # 4. Solve per date
    def parse_gcal_events(raw_events, sched):
        for evt in raw_events:
            start_str = evt.get('start', {}).get('dateTime') or evt.get('start', {}).get('date')
            end_str = evt.get('end', {}).get('dateTime') or evt.get('end', {}).get('date')
            if 'T' not in str(start_str):
                continue
            try:
                if str(start_str).endswith('Z'):
                    start_str = str(start_str).replace('Z', '+00:00')
                if str(end_str).endswith('Z'):
                    end_str = str(end_str).replace('Z', '+00:00')
                s = datetime.datetime.fromisoformat(start_str)
                e = datetime.datetime.fromisoformat(end_str)
                if s.tzinfo is not None:
                    s = s.replace(tzinfo=None)
                if e.tzinfo is not None:
                    e = e.replace(tzinfo=None)
                sched.add_existing_event(s, e)
            except Exception as parse_err:
                print(f"   Warning: skipped event due to parse error: {parse_err}")

    print("\n🧩 Optimizing schedule...")
    constraint = models.ScheduleConstraint(work_start_hour=5, work_end_hour=24)
    all_results = []  # list of (date, schedule_state)

    for target_date in sorted(tasks_by_date.keys()):
        day_start = datetime.datetime.combine(target_date, datetime.time.min)
        day_end = datetime.datetime.combine(target_date, datetime.time.max)
        try:
            existing_events = gcal.list_events(time_min=day_start, time_max=day_end, limit=50)
        except Exception as e:
            print(f"❌ Error fetching GCal events for {target_date}: {e}")
            continue

        sched = solver.AppointmentScheduler(target_date, constraint)
        parse_gcal_events(existing_events, sched)
        for t in tasks_by_date[target_date]:
            sched.add_task(t)

        schedule_state = sched.solve(current_dt=datetime.datetime.now())
        all_results.append((target_date, schedule_state))

    # 5. Display grouped by date
    print("\n📝 Proposed Schedule:")
    for target_date, schedule_state in all_results:
        label = "Today" if target_date == today else target_date.strftime("%A, %B %d")
        print(f"\n  📅 {label}:")
        if not schedule_state.scheduled_tasks:
            print("     ❌ No tasks could be scheduled. (Too many constraints?)")
        else:
            for slot in sorted(schedule_state.scheduled_tasks, key=lambda x: x.start_time):
                print(f"     👉 {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}: {slot.description}")
        if schedule_state.pending_tasks:
            print("     ⚠️  Could not schedule:")
            for t in schedule_state.pending_tasks:
                print(f"        - {t.title}")

    # 6. Push to GCal
    all_slots = [(d, slot) for d, ss in all_results for slot in ss.scheduled_tasks]
    if all_slots:
        try:
            confirm = input("\n🚀 Push to Google Calendar? (y/N): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            return

        if confirm.lower() == 'y':
            print("   Uploading...")
            count = 0
            for _, slot in all_slots:
                res = gcal.create_event(
                    summary=slot.description,
                    start_time=slot.start_time,
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
