import pytest
import asyncio
from httpx import AsyncClient, ASGITransport # <-- Importar ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Ajuste o caminho de importação se a sua app principal não estiver em src.main
from src.main import app
from src.database.models import Base
from src.database.session import get_db

# Usa uma base de dados SQLite em memória para os testes
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Sobrescreve a dependência get_db para usar a base de dados de teste
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Cria uma instância do event loop para a sessão de teste."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Cria as tabelas da base de dados antes dos testes e apaga depois."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão de base de dados para cada teste."""
    async with TestingSessionLocal() as session:
        yield session
        await session.flush()
        await session.rollback()

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Fornece um cliente HTTP assíncrono para fazer requisições à API."""
    # --- CORREÇÃO APLICADA AQUI ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client