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

def test_agent_message_empty_rejected(client):
    resp = client.post("/agent/message", json={"message": ""})
    assert resp.status_code == 422  # Pydantic validation
