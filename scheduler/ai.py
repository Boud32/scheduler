import os
import json
import datetime
from typing import List
from google import genai
from scheduler.models import Task, Priority, TaskCategory

# Configure API Key
# Best practice: User should set GEMINI_API_KEY in their shell or .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Client initialization will happen where needed or we can initialize a global one differently if we want, 
# but for this script structure, we'll verify key existence and init client later.
if not GEMINI_API_KEY:
    # We might want to warn or just let it fail later, but the original code had a check.
    pass

def parse_user_input(text_input: str, reference_date: datetime.date = datetime.date.today()) -> List[Task]:
    """
    Uses Gemini to parse natural language text into a list of structured Task objects.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    You are an intelligent scheduling assistant. 
    Transform the following user request into a JSON list of tasks.
    
    User Request: "{text_input}"
    
    Output Format (JSON List):
    [
      {{
        "title": "Short descriptive title",
        "duration_minutes": 60,
        "priority": "P0" | "P1" | "P2" | "P3" | "P4",
        "category": "Deep Work" | "Admin" | "Research" | "Meeting" | "Break" | "Learning" | "Other",
        "specific_start_time": "HH:MM" // Optional: 24h format if user specifies EXACT start time (e.g., "at 6pm" -> "18:00")
      }}
    ]
    
    Rules:
    - Default duration: 30 minutes if not specified.
    - Default priority: P2 (Medium) if not obvious.
    - Default category: Other.
    - If user says "from X to Y", calculate duration and set specific_start_time.
    - STRICTLY return only valid JSON. No markdown formatting.
    """

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt
        )
        # Clean potential markdown code blocks
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        data = json.loads(clean_text)
        
        parsed_tasks = []
        for item in data:
            # Map string to Enum if needed, but Pydantic handles string->Enum conversion mostly
            # Priority mapping just in case
            p_map = {
                "P0": Priority.P0_CRITICAL,
                "P1": Priority.P1_HIGH,
                "P2": Priority.P2_MEDIUM,
                "P3": Priority.P3_LOW,
                "P4": Priority.P4_OPTIONAL
            }
            
            # Helper to map category strings to Enum values
            c_map = {
                "Deep Work": TaskCategory.DEEP_WORK,
                "Admin": TaskCategory.ADMIN,
                "Research": TaskCategory.RESEARCH,
                "Meeting": TaskCategory.MEETING,
                "Break": TaskCategory.BREAK,
                "Learning": TaskCategory.LEARNING,
                "Other": TaskCategory.OTHER
            }

            task = Task(
                title=item.get("title", "Untitled Task"),
                duration_minutes=item.get("duration_minutes", 30),
                priority=p_map.get(item.get("priority"), Priority.P2_MEDIUM),
                category=c_map.get(item.get("category"), TaskCategory.OTHER)
            )
            
            # Handle specific time constraint
            start_str = item.get("specific_start_time")
            if start_str:
                try:
                    # Parse HH:MM
                    h, m = map(int, start_str.split(':'))
                    # Create datetime for reference date
                    start_dt = datetime.datetime.combine(reference_date, datetime.time(h, m))
                    end_dt = start_dt + datetime.timedelta(minutes=task.duration_minutes)
                    
                    # Add to preferrred windows
                    from scheduler.models import TimeRange, ConstraintType
                    task.preferred_time_windows = [TimeRange(start_time=start_dt, end_time=end_dt)]
                    task.constraint_type = ConstraintType.HARD # Treat as hard constraint
                except Exception as time_err:
                    print(f"Warning: could not parse specific time '{start_str}': {time_err}")
            
            parsed_tasks.append(task)
            
        return parsed_tasks

    except Exception as e:
        print(f"Error communicating with Gemini: {e}")
        return []
