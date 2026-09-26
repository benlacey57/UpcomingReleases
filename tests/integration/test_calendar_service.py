from src.calendar_service import CalendarService

def test_calendar_service_reminders():
    service = CalendarService()
    assert len(service.DEFAULT_REMINDERS) == 2
    assert service.DEFAULT_REMINDERS[0]["minutes"] == 1440

def test_calendar_sync_dry_run():
    service = CalendarService()
    result = service.sync_event("Test Summary", "2026-12-01", "tv-releases", dry_run=True)
    assert result is True
  
