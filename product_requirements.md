# Product Requirements Document: AI Accountability Scheduler

## 1. Project Overview
**Goal:** Create an intelligent, proactive scheduling layer for Google Calendar that bridges the gap between abstract weekly goals and daily execution.
**Core Philosophy:** The app acts as a "Senior Engineer/Coach" that dynamically manages time, enforces constraints, and learns from user habits to optimize future scheduling.

---

## 2. System Architecture
The system follows a **Closed-Loop Constraint Satisfaction** model:
1. **Intake:** LLM parses natural language tasks and priorities.
2. **Optimization:** A deterministic solver (e.g., Google OR-Tools) handles the NP-hard task of fitting blocks into GCal gaps.
3. **Execution:** Real-time polling updates the state of the calendar.
4. **Learning:** Historical data is fed back into the LLM to refine duration estimates.

---

## 3. Functional Requirements

### 3.1 Weekly Intake (The Sunday Routine)
* **Input Format:** User provides abstract tasks with estimated durations (e.g., "Research FNOs: 4 hours").
* **GCal Integration:** Fetch "Hard Constraints" (pre-existing meetings/classes) from Google Calendar.
* **Initial Solve:** Generate a weekly view that respects work-hour constraints and priority weights.

### 3.2 Dynamic Scheduling & Accountability
* **Active Polling:** The system checks in at task boundaries or every hour.
* **State Updates:**
    * **Complete:** Mark as done; pull the next task forward or offer a break.
    * **Need More Time:** Extend the current block and trigger a "Ripple Reschedule" for the remaining tasks.
    * **Early Finish:** User indicates completion; system optimizes the "found time."
* **Conflict Resolution:** If a new manual event is added to GCal, the scheduler must automatically shift "Soft Tasks" to future slots.

### 3.3 Analytics & Habit Learning
* **Categorization:** Tagging tasks (Deep Work, Admin, Career, Research) via NLP.
* **Productivity Metric:** A calculated score based on `(Actual Time / Estimated Time)` weighted by task priority.
* **Insights:** Weekly "Post-Mortem" reports identifying when productivity dips (e.g., "Tuesday afternoons are low-energy; suggest shorter tasks").

---

## 4. Engineering Constraints

### 4.1 Non-Negotiable Constraints (Hard Logic)
* **Work Window:** No tasks scheduled outside of **08:00 - 22:00** (user-adjustable).
* **Buffer Time:** Mandatory 5-15 minute gap between tasks to prevent burnout.
* **Deep Work Breaks:** Logic-enforced breaks every 45-60 minutes of "Deep Work" flagged tasks.
* **Non-Overlap:** Zero tolerance for task overlapping with GCal "Hard Blocks."

### 4.2 Tweakable Parameters (The Objective Function)
* **Priority Weighting:** Ability to shift focus (e.g., "This week, prioritize job research over coding").
* **Fragmentation Preference:** Choice between "Clumped" tasks (for flow state) or "Spread Out" tasks (to reduce fatigue).

---

## 5. Tech Stack
* **Language:** Python 3.11+
* **Environment:** Google Antigravity / GitHub
* **APIs:** Google Calendar API (OAuth 2.0)
* **AI Model:** Gemini (for NLP parsing and insight generation)
* **Solver:** Google OR-Tools (for the scheduling objective function)

---

## 6. Future Roadmap
* **Biometric Integration:** WHOOP integration to adjust task intensity based on recovery scores.
* **Notification Layer:** Move from CLI polling to Push Notifications (mobile/desktop).