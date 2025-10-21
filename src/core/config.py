# fideliza_backend/src/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Carrega apenas o .env padrão
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")
    MAIL_FROM: str = os.getenv("MAIL_FROM")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER")
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "true").lower() == "true"
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "false").lower() == "true"

    # Deep link e Web reset configuráveis
    CLIENT_APP_SCHEME: str = os.getenv("CLIENT_APP_SCHEME", "fidelizacliente")
    GESTAO_APP_SCHEME: str = os.getenv("GESTAO_APP_SCHEME", "fidelizagestao")

    ANDROID_CLIENT_PACKAGE: str = os.getenv("ANDROID_CLIENT_PACKAGE", "com.fideliza_cliente")
    ANDROID_GESTAO_PACKAGE: str = os.getenv("ANDROID_GESTAO_PACKAGE", "com.fideliza_gestao")

    # URLs completas para a página web de reset.
    # Para ambiente local, por padrão aponte para um frontend local (ex.: React em :3000)
    CLIENT_WEB_RESET_URL: str = os.getenv("CLIENT_WEB_RESET_URL", "http://localhost:3000")
    GESTAO_WEB_RESET_URL: str = os.getenv("GESTAO_WEB_RESET_URL", "http://localhost:3000")

    model_config = {
        'env_file': '.env',
        'extra': 'ignore'
    }

settings = Settings()