from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User
from helpers.schemas import (
    IdeaCreate, IdeaUpdate, IdeaResponse, IdeaDetailResponse, PaginatedIdeasResponse
)
from services.users import get_current_user
import services.ideas as idea_services

router = APIRouter(prefix="/ideas", tags=["Ideas"])


@router.post("/", response_model=IdeaDetailResponse, status_code=201)
def create_idea(
    idea: IdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return idea_services.create_idea(db, current_user.id, idea)


@router.get("/", response_model=PaginatedIdeasResponse)
def list_ideas(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return idea_services.get_ideas(db, current_user.id, page, limit)


@router.get("/{idea_id}", response_model=IdeaDetailResponse)
def get_idea(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return idea_services.get_idea(db, current_user.id, idea_id)


@router.put("/{idea_id}", response_model=IdeaDetailResponse)
def update_idea(
    idea_id: int,
    update_data: IdeaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return idea_services.update_idea(db, current_user.id, idea_id, update_data)


@router.delete("/{idea_id}", status_code=204)
def delete_idea(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    idea_services.delete_idea(db, current_user.id, idea_id)


@router.post("/{idea_id}/retry-validation", response_model=IdeaDetailResponse)
def retry_validation(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return idea_services.retry_validation(db, current_user.id, idea_id)


@router.post("/{idea_id}/retry-business-plan", response_model=IdeaDetailResponse)
def retry_business_plan(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return idea_services.retry_business_plan(db, current_user.id, idea_id)