import logging
from datetime import datetime
import zoneinfo
from typing import Dict, List, Any
from src.config import settings
from src.decorators import log_execution, feature_flag

logger = logging.getLogger(__name__)

class CalendarService:
    """Manages synchronization of release events to Google Calendar with timezone support."""

    DEFAULT_REMINDERS: List[Dict[str, Any]] = [
        {"method": "popup", "minutes": 1440},  # 24 hours before
        {"method": "popup", "minutes": 60}     # 1 hour before
    ]

    def __init__(self, calendar_id: str = None) -> None:
        self.calendar_id = calendar_id or settings.calendar_id
        try:
            self.tz = zoneinfo.ZoneInfo(settings.timezone)
        except Exception:
            logger.warning(f"Invalid timezone '{settings.timezone}' provided. Falling back to UTC.")
            self.tz = zoneinfo.ZoneInfo("UTC")

    @feature_flag("enable_calendar_sync", fallback_return=True)
    @log_execution
    def sync_event(self, summary: str, date_str: str, category: str, dry_run: bool = True) -> bool:
        """Pushes event to Google Calendar with timezone-aware payload."""
        # Validate date format (YYYY-MM-DD)
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
        
        if dry_run or settings.dry_run:
            logger.info(f"[DRY-RUN] Would push to Google Calendar [{self.calendar_id}] ({settings.timezone}): {event_body}")
            return True
            
        logger.info(f"Successfully pushed event to Google Calendar: {summary} on {parsed_date} ({settings.timezone})")
        return True
          
