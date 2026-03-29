import json

def test_read_file_returns_content(tmp_path):
    from storage import read_file
    f = tmp_path / "test.md"
    f.write_text("hello world", encoding="utf-8")
    assert read_file(str(f)) == "hello world"

def test_read_file_returns_empty_for_missing():
    from storage import read_file
    assert read_file("/nonexistent/path/file.md") == ""

def test_write_file_creates_file(tmp_path):
    from storage import write_file
    path = str(tmp_path / "sub" / "test.txt")
    write_file(path, "content")
    assert open(path, encoding="utf-8").read() == "content"

def test_build_system_prompt_includes_services():
    from storage import build_system_prompt
    prompt = build_system_prompt()
    assert "Our Services" in prompt
    assert "Cloud Architecture Migration" in prompt
    assert "Penetration Testing" in prompt

def test_sanitize_session_id():
    from storage import sanitize_session_id
    assert sanitize_session_id("abc-123_def") == "abc-123_def"
    assert sanitize_session_id("a/b\\c:d") == "a_b_c_d"
    assert len(sanitize_session_id("x" * 200)) == 128

def test_load_services(tmp_path, monkeypatch):
    from storage import load_services
    path = tmp_path / "services.json"
    path.write_text('[{"id": "svc1", "name": "Test"}]', encoding="utf-8")
    monkeypatch.setattr("storage.SERVICES_FILE", str(path))
    result = load_services()
    assert result[0]["id"] == "svc1"

# --- SQLite-backed: conversations ---

def test_add_and_get_messages(test_db):
    from storage import add_message, get_session_history
    add_message("s1", "user", "hello")
    add_message("s1", "assistant", "hi there")
    history = get_session_history("s1")
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "hello"}
    assert history[1] == {"role": "assistant", "content": "hi there"}

def test_get_session_history_empty(test_db):
    from storage import get_session_history
    assert get_session_history("nonexistent") == []

def test_get_all_sessions(test_db):
    from storage import add_message, get_all_sessions
    add_message("s1", "user", "hi")
    add_message("s2", "user", "hello")
    sessions = get_all_sessions()
    assert set(sessions) == {"s1", "s2"}

def test_get_all_conversation_history(test_db):
    from storage import add_message, get_all_conversation_history
    add_message("s1", "user", "hi")
    add_message("s1", "assistant", "hello")
    add_message("s2", "user", "hey")
    history = get_all_conversation_history()
    assert "s1" in history
    assert "s2" in history
    assert len(history["s1"]) == 2
    assert len(history["s2"]) == 1

# --- SQLite-backed: leads ---

def test_save_and_get_leads(test_db):
    from storage import save_lead, get_leads
    save_lead({"service_id": "svc1", "responses": {"q1": "a1"}})
    save_lead({"service_id": "svc2", "responses": {"q2": "a2"}})
    leads = get_leads()
    assert len(leads) == 2
    assert leads[0]["service_id"] == "svc1"
    assert leads[0]["responses"] == {"q1": "a1"}

# --- SQLite-backed: features ---

def test_load_feature_config_defaults(test_db, monkeypatch):
    from storage import load_feature_config
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    config = load_feature_config()
    assert config["enable_audio"] is False
    assert config["enable_images"] is False

def test_save_and_load_feature_config(test_db, monkeypatch):
    from storage import save_feature_config, load_feature_config
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    save_feature_config({"enable_audio": True, "enable_images": False, "enable_tts": False})
    loaded = load_feature_config()
    assert loaded["enable_audio"] is True
    assert loaded["enable_images"] is False
