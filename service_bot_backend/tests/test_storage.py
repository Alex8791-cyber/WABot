import json
import os

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

def test_load_conversation_history_empty(tmp_path, monkeypatch):
    from storage import load_conversation_history
    monkeypatch.setattr("storage.CONVERSATIONS_FILE", str(tmp_path / "missing.json"))
    assert load_conversation_history() == {}

def test_save_and_load_conversation_history(tmp_path, monkeypatch):
    from storage import save_conversation_history, load_conversation_history
    path = str(tmp_path / "convos.json")
    monkeypatch.setattr("storage.CONVERSATIONS_FILE", path)
    data = {"session1": [{"role": "user", "content": "hi"}]}
    save_conversation_history(data)
    loaded = load_conversation_history()
    assert loaded == data

def test_save_customer_history(tmp_path, monkeypatch):
    from storage import save_customer_history
    monkeypatch.setattr("storage.CUSTOMERS_DIR", str(tmp_path))
    save_customer_history("test-session", [{"role": "user", "content": "hi"}])
    path = tmp_path / "test-session" / "history.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 1

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

def test_save_and_load_leads(tmp_path, monkeypatch):
    from storage import save_lead
    path = str(tmp_path / "leads.json")
    monkeypatch.setattr("storage.LEADS_FILE", path)
    save_lead({"service_id": "x", "responses": {}})
    data = json.loads(open(path, encoding="utf-8").read())
    assert len(data) == 1

def test_load_feature_config_defaults(tmp_path, monkeypatch):
    from storage import load_feature_config
    monkeypatch.setattr("storage.FEATURES_FILE", str(tmp_path / "missing.json"))
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    config = load_feature_config()
    assert config["enable_audio"] is False
    assert config["enable_images"] is False

def test_save_and_load_feature_config(tmp_path, monkeypatch):
    from storage import save_feature_config, load_feature_config
    path = str(tmp_path / "features.json")
    monkeypatch.setattr("storage.FEATURES_FILE", path)
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    save_feature_config({"enable_audio": True, "enable_images": False, "enable_tts": False})
    loaded = load_feature_config()
    assert loaded["enable_audio"] is True
