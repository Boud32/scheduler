import json
import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Confirm

from scheduler import gcal

STATE_FILE = "daily_state.json"

RECRUITING_BLOCKS = {
    "block_1_applications": {"name": "Applications",      "weight": 40},
    "block_2_leetcode":     {"name": "LeetCode",          "weight": 20},
    "block_3_networking":   {"name": "Networking",        "weight": 15},
    "block_4_ddia":         {"name": "DDIA / System Design", "weight": 15},
    "block_5_hackernews":   {"name": "Hacker News",       "weight": 10},
}

console = Console()


def get_color_id(progress: int) -> str:
    if progress >= 100:
        return "10"   # Green
    elif progress >= 80:
        return "9"    # Blue
    elif progress >= 50:
        return "5"    # Yellow
    else:
        return "11"   # Red


def _progress_color(progress: int) -> str:
    if progress >= 100:
        return "green"
    elif progress >= 80:
        return "blue"
    elif progress >= 50:
        return "yellow"
    else:
        return "red"


def load_or_create_state() -> dict:
    today = datetime.date.today().isoformat()
    path = Path(STATE_FILE)

    if path.exists():
        with open(path) as f:
            state = json.load(f)
        if state.get("date") == today:
            return state

    state = {
        "date": today,
        "calendar_event_id": None,
        "blocks": {key: False for key in RECRUITING_BLOCKS},
    }
    save_state(state)
    return state


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def calculate_progress(state: dict) -> int:
    return sum(
        meta["weight"]
        for key, meta in RECRUITING_BLOCKS.items()
        if state["blocks"].get(key)
    )


def _print_progress(progress: int):
    color = _progress_color(progress)
    console.print(f"\n[bold]Recruiting Progress:[/bold] [{color}]{progress}%[/{color}]")
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=color),
        TextColumn("{task.percentage:.0f}%"),
        console=console,
        transient=False,
    ) as bar:
        bar.add_task("Progress", total=100, completed=progress)


def run_tracker():
    today = datetime.date.today()
    state = load_or_create_state()

    if state["calendar_event_id"] is None:
        event_id = gcal.create_tracker_event(today)
        if event_id:
            state["calendar_event_id"] = event_id
            save_state(state)

    _print_progress(calculate_progress(state))

    changed = False
    for key, meta in RECRUITING_BLOCKS.items():
        if state["blocks"].get(key):
            console.print(f"  [green]✓[/green] {meta['name']} (already complete)")
            continue

        answer = Confirm.ask(f"  Did you complete [bold]{meta['name']}[/bold]?", default=False)
        if answer:
            state["blocks"][key] = True
            changed = True

    if changed:
        save_state(state)

    progress = calculate_progress(state)
    color_id = get_color_id(progress)

    if state["calendar_event_id"]:
        service = gcal.get_service()
        gcal.update_event_color(service, "primary", state["calendar_event_id"], color_id)

    _print_progress(progress)
