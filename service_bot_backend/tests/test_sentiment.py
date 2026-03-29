def test_analyze_sentiment_negative_en():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("This is terrible and awful", lang="en")
    assert score < 0

def test_analyze_sentiment_positive_en():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("This is great and wonderful", lang="en")
    assert score > 0

def test_analyze_sentiment_neutral():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("The sky is blue", lang="en")
    assert -0.5 <= score <= 0.5

def test_analyze_sentiment_negative_de():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("Das ist furchtbar und schrecklich", lang="de")
    assert score < 0

def test_analyze_sentiment_positive_de():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("Das ist super und wunderbar", lang="de")
    assert score > 0

def test_analyze_sentiment_empty():
    from services.sentiment import analyze_sentiment
    assert analyze_sentiment("", lang="en") == 0.0

def test_analyze_sentiment_clamped():
    from services.sentiment import analyze_sentiment
    # Many negative words — should clamp at -1.0
    text = " ".join(["problem", "angry", "bad", "terrible", "frustrated", "awful", "horrible"])
    score = analyze_sentiment(text, lang="de")  # force keyword fallback
    assert score >= -1.0

def test_check_handoff_triggers():
    from services.sentiment import check_handoff
    # First negative — no handoff yet
    result1 = check_handoff("s1", "terrible awful", "en")
    assert result1 is None
    # Second negative — handoff triggered (threshold=2)
    result2 = check_handoff("s1", "horrible angry", "en")
    assert result2 is not None
    assert "connect" in result2.lower() or "support" in result2.lower()

def test_check_handoff_resets_on_positive():
    from services.sentiment import check_handoff, _negative_counts
    _negative_counts.clear()
    check_handoff("s2", "terrible awful", "en")
    check_handoff("s2", "thanks great", "en")  # positive resets
    result = check_handoff("s2", "terrible awful", "en")
    assert result is None  # only 1 negative after reset
