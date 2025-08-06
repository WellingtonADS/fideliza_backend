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
    PointsByCompany, RewardCreate, RewardResponse, RewardStatusResponse,
    RewardRedeemRequest, RedeemedRewardResponse
)
from ...database.models import User, Company, PointTransaction, Reward, RedeemedReward
from ...database.session import get_db
from ...core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user, get_current_admin_user,
    get_current_collaborator_or_admin
)
from ...core.config import settings

router = APIRouter()

@router.get("/", tags=["Status"])
def read_root():
    return {"message": "Bem-vindo à API do Fideliza+"}

# --- Autenticação ---
@router.post("/token", response_model=Token, tags=["Autenticação"])
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

# --- Registo de Usuários e Empresas ---
@router.post("/register/client/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Registo"])
async def register_client(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já registrado")
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email, hashed_password=hashed_password, name=user.name, user_type="CLIENT"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    new_user.generate_qr_code()
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/register/company-admin/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, tags=["Registo"])
async def register_company_and_admin(
    payload: CompanyAdminCreate, db: AsyncSession = Depends(get_db)
):
    company_name = payload.company_name
    admin_user = payload.admin_user
    result = await db.execute(select(User).filter(User.email == admin_user.email))
    if result.scalar_one_or_none():
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

# --- Gestão de Usuários (Endpoints Protegidos) ---
@router.get("/users/me/", response_model=UserResponse, tags=["Usuários"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/collaborators/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Usuários"])
async def create_collaborator(
    collaborator: CollaboratorCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(User).filter(User.email == collaborator.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já registrado")
    company_id = current_admin.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Administrador não está associado a nenhuma empresa.")
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

# --- Pontuação ---
@router.post("/points/add", response_model=PointTransactionResponse, status_code=status.HTTP_201_CREATED, tags=["Pontuação"])
async def add_points_to_client(
    payload: PointAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Usuário não está associado a nenhuma empresa.")
    try:
        client_id = int(payload.client_identifier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Identificador do cliente inválido.")
    result = await db.execute(select(User).filter(User.id == client_id))
    client = result.scalar_one_or_none()
    if not client or client.user_type != 'CLIENT':
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    new_transaction = PointTransaction(
        client_id=client.id, company_id=company_id, awarded_by_id=current_user.id, points=1
    )
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)
    return new_transaction

@router.get("/points/my-points", response_model=List[PointsByCompany], tags=["Pontuação"])
async def get_my_points(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem consultar seus pontos.")
    query = (
        select(func.sum(PointTransaction.points).label("total_points"), Company)
        .join(Company, PointTransaction.company_id == Company.id)
        .filter(PointTransaction.client_id == current_user.id)
        .group_by(Company.id)
    )
    result = await db.execute(query)
    return [{"total_points": total, "company": company} for total, company in result.all()]

# --- Recompensas ---
@router.post("/rewards/", response_model=RewardResponse, status_code=status.HTTP_201_CREATED, tags=["Recompensas"])
async def create_reward(
    reward: RewardCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    company_id = current_admin.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Administrador não está associado a nenhuma empresa.")
    new_reward = Reward(**reward.model_dump(), company_id=company_id)
    db.add(new_reward)
    await db.commit()
    await db.refresh(new_reward)
    return new_reward

@router.get("/rewards/", response_model=List[RewardResponse], tags=["Recompensas"])
async def list_company_rewards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Usuário não está associado a nenhuma empresa.")
    result = await db.execute(select(Reward).filter(Reward.company_id == company_id))
    return result.scalars().all()

@router.get("/rewards/my-status", response_model=List[RewardStatusResponse], tags=["Recompensas"])
async def get_my_rewards_status(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem consultar o status de seus prémios.")
    points_query = (
        select(PointTransaction.company_id, func.sum(PointTransaction.points).label("total_points"))
        .filter(PointTransaction.client_id == current_user.id).group_by(PointTransaction.company_id)
    )
    points_result = await db.execute(points_query)
    client_points_map = {company_id: total for company_id, total in points_result.all()}
    if not client_points_map:
        return []
    rewards_query = select(Reward).filter(Reward.company_id.in_(list(client_points_map.keys())))
    rewards_result = await db.execute(rewards_query)
    all_rewards = rewards_result.scalars().all()
    response_data = []
    for reward in all_rewards:
        client_points_in_company = client_points_map.get(reward.company_id, 0)
        points_needed = reward.points_required - client_points_in_company
        reward_status = RewardStatusResponse(
            **reward.__dict__,
            redeemable=(client_points_in_company >= reward.points_required),
            points_to_redeem=max(0, points_needed)
        )
        response_data.append(reward_status)
    return response_data

@router.post("/rewards/redeem", response_model=RedeemedRewardResponse, status_code=status.HTTP_201_CREATED, tags=["Recompensas"])
async def redeem_reward(
    payload: RewardRedeemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem resgatar prémios.")
    result = await db.execute(select(Reward).filter(Reward.id == payload.reward_id))
    reward = result.scalar_one_or_none()
    if not reward:
        raise HTTPException(status_code=404, detail="Prémio não encontrado.")
    points_query = (
        select(func.sum(PointTransaction.points))
        .filter(PointTransaction.client_id == current_user.id, PointTransaction.company_id == reward.company_id)
    )
    total_points = (await db.execute(points_query)).scalar_one_or_none() or 0
    if total_points < reward.points_required:
        raise HTTPException(
            status_code=400,
            detail=f"Pontos insuficientes. Você tem {total_points}, mas precisa de {reward.points_required}."
        )
    spend_transaction = PointTransaction(
        client_id=current_user.id,
        company_id=reward.company_id,
        awarded_by_id=current_user.id,
        points=-reward.points_required
    )
    new_redeemed_reward = RedeemedReward(
        reward_id=reward.id,
        client_id=current_user.id,
        company_id=reward.company_id,
        points_spent=reward.points_required
    )
    db.add(spend_transaction)
    db.add(new_redeemed_reward)
    await db.commit()
    await db.refresh(new_redeemed_reward)
    return new_redeemed_reward
