"""Audio transcription and image analysis."""

import io
import base64
import logging

from config import OPENAI_API_KEY, VISION_MODEL
from i18n import t
from storage import load_feature_config

logger = logging.getLogger("service_bot")

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    OpenAI = None


def transcribe_audio(data_b64: str, lang: str) -> str:
    config = load_feature_config()
    if not config.get("enable_audio", False):
        return t(lang, "audio_fallback")
    try:
        audio_bytes = base64.b64decode(data_b64)
    except Exception:
        return t(lang, "audio_fallback")

    # Try local whisper
    try:
        import whisper  # type: ignore
        model_name = config.get("whisper_model") or "base"
        model = whisper.load_model(model_name)
        result = model.transcribe(
            io.BytesIO(audio_bytes),
            language=lang if lang in ("de", "en") else None,
        )
        text = result.get("text", "")
        if text:
            return text
    except ImportError:
        logger.info("whisper not installed — trying OpenAI API")
    except Exception as e:
        logger.warning("Local whisper failed: %s", e)

    # Fallback to OpenAI Whisper API
    if _openai_available and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.webm"
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file,
            )
            if transcript.text:
                return transcript.text
        except Exception as e:
            logger.warning("OpenAI Whisper API failed: %s", e)

    return t(lang, "audio_fallback")


def describe_image(data_b64: str, lang: str) -> str:
    config = load_feature_config()
    if not config.get("enable_images", False):
        return t(lang, "image_fallback")
    if not _openai_available:
        return t(lang, "image_fallback")
    api_key = config.get("vision_api_key") or OPENAI_API_KEY
    if not api_key:
        return t(lang, "image_fallback")

    try:
        client = OpenAI(api_key=api_key)
        system_msg = {
            "en": "Describe the contents of the image in English.",
            "de": "Beschreibe den Inhalt des Bildes auf Deutsch.",
        }.get(lang, "Describe the contents of the image.")

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{data_b64}",
                    }},
                ]},
            ],
            max_tokens=256,
        )
        content = response.choices[0].message.content
        if content:
            return content
    except Exception as e:
        logger.warning("Image description failed: %s", e)

    return t(lang, "image_fallback")
