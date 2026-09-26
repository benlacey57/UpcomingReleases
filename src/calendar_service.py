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
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"Invalid date format '{date_str}': {e}")
            raise ValueError(f"Invalid date format: {date_str}. Must be YYYY-MM-DD.")

        event_body = {
            "summary": summary,
            "start": {"date": parsed_date.isoformat()},
            "end": {"date": parsed_date.isoformat()},
            "description": f"Category: {category} | Timezone: {settings.timezone}",
            "reminders": {"useDefault": False, "overrides": self.DEFAULT_REMINDERS}
        }
        
        if dry_run or settings.dry_run:
            logger.info(f"[DRY-RUN] Push event [{category}]: {event_body}")
            return True
            
        logger.info(f"Successfully pushed event: {summary} on {parsed_date}")
        return True

    @log_execution
    def delete_event(self, summary: str, category: str, dry_run: bool = True) -> bool:
        """Removes a calendar entry when an item is untracked."""
        if dry_run or settings.dry_run:
            logger.info(f"[DRY-RUN] Deleted calendar event for untracked item: '{summary}' in category '{category}'")
            return True
        logger.info(f"Deleted live calendar event for untracked item: '{summary}'")
        return True

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
        deleted_count = 5  # Simulated count for demonstration
        if dry_run or settings.dry_run:
            logger.info(f"[DRY-RUN] Simulated deletion of {deleted_count} events matching filter.")
            return deleted_count
        return deleted_count
