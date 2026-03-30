# service_bot_backend/services/sentiment.py
"""Sentiment analysis with VADER (EN) and keyword fallback (DE)."""

import logging
from typing import Optional

import config as cfg
from i18n import t

logger = logging.getLogger("service_bot")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _sentiment_analyzer = SentimentIntensityAnalyzer()
except Exception:
    _sentiment_analyzer = None
    logger.info("vaderSentiment not available — using keyword fallback")

_NEGATIVE_DE = [
    "problem", "schlecht", "wütend", "ärgerlich", "enttäuscht", "furchtbar",
    "schrecklich", "miserabel", "katastrophe", "unzufrieden", "verärgert",
    "nervig", "frustriert", "sauer", "genervt", "unbrauchbar", "mangelhaft",
]
_POSITIVE_DE = [
    "gut", "super", "danke", "zufrieden", "toll", "wunderbar", "hervorragend",
    "perfekt", "prima", "klasse", "ausgezeichnet", "freundlich", "hilfreich",
]
_NEGATIVE_EN = [
    "problem", "angry", "bad", "terrible", "frustrated", "awful", "horrible",
    "disappointed", "unacceptable", "useless", "annoying", "poor", "worst",
]
_POSITIVE_EN = [
    "good", "great", "happy", "thanks", "excellent", "wonderful", "helpful",
    "perfect", "amazing", "fantastic", "satisfied", "love",
]

_negative_counts: dict[str, int] = {}


def analyze_sentiment(text: str, lang: str = "en") -> float:
    if not text:
        return 0.0
    if lang == "en" and _sentiment_analyzer is not None:
        try:
            return _sentiment_analyzer.polarity_scores(text).get("compound", 0.0)
        except Exception as e:
            logger.warning("VADER sentiment failed: %s", e)
    negatives = _NEGATIVE_DE if lang == "de" else _NEGATIVE_EN
    positives = _POSITIVE_DE if lang == "de" else _POSITIVE_EN
    text_lower = text.lower()
    score = 0.0
    for word in negatives:
        if word in text_lower:
            score -= 0.25
    for word in positives:
        if word in text_lower:
            score += 0.25
    return max(-1.0, min(1.0, score))


def check_handoff(session_id: str, text: str, lang: str) -> Optional[str]:
    # Prevent memory leak — cap dict size
    if len(_negative_counts) > 10000:
        _negative_counts.clear()
    sentiment = analyze_sentiment(text, lang=lang)
    if sentiment < -0.5:
        _negative_counts[session_id] = _negative_counts.get(session_id, 0) + 1
    else:
        _negative_counts[session_id] = 0
    if _negative_counts.get(session_id, 0) >= cfg.HANDOFF_THRESHOLD:
        return t(lang, "handoff")
    return None
