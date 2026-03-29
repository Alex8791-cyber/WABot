from fastapi import APIRouter
from config import MODEL_NAME
from services.llm import is_llm_available

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "llm_available": is_llm_available(),
        "model": MODEL_NAME,
    }
