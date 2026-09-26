import pytest
from src.fetchers import StudioReleaseChecker
from src.storage import ReleaseStorage

def test_studio_fetcher_mixed_media():
    """Test that a studio release checker correctly parses and separates movies and TV series."""
    mock_studio_api_response = [
        {
            "media_type": "movie",
            "title": "Avengers: Secret Wars",
            "release_date": "2027-05-01"
        },
        {
            "media_type": "tv",
            "title": "Daredevil: Born Again",
            "season": 1,
            "episode": 2,
            "episode_name": "New York's Finest",
            "release_date": "2026-11-10"
        }
    ]
    
    checker = StudioReleaseChecker(studio_name="Marvel", raw_mock_data=mock_studio_api_response)
    releases = checker.fetch_releases()

    # Verify Movie parsing
    movie_key = ReleaseStorage.normalize_key("movie", "Avengers: Secret Wars")
    assert movie_key in releases
    assert releases[movie_key]["type"] == "movie"
    assert releases[movie_key]["category"] == "movie-releases"
    assert releases[movie_key]["date"] == "2027-05-01"

    # Verify TV Series nested episode parsing
    tv_key = ReleaseStorage.normalize_key("tv", "Daredevil: Born Again")
    assert tv_key in releases
    assert releases[tv_key]["type"] == "tv"
    assert releases[tv_key]["category"] == "tv-releases"
    assert "s01e02" in releases[tv_key]["episodes"]
    assert releases[tv_key]["episodes"]["s01e02"]["episode_name"] == "New York's Finest"
    assert releases[tv_key]["episodes"]["s01e02"]["date"] == "2026-11-10"

def test_studio_fetcher_empty_response():
    """Edge Case: Studio returns no upcoming releases."""
    checker = StudioReleaseChecker(studio_name="UnknownStudio", raw_mock_data=[])
    releases = checker.fetch_releases()
    assert releases == {}

def test_studio_fetcher_malformed_item():
    """Edge Case: Studio response contains items missing essential fields."""
    malformed_data = [
        {"title": "Incomplete Item"} # Missing media_type, date, etc.
    ]
    checker = StudioReleaseChecker(studio_name="DC", raw_mock_data=malformed_data)
    releases = checker.fetch_releases()
    
    # Should default safely without crashing
    key = ReleaseStorage.normalize_key("movie", "Incomplete Item")
    assert key in releases
    assert releases[key]["date"] == "2026-12-31"
  
def test_studio_fetcher_logs_to_storage(tmp_path):
    """Test that studio release checking writes an audit record to the version-controlled log."""
    state_file = tmp_path / "state.json"
    cache_file = tmp_path / "cache.json"
    log_file = tmp_path / "history.log"
    storage = ReleaseStorage(str(state_file), str(cache_file), str(log_file))

    mock_data = [
        {"media_type": "movie", "title": "Thunderbolts", "release_date": "2027-05-01"}
    ]
    
    checker = StudioReleaseChecker(studio_name="Marvel", raw_mock_data=mock_data, storage=storage)
    releases = checker.fetch_releases()

    assert len(releases) == 1
    assert log_file.exists()
    
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        assert "STUDIO_FETCH" in log_content
        assert "Marvel" in log_content
