import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine
from app.db.base import Base

@pytest.fixture(autouse=True)
async def setup_db():
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
        assert token == token2  # в нашем usecase оба возвращают токен – они одинаковы, но по логике могут быть разными

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