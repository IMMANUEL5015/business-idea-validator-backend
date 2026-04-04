from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from helpers.schemas import UserCreate, UserResponse, LoginResponse, VerifyCodeRequest, TokenResponse
from helpers.request import send_login_email
import services.users as user_services

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_services.create_user(db, user)


@router.post("/login", response_model=LoginResponse)
async def login_user(user: UserCreate, db: Session = Depends(get_db)):
    code, email = user_services.login_user(db, user)
    await send_login_email(email, code)
    return LoginResponse(message="Login code sent to your email.")


@router.post("/verify", response_model=TokenResponse)
async def verify_code(body: VerifyCodeRequest, db: Session = Depends(get_db)):
    token = user_services.verify_login_code(db, body.email, body.code)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(user_services.get_current_user)):
    return current_user
