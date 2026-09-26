import os
from src.storage import ReleaseStorage

def test_normalization_keys():
    assert ReleaseStorage.normalize_key("tv", "Breaking Bad") == "tv:breaking-bad"
    assert ReleaseStorage.normalize_key("movie", "Dune: Part Two") == "movie:dune-part-two"

def test_storage_lifecycle(tmp_path):
    state_file = tmp_path / "state.json"
    cache_file = tmp_path / "cache.json"
    log_file = tmp_path / "history.log"

    storage = ReleaseStorage(str(state_file), str(cache_file), str(log_file))
    
    state = storage.load_state()
    assert state == {"releases": {}}

    state["releases"]["movie:test"] = {"title": "Test Movie", "synced": False}
    storage.save_state(state)
    assert storage.load_state()["releases"]["movie:test"]["title"] == "Test Movie"

    storage.log_event("Test log entry")
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        assert "Test log entry" in f.read()
      
