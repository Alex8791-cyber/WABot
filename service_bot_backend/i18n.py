"""Localized message templates for the service bot."""

LANGUAGE_TEMPLATES = {
    "en": {
        "audio_fallback": (
            "[Audio processing unavailable] An audio message was received, "
            "but audio processing is disabled or not configured."
        ),
        "image_fallback": (
            "[Image processing unavailable] An image was received, "
            "but image processing is disabled or not configured."
        ),
        "handoff": (
            "I see you're having a tough time. I'd like to connect you "
            "with one of our human support specialists who can assist you further."
        ),
        "llm_unavailable": (
            "[LLM unavailable] I received your message but the AI service "
            "is not configured. Please set the OPENAI_API_KEY."
        ),
        "directive": "Please answer in English.",
    },
    "de": {
        "audio_fallback": (
            "[Audiobearbeitung nicht verfügbar] Eine Sprachnachricht wurde empfangen, "
            "aber die Audioverarbeitung ist deaktiviert oder nicht konfiguriert."
        ),
        "image_fallback": (
            "[Bildverarbeitung nicht verfügbar] Ein Bild wurde empfangen, "
            "aber die Bildverarbeitung ist deaktiviert oder nicht konfiguriert."
        ),
        "handoff": (
            "Ich sehe, dass Sie Schwierigkeiten haben. Ich werde Sie mit einem "
            "unserer menschlichen Support-Mitarbeiter verbinden, der Ihnen weiterhelfen kann."
        ),
        "llm_unavailable": (
            "[LLM nicht verfügbar] Ich habe Ihre Nachricht erhalten, aber der "
            "KI-Dienst ist nicht konfiguriert. Bitte setzen Sie den OPENAI_API_KEY."
        ),
        "directive": "Bitte antworte auf Deutsch.",
    },
}


def t(lang: str, key: str) -> str:
    """Get a localized template string. Falls back to English, then empty string."""
    templates = LANGUAGE_TEMPLATES.get(lang, LANGUAGE_TEMPLATES["en"])
    return templates.get(key, LANGUAGE_TEMPLATES["en"].get(key, ""))
