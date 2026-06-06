from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, User
from app.schemas import ChatRequest, ChatResponse
from app.services.ai_service import check_ai_status, generate_chat_response

router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.get("/status")
async def chat_status():
    return await check_ai_status()


@router.post("/guest", response_model=ChatResponse)
async def chat_guest(data: ChatRequest):
    """AI chat without login — connects to local Ollama."""
    result = await generate_chat_response(data.message, data.chat_type, data.language)
    return ChatResponse(
        reply=result["reply"],
        chat_type=result["chat_type"],
        structured_data=result.get("structured_data"),
        ai_available=result.get("ai_available", True),
    )


@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    language = data.language or user.language
    result = await generate_chat_response(data.message, data.chat_type, language)

    chat_log = Chat(
        user_id=user.id,
        user_message=data.message,
        ai_response=result["reply"],
        chat_type=result["chat_type"],
    )
    db.add(chat_log)
    db.commit()

    return ChatResponse(
        reply=result["reply"],
        chat_type=result["chat_type"],
        structured_data=result.get("structured_data"),
        ai_available=result.get("ai_available", True),
    )
