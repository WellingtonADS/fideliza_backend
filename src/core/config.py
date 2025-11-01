# src/core/config.py
"""
# Configuração da aplicação (Pydantic Settings)

Centraliza as configurações do backend (BD, JWT, e-mail, deep links e URLs de reset web)
usando Pydantic Settings. Valores vêm de variáveis de ambiente e um arquivo `.env` (opcional),
com defaults seguros para desenvolvimento local.

## Principais variáveis
- `DATABASE_URL`: URL assíncrona da base de dados (postgresql+asyncpg ou sqlite+aiosqlite).
- `SECRET_KEY`: Chave secreta do JWT.
- `ALGORITHM`: Algoritmo do JWT (ex.: HS256).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiração do token em minutos.
- `MAIL_*`: Configuração de SMTP (username, password, from, server/port, TLS).
- `CLIENT_APP_SCHEME`/`GESTAO_APP_SCHEME`: Esquemas de deep link dos apps.
- `CLIENT_WEB_RESET_URL`/`GESTAO_WEB_RESET_URL`: URLs base para reset de senha via web.

## Validação
- `DATABASE_URL` aceita apenas `postgresql+asyncpg://` ou `sqlite+aiosqlite://` (vazio/None permitido).
- `SECRET_KEY` e `ALGORITHM` não podem ser vazios.
- URLs de reset devem iniciar com `http://` ou `https://`.
"""

from functools import lru_cache
from typing import Optional

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Base de dados — aceitar async Postgres por padrão; permitir sqlite+aiosqlite em testes/dev
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description=(
            "URL de conexão da BD. Recomendado 'postgresql+asyncpg://...'. "
            "Em testes/local pode usar 'sqlite+aiosqlite:///./dev.db'."
        ),
    )

    # Alternativa: URL do banco no Render + chave para alternar
    RENDER_DATABASE_URL: Optional[str] = Field(
        default=None,
        description=(
            "URL do BD no Render (pode vir como 'postgres://...'); será normalizada para 'postgresql+asyncpg://'."
        ),
    )
    USE_RENDER_DB: bool = Field(
        default=False,
        description=(
            "Quando true, usa RENDER_DATABASE_URL; quando false, usa DATABASE_URL."
        ),
    )

    # JWT
    SECRET_KEY: str = Field(
        default="dev-secret-key", description="Chave secreta do JWT"
    )
    ALGORITHM: str = Field(
        default="HS256", description="Algoritmo de assinatura do JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, ge=1, description="Expiração do token (min)"
    )

    # E-mail
    # Para evitar erros de tipo em pontos de uso (ex.: ConnectionConfig),
    # fornecemos defaults não-opcionais onde aplicável.
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: EmailStr = Field(default="no-reply@example.com")
    MAIL_PORT: int = Field(default=587, ge=1)
    MAIL_SERVER: str = ""
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # Deep link / Apps
    CLIENT_APP_SCHEME: str = Field(default="fidelizacliente")
    GESTAO_APP_SCHEME: str = Field(default="fidelizagestao")
    ANDROID_CLIENT_PACKAGE: str = Field(default="com.fideliza_cliente")
    ANDROID_GESTAO_PACKAGE: str = Field(default="com.fideliza_gestao")

    # URLs Web reset (mantidas como str e validadas por prefixo http/https)
    CLIENT_WEB_RESET_URL: str = Field(default="http://localhost:3000")
    GESTAO_WEB_RESET_URL: str = Field(default="http://localhost:3000")

    # Configurações do Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # =============================
    # Validadores
    # =============================
    @field_validator("DATABASE_URL", "RENDER_DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza e valida a URL de banco.

        - Aceita valores do Render em `postgres://` ou `postgresql://` e converte
          para `postgresql+asyncpg://` (obrigatório para engine assíncrona).
        - Remove espaços e aspas envolvendo o valor, caso existam.
        - Mantém suporte a `sqlite+aiosqlite://` em dev/testes.
        """
        if v is None:
            return None
        v = v.strip().strip("'\"")
        if v == "":
            return None

        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        allowed_prefixes = ("postgresql+asyncpg://", "sqlite+aiosqlite://")
        if not v.startswith(allowed_prefixes):
            raise ValueError(
                "DATABASE_URL deve usar 'postgresql+asyncpg://' (produção) ou 'sqlite+aiosqlite://' (dev/teste)."
            )
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("SECRET_KEY não pode ser vazio")
        return v

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("ALGORITHM não pode ser vazio")
        return v

    @field_validator("CLIENT_WEB_RESET_URL", "GESTAO_WEB_RESET_URL")
    @classmethod
    def validate_reset_urls(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URLs de reset devem começar com http:// ou https://")
        return v


@lru_cache()
def get_settings() -> Settings:
    # Instância única de Settings durante o ciclo de vida do processo
    return Settings()


# Mantém compatibilidade com importações existentes: from ..core.config import settings
settings = get_settings()
