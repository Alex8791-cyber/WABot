# service_bot_backend/tests/test_routes_agent.py

def test_get_agent_config(client):
    resp = client.get("/agent/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "agents" in data
    assert "soul" in data

def test_agent_message_without_llm(client):
    resp = client.post("/agent/message", json={
        "message": "Hello",
        "lang": "en"
    })
    # Without OPENAI_API_KEY, should return LLM unavailable fallback
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "session_id" in data

def test_agent_message_persists_to_db(client):
    resp = client.post("/agent/message", json={
        "message": "Hello",
        "session_id": "test-persist",
        "lang": "en"
    })
    assert resp.status_code == 200
    # Verify message was persisted
    from storage import get_session_history
    history = get_session_history("test-persist")
    assert len(history) >= 2  # user message + assistant reply
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"

def test_agent_message_empty_rejected(client):
    resp = client.post("/agent/message", json={"message": ""})
    assert resp.status_code == 422  # Pydantic validation
