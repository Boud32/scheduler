import os.path
import datetime
from typing import List, Optional

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
]

CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def get_creds():
    """Returns valid OAuth credentials, refreshing or re-authenticating as needed."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                print("⚠️  Saved token is invalid or revoked. Re-authenticating...")
                os.remove(TOKEN_FILE)
                creds = None
        if not creds or not creds.valid:
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(f"Missing {CREDS_FILE}. Please download OAuth client ID from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def get_service():
    """Returns an authenticated Google Calendar service."""
    return build("calendar", "v3", credentials=get_creds())


def get_drive_service():
    """Returns an authenticated Google Drive service."""
    return build("drive", "v3", credentials=get_creds())

def list_events(limit: int = 10, time_min: Optional[datetime.datetime] = None, time_max: Optional[datetime.datetime] = None):
    """Prints the start and name of the next 'limit' events on the user's calendar."""
    service = get_service()
    
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    
    if time_min:
        time_min_str = time_min.isoformat() + "Z"
    else:
        time_min_str = now
        
    print(f"Fetching events from {time_min_str}...")
    
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min_str,
            timeMax=time_max.isoformat() + "Z" if time_max else None,
            maxResults=limit,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
        return []

    return events

def create_tracker_event(date) -> str:
    """Creates an all-day recruiting tracker event on the given date."""
    service = get_service()

    next_day = (date + datetime.timedelta(days=1)).isoformat()

    event = {
        'summary': '🎯 Recruiting Tracker',
        'colorId': '11',
        'start': {'date': date.isoformat()},
        'end': {'date': next_day},
    }

    try:
        result = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Tracker event created: {result.get('htmlLink')}")
        return result['id']
    except HttpError as error:
        print(f"An error occurred creating tracker event: {error}")
        return None


def update_event_color(service, calendar_id: str, event_id: str, color_id: str):
    """Patches only the colorId field of an existing event."""
    try:
        service.events().patch(
            calendarId=calendar_id,
            eventId=event_id,
            body={'colorId': color_id}
        ).execute()
        print(f"Event color updated to colorId={color_id}")
    except HttpError as error:
        print(f"Failed to update event color: {error}")


def create_event(summary: str, start_time: datetime.datetime, end_time: datetime.datetime, description: str = ""):
    """Creates an event in the calendar."""
    service = get_service()
    
    # Ensure times are timezone aware (Local Time)
    if start_time.tzinfo is None:
        start_time = start_time.astimezone()
    if end_time.tzinfo is None:
        end_time = end_time.astimezone()
    
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
        },
        'end': {
            'dateTime': end_time.isoformat(),
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
        return event
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
