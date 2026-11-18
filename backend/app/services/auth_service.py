from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.errors import BadRequestException, UnauthorizedException, NotFoundException
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        existing = db.query(User).filter(User.email == user_in.email).first()
        if existing:
            raise BadRequestException("User with this email already exists.")
        
        user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> Token:
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password.")
        
        if not user.is_active:
            raise UnauthorizedException("User account is disabled.")

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "refresh":
            raise UnauthorizedException("Invalid refresh token.")

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive.")

        access_token = create_access_token(subject=user.id)
        new_refresh = create_refresh_token(subject=user.id)
        return Token(access_token=access_token, refresh_token=new_refresh, token_type="bearer")

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User", user_id)
        return user
