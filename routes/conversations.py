from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User
from helpers.schemas import SendMessageRequest, ConversationResponse
from services.users import get_current_user
import services.conversations as conversation_services

router = APIRouter(prefix="/ideas/{idea_id}/conversations", tags=["Conversations"])


@router.post("/", response_model=ConversationResponse, status_code=201)
def send_message(
    idea_id: int,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conversation_services.send_message(db, current_user.id, idea_id, body.message)


@router.get("/", response_model=list[ConversationResponse])
def get_conversations(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conversation_services.get_conversations(db, current_user.id, idea_id)


@router.delete("/", status_code=204)
def clear_conversations(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation_services.clear_conversations(db, current_user.id, idea_id)