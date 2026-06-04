from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.users import UserRepository
from app.usecases.auth import AuthUsecase
from app.core.security import decode_token
from app.core.exceptions import InvalidTokenError, TokenExpiredError
from jose import ExpiredSignatureError, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_auth_uc(user_repo: UserRepository = Depends(get_user_repo)) -> AuthUsecase:
    return AuthUsecase(user_repo)

    
security = HTTPBearer()   

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials  
 
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidTokenError()
        return int(user_id)
    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise InvalidTokenError()