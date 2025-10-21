# fideliza_backend/src/database/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

# CORREÇÃO: Alterar a importação para ser relativa
from ..core.config import settings 

DATABASE_URL = str(settings.DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Use a mesma Base declarativa definida em models.py para evitar divergências
from ..database.models import Base  # garante que todos os modelos sejam importados

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session

async def create_db_and_tables():
    async with engine.begin() as conn:
        # Esta função agora irá encontrar as tabelas importadas de models.py
        await conn.run_sync(Base.metadata.create_all)
