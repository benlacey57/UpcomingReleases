from src.fetchers import TMDBReleaseChecker

def test_tmdb_fetcher_hierarchy():
    tracked = [
        {"type": "tv", "title": "Breaking Bad", "season": 1, "episode": 1, "episode_name": "Pilot", "release_date": "2026-10-15"},
        {"type": "movie", "title": "Inception", "release_date": "2026-11-01"}
    ]
    checker = TMDBReleaseChecker(tracked)
    releases = checker.fetch_releases()

    assert "tv:breaking-bad" in releases
    assert releases["tv:breaking-bad"]["episodes"]["s01e01"]["episode_name"] == "Pilot"
    
    assert "movie:inception" in releases
    assert releases["movie:inception"]["date"] == "2026-11-01"
  
