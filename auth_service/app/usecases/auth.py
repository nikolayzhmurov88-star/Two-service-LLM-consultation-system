from app.repositories.users import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError

class AuthUsecase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, email: str, password: str) -> dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError()
        hashed = hash_password(password)
        user = await self.user_repo.create(email, hashed)
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return {"access_token": token, "token_type": "bearer"}

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return {"access_token": token, "token_type": "bearer"}

    async def get_profile(self, user_id: int) -> dict:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return {"id": user.id, "email": user.email, "role": user.role, "created_at": user.created_at.isoformat()}