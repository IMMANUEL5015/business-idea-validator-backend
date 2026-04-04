from database.db import Base
from sqlalchemy import Integer, Column, String, JSON, Text, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

# --- Enums ---

class IdeaStatus(str, enum.Enum):
    draft = "draft"
    validated = "validated"
    completed = "completed"

class ConversationRole(str, enum.Enum):
    user = "user"
    ai = "ai"

# --- Models ---

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ideas = relationship("Idea", back_populates="user", cascade="all, delete-orphan")
    login_codes = relationship("LoginCode", back_populates="user", cascade="all, delete-orphan")


class Idea(Base):
    __tablename__ = "Ideas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(IdeaStatus), default=IdeaStatus.draft, nullable=False)

    user = relationship("User", back_populates="ideas")
    validation = relationship("Validation", back_populates="idea", uselist=False, cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="idea", cascade="all, delete-orphan")
    business_plan = relationship("BusinessPlan", back_populates="idea", uselist=False, cascade="all, delete-orphan")


class Validation(Base):
    __tablename__ = "Validations"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("Ideas.id"), nullable=False, index=True)
    score = Column(Float, nullable=True)
    risks = Column(Text, nullable=True)
    opportunities = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)

    idea = relationship("Idea", back_populates="validation")


class Conversation(Base):
    __tablename__ = "Conversations"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("Ideas.id"), nullable=False, index=True)
    role = Column(Enum(ConversationRole), nullable=False)
    message = Column(Text, nullable=False)

    idea = relationship("Idea", back_populates="conversations")


class BusinessPlan(Base):
    __tablename__ = "BusinessPlans"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("Ideas.id"), nullable=False, index=True)
    content = Column(JSON, nullable=False)

    idea = relationship("Idea", back_populates="business_plan")


class LoginCode(Base):
    __tablename__ = "LoginCodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.id"), nullable=False, index=True)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="login_codes")
                