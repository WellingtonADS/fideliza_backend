# fideliza_backend/src/api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import timedelta
from typing import List

from ..schemas import (
    UserCreate, UserResponse, Token, CompanyResponse, TokenData, 
    CollaboratorCreate, CompanyAdminCreate, PointAdd, PointTransactionResponse,
    PointsByCompany # NOVO: Importa o esquema de resposta de pontos
)
# AJUSTE: Importa o modelo PointTransaction
from ...database.models import User, Company, PointTransaction
from ...database.session import get_db
from ...core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user, get_current_admin_user,
    get_current_collaborator_or_admin # AJUSTE: Importa a dependência de segurança
)
from ...core.config import settings

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Fideliza+"}

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": user.user_type, "company_id": user.company_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register/client/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_client(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        user_type="CLIENT"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    new_user.generate_qr_code()
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/register/company-admin/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def register_company_and_admin(
    payload: CompanyAdminCreate,
    db: AsyncSession = Depends(get_db)
):
    company_name = payload.company_name
    admin_user = payload.admin_user
    result = await db.execute(select(User).filter(User.email == admin_user.email))
    db_admin_user = result.scalar_one_or_none()
    if db_admin_user:
        raise HTTPException(status_code=400, detail="Email de administrador já registrado")
    new_company = Company(name=company_name)
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    hashed_password = get_password_hash(admin_user.password)
    new_admin = User(
        email=admin_user.email,
        hashed_password=hashed_password,
        name=admin_user.name,
        user_type="ADMIN",
        company_id=new_company.id
    )
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)
    new_company.admin_user_id = new_admin.id
    await db.commit()
    await db.refresh(new_company)
    return new_company

@router.get("/users/me/", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/collaborators/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_collaborator(
    collaborator: CollaboratorCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(User).filter(User.email == collaborator.email))
    db_user = result.scalar_one_or_none()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    company_id = current_admin.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrador não está associado a nenhuma empresa."
        )
    hashed_password = get_password_hash(collaborator.password)
    new_collaborator = User(
        email=collaborator.email,
        hashed_password=hashed_password,
        name=collaborator.name,
        user_type="COLLABORATOR",
        company_id=company_id
    )
    db.add(new_collaborator)
    await db.commit()
    await db.refresh(new_collaborator)
    return new_collaborator

@router.post("/points/add", response_model=PointTransactionResponse, status_code=status.HTTP_201_CREATED)
async def add_points_to_client(
    payload: PointAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    """
    Adiciona um ponto a um cliente.
    Apenas um usuário autenticado do tipo 'ADMIN' ou 'COLLABORATOR' pode executar esta ação.
    O cliente é identificado pelo seu ID (que pode ser lido de um QR Code).
    """
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não está associado a nenhuma empresa."
        )
    try:
        client_id = int(payload.client_identifier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Identificador do cliente inválido.")
    result = await db.execute(select(User).filter(User.id == client_id))
    client = result.scalar_one_or_none()
    if not client or client.user_type != 'CLIENT':
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    new_transaction = PointTransaction(
        client_id=client.id,
        company_id=company_id,
        awarded_by_id=current_user.id,
        points=1
    )
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)
    return new_transaction

# --- NOVO ENDPOINT: Consultar Pontos do Cliente Logado ---
@router.get("/points/my-points", response_model=List[PointsByCompany])
async def get_my_points(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna o total de pontos do cliente logado, agrupado por empresa.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas clientes podem consultar seus pontos."
        )

    # Consulta que agrupa as transações por empresa e soma os pontos
    query = (
        select(
            func.sum(PointTransaction.points).label("total_points"),
            Company
        )
        .join(Company, PointTransaction.company_id == Company.id)
        .filter(PointTransaction.client_id == current_user.id)
        .group_by(Company.id)
    )
    
    result = await db.execute(query)
    points_data = result.all()

    # Formata os dados para a resposta
    response_data = [
        {"total_points": total, "company": company} for total, company in points_data
    ]

    return response_data
