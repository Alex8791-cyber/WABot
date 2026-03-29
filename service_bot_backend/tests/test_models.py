# service_bot_backend/tests/test_models.py
import pytest
from pydantic import ValidationError

def test_agent_message_valid():
    from models import AgentMessage
    msg = AgentMessage(message="Hello")
    assert msg.message == "Hello"
    assert msg.lang == "en"
    assert msg.session_id is None
    assert msg.message_type is None

def test_agent_message_empty_rejected():
    from models import AgentMessage
    with pytest.raises(ValidationError):
        AgentMessage(message="")

def test_agent_message_invalid_lang_rejected():
    from models import AgentMessage
    with pytest.raises(ValidationError):
        AgentMessage(message="hi", lang="english")

def test_agent_message_invalid_type_rejected():
    from models import AgentMessage
    with pytest.raises(ValidationError):
        AgentMessage(message="hi", message_type="video")

def test_lead_model():
    from models import Lead
    lead = Lead(service_id="test", responses={"q1": "a1"})
    assert lead.service_id == "test"

def test_agent_config_model():
    from models import AgentConfig
    config = AgentConfig()
    assert config.agents is None
    assert config.soul is None
    assert config.api_key is None

def test_features_config_model():
    from models import FeaturesConfig
    config = FeaturesConfig(enable_audio=True)
    assert config.enable_audio is True
    assert config.enable_images is None
