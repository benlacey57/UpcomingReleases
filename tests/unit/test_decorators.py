import pytest
from src.decorators import log_execution, feature_flag, retry_on_failure
from src.config import settings

def test_log_execution_decorator(caplog):
    @log_execution
    def sample_func(x: int) -> int:
        return x * 2

    res = sample_func(5)
    assert res == 10
    assert "Executing 'sample_func'" in caplog.text

def test_feature_flag_decorator(monkeypatch):
    monkeypatch.setattr(settings, "enable_calendar_sync", False)

    @feature_flag("enable_calendar_sync", fallback_return="bypassed")
    def guarded_func():
        return "executed"

    assert guarded_func() == "bypassed"

def test_retry_on_failure_decorator():
    attempts = 0

    @retry_on_failure(retries=3, delay=0.01)
    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Temporary failure")
        return "success"

    assert flaky_func() == "success"
    assert attempts == 3
  
