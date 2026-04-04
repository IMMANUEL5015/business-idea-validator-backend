import math
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from database.models import Idea, Validation, BusinessPlan, IdeaStatus
from helpers.schemas import IdeaCreate, IdeaUpdate
from helpers import AI

# Ideas with a validation score at or above this threshold are considered
# market-worthy and will have a business plan generated automatically.
# Scale: 0–100. Will be refined when the AI section is implemented.
VALIDATION_THRESHOLD = 80.0


# ─────────────────────────────────────────────
# CREATE IDEA
# ─────────────────────────────────────────────

def create_idea(db: Session, user_id: int, idea_data: IdeaCreate) -> Idea:
    idea = Idea(
        user_id=user_id,
        title=idea_data.title,
        description=idea_data.description,
        status=IdeaStatus.draft,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)

    _run_validation(db, idea)
    return get_idea(db, user_id, idea.id)


# ─────────────────────────────────────────────
# LIST IDEAS — Paginated, most recent first
# ─────────────────────────────────────────────

def get_ideas(db: Session, user_id: int, page: int, limit: int) -> dict:
    total = db.query(Idea).filter(Idea.user_id == user_id).count()
    ideas = (
        db.query(Idea)
        .filter(Idea.user_id == user_id)
        .order_by(Idea.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "ideas": ideas,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total > 0 else 1,
    }


# ─────────────────────────────────────────────
# GET SPECIFIC IDEA — With validation and business plan
# ─────────────────────────────────────────────

def get_idea(db: Session, user_id: int, idea_id: int) -> Idea:
    idea = (
        db.query(Idea)
        .options(joinedload(Idea.validation), joinedload(Idea.business_plan))
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found.")
    return idea


# ─────────────────────────────────────────────
# UPDATE IDEA
# ─────────────────────────────────────────────

def update_idea(db: Session, user_id: int, idea_id: int, update_data: IdeaUpdate) -> Idea:
    idea = get_idea(db, user_id, idea_id)

    content_changed = (
        (update_data.title is not None and update_data.title != idea.title)
        or (update_data.description is not None and update_data.description != idea.description)
    )

    if update_data.title is not None:
        idea.title = update_data.title
    if update_data.description is not None:
        idea.description = update_data.description
    if update_data.status is not None:
        idea.status = update_data.status

    db.commit()
    db.refresh(idea)

    if content_changed:
        _clear_ai_results(db, idea)
        _run_validation(db, idea)

    return get_idea(db, user_id, idea_id)


# ─────────────────────────────────────────────
# DELETE IDEA
# ─────────────────────────────────────────────

def delete_idea(db: Session, user_id: int, idea_id: int) -> None:
    idea = get_idea(db, user_id, idea_id)
    db.delete(idea)  # cascades to validation, business plan, and conversations
    db.commit()


# ─────────────────────────────────────────────
# RETRY VALIDATION
# ─────────────────────────────────────────────

def retry_validation(db: Session, user_id: int, idea_id: int) -> Idea:
    idea = get_idea(db, user_id, idea_id)

    _clear_ai_results(db, idea)
    _run_validation(db, idea)
    return get_idea(db, user_id, idea_id)


# ─────────────────────────────────────────────
# RETRY BUSINESS PLAN
# ─────────────────────────────────────────────

def retry_business_plan(db: Session, user_id: int, idea_id: int) -> Idea:
    idea = get_idea(db, user_id, idea_id)

    if not idea.validation or idea.validation.score < VALIDATION_THRESHOLD:
        raise HTTPException(
            status_code=400,
            detail="Idea must pass validation before a business plan can be generated.",
        )

    if idea.business_plan:
        db.delete(idea.business_plan)
        db.commit()
        db.refresh(idea)

    _run_business_plan(db, idea)
    return get_idea(db, user_id, idea_id)


# ─────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────

def _run_validation(db: Session, idea: Idea) -> None:
    result = AI.validate_idea(idea.title, idea.description)

    validation = Validation(
        idea_id=idea.id,
        score=result["score"],
        risks=result["risks"],
        opportunities=result["opportunities"],
        ai_feedback=result["ai_feedback"],
    )
    db.add(validation)

    if result["score"] >= VALIDATION_THRESHOLD:
        idea.status = IdeaStatus.validated
        db.commit()
        db.refresh(idea)
        _run_business_plan(db, idea)
    else:
        db.commit()


def _run_business_plan(db: Session, idea: Idea) -> None:
    db.refresh(idea)
    validation_data = {
        "score": idea.validation.score,
        "risks": idea.validation.risks,
        "opportunities": idea.validation.opportunities,
        "ai_feedback": idea.validation.ai_feedback,
    }

    plan = BusinessPlan(
        idea_id=idea.id,
        content=AI.generate_business_plan(idea.title, idea.description, validation_data),
    )
    db.add(plan)
    idea.status = IdeaStatus.completed
    db.commit()


def _clear_ai_results(db: Session, idea: Idea) -> None:
    if idea.validation:
        db.delete(idea.validation)
    if idea.business_plan:
        db.delete(idea.business_plan)
    idea.status = IdeaStatus.draft
    db.commit()
    db.refresh(idea)