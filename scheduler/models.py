from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, date
from pydantic import BaseModel, Field

# --- Enums ---

class Priority(str, Enum):
    P0_CRITICAL = "P0"
    P1_HIGH = "P1"
    P2_MEDIUM = "P2"
    P3_LOW = "P3"
    P4_OPTIONAL = "P4"

class TaskCategory(str, Enum):
    DEEP_WORK = "Deep Work"
    ADMIN = "Admin"
    RESEARCH = "Research"
    MEETING = "Meeting"
    BREAK = "Break"
    LEARNING = "Learning"
    OTHER = "Other"

class TaskStatus(str, Enum):
    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    ROLLED_OVER = "Rolled Over"
    IN_PROGRESS = "In Progress"
    CANCELLED = "Cancelled"

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
    
    priority: Priority = Priority.P2_MEDIUM
    category: TaskCategory = TaskCategory.OTHER
    
    constraint_type: ConstraintType = ConstraintType.SOFT
    
    # Optional constraints
    preferred_time_windows: List[TimeRange] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    
    status: TaskStatus = TaskStatus.PENDING
    
    @property
    def priority_score(self) -> int:
        """Numeric score for the solver based on Priority Enum. Higher is more important."""
        scores = {
            Priority.P0_CRITICAL: 100,
            Priority.P1_HIGH: 50,
            Priority.P2_MEDIUM: 25,
            Priority.P3_LOW: 10,
            Priority.P4_OPTIONAL: 1
        }
        return scores.get(self.priority, 1)

class ScheduleConstraint(BaseModel):
    """
    Global constraints for the scheduler (Work bounds, buffers, etc.)
    """
    work_start_hour: int = 5
    work_end_hour: int = 24
    buffer_minutes: int = 15
    max_deep_work_block_minutes: int = 90

class TimeSlot(BaseModel):
    """A scheduled block of time."""
    start_time: datetime
    end_time: datetime
    task_id: Optional[UUID] = None
    description: str
    category: TaskCategory = TaskCategory.OTHER

class ScheduleState(BaseModel):
    """
    Represents the state of a specific day or schedule window.
    """
    date_val: date
    available_slots: List[TimeRange] = Field(default_factory=list) 
    scheduled_tasks: List[TimeSlot] = Field(default_factory=list)
    pending_tasks: List[Task] = Field(default_factory=list)

