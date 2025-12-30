from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, date
from pydantic import BaseModel, Field

# --- Enums ---

class Priority(str, Enum):
    # TODO: Define High, Medium, Low
    pass

class TaskCategory(str, Enum):
    # TODO: Define categories (Deep Work, Admin, Research, Meeting, Break, Other)
    pass

class TaskStatus(str, Enum):
    # TODO: Define statuses (Pending, Scheduled, Completed, RolledOver)
    pass

class ConstraintType(str, Enum):
    HARD = "Hard"
    SOFT = "Soft"

# --- Helper Models ---

class TimeRange(BaseModel):
    start_time: datetime
    end_time: datetime

# --- Core Models ---

class Task(BaseModel):
    """
    Represents an atomic unit of work to be scheduled.
    """
    id: UUID = Field(default_factory=uuid4)
    title: str
    duration_minutes: int = Field(gt=0, description="Estimated duration in minutes")
    
    # TODO: Add Priority and Category fields
    # priority: Priority = ...
    # category: TaskCategory = ...
    
    constraint_type: ConstraintType = ConstraintType.SOFT
    
    # Optional constraints
    preferred_time_windows: List[TimeRange] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    
    # status: TaskStatus = ...
    
    @property
    def priority_score(self) -> int:
        """Numeric score for the solver based on Priority Enum."""
        # TODO: Implement mapping logic
        return 0

class ScheduleConstraint(BaseModel):
    """
    Global constraints for the scheduler (Work bounds, buffers, etc.)
    """
    # TODO: Define standard working hours and buffers
    # work_start_hour: int = 8
    # work_end_hour: int = 22
    pass

class TimeSlot(BaseModel):
    """A scheduled block of time."""
    start_time: datetime
    end_time: datetime
    task_id: Optional[UUID] = None
    description: str

class ScheduleState(BaseModel):
    """
    Represents the state of a specific day or schedule window.
    """
    date_val: date
    # available_slots: List[TimeRange] = [] 
    # scheduled_tasks: List[TimeSlot] = []
    # pending_tasks: List[Task] = []
