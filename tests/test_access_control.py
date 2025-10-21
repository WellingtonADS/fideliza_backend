import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import timedelta

from src.core.security import create_access_token, get_password_hash
from src.database.models import User, Company


@pytest.mark.asyncio
async def test_login_success_and_unauthorized(async_client: AsyncClient, db_session):
    # cria usuário válido
    email = "login_user@test.com"
    password = "Senha1234"
    user = User(email=email, name="Login User", user_type="CLIENT", hashed_password=get_password_hash(password))
    db_session.add(user)
    await db_session.commit()

    # login OK
    form = {"username": email, "password": password}
    res_ok = await async_client.post("/api/v1/token", data=form)
    assert res_ok.status_code == status.HTTP_200_OK
    assert "access_token" in res_ok.json()

    # login 401
    res_bad = await async_client.post("/api/v1/token", data={"username": email, "password": "SenhaErrada"})
    assert res_bad.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_protected_requires_auth(async_client: AsyncClient):
    res = await async_client.get("/api/v1/dashboard")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_role_forbidden_for_client_on_admin_routes(async_client: AsyncClient, db_session):
    # cria um CLIENT sem empresa
    email = "cliente_role@test.com"
    user = User(email=email, name="Cliente", user_type="CLIENT", hashed_password=get_password_hash("Senha1234"))
    db_session.add(user)
    await db_session.commit()

    token = create_access_token({"sub": email, "user_type": "CLIENT", "company_id": None}, expires_delta=timedelta(minutes=15))
    headers = {"Authorization": f"Bearer {token}"}

    # rota exclusiva de ADMIN deve 403
    res = await async_client.get("/api/v1/companies/me", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "Requer administrador" in res.json()["detail"]


@pytest.mark.asyncio
async def test_role_forbidden_for_admin_on_client_dashboard(async_client: AsyncClient, db_session):
    # cria empresa e admin
    company = Company(name="Empresa Teste")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    email = "admin_role@test.com"
    admin = User(email=email, name="Admin", user_type="ADMIN", company_id=company.id, hashed_password=get_password_hash("Senha1234"))
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token({"sub": email, "user_type": "ADMIN", "company_id": company.id}, expires_delta=timedelta(minutes=15))
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/dashboard", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "Acesso restrito a clientes" in res.json()["detail"]


@pytest.mark.asyncio
async def test_token_expired_unauthorized(async_client: AsyncClient, db_session):
    # cria cliente
    email = "expired@test.com"
    user = User(email=email, name="Cliente", user_type="CLIENT", hashed_password=get_password_hash("Senha1234"))
    db_session.add(user)
    await db_session.commit()

    # token já expirado
    token = create_access_token({"sub": email, "user_type": "CLIENT", "company_id": None}, expires_delta=timedelta(seconds=-1))
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/dashboard", headers=headers)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    # Aceita tanto a mensagem específica quanto a genérica de expiração
    assert ("Token expirado" in res.json()["detail"]) or ("Signature has expired" in res.json()["detail"]) 


@pytest.mark.asyncio
async def test_missing_claims_unauthorized(async_client: AsyncClient, db_session):
    # cria cliente
    email = "noclaims@test.com"
    user = User(email=email, name="Cliente", user_type="CLIENT", hashed_password=get_password_hash("Senha1234"))
    db_session.add(user)
    await db_session.commit()

    # sem user_type e company_id
    token = create_access_token({"sub": email}, expires_delta=timedelta(minutes=15))
    headers = {"Authorization": f"Bearer {token}"}

    res = await async_client.get("/api/v1/dashboard", headers=headers)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Claim obrigatório ausente" in res.json()["detail"]


@pytest.mark.asyncio
async def test_rate_limit_register_client(async_client: AsyncClient):
    # 5 por minuto - a 6ª deve ser 429
    statuses = []
    for i in range(6):
        payload = {"email": f"rl{i}@test.com", "password": "Senha1234", "name": f"User {i}"}
        resp = await async_client.post("/api/v1/register/client/", json=payload, headers={"X-Test-Id": "rate-limit-suite"})
        statuses.append(resp.status_code)

    # As 5 primeiras são 201 ou 400 se travar por duplicidade inesperada; a 6ª deve ser 429
    assert statuses[-1] == status.HTTP_429_TOO_MANY_REQUESTS
