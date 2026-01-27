import os.path
import datetime
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_service():
    """Shows basic usage of the Google Calendar API."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(f"Missing {CREDS_FILE}. Please download OAuth client ID from Google Cloud Console.")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service

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
