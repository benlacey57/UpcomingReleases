import os
from src.config import Settings

def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("CALENDAR_ID", raising=False)
    settings = Settings()
    assert settings.calendar_id == "primary"
    assert settings.dry_run is True

def test_settings_custom_env(monkeypatch):
    monkeypatch.setenv("CALENDAR_ID", "custom-calendar-id")
    monkeypatch.setenv("DRY_RUN", "false")
    settings = Settings()
    assert settings.calendar_id == "custom-calendar-id"
    assert settings.dry_run is False
  
