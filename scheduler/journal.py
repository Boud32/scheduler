import datetime
import json
import subprocess
from pathlib import Path

from googleapiclient.errors import HttpError

from scheduler.gcal import get_drive_service

THOUGHTS_FOLDER_ID = "1TyPdF8_04HmAePUfSfVReE1Aq7NbM5MM"
STATE_FILE = "journal_state.json"


def _load_state() -> dict:
    path = Path(STATE_FILE)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run_journal():
    today = datetime.date.today()
    today_str = today.isoformat()
    title = today.strftime('%m-%d-%Y')

    state = _load_state()

    # Already created one today — just open it
    if state.get("date") == today_str and state.get("url"):
        print(f"📝 Opening today's journal entry...")
        subprocess.run(['open', '-a', 'Safari', state["url"]])
        return

    print(f"📝 Creating journal entry: {title}...")

    try:
        drive = get_drive_service()

        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [THOUGHTS_FOLDER_ID],
        }

        file = drive.files().create(body=file_metadata, fields='id,webViewLink').execute()
        url = file.get('webViewLink')

        _save_state({"date": today_str, "url": url})

        print(f"✅ Doc created: {url}")
        subprocess.run(['open', '-a', 'Safari', url])

    except HttpError as e:
        print(f"❌ Error creating journal entry: {e}")
