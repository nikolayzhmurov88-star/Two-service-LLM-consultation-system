from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUsecase
from app.api.deps import get_auth_uc, get_current_user_id
from app.core.exceptions import BaseHTTPException

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, uc: AuthUsecase = Depends(get_auth_uc)):
    try:
        return await uc.register(data.email, data.password)
    except BaseHTTPException as e:
        raise e

@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), uc: AuthUsecase = Depends(get_auth_uc)):
    try:
        return await uc.login(form.username, form.password)
    except BaseHTTPException as e:
        raise e

@router.get("/me", response_model=UserPublic)
async def me(user_id: int = Depends(get_current_user_id), uc: AuthUsecase = Depends(get_auth_uc)):
    return await uc.get_profile(user_id)