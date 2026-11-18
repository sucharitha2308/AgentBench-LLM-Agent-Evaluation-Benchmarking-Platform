from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token, TokenRefresh
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    user = AuthService.register_user(db, user_in)
    return user


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and obtain JWT access & refresh tokens."""
    return AuthService.authenticate_user(db, login_data)


@router.post("/login/oauth", response_model=Token, include_in_schema=False)
def login_oauth(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible login endpoint."""
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    return AuthService.authenticate_user(db, login_data)


@router.post("/refresh", response_model=Token)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh expired access token using valid refresh token."""
    return AuthService.refresh_access_token(db, token_data.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Fetch profile of current authenticated user."""
    return current_user
