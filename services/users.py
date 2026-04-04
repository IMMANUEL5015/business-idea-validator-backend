import secrets
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User, LoginCode
from helpers.schemas import UserCreate
from helpers.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer()

def create_user(db: Session, user: UserCreate):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    new_user = User(email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(db: Session, user: UserCreate):
    existing = db.query(User).filter(User.email == user.email).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Email not registered.")

    code = str(secrets.randbelow(1_000_000)).zfill(6)
    hashed_code = pwd_context.hash(code)

    db.query(LoginCode).filter(
        LoginCode.user_id == existing.id,
        LoginCode.used == False,
    ).update({"used": True})

    login_code = LoginCode(
        user_id=existing.id,
        code=hashed_code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(login_code)
    db.commit()

    return code, existing.email

def verify_login_code(db: Session, email: str, code: str) -> str:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered.")

    login_code = (
        db.query(LoginCode)
        .filter(
            LoginCode.user_id == user.id,
            LoginCode.used == False,
            LoginCode.expires_at > datetime.now(timezone.utc),
        )
        .order_by(LoginCode.expires_at.desc())
        .first()
    )

    if not login_code or not pwd_context.verify(code, login_code.code):
        raise HTTPException(status_code=400, detail="Invalid or expired code.")

    login_code.used = True
    db.commit()

    return _create_access_token({"sub": str(user.id)})


def _create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user
