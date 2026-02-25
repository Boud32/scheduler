# AI Accountability Scheduler

A command-line tool that combines AI-powered task parsing with Google Calendar integration to help plan and track your day.

## Features

### Task Scheduler
Describe what you want to accomplish in plain English. The tool uses an LLM to parse your input into structured tasks, then uses a constraint solver (Google OR-Tools) to fit them into your available calendar gaps — respecting existing meetings and configurable work hours.

### Recruitment Tracker
A daily progress tracker that creates a Google Calendar event whose color updates in real time as you complete structured work blocks throughout the day.

- State persists across multiple runs so you can check in without losing progress
- Visual progress bar rendered in the terminal via Rich
- Calendar event color reflects completion percentage (Red → Yellow → Blue → Green)

## How It Works

1. **AI Parsing** — Natural language input is sent to Gemini, which returns structured task objects with duration, priority, and category.
2. **Constraint Solving** — OR-Tools places tasks into time slots that don't overlap with existing calendar events, optimizing by priority.
3. **GCal Integration** — Scheduled tasks (or tracker events) are written to Google Calendar via the Calendar API.

## Setup

### Prerequisites
- Python 3.11+
- A Google Cloud project with the Calendar API enabled
- OAuth 2.0 credentials (`credentials.json`) downloaded from Google Cloud Console
- A Gemini API key

### Install
```bash
pip install -r requirements.txt
```

### Google Calendar Auth
On first run, a browser window will open for OAuth consent. A `token.json` file will be saved locally for subsequent runs.

### Environment Variables
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```

## Usage

```bash
python -m scheduler.main
```

You will be prompted to choose a mode:
- **[1] Schedule tasks** — describe your tasks in plain English and get a proposed schedule
- **[2] Recruitment Tracker** — check off structured work blocks and sync progress to your calendar

## Project Structure

```
scheduler/
├── main.py       # Entry point and mode selector
├── ai.py         # LLM task parsing via Gemini
├── gcal.py       # Google Calendar API helpers
├── models.py     # Pydantic data models
├── solver.py     # OR-Tools constraint solver
└── tracker.py    # Recruitment tracker logic
```
