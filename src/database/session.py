"""Sessão e engine do banco de dados (assíncronos).

Cria a engine e a fábrica de sessões de forma preguiçosa (lazy),
evitando falhas em ambientes de teste onde a variável DATABASE_URL
não está definida. Em ausência de DATABASE_URL, usa-se um SQLite local
(`sqlite+aiosqlite:///./dev.db`) apenas para desenvolvimento/testes.
"""

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import settings
from ..database.models import Base

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _ensure_engine() -> None:
    """Garante que a engine e a session factory existam."""
    global _engine, _session_factory
    if _engine is not None and _session_factory is not None:
        return

    database_url = settings.DATABASE_URL or "sqlite+aiosqlite:///./dev.db"
    _engine = create_async_engine(database_url, echo=True)
    _session_factory = async_sessionmaker(
        _engine, expire_on_commit=False, class_=AsyncSession
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    _ensure_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session


async def create_db_and_tables():
    _ensure_engine()
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
