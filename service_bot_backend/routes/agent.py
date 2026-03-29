import uuid
import asyncio

from fastapi import APIRouter, Depends

from models import AgentMessage, AgentConfig
from auth import require_admin
from i18n import t
from storage import (
    read_agents, write_agents, read_soul, write_soul,
    build_system_prompt, load_conversation_history, save_conversation_history,
    save_customer_history,
)
from services.sentiment import check_handoff
from services.llm import is_llm_available, chat
from services.multimedia import transcribe_audio, describe_image
import config as cfg

router = APIRouter()

# Shared mutable state
conversation_history = load_conversation_history()
_state_lock = asyncio.Lock()


@router.get("/agent/config")
def get_agent_config():
    return AgentConfig(
        agents=read_agents(),
        soul=read_soul(),
        api_key="***" if cfg.OPENAI_API_KEY else None,
    )


@router.post("/agent/config", dependencies=[Depends(require_admin)])
def update_agent_config(agent_config: AgentConfig):
    if agent_config.agents is not None:
        write_agents(agent_config.agents)
    if agent_config.soul is not None:
        write_soul(agent_config.soul)
    if agent_config.api_key is not None:
        cfg.OPENAI_API_KEY = agent_config.api_key
    return AgentConfig(
        agents=read_agents(),
        soul=read_soul(),
        api_key="***" if cfg.OPENAI_API_KEY else None,
    )


@router.post("/agent/message")
async def agent_message(msg: AgentMessage):
    lang = (msg.lang or "en").lower()
    session_id = msg.session_id or str(uuid.uuid4())

    # Process multimedia
    user_text = msg.message
    if msg.message_type == "audio" and msg.data_base64:
        user_text = transcribe_audio(msg.data_base64, lang)
    elif msg.message_type == "image" and msg.data_base64:
        user_text = describe_image(msg.data_base64, lang)

    async with _state_lock:
        history = conversation_history.setdefault(session_id, [])
        history.append({"role": "user", "content": user_text})

        # Handoff check
        handoff_msg = check_handoff(session_id, user_text, lang)
        if handoff_msg:
            history.append({"role": "assistant", "content": handoff_msg})
            save_conversation_history(conversation_history)
            save_customer_history(session_id, history)
            return {"reply": handoff_msg, "session_id": session_id, "handoff": True}

    # LLM fallback
    if not is_llm_available():
        fallback = t(lang, "llm_unavailable")
        async with _state_lock:
            history.append({"role": "assistant", "content": fallback})
            save_conversation_history(conversation_history)
            save_customer_history(session_id, history)
        return {"reply": fallback, "session_id": session_id}

    # Build system prompt with language directive
    system_prompt = build_system_prompt()
    directive = t(lang, "directive")
    if directive:
        system_prompt = f"{directive}\n\n{system_prompt}" if system_prompt else directive

    reply = chat(system_prompt, history)

    async with _state_lock:
        history.append({"role": "assistant", "content": reply})
        save_conversation_history(conversation_history)
        save_customer_history(session_id, history)

    return {"reply": reply, "session_id": session_id}
