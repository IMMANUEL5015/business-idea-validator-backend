from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from database.models import Idea, Conversation, ConversationRole
from helpers import AI

SUMMARY_THRESHOLD = 10

RECENT_MESSAGES_KEPT = 6

_summary_cache: dict[int, dict] = {}

def send_message(db: Session, user_id: int, idea_id: int, message: str) -> Conversation:
    idea = (
        db.query(Idea)
        .options(joinedload(Idea.validation), joinedload(Idea.business_plan))
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    user_msg = Conversation(idea_id=idea_id, role=ConversationRole.user, message=message)
    db.add(user_msg)
    db.commit()

    all_messages = (
        db.query(Conversation)
        .filter(Conversation.idea_id == idea_id)
        .order_by(Conversation.id.asc())
        .all()
    )

    if len(all_messages) > RECENT_MESSAGES_KEPT:
        old_messages = all_messages[:-RECENT_MESSAGES_KEPT]
        recent_messages = all_messages[-RECENT_MESSAGES_KEPT:]
    else:
        old_messages = []
        recent_messages = all_messages

    summary = _get_summary(idea_id, old_messages)

    ai_reply = AI.chat(
        title=idea.title,
        description=idea.description,
        summary=summary,
        recent_messages=recent_messages,
        validation=idea.validation,
        business_plan=idea.business_plan,
        user_message=message,
    )

    ai_msg = Conversation(idea_id=idea_id, role=ConversationRole.ai, message=ai_reply)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return ai_msg


def get_conversations(db: Session, user_id: int, idea_id: int) -> list[Conversation]:
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    return (
        db.query(Conversation)
        .filter(Conversation.idea_id == idea_id)
        .order_by(Conversation.id.asc())
        .all()
    )

def clear_conversations(db: Session, user_id: int, idea_id: int) -> None:
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    db.query(Conversation).filter(Conversation.idea_id == idea_id).delete()
    db.commit()

    _summary_cache.pop(idea_id, None)

def _get_summary(idea_id: int, old_messages: list) -> str:
    """
    Returns a cached summary of old_messages if still valid,
    otherwise generates a fresh one via AI and caches it.
    Returns an empty string if there are no old messages to summarise.
    """
    if not old_messages:
        return ""

    cached = _summary_cache.get(idea_id)

    if cached and cached["count"] == len(old_messages):
        return cached["summary"]

    summary = AI.summarize_conversations(old_messages)
    _summary_cache[idea_id] = {"count": len(old_messages), "summary": summary}
    return summary