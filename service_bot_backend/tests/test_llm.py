import pytest
from fastapi import HTTPException

def test_get_openai_client_raises_without_key(monkeypatch):
    from services.llm import get_openai_client
    monkeypatch.setattr("services.llm.OPENAI_API_KEY", "")
    monkeypatch.setattr("services.llm._openai_available", True)
    with pytest.raises(HTTPException) as exc_info:
        get_openai_client()
    assert exc_info.value.status_code == 503

def test_get_openai_client_raises_without_package(monkeypatch):
    from services.llm import get_openai_client
    monkeypatch.setattr("services.llm._openai_available", False)
    with pytest.raises(HTTPException) as exc_info:
        get_openai_client()
    assert exc_info.value.status_code == 503

def test_truncate_history_short_list():
    from services.llm import truncate_history
    history = [{"role": "user", "content": "hi"}]
    assert truncate_history(history) == history

def test_truncate_history_long_list():
    from services.llm import truncate_history
    history = [{"role": "user", "content": f"msg{i}"} for i in range(100)]
    result = truncate_history(history)
    assert len(result) == 40  # MAX_HISTORY_MESSAGES default
    assert result[-1]["content"] == "msg99"

def test_openai_available_flag():
    from services.llm import is_llm_available
    result = is_llm_available()
    assert isinstance(result, bool)
