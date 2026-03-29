def test_t_returns_english_by_default():
    from i18n import t
    result = t("en", "handoff")
    assert "human support" in result.lower() or "connect you" in result.lower()

def test_t_returns_german():
    from i18n import t
    result = t("de", "handoff")
    assert "mitarbeiter" in result.lower() or "verbinden" in result.lower()

def test_t_unknown_lang_falls_back_to_english():
    from i18n import t
    result = t("fr", "handoff")
    assert result == t("en", "handoff")

def test_t_unknown_key_returns_empty():
    from i18n import t
    assert t("en", "nonexistent_key") == ""
