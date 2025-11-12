from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Iterable, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"


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


def fetch_events(calendar_id: str = "primary", time_min: datetime | None = None, time_max: datetime | None = None,
                 max_results: int = 2500) -> Iterable[Dict[str, Any]]:
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
        external_id = item.get("id")
        title = item.get("summary") or ""
        description = item.get("description") or ""
        location = item.get("location") or ""
        attendees = [a.get("email") or a.get("displayName") or "" for a in item.get("attendees", [])]

        def to_iso(dct: dict, key: str) -> str:
            if not dct:
                return ""
            if dct.get("dateTime"):
                return dct["dateTime"]
            if dct.get("date"):
                return dct["date"] + "T00:00:00Z"
            return ""

        start_iso = to_iso(item.get("start", {}), "start")
        end_iso = to_iso(item.get("end", {}), "end")

        yield {
            "external_id": external_id,
            "title": title,
            "description": description,
            "location": location,
            "participants": [p for p in attendees if p],
            "start_ts": start_iso,
            "end_ts": end_iso,
        }
