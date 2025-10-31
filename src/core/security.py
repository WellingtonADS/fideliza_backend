"""
# Segurança e Autenticação

Implementa hashing de senhas, geração/validação de JWT e dependências de
autorização usadas nas rotas (FastAPI).

## Conteúdo
- Hash de senhas (passlib) com fallback seguro para bcrypt legado
- Criação de token JWT (claims mínimos: sub, user_type, company_id, exp)
- Dependências de segurança (`get_current_user`, `get_current_admin_user`, etc.)
"""

# fideliza_backend/src/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict, cast
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# CORREÇÃO: Importações relativas corrigidas
from ..database.models import User
from ..api.schemas import TokenData
from ..database.session import get_db
from ..core.config import settings

# Configuração para hashing de senhas
# Evita erros com bcrypt no Windows/Python 3.12 durante autodetecção e senhas longas
# Importante: não incluir "bcrypt" aqui para evitar bugs do backend do passlib no Windows/Python.
# Usamos verificação direta com a lib "bcrypt" apenas quando detectar hash $2a/$2b/$2y.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

# Configuração para OAuth2 com esquema de token de senha
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica a senha contra o hash armazenado.

    - Primeiro tenta pbkdf2_sha256 via passlib (padrão atual);
    - Se o hash for bcrypt ($2a/$2b/$2y), usa a biblioteca 'bcrypt' diretamente para evitar bugs do passlib;
    - Em último caso, compara texto puro (migração legada).
    """
    # 1) pbkdf2 (padrão)
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except UnknownHashError:
        # seguirá para outras estratégias
        pass
    except Exception:
        # qualquer outra falha, tenta caminhos seguintes
        pass

    # 2) bcrypt direto, se detectado pelo prefixo
    try:
        if hashed_password and hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            try:
                import bcrypt as _bcrypt  # type: ignore
                return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
            except Exception:
                # se a lib bcrypt não estiver disponível/ok, segue para fallback
                pass
    except Exception:
        pass

    # 3) Fallback: texto puro legado
    try:
        return plain_password == hashed_password
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Gera o hash da senha usando o contexto configurado."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT com expiração opcional.

    Args:
        data: Claims a codificar no token (ex.: sub, user_type, company_id).
        expires_delta: Delta de tempo para expiração. Default 15 minutos.

    Returns:
        Token JWT assinado (string).
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def validate_jwt_claims(payload: Dict[str, Any]):
    """
    Valida os claims obrigatórios no payload do JWT.
    """
    required_claims = ["sub", "user_type", "company_id", "exp"]
    for claim in required_claims:
        if claim not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Claim obrigatório ausente: {claim}",
                headers={"WWW-Authenticate": "Bearer"},
            )

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        validate_jwt_claims(payload)  # Valida os claims obrigatórios

        email: str = cast(str, payload.get("sub"))
        user_type: str = cast(str, payload.get("user_type"))
        company_id: Optional[int] = cast(Optional[int], payload.get("company_id"))
        exp: int = cast(int, payload.get("exp"))

        # Verifica se o token expirou
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(email=email, user_type=user_type, company_id=company_id)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erro ao decodificar o token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).filter(User.email == token_data.email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.user_type != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissões insuficientes (Requer administrador)"
        )
    return current_user

async def get_current_collaborator_or_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.user_type not in ["ADMIN", "COLLABORATOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissões insuficientes (Requer administrador ou colaborador)"
        )
    return current_user