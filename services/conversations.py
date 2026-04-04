from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from database.models import Idea, Conversation, ConversationRole
from helpers import AI

# Number of messages that triggers summarisation of older history.
# Once total messages exceed this, everything except the most recent
# RECENT_MESSAGES_KEPT messages is compressed into a cached summary.
SUMMARY_THRESHOLD = 10

# These most-recent messages are always passed verbatim to the AI,
# regardless of whether a summary exists, to preserve immediate context.
RECENT_MESSAGES_KEPT = 6

# In-memory summary cache.
# Structure: { idea_id: { "count": int, "summary": str } }
# "count" is the number of OLD messages (total - RECENT_MESSAGES_KEPT)
# at the time the summary was generated. If that count hasn't changed,
# the cached summary is still valid — no re-summarisation needed.
_summary_cache: dict[int, dict] = {}


# ─────────────────────────────────────────────
# SEND MESSAGE
# ─────────────────────────────────────────────

def send_message(db: Session, user_id: int, idea_id: int, message: str) -> Conversation:
    idea = (
        db.query(Idea)
        .options(joinedload(Idea.validation), joinedload(Idea.business_plan))
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    # Persist the user's message first
    user_msg = Conversation(idea_id=idea_id, role=ConversationRole.user, message=message)
    db.add(user_msg)
    db.commit()

    # Fetch full conversation history in chronological order
    all_messages = (
        db.query(Conversation)
        .filter(Conversation.idea_id == idea_id)
        .order_by(Conversation.id.asc())
        .all()
    )

    # Split into old (to be summarised) and recent (passed verbatim)
    if len(all_messages) > RECENT_MESSAGES_KEPT:
        old_messages = all_messages[:-RECENT_MESSAGES_KEPT]
        recent_messages = all_messages[-RECENT_MESSAGES_KEPT:]
    else:
        old_messages = []
        recent_messages = all_messages

    # Get a cached or freshly generated summary of the older messages
    summary = _get_summary(idea_id, old_messages)

    # Call the AI with the full RAG context
    ai_reply = AI.chat(
        title=idea.title,
        description=idea.description,
        summary=summary,
        recent_messages=recent_messages,
        validation=idea.validation,
        business_plan=idea.business_plan,
        user_message=message,
    )

    # Persist the AI's reply
    ai_msg = Conversation(idea_id=idea_id, role=ConversationRole.ai, message=ai_reply)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return ai_msg


# ─────────────────────────────────────────────
# GET CONVERSATIONS
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# CLEAR CONVERSATIONS
# ─────────────────────────────────────────────

def clear_conversations(db: Session, user_id: int, idea_id: int) -> None:
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == user_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")

    db.query(Conversation).filter(Conversation.idea_id == idea_id).delete()
    db.commit()

    # Invalidate this idea's summary cache
    _summary_cache.pop(idea_id, None)


# ─────────────────────────────────────────────
# PRIVATE — SUMMARY CACHE LOGIC
# ─────────────────────────────────────────────

def _get_summary(idea_id: int, old_messages: list) -> str:
    """
    Returns a cached summary of old_messages if still valid,
    otherwise generates a fresh one via AI and caches it.
    Returns an empty string if there are no old messages to summarise.
    """
    if not old_messages:
        return ""

    cached = _summary_cache.get(idea_id)

    # Cache hit: the set of old messages hasn't grown since last summarisation
    if cached and cached["count"] == len(old_messages):
        return cached["summary"]

    # Cache miss: generate a new summary and store it
    summary = AI.summarize_conversations(old_messages)
    _summary_cache[idea_id] = {"count": len(old_messages), "summary": summary}
    return summary