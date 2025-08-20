import pytest
from httpx import AsyncClient
from fastapi import status

# Supõe que a sua aplicação FastAPI principal está em `src.main.app`
# Ajuste o caminho de importação se for diferente.
from src.main import app 
from src.database.models import Company, User, PointTransaction
from src.core.security import create_access_token
from datetime import timedelta

# --- Configuração dos Testes (Fixtures) ---

@pytest.fixture
async def setup_test_data(db_session):
    """
    Fixture para popular a base de dados de teste com dados previsíveis.
    Esta fixture é executada antes de cada teste que a solicita.
    """
    # Limpa dados de testes anteriores para garantir isolamento
    await db_session.execute(PointTransaction.__table__.delete())
    await db_session.execute(User.__table__.delete())
    await db_session.execute(Company.__table__.delete())
    await db_session.commit() # Garante que a limpeza seja efetivada

    # Criar Empresas
    company1 = Company(id=1, name="Café do Bairro", category="Alimentação", address="Rua Principal, 123")
    company2 = Company(id=2, name="Livraria Saber", category="Lazer", address="Av. Central, 456")
    db_session.add_all([company1, company2])
    await db_session.commit()

    # Criar Utilizadores
    client_user = User(id=10, name="Cliente Teste", email="cliente@teste.com", hashed_password="fake_password", user_type="CLIENT")
    admin_user = User(id=11, name="Admin Teste", email="admin@teste.com", hashed_password="fake_password", user_type="ADMIN", company_id=1)
    db_session.add_all([client_user, admin_user])
    await db_session.commit()

    # Criar Transações de Pontos
    transaction1 = PointTransaction(client_id=10, company_id=1, awarded_by_id=11, points=1)
    transaction2 = PointTransaction(client_id=10, company_id=2, awarded_by_id=11, points=1) # Simulação de admin de outra empresa
    transaction3 = PointTransaction(client_id=10, company_id=1, awarded_by_id=11, points=1)
    db_session.add_all([transaction1, transaction2, transaction3])
    await db_session.commit()

    # Retorna os IDs para uso nos testes
    return {"client_id": 10, "admin_id": 11, "company1_id": 1, "company2_id": 2}

@pytest.fixture
def client_auth_headers():
    """Cria um token de acesso para o utilizador cliente."""
    access_token = create_access_token(
        data={"sub": "cliente@teste.com", "user_type": "CLIENT"},
        expires_delta=timedelta(minutes=15)
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_auth_headers():
    """Cria um token de acesso para o utilizador admin."""
    access_token = create_access_token(
        data={"sub": "admin@teste.com", "user_type": "ADMIN", "company_id": 1},
        expires_delta=timedelta(minutes=15)
    )
    return {"Authorization": f"Bearer {access_token}"}


# --- Testes para os Novos Endpoints ---

@pytest.mark.asyncio
async def test_get_all_companies(async_client: AsyncClient, setup_test_data):
    """
    Testa o endpoint GET /companies.
    Verifica se retorna a lista de empresas corretamente.
    """
    response = await async_client.get("/api/v1/companies")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Café do Bairro"
    assert data[0]["category"] == "Alimentação"
    assert "address" in data[0]

@pytest.mark.asyncio
async def test_get_client_dashboard_success(async_client: AsyncClient, setup_test_data, client_auth_headers):
    """
    Testa o endpoint GET /dashboard com um cliente autenticado.
    Verifica se o total de pontos e a última atividade estão corretos.
    """
    response = await async_client.get("/api/v1/dashboard", headers=client_auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # O cliente tem 3 transações de 1 ponto cada
    assert data["total_points"] == 3
    assert data["last_activity"] is not None
    # CORREÇÃO: Acessar o ID do cliente dentro do objeto 'client' no schema de resposta
    assert data["last_activity"]["client"]["id"] == 10

@pytest.mark.asyncio
async def test_get_client_dashboard_forbidden_for_admin(async_client: AsyncClient, setup_test_data, admin_auth_headers):
    """
    Testa se o endpoint GET /dashboard é proibido para utilizadores que não são clientes.
    """
    response = await async_client.get("/api/v1/dashboard", headers=admin_auth_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Acesso restrito a clientes"

@pytest.mark.asyncio
async def test_get_client_dashboard_unauthorized(async_client: AsyncClient):
    """
    Testa se o endpoint GET /dashboard requer autenticação.
    """
    response = await async_client.get("/api/v1/dashboard")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_my_points_by_company(async_client: AsyncClient, setup_test_data, client_auth_headers):
    """
    Testa o endpoint GET /points/my-points.
    Verifica se os pontos são agrupados corretamente por empresa.
    """
    response = await async_client.get("/api/v1/points/my-points", headers=client_auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data) == 2
    
    # Encontra os resultados para cada empresa
    company1_data = next((item for item in data if item["company"]["id"] == 1), None)
    company2_data = next((item for item in data if item["company"]["id"] == 2), None)
    
    assert company1_data is not None
    assert company1_data["total_points"] == 2 # 2 transações para a empresa 1
    assert company1_data["company"]["name"] == "Café do Bairro"
    
    assert company2_data is not None
    assert company2_data["total_points"] == 1 # 1 transação para a empresa 2
    assert company2_data["company"]["name"] == "Livraria Saber"
