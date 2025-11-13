import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from shared.models.calendar_event import CalendarEvent

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS")
TOKEN_PATH = os.getenv("GOOGLE_TOKEN")


def _get_creds():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def to_iso(dct: dict):
    if not dct:
        return ""
    if dct.get("dateTime"):
        return dct["dateTime"]
    if dct.get("date"):
        return dct["date"] + "T00:00:00Z"
    return ""


def fetch_events(calendar_id: str = "primary", time_min: datetime | None = None, time_max: datetime | None = None,
                 max_results: int = 2500) -> [CalendarEvent]:
    creds = _get_creds()
    service = build("calendar", "v3", credentials=creds)

    if time_min is None:
        time_min = datetime.utcnow() - timedelta(days=7)
    if time_max is None:
        time_max = datetime.utcnow() + timedelta(days=180)

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min.isoformat() + "Z",
        timeMax=time_max.isoformat() + "Z",
        singleEvents=True,
        orderBy="startTime",
        maxResults=max_results,
    ).execute()

    for item in events_result.get("items", []):
        yield CalendarEvent(
            id=item.get("id"),
            calendar="google",
            calendar_type=calendar_id,
            title=item.get("summary"),
            description=item.get("description"),
            location=item.get("location"),
            participants=[a.get("email") or a.get("displayName") or "" for a in item.get("attendees", [])],
            start_ts=to_iso(item.get("start", {})),
            end_ts=to_iso(item.get("end", {}))
        )