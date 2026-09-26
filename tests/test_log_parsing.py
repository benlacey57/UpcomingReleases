import os
from src.storage import ReleaseStorage

def test_log_parsing_and_structure(tmp_path):
    log_file = tmp_path / "test.log"
    storage = ReleaseStorage(state_file=str(tmp_path / "state.json"), cache_file=str(tmp_path / "cache.json"), log_file=str(log_file))
    
    storage.log_event("Synced event: Breaking Bad S01E01")
    
    assert os.path.exists(log_file)
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "UTC" in content
        assert "Synced event: Breaking Bad S01E01" in content
      
