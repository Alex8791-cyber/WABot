"""Pydantic request/response models."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from config import MAX_MESSAGE_LENGTH


class Lead(BaseModel):
    service_id: str
    responses: Dict[str, Any]


class AgentConfig(BaseModel):
    agents: Optional[str] = None
    soul: Optional[str] = None
    api_key: Optional[str] = None


class AgentMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    session_id: Optional[str] = None
    lang: Optional[str] = Field(default="en", pattern=r"^[a-z]{2}$")
    message_type: Optional[str] = Field(default=None, pattern=r"^(text|audio|image)$")
    data_base64: Optional[str] = None


class FeaturesConfig(BaseModel):
    enable_audio: Optional[bool] = None
    enable_images: Optional[bool] = None
    enable_tts: Optional[bool] = None
    whisper_model: Optional[str] = None
    vision_api_key: Optional[str] = None
