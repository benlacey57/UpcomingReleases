import os
import pytest
from typing import Generator
from src.storage import ReleaseStorage

@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically isolates environment variables for every test to prevent live leaks."""
    monkeypatch.setenv("ENCRYPTION_KEY", "K1_DummY_EncRyptIoN_Key_For_TesTs_OnLy==")
    monkeypatch.setenv("CALENDAR_ID", "primary")
    monkeypatch.setenv("TIMEZONE", "UTC")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("ENABLE_CALENDAR_SYNC", "true")
    monkeypatch.setenv("ENABLE_GIT_COMMIT", "false")
    monkeypatch.setenv("ENABLE_API_FETCH", "true")

@pytest.fixture
def temp_storage(tmp_path) -> ReleaseStorage:
    """Provides an isolated ReleaseStorage instance using temporary test directories."""
    state_file = tmp_path / "data" / "state.json"
    cache_file = tmp_path / "data" / "cache.json"
    tracked_file = tmp_path / "data" / "tracked_media.json"
    log_file = tmp_path / "logs" / "release_history.log"
    
    return ReleaseStorage(
        state_file=str(state_file),
        cache_file=str(cache_file),
        tracked_file=str(tracked_file),
        log_file=str(log_file)
    )
  
