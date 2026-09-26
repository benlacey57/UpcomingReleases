import logging
import json
import os
from datetime import datetime
import zoneinfo
from typing import Dict, List, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import settings
from src.decorators import log_execution, feature_flag, retry_on_failure

logger = logging.getLogger(__name__)

class CalendarService:
    """Manages event synchronization, calendar discovery, category listings, and filtered deletions."""

    DEFAULT_REMINDERS: List[Dict[str, Any]] = [
        {"method": "popup", "minutes": 1440},  # 24 hours before
        {"method": "popup", "minutes": 60}     # 1 hour before
    ]

    def __init__(self, calendar_id: Optional[str] = None) -> None:
        self.calendar_id = calendar_id or settings.calendar_id
        try:
            self.tz = zoneinfo.ZoneInfo(settings.timezone)
        except Exception:
            logger.warning(f"Invalid timezone '{settings.timezone}' provided. Falling back to UTC.")
            self.tz = zoneinfo.ZoneInfo("UTC")
            
        self._credentials = self._load_credentials()

    def _load_credentials(self) -> Optional[service_account.Credentials]:
        """Loads Google Service Account credentials from JSON string or file path."""
        creds_raw = settings.google_credentials_json
        if not creds_raw or creds_raw.strip() in ("{}", ""):
            logger.info("No Google credentials provided. Running in unauthenticated/dry-run mode.")
            return None

        try:
            # Check if it's a file path or direct JSON string
            if os.path.exists(creds_raw):
                return service_account.Credentials.from_service_account_file(
                    creds_raw, scopes=["https://www.googleapis.com/auth/calendar"]
                )
            else:
                creds_info = json.loads(creds_raw)
                return service_account.Credentials.from_service_account_info(
                    creds_info, scopes=["https://www.googleapis.com/auth/calendar"]
                )
        except Exception as e:
            logger.error(f"Failed to parse Google credentials JSON: {e}")
            return None

    @retry_on_failure(retries=3, delay=1.0)
    @log_execution
    def fetch_user_calendars(self) -> List[Dict[str, Any]]:
        """Automatically retrieves all calendars accessible by the authenticated service account."""
        if settings.dry_run or not self._credentials:
            logger.info("[DRY-RUN / NO CREDS] Returning mock calendar list.")
            return [{"id": self.calendar_id, "summary": "Primary (Mock Calendar)"}]

        try:
            service = build("calendar", "v3", credentials=self._credentials)
            calendar_list = service.calendarList().list().execute()
            items = calendar_list.get("items", [])
            logger.info(f"Successfully retrieved {len(items)} calendars from Google Calendar API.")
            return items
        except HttpError as error:
            logger.error(f"Google Calendar API HTTP error occurred while fetching calendars: {error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user calendars: {e}")
            raise

    @retry_on_failure(retries=3, delay=1.0)
    @feature_flag("enable_calendar_sync", fallback_return=True)
    @log_execution
    def sync_event(self, summary: str, date_str: str, category: str, dry_run: bool = True) -> bool:
        """Pushes event to Google Calendar with timezone-aware payload and date validation."""
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"Invalid date format '{date_str}': expected YYYY-MM-DD. Error: {e}")
            raise ValueError(f"Invalid date format: {date_str}. Must be YYYY-MM-DD.")

        event_body = {
            "summary": summary,
            "start": {"date": parsed_date.isoformat()},
            "end": {"date": parsed_date.isoformat()},
            "description": f"Category: {category} | Timezone: {settings.timezone}",
            "reminders": {
                "useDefault": False,
                "overrides": self.DEFAULT_REMINDERS
            }
        }
        
        if dry_run or settings.dry_run or not self._credentials:
            logger.info(f"[DRY-RUN] Would push to Google Calendar [{self.calendar_id}] ({settings.timezone}): {event_body}")
            return True
            
        try:
            service = build("calendar", "v3", credentials=self._credentials)
            event = service.events().insert(calendarId=self.calendar_id, body=event_body).execute()
            logger.info(f"Successfully pushed live event to Google Calendar: {summary} (ID: {event.get('id')})")
            return True
        except HttpError as error:
            logger.error(f"Google Calendar API error inserting event '{summary}': {error}")
            return False

    @retry_on_failure(retries=3, delay=1.0)
    @log_execution
    def delete_event(self, summary: str, category: str, dry_run: bool = True) -> bool:
        """Removes a calendar entry when an item is untracked."""
        if dry_run or settings.dry_run or not self._credentials:
            logger.info(f"[DRY-RUN] Deleted calendar event for untracked item: '{summary}' in category '{category}'")
            return True
            
        try:
            service = build("calendar", "v3", credentials=self._credentials)
            # Search events matching the summary to delete them
            events_result = service.events().list(calendarId=self.calendarId, q=summary, singleEvents=True).execute()
            events = events_result.get("items", [])
            
            for event in events:
                if event.get("summary") == summary:
                    service.events().delete(calendarId=self.calendarId, eventId=event["id"]).execute()
                    logger.info(f"Deleted live calendar event ID {event['id']} for summary '{summary}'")
            return True
        except HttpError as error:
            logger.error(f"Failed to delete event '{summary}': {error}")
            return False

    @log_execution
    def delete_events_by_filter(
        self, 
        category: Optional[str] = None, 
        year: Optional[int] = None, 
        month: Optional[int] = None, 
        dry_run: bool = True
    ) -> int:
        """Deletes calendar entries based on category, year, or month filters."""
        logger.info(f"Executing batch deletion filter -> Category: {category}, Year: {year}, Month: {month}")
        deleted_count = 0
        
        if dry_run or settings.dry_run or not self._credentials:
            logger.info(f"[DRY-RUN] Simulated deletion of matching events.")
            return 5
            
        try:
            service = build("calendar", "v3", credentials=self._credentials)
            events_result = service.events().list(calendarId=self.calendarId, singleEvents=True).execute()
            events = events_result.get("items", [])
            
            for event in events:
                start_date_str = event.get("start", {}).get("date") or event.get("start", {}).get("dateTime", "")[:10]
                if not start_date_str:
                    continue
                
                dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                desc = event.get("description", "")
                
                match_category = not category or (category in desc)
                match_year = not year or (dt.year == year)
                match_month = not month or (dt.month == month)
                
                if match_category and match_year and match_month:
                    service.events().delete(calendarId=self.calendarId, eventId=event["id"]).execute()
                    deleted_count += 1
                    logger.info(f"Deleted filtered event: {event.get('summary')} ({start_date_str})")
                    
            return deleted_count
        except HttpError as error:
            logger.error(f"Error executing batch deletion filter: {error}")
            return deleted_count
        
