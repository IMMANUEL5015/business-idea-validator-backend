from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime
from database.models import IdeaStatus, ConversationRole


# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    pass  # Only email needed to create a user

class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class LoginResponse(BaseModel):
    message: str

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─────────────────────────────────────────────
# IDEA
# ─────────────────────────────────────────────

class IdeaBase(BaseModel):
    title: str
    description: Optional[str] = None

class IdeaCreate(IdeaBase):
    pass  # user_id will be injected from the auth context, not the request body

class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IdeaStatus] = None

class IdeaResponse(IdeaBase):
    id: int
    user_id: int
    status: IdeaStatus

    model_config = {"from_attributes": True}

class IdeaDetailResponse(IdeaBase):
    id: int
    user_id: int
    status: IdeaStatus
    validation: Optional["ValidationResponse"] = None
    business_plan: Optional["BusinessPlanResponse"] = None

    model_config = {"from_attributes": True}

class PaginatedIdeasResponse(BaseModel):
    ideas: list[IdeaResponse]
    total: int
    page: int
    limit: int
    pages: int


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

class ValidationBase(BaseModel):
    score: Optional[float] = None
    risks: Optional[str] = None
    opportunities: Optional[str] = None
    ai_feedback: Optional[str] = None

class ValidationCreate(ValidationBase):
    idea_id: int

class ValidationResponse(ValidationBase):
    id: int
    idea_id: int

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# CONVERSATION
# ─────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    message: str

class ConversationResponse(BaseModel):
    id: int
    idea_id: int
    role: ConversationRole
    message: str

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# BUSINESS PLAN
# ─────────────────────────────────────────────

class BusinessPlanBase(BaseModel):
    content: dict[str, Any]

class BusinessPlanCreate(BusinessPlanBase):
    idea_id: int

class BusinessPlanResponse(BusinessPlanBase):
    id: int
    idea_id: int

    model_config = {"from_attributes": True}