from fastapi import APIRouter, Depends
from models import FeaturesConfig
from auth import require_admin
from storage import load_feature_config, save_feature_config

router = APIRouter()


@router.get("/features/config")
def get_features_config():
    config = load_feature_config()
    return FeaturesConfig(
        enable_audio=config.get("enable_audio", False),
        enable_images=config.get("enable_images", False),
        enable_tts=config.get("enable_tts", False),
        whisper_model=config.get("whisper_model"),
        vision_api_key="***" if config.get("vision_api_key") else None,
    )


@router.post("/features/config", dependencies=[Depends(require_admin)])
def update_features_config(config: FeaturesConfig):
    current = load_feature_config()
    for field in ("enable_audio", "enable_images", "enable_tts", "whisper_model", "vision_api_key"):
        val = getattr(config, field)
        if val is not None:
            current[field] = val if val != "" else None
    save_feature_config(current)
    return FeaturesConfig(
        enable_audio=current.get("enable_audio", False),
        enable_images=current.get("enable_images", False),
        enable_tts=current.get("enable_tts", False),
        whisper_model=current.get("whisper_model"),
        vision_api_key="***" if current.get("vision_api_key") else None,
    )
