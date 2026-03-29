import json
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

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
    assert len(result) == 40
    assert result[-1]["content"] == "msg99"

def test_openai_available_flag():
    from services.llm import is_llm_available
    result = is_llm_available()
    assert isinstance(result, bool)

@patch("services.llm.get_openai_client")
def test_chat_no_tool_calls(mock_client_fn):
    """When LLM returns plain text, chat() returns that text."""
    mock_msg = MagicMock()
    mock_msg.content = "Hello, how can I help?"
    mock_msg.tool_calls = None
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client_fn.return_value.chat.completions.create.return_value = mock_response

    from services.llm import chat
    result = chat("system prompt", [{"role": "user", "content": "hi"}])
    assert result == "Hello, how can I help?"

@patch("services.llm.dispatch_tool")
@patch("services.llm.get_openai_client")
def test_chat_with_tool_call(mock_client_fn, mock_dispatch):
    """When LLM makes a tool call, chat() executes it and returns the final response."""
    # First call: LLM returns a tool call
    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = "list_calendar_events"
    tool_call.function.arguments = '{"start": "2026-04-01T00:00:00Z", "end": "2026-04-02T00:00:00Z"}'

    msg_with_tool = MagicMock()
    msg_with_tool.content = None
    msg_with_tool.tool_calls = [tool_call]
    msg_with_tool.role = "assistant"

    choice1 = MagicMock()
    choice1.message = msg_with_tool
    resp1 = MagicMock()
    resp1.choices = [choice1]

    # Second call: LLM returns final text
    msg_final = MagicMock()
    msg_final.content = "You have 2 meetings tomorrow."
    msg_final.tool_calls = None

    choice2 = MagicMock()
    choice2.message = msg_final
    resp2 = MagicMock()
    resp2.choices = [choice2]

    mock_client_fn.return_value.chat.completions.create.side_effect = [resp1, resp2]
    mock_dispatch.return_value = {"events": [{"summary": "Meeting 1"}, {"summary": "Meeting 2"}]}

    from services.llm import chat
    result = chat("system prompt", [{"role": "user", "content": "What meetings do I have?"}])
    assert result == "You have 2 meetings tomorrow."
    mock_dispatch.assert_called_once_with(
        "list_calendar_events",
        {"start": "2026-04-01T00:00:00Z", "end": "2026-04-02T00:00:00Z"},
    )
