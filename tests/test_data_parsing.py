from src.storage import ReleaseStorage
from src.fetchers import TMDBReleaseChecker

def test_nested_data_parsing_integrity():
    tracked_data = [
        {"type": "tv", "title": "The Mandalorian", "season": 3, "episode": 4, "episode_name": "Chapter 20", "release_date": "2026-05-10"}
    ]
    checker = TMDBReleaseChecker(tracked_data)
    result = checker.fetch_releases()

    key = ReleaseStorage.normalize_key("tv", "The Mandalorian")
    assert key == "tv:the-mandalorian"
    assert result[key]["type"] == "tv"
    assert result[key]["category"] == "tv-releases"
    assert "s03e04" in result[key]["episodes"]
    assert result[key]["episodes"]["s03e04"]["episode_name"] == "Chapter 20"
  
