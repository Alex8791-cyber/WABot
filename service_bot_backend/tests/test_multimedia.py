import base64

def test_transcribe_audio_disabled(monkeypatch):
    from services.multimedia import transcribe_audio
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_audio": False})
    result = transcribe_audio(base64.b64encode(b"fake").decode(), "en")
    assert "unavailable" in result.lower() or "disabled" in result.lower()

def test_transcribe_audio_invalid_base64(monkeypatch):
    from services.multimedia import transcribe_audio
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_audio": True})
    result = transcribe_audio("not-valid-base64!!!", "en")
    assert "unavailable" in result.lower()

def test_describe_image_disabled(monkeypatch):
    from services.multimedia import describe_image
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_images": False})
    result = describe_image(base64.b64encode(b"fake").decode(), "en")
    assert "unavailable" in result.lower() or "disabled" in result.lower()

def test_describe_image_no_openai(monkeypatch):
    from services.multimedia import describe_image
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_images": True})
    monkeypatch.setattr("services.multimedia._openai_available", False)
    result = describe_image(base64.b64encode(b"fake").decode(), "en")
    assert "unavailable" in result.lower()
