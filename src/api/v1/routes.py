# fideliza_backend/src/api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, distinct
from sqlalchemy.orm import selectinload
from datetime import timedelta
from typing import List

from ..schemas import (
    UserCreate, UserResponse, Token, CompanyResponse, TokenData, 
    CollaboratorCreate, CompanyAdminCreate, PointAdd, PointTransactionResponse,
    PointsByCompany, RewardCreate, RewardResponse, RewardStatusResponse,
    RewardRedeemRequest, RedeemedRewardResponse, CompanyReport, UserUpdate
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

# =============================================================================
# 1. STATUS E AUTENTICAÇÃO
# =============================================================================

@router.get("/", tags=["Status"], summary="Verifica o estado da API")
def read_root():
    """Endpoint inicial para verificar se a API está a funcionar."""
    return {"message": "Bem-vindo à API do Fideliza+"}

@router.post("/token", response_model=Token, tags=["Autenticação"], summary="Obtém um token de acesso")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica um utilizador com email e senha e retorna um token JWT.
    """
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de utilizador ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": user.user_type, "company_id": user.company_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# =============================================================================
# 2. REGISTO DE NOVOS UTILIZADORES E EMPRESAS
# =============================================================================

@router.post("/register/client/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Registo"], summary="Regista um novo cliente")
async def register_client(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Cria um novo utilizador do tipo 'CLIENTE'.
    Verifica se o email já existe antes de criar.
    """
    result = await db.execute(select(User).filter(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já registado")
        
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email, hashed_password=hashed_password, name=user.name, user_type="CLIENT"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Gera o QR code após o utilizador ter um ID
    new_user.generate_qr_code()
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.post("/register/company-admin/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, tags=["Registo"], summary="Regista uma nova empresa e o seu administrador")
async def register_company_and_admin(
    payload: CompanyAdminCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova empresa e, em seguida, cria o utilizador administrador associado a ela.
    """
    result = await db.execute(select(User).filter(User.email == payload.admin_user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email de administrador já registado")
        
    # 1. Criar a empresa
    new_company = Company(name=payload.company_name)
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    
    # 2. Criar o utilizador administrador
    hashed_password = get_password_hash(payload.admin_user.password)
    new_admin = User(
        email=payload.admin_user.email,
        hashed_password=hashed_password,
        name=payload.admin_user.name,
        user_type="ADMIN",
        company_id=new_company.id
    )
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)
    
    # 3. Associar o admin à empresa (opcional, se o modelo tiver a coluna)
    new_company.admin_user_id = new_admin.id
    await db.commit()
    await db.refresh(new_company)
    
    return new_company

# =============================================================================
# 3. GESTÃO DE UTILIZADORES (ADMIN & PERFIL)
# =============================================================================

@router.get("/users/me/", response_model=UserResponse, tags=["Utilizadores"], summary="Obtém os dados do utilizador logado")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retorna os detalhes do utilizador atualmente autenticado."""
    return current_user

@router.post("/collaborators/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Utilizadores"], summary="Cria um novo colaborador")
async def create_collaborator(
    collaborator: CollaboratorCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Cria um novo utilizador do tipo 'COLABORADOR'.
    Apenas utilizadores 'ADMIN' podem aceder.
    O colaborador é associado à mesma empresa do admin.
    """
    result = await db.execute(select(User).filter(User.email == collaborator.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já registado")
        
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

@router.get("/collaborators/", response_model=List[UserResponse], tags=["Utilizadores"], summary="Lista os colaboradores da empresa")
async def list_collaborators(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Lista todos os colaboradores da empresa do administrador logado.
    Apenas utilizadores 'ADMIN' podem aceder.
    """
    company_id = current_admin.company_id
    query = (
        select(User)
        .filter(User.company_id == company_id, User.user_type == "COLLABORATOR")
        .options(selectinload(User.company)) # Otimização para pré-carregar dados
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/collaborators/{collaborator_id}", response_model=UserResponse, tags=["Utilizadores"], summary="Atualiza um colaborador")
async def update_collaborator(
    collaborator_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Atualiza os dados de um colaborador específico.
    Apenas utilizadores 'ADMIN' podem aceder.
    """
    company_id = current_admin.company_id
    result = await db.execute(select(User).filter(User.id == collaborator_id))
    db_collaborator = result.scalar_one_or_none()
    
    if not db_collaborator or db_collaborator.company_id != company_id or db_collaborator.user_type != "COLLABORATOR":
        raise HTTPException(status_code=404, detail="Colaborador não encontrado ou não pertence a esta empresa.")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_collaborator, key, value)
        
    await db.commit()
    await db.refresh(db_collaborator)
    return db_collaborator

@router.delete("/collaborators/{collaborator_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Utilizadores"], summary="Exclui um colaborador")
async def delete_collaborator(
    collaborator_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Exclui um colaborador da empresa.
    Apenas utilizadores 'ADMIN' podem aceder.
    """
    company_id = current_admin.company_id
    result = await db.execute(select(User).filter(User.id == collaborator_id))
    db_collaborator = result.scalar_one_or_none()
    
    if not db_collaborator or db_collaborator.company_id != company_id or db_collaborator.user_type != "COLLABORATOR":
        raise HTTPException(status_code=404, detail="Colaborador não encontrado ou não pertence a esta empresa.")
        
    await db.delete(db_collaborator)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# =============================================================================
# 4. SISTEMA DE PONTUAÇÃO
# =============================================================================

@router.post("/points/add", response_model=PointTransactionResponse, status_code=status.HTTP_201_CREATED, tags=["Pontuação"], summary="Adiciona um ponto a um cliente")
async def add_points_to_client(
    payload: PointAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    """
    Adiciona 1 ponto a um cliente, identificado pelo seu ID.
    Acessível por 'ADMIN' e 'COLABORADOR'.
    """
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Utilizador não está associado a nenhuma empresa.")
        
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

@router.get("/points/my-points", response_model=List[PointsByCompany], tags=["Pontuação"], summary="Consulta os pontos do cliente")
async def get_my_points(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Retorna o total de pontos que o cliente logado possui, agrupado por empresa.
    Acessível apenas por 'CLIENTE'.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem consultar os seus pontos.")
        
    query = (
        select(func.sum(PointTransaction.points).label("total_points"), Company)
        .join(Company, PointTransaction.company_id == Company.id)
        .filter(PointTransaction.client_id == current_user.id)
        .group_by(Company.id)
    )
    result = await db.execute(query)
    return [{"total_points": total, "company": company} for total, company in result.all()]

@router.get("/points/transactions/", response_model=List[PointTransactionResponse], tags=["Pontuação"], summary="Lista as transações de pontos da empresa")
async def list_company_point_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    """
    Lista as últimas transações de pontos da empresa do utilizador logado.
    Acessível por 'ADMIN' e 'COLABORADOR'.
    """
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Utilizador não está associado a nenhuma empresa.")

    query = (
        select(PointTransaction)
        .filter(PointTransaction.company_id == company_id)
        .order_by(PointTransaction.created_at.desc())
        .limit(50) # Limita às últimas 50 transações para performance
        .options(
            selectinload(PointTransaction.client), # Otimização para pré-carregar dados
            selectinload(PointTransaction.awarded_by)
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

# =============================================================================
# 5. GESTÃO DE RECOMPENSAS
# =============================================================================

@router.post("/rewards/", response_model=RewardResponse, status_code=status.HTTP_201_CREATED, tags=["Recompensas"], summary="Cria uma nova recompensa")
async def create_reward(
    reward: RewardCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Cria uma nova recompensa para a empresa.
    Acessível apenas por 'ADMIN'.
    """
    company_id = current_admin.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Administrador não está associado a nenhuma empresa.")
        
    new_reward = Reward(**reward.model_dump(), company_id=company_id)
    db.add(new_reward)
    await db.commit()
    await db.refresh(new_reward)
    return new_reward

@router.get("/rewards/", response_model=List[RewardResponse], tags=["Recompensas"], summary="Lista as recompensas da empresa")
async def list_company_rewards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    """
    Lista todas as recompensas disponíveis na empresa do utilizador logado.
    Acessível por 'ADMIN' e 'COLABORADOR'.
    """
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=403, detail="Utilizador não está associado a nenhuma empresa.")
        
    result = await db.execute(select(Reward).filter(Reward.company_id == company_id))
    return result.scalars().all()

@router.get("/rewards/my-status", response_model=List[RewardStatusResponse], tags=["Recompensas"], summary="Verifica o estado das recompensas para o cliente")
async def get_my_rewards_status(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Mostra ao cliente todas as recompensas das empresas onde ele tem pontos,
    indicando se já pode resgatar ou quantos pontos faltam.
    Acessível apenas por 'CLIENTE'.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem consultar o estado dos seus prémios.")
    
    # 1. Obter todos os pontos do cliente, por empresa
    points_query = (
        select(PointTransaction.company_id, func.sum(PointTransaction.points).label("total_points"))
        .filter(PointTransaction.client_id == current_user.id).group_by(PointTransaction.company_id)
    )
    points_result = await db.execute(points_query)
    client_points_map = {company_id: total for company_id, total in points_result.all()}

    if not client_points_map:
        return []

    # 2. Obter todas as recompensas das empresas relevantes
    rewards_query = select(Reward).filter(Reward.company_id.in_(list(client_points_map.keys())))
    rewards_result = await db.execute(rewards_query)
    all_rewards = rewards_result.scalars().all()
    
    # 3. Calcular o estado de cada recompensa
    response_data = []
    for reward in all_rewards:
        client_points_in_company = client_points_map.get(reward.company_id, 0)
        points_needed = reward.points_required - client_points_in_company
        
        reward_status = RewardStatusResponse(
            id=reward.id,
            name=reward.name,
            description=reward.description,
            points_required=reward.points_required,
            company_id=reward.company_id,
            created_at=reward.created_at,
            redeemable=(client_points_in_company >= reward.points_required),
            points_to_redeem=max(0, points_needed)
        )
        response_data.append(reward_status)
        
    return response_data

@router.post("/rewards/redeem", response_model=RedeemedRewardResponse, status_code=status.HTTP_201_CREATED, tags=["Recompensas"], summary="Resgata uma recompensa")
async def redeem_reward(
    payload: RewardRedeemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Permite que um cliente resgate uma recompensa.
    Verifica se o cliente tem pontos suficientes e cria uma transação negativa
    de pontos, registando o resgate.
    Acessível apenas por 'CLIENTE'.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem resgatar prémios.")
        
    result = await db.execute(select(Reward).filter(Reward.id == payload.reward_id))
    reward = result.scalar_one_or_none()
    if not reward:
        raise HTTPException(status_code=404, detail="Prémio não encontrado.")
        
    # Verifica o saldo de pontos na empresa específica
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
        
    # Cria a transação de gasto de pontos
    spend_transaction = PointTransaction(
        client_id=current_user.id,
        company_id=reward.company_id,
        awarded_by_id=current_user.id, # O próprio cliente "concedeu" o gasto
        points=-reward.points_required
    )
    
    # Regista o prémio resgatado
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

# =============================================================================
# 6. RELATÓRIOS
# =============================================================================

@router.get("/reports/summary", response_model=CompanyReport, tags=["Relatórios"], summary="Obtém um relatório resumido da empresa")
async def get_company_summary_report(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Fornece um relatório resumido para a empresa do administrador logado,
    incluindo total de pontos, clientes únicos e prémios resgatados.
    Acessível apenas por 'ADMIN'.
    """
    company_id = current_admin.company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrador não está associado a nenhuma empresa."
        )

    # Otimização: Consulta única para buscar todos os dados do relatório.
    report_query = (
        select(
            func.coalesce(func.sum(PointTransaction.points).filter(PointTransaction.points > 0), 0),
            func.coalesce(func.count(distinct(PointTransaction.client_id)), 0),
            func.coalesce(func.count(RedeemedReward.id), 0)
        )
        .select_from(PointTransaction)
        .outerjoin(RedeemedReward, RedeemedReward.company_id == PointTransaction.company_id)
        .filter(PointTransaction.company_id == company_id)
    )
    
    result = await db.execute(report_query)
    total_points_awarded, unique_customers, total_rewards_redeemed = result.one_or_none() or (0, 0, 0)

    return CompanyReport(
        total_points_awarded=total_points_awarded,
        total_rewards_redeemed=total_rewards_redeemed,
        unique_customers=unique_customers
    )
