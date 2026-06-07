import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine
from app.db.base import Base
from app.core.security import decode_token

@pytest.fixture(autouse=True)
async def setup_db():

    # Проверка, что используется тестовая база
    from app.core.config import settings
    assert "memory" in settings.database_url, "Тесты должны использовать in‑memory БД"


    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def test_register_login_me():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # регистрация
        resp = await client.post("/auth/register", json={"email": "test@example.com", "password": "123456"})
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # логин через form data
        resp = await client.post("/auth/login", data={"username": "test@example.com", "password": "123456"})
        assert resp.status_code == 200
        token2 = resp.json()["access_token"]
        
        assert decode_token(token)["sub"] == decode_token(token2)["sub"]

        # me
        resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert "id" in data

async def test_register_duplicate():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json={"email": "duplicate@example.com", "password": "123"})
        resp = await client.post("/auth/register", json={"email": "duplicate@example.com", "password": "123"})
        assert resp.status_code == 409

async def test_login_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/auth/login", data={"username": "no@exists.com", "password": "x"})
        assert resp.status_code == 401

async def test_me_user_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Регистрируем пользователя
        resp = await client.post("/auth/register", json={"email": "todelete@example.com", "password": "123"})
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # Удаляем пользователя напрямую из БД (через engine)
        from app.db.models import User
        from sqlalchemy import delete
        async with engine.begin() as conn:
            await conn.execute(delete(User).where(User.email == "todelete@example.com"))
        
        # Пытаемся получить профиль по токену удалённого пользователя
        resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Пользователь не найден"