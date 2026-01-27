from typing import List, Optional
from datetime import datetime, date, timedelta
from ortools.sat.python import cp_model
from scheduler.models import Task, ScheduleState, TimeSlot, ScheduleConstraint, TimeRange

class AppointmentScheduler:
    def __init__(self, date_val: date, constraints: ScheduleConstraint):
        self.date_val = date_val
        self.constraints = constraints
        self.existing_events: List[TimeRange] = []
        self.tasks_to_schedule: List[Task] = []
        
        # Define day start/end in minutes from midnight
        self.day_start_min = self.constraints.work_start_hour * 60
        self.day_end_min = self.constraints.work_end_hour * 60

    def add_existing_event(self, start: datetime, end: datetime):
        """Adds a hard constraint (busy block)."""
        # Convert to minutes from midnight
        # Check if event overlaps with the day
        day_start_dt = datetime.combine(self.date_val, datetime.min.time())
        
        start_min = int((start - day_start_dt).total_seconds() / 60)
        end_min = int((end - day_start_dt).total_seconds() / 60)
        
        # Clamp to work day? Or just enforce hard constraint even if outside?
        # Usually hard constraints outside work hours don't matter, but 
        # inside they clearly block time.
        self.existing_events.append(TimeRange(start_time=start, end_time=end))

    def add_task(self, task: Task):
        self.tasks_to_schedule.append(task)

    def solve(self, current_dt: Optional[datetime] = None) -> ScheduleState:
        model = cp_model.CpModel()
        
        # --- Variables ---
        day_start_dt = datetime.combine(self.date_val, datetime.min.time())
        
        # Adjust start time if we are scheduling for 'today' and it's already later than work start
        effective_start_min = self.day_start_min
        if current_dt and current_dt.date() == self.date_val:
            current_min = int((current_dt - day_start_dt).total_seconds() / 60)
            # Add a small buffer (e.g. 5 mins) so we don't schedule exactly at this second
            effective_start_min = max(self.day_start_min, current_min + 5)

        # We need to map tasks to their CP variables to reconstruct solution
        task_vars = {} 
        all_intervals = []

        # 1. Add Hard Constraints (Existing Events) as fixed intervals
        for evt in self.existing_events:
            start_min = int((evt.start_time - day_start_dt).total_seconds() / 60)
            end_min = int((evt.end_time - day_start_dt).total_seconds() / 60)
            duration = end_min - start_min
            
            # Create a fixed interval
            interval = model.NewIntervalVar(start_min, duration, end_min, f"event_{start_min}")
            all_intervals.append(interval)

        # 2. Add Soft Tasks as Optional Intervals
        total_score_objective = 0
        
        for task in self.tasks_to_schedule:
            # Duration is fixed
            duration = task.duration_minutes
            
            # Start/End variables
            # Domain: Effective Start to Work End
            
            # Default Domain
            min_start = effective_start_min
            max_start = self.day_end_min - duration
            
            # If Task has strict Time Window constraint (e.g. specific time set by AI)
            from scheduler.models import ConstraintType
            if task.constraint_type == ConstraintType.HARD and task.preferred_time_windows:
                # Assuming single window for now for simplicity of parsing
                window = task.preferred_time_windows[0]
                day_start_dt = datetime.combine(self.date_val, datetime.min.time())
                
                # Convert window start to minutes
                win_start_min = int((window.start_time - day_start_dt).total_seconds() / 60)
                
                # Update domain to force this start time
                # We essentially lock it to the specific time
                min_start = win_start_min
                max_start = win_start_min
            
            
            # If effective start + duration > day end, task is impossible in this window
            if min_start + duration > self.day_end_min or min_start > max_start:
                # Task can't fit, force it to be absent (or rely on solver to find it impossible)
                start_var = model.NewIntVar(effective_start_min, effective_start_min, f"start_{task.id}") # Dummy
                end_var = model.NewIntVar(effective_start_min, effective_start_min, f"end_{task.id}")     # Dummy
                is_present_var = model.NewConstant(0)
            else:
                start_var = model.NewIntVar(min_start, max_start, f"start_{task.id}")
                end_var = model.NewIntVar(min_start + duration, max_start + duration, f"end_{task.id}")
                is_present_var = model.NewBoolVar(f"present_{task.id}")
            
            # Interval variable (Optional)
            interval_var = model.NewOptionalIntervalVar(
                start_var, duration, end_var, is_present_var, f"interval_{task.id}"
            )
            
            all_intervals.append(interval_var)
            
            task_vars[task.id] = {
                "start": start_var,
                "end": end_var,
                "present": is_present_var,
                "task": task
            }
            
            # Objective: Maximize priority score of scheduled tasks
            total_score_objective += (is_present_var * task.priority_score)

        # --- Constraints ---
        
        # No Overlap
        model.AddNoOverlap(all_intervals)
        
        # Buffer Constraints? (Optional for V1, but easy to add: expand duration by buffer)
        # For strict implementation, we would model buffer as part of duration or gap constraint.
        # Leaving out complex buffer logic for V1 to ensure basic solution works.

        # --- Objective ---
        model.Maximize(total_score_objective)
        
        # --- Solve ---
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        
        result_state = ScheduleState(
            date_val=self.date_val,
            available_slots=[], # To be filled logic later
            scheduled_tasks=[],
            pending_tasks=[]
        )
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"Solution Found! Status: {solver.StatusName(status)}")
            print(f"Objective Value: {solver.ObjectiveValue()}")
            
            for task_id, vars_data in task_vars.items():
                if solver.Value(vars_data["present"]):
                    # Task is scheduled
                    start_min = solver.Value(vars_data["start"])
                    end_min = solver.Value(vars_data["end"])
                    
                    real_start = day_start_dt + timedelta(minutes=start_min)
                    real_end = day_start_dt + timedelta(minutes=end_min)
                    
                    slot = TimeSlot(
                        start_time=real_start,
                        end_time=real_end,
                        task_id=task_id,
                        description=vars_data["task"].title,
                        category=vars_data["task"].category
                    )
                    result_state.scheduled_tasks.append(slot)
                else:
                    # Task not scheduled
                    result_state.pending_tasks.append(vars_data["task"])
        else:
            print("No solution found.")
            # All tasks pending
            result_state.pending_tasks = self.tasks_to_schedule

        return result_state
