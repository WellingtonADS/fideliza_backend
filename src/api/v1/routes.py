# -*- coding: utf-8 -*-

"""
API Principal para o Sistema de Fidelidade Fideliza+

Este arquivo contém todos os endpoints da API, organizados de forma lógica
para facilitar a manutenção e a compreensão.

A estrutura do arquivo é a seguinte:
1.  Importações e Configuração Inicial
2.  Funções Auxiliares (Helpers) de Acesso a Dados
3.  Endpoints de Autenticação e Acesso Público
4.  Endpoints de Registo de Novas Contas
5.  Endpoints Focados na Experiência do Cliente
6.  Endpoints de Gestão para Administradores e Colaboradores
    - Gestão de Perfil da Empresa
    - Gestão de Colaboradores
    - Gestão de Pontos
    - Gestão de Recompensas
    - Relatórios
7.  Endpoints de Perfil de Utilizador (Comum a todos)

Esta organização visa separar as responsabilidades e agrupar funcionalidades
relacionadas, mesmo mantendo o código em um único arquivo.
"""

# =============================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO INICIAL
# =============================================================================
from fastapi import APIRouter, Depends, HTTPException, status, Response, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, distinct
from sqlalchemy.orm import selectinload
from datetime import timedelta
from typing import List, Optional
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from jose import jwt, JWTError

# Importações de módulos locais (schemas, modelos, etc.)
from ..schemas import (
    UserCreate, UserResponse, Token, CompanyResponse, TokenData, 
    CollaboratorCreate, CompanyAdminCreate, PointAdd, PointTransactionResponse,
    PointsByCompany, RewardCreate, RewardResponse, RewardStatusResponse,
    RewardRedeemRequest, RedeemedRewardResponse, CompanyReport, UserUpdate,
    CompanyDetails, DashboardData, PasswordRecoveryRequest, PasswordReset, CompanyUpdate, RewardUpdate 
)
from ...database.models import User, Company, PointTransaction, Reward, RedeemedReward
from ...database.session import get_db
from ...core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user, get_current_admin_user,
    get_current_collaborator_or_admin, decode_password_reset_token
)
from ...core.config import settings

# --- Configuração do Serviço de Email ---
conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_FROM,
    MAIL_PORT = settings.MAIL_PORT,
    MAIL_SERVER = settings.MAIL_SERVER,
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

# --- Inicialização do Roteador Principal ---
router = APIRouter()


# =============================================================================
# 2. FUNÇÕES AUXILIARES (HELPERS) DE ACESSO A DADOS
# =============================================================================

async def _get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Busca um utilizador pelo seu endereço de email."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

async def _get_collaborator_or_404(db: AsyncSession, collaborator_id: int, company_id: int) -> User:
    """Busca um colaborador específico de uma empresa ou levanta uma exceção 404."""
    result = await db.execute(select(User).filter(User.id == collaborator_id))
    db_collaborator = result.scalar_one_or_none()
    
    if not db_collaborator or db_collaborator.company_id != company_id or db_collaborator.user_type != "COLLABORATOR":
        raise HTTPException(status_code=404, detail="Colaborador não encontrado ou não pertence a esta empresa.")
    return db_collaborator

async def _get_reward_or_404(db: AsyncSession, reward_id: int, company_id: int) -> Reward:
    """Busca uma recompensa específica de uma empresa ou levanta uma exceção 404."""
    db_reward = await db.get(Reward, reward_id)
    if not db_reward or db_reward.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recompensa não encontrada.")
    return db_reward

async def _send_password_recovery_email(
    background_tasks: BackgroundTasks, user: User, app_type: str
):
    """Gera um token de recuperação e envia o email em segundo plano."""
    token = create_access_token(
        data={"sub": user.email, "purpose": "password-reset"},
        expires_delta=timedelta(minutes=15)
    )
    
    reset_link = f"fidelizagestao://reset-password?token={token}" if app_type == 'gestao' else f"fidelizacliente://reset-password?token={token}"
    
    message = MessageSchema(
        subject="Recuperação de Senha - Fideliza+",
        recipients=[user.email],
        body=f"Olá {user.name},\n\nUse o seguinte link para redefinir a sua senha: {reset_link}\n\nSe não foi você que solicitou, ignore este email.\n\nObrigado,\nEquipa Fideliza+",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)


# =============================================================================
# 3. ENDPOINTS DE AUTENTICAÇÃO E ACESSO PÚBLICO
# =============================================================================

@router.get("/", tags=["Status"], summary="Verifica o estado da API")
def read_root():
    """Endpoint inicial para verificar se a API está a funcionar."""
    return {"message": "Bem-vindo à API do Fideliza+"}

@router.post("/login", response_model=Token, tags=["Autenticação"], summary="Autentica um utilizador")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Autentica um utilizador com email e senha, retornando um token JWT."""
    user = await _get_user_by_email(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de utilizador ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email, "user_type": user.user_type, "company_id": user.company_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/request-password-recovery", status_code=status.HTTP_200_OK, tags=["Autenticação"])
async def request_password_recovery(
    payload: PasswordRecoveryRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Inicia o processo de recuperação de senha. Sempre retorna sucesso para evitar enumeração de emails."""
    user = await _get_user_by_email(db, payload.email)
    if user:
        await _send_password_recovery_email(background_tasks, user, payload.app_type)
    
    return {"message": "Se existir uma conta com este e-mail, um link de recuperação foi enviado."}

@router.post("/reset-password", status_code=status.HTTP_200_OK, tags=["Autenticação"])
async def reset_password(payload: PasswordReset, db: AsyncSession = Depends(get_db)):
    """Redefine a senha do utilizador usando um token de recuperação válido."""
    try:
        email = decode_password_reset_token(payload.token)
        user = await _get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador inválido.")

        user.hashed_password = get_password_hash(payload.new_password)
        await db.commit()
        return {"message": "Senha redefinida com sucesso."}
        
    except (JWTError, HTTPException) as e:
        # Centraliza o tratamento de erro de token
        detail = e.detail if isinstance(e, HTTPException) else "Token inválido ou expirado"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


# =============================================================================
# 4. ENDPOINTS DE REGISTO DE NOVAS CONTAS
# =============================================================================

@router.post("/register/client", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Registo"])
async def register_client(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo utilizador do tipo 'CLIENTE' e gera o seu QR Code."""
    if await _get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email já registado")
        
    new_user = User(email=user.email, hashed_password=get_password_hash(user.password), name=user.name, user_type="CLIENT")
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    new_user.generate_qr_code() # Gera QR code após ter um ID
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.post("/register/company-admin", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, tags=["Registo"])
async def register_company_and_admin(payload: CompanyAdminCreate, db: AsyncSession = Depends(get_db)):
    """Cria uma nova empresa e o seu utilizador administrador associado."""
    if await _get_user_by_email(db, payload.admin_user.email):
        raise HTTPException(status_code=400, detail="Email de administrador já registado")
        
    # 1. Cria a empresa
    new_company = Company(name=payload.company_name)
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    
    # 2. Cria o utilizador administrador
    hashed_password = get_password_hash(payload.admin_user.password)
    new_admin = User(
        email=payload.admin_user.email, hashed_password=hashed_password,
        name=payload.admin_user.name, user_type="ADMIN", company_id=new_company.id
    )
    db.add(new_admin)
    await db.commit()
    
    return new_company


# =============================================================================
# 5. ENDPOINTS FOCADOS NA EXPERIÊNCIA DO CLIENTE
# =============================================================================

@router.get("/companies", response_model=List[CompanyDetails], tags=["Experiência do Cliente"], summary="Lista todas as empresas parceiras")
async def get_all_companies(db: AsyncSession = Depends(get_db)):
    """Endpoint público para obter a lista de todas as empresas. Usado na tela 'Explorar Lojas'."""
    result = await db.execute(select(Company))
    return result.scalars().all()

@router.get("/dashboard", response_model=DashboardData, tags=["Experiência do Cliente"], summary="Obtém os dados do dashboard do cliente")
async def get_client_dashboard(
    current_user: User = Depends(get_current_active_user), 
    db: AsyncSession = Depends(get_db)
):
    """Retorna dados agregados para o dashboard do cliente, como total de pontos e última atividade."""
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a clientes")

    total_points = (await db.execute(select(func.sum(PointTransaction.points)).where(PointTransaction.client_id == current_user.id))).scalar_or_none() or 0
    
    last_transaction = (await db.execute(
        select(PointTransaction)
        .where(PointTransaction.client_id == current_user.id)
        .order_by(PointTransaction.created_at.desc())
        .limit(1)
        .options(selectinload(PointTransaction.company))
    )).scalar_one_or_none()

    return DashboardData(
        total_points=total_points,
        last_activity=last_transaction,
        qr_code_base64=current_user.qr_code_base64
    )

@router.get("/points/my-points", response_model=List[PointsByCompany], tags=["Experiência do Cliente"], summary="Obtém os pontos do cliente por empresa")
async def get_my_points(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Retorna o total de pontos que o cliente logado possui, agrupado por empresa."""
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

@router.get("/points/my-transactions/{company_id}", response_model=List[PointTransactionResponse], tags=["Experiência do Cliente"])
async def get_my_transactions_for_company(
    company_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Retorna o histórico de transações de pontos do cliente para uma empresa específica."""
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem aceder.")

    query = (
        select(PointTransaction)
        .where(PointTransaction.client_id == current_user.id, PointTransaction.company_id == company_id)
        .options(selectinload(PointTransaction.awarded_by))
        .order_by(PointTransaction.created_at.desc())
    )
    transactions = (await db.execute(query)).scalars().all()
    return transactions

@router.get("/rewards/my-status", response_model=List[RewardStatusResponse], tags=["Experiência do Cliente"])
async def get_my_rewards_status(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Mostra ao cliente as recompensas das empresas onde tem pontos, indicando se são resgatáveis."""
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Acesso restrito a clientes.")
    
    points_result = await db.execute(
        select(PointTransaction.company_id, func.sum(PointTransaction.points).label("total_points"))
        .filter(PointTransaction.client_id == current_user.id).group_by(PointTransaction.company_id)
    )
    client_points_map = {company_id: total for company_id, total in points_result}

    if not client_points_map:
        return []

    rewards = (await db.execute(select(Reward).filter(Reward.company_id.in_(client_points_map.keys())))).scalars().all()
    
    response_data = []
    for reward in rewards:
        points = client_points_map.get(reward.company_id, 0)
        response_data.append(
            RewardStatusResponse.model_validate(
                reward,
                update={
                    "redeemable": points >= reward.points_required,
                    "points_to_redeem": max(0, reward.points_required - points)
                }
            )
        )
    return response_data

@router.post("/rewards/redeem", response_model=RedeemedRewardResponse, status_code=status.HTTP_201_CREATED, tags=["Experiência do Cliente"])
async def redeem_reward(
    payload: RewardRedeemRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Permite que um cliente resgate uma recompensa, verificando o saldo de pontos e registando a transação."""
    if current_user.user_type != 'CLIENT':
        raise HTTPException(status_code=403, detail="Apenas clientes podem resgatar prémios.")
        
    reward = await db.get(Reward, payload.reward_id)
    if not reward:
        raise HTTPException(status_code=404, detail="Recompensa não encontrada.")
        
    total_points = (await db.execute(
        select(func.sum(PointTransaction.points))
        .filter(PointTransaction.client_id == current_user.id, PointTransaction.company_id == reward.company_id)
    )).scalar_or_none() or 0
    
    if total_points < reward.points_required:
        raise HTTPException(status_code=400, detail=f"Pontos insuficientes. Você tem {total_points}, mas precisa de {reward.points_required}.")
        
    # Cria a transação de gasto e o registo do resgate
    spend_transaction = PointTransaction(
        client_id=current_user.id, company_id=reward.company_id,
        awarded_by_id=current_user.id, points=-reward.points_required
    )
    new_redeemed_reward = RedeemedReward(
        reward_id=reward.id, client_id=current_user.id,
        company_id=reward.company_id, points_spent=reward.points_required
    )
    
    db.add_all([spend_transaction, new_redeemed_reward])
    await db.commit()
    await db.refresh(new_redeemed_reward)
    
    return new_redeemed_reward


# =============================================================================
# 6. ENDPOINTS DE GESTÃO (ADMINISTRADORES E COLABORADORES)
# =============================================================================

# -----------------------------------------------------------------------------
# 6.1 Gestão de Perfil da Empresa (Apenas Admin)
# -----------------------------------------------------------------------------
@router.get("/companies/me", response_model=CompanyDetails, tags=["Gestão da Empresa"], summary="Obtém detalhes da empresa do admin")
async def get_my_company_details(current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    """Obtém os detalhes da empresa associada ao administrador autenticado."""
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")
    return company

@router.patch("/companies/me", response_model=CompanyDetails, tags=["Gestão da Empresa"], summary="Atualiza detalhes da empresa do admin")
async def update_my_company_details(
    company_data: CompanyUpdate, current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)
):
    """Atualiza os detalhes da empresa do administrador autenticado."""
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")

    update_data = company_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)

    await db.commit()
    await db.refresh(company)
    return company

# -----------------------------------------------------------------------------
# 6.2 Gestão de Colaboradores (Apenas Admin)
# -----------------------------------------------------------------------------
@router.post("/collaborators", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Gestão da Empresa"])
async def create_collaborator(
    collaborator: CollaboratorCreate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user)
):
    """Cria um novo utilizador 'COLABORADOR' para a empresa do administrador."""
    if await _get_user_by_email(db, collaborator.email):
        raise HTTPException(status_code=400, detail="Email já registado")
        
    new_collaborator = User(
        email=collaborator.email, hashed_password=get_password_hash(collaborator.password),
        name=collaborator.name, user_type="COLLABORATOR", company_id=current_admin.company_id
    )
    db.add(new_collaborator)
    await db.commit()
    await db.refresh(new_collaborator)
    return new_collaborator

@router.get("/collaborators", response_model=List[UserResponse], tags=["Gestão da Empresa"])
async def list_collaborators(db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Lista todos os colaboradores da empresa do administrador autenticado."""
    query = select(User).filter(User.company_id == current_admin.company_id, User.user_type == "COLLABORATOR")
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/collaborators/{collaborator_id}", response_model=UserResponse, tags=["Gestão da Empresa"])
async def update_collaborator(
    collaborator_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user)
):
    """Atualiza os dados (nome/senha) de um colaborador específico."""
    db_collaborator = await _get_collaborator_or_404(db, collaborator_id, current_admin.company_id)
        
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        db_collaborator.name = update_data["name"]
    if "password" in update_data and update_data["password"]:
        db_collaborator.hashed_password = get_password_hash(update_data["password"])
        
    await db.commit()
    await db.refresh(db_collaborator)
    return db_collaborator

@router.delete("/collaborators/{collaborator_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Gestão da Empresa"])
async def delete_collaborator(
    collaborator_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user)
):
    """Exclui um colaborador da empresa."""
    db_collaborator = await _get_collaborator_or_404(db, collaborator_id, current_admin.company_id)
    await db.delete(db_collaborator)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------
# 6.3 Gestão de Pontos (Admin e Colaborador)
# -----------------------------------------------------------------------------
@router.post("/points/add", response_model=PointTransactionResponse, status_code=status.HTTP_201_CREATED, tags=["Gestão da Empresa"])
async def add_points_to_client(
    payload: PointAdd, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_collaborator_or_admin)
):
    """Adiciona uma quantidade específica de pontos a um cliente, identificado pelo seu ID."""
    try:
        client_id = int(payload.client_identifier)
        client = await db.get(User, client_id)
        if not client or client.user_type != 'CLIENT':
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Identificador do cliente inválido.")

    new_transaction = PointTransaction(
        client_id=client.id, company_id=current_user.company_id,
        awarded_by_id=current_user.id, points=payload.points
    )
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction, attribute_names=['client', 'awarded_by']) # Força o carregamento das relações
    
    return new_transaction

@router.get("/points/transactions", response_model=List[PointTransactionResponse], tags=["Gestão da Empresa"])
async def list_company_point_transactions(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_collaborator_or_admin)
):
    """Lista todas as transações de pontos da empresa do utilizador logado."""
    query = (
        select(PointTransaction)
        .where(PointTransaction.company_id == current_user.company_id)
        .options(selectinload(PointTransaction.client), selectinload(PointTransaction.awarded_by))
        .order_by(PointTransaction.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()

# -----------------------------------------------------------------------------
# 6.4 Gestão de Recompensas (Apenas Admin)
# -----------------------------------------------------------------------------
@router.post("/rewards", response_model=RewardResponse, status_code=status.HTTP_201_CREATED, tags=["Gestão da Empresa"])
async def create_reward(
    reward: RewardCreate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user)
):
    """Cria uma nova recompensa para a empresa."""
    new_reward = Reward(**reward.model_dump(), company_id=current_admin.company_id)
    db.add(new_reward)
    await db.commit()
    await db.refresh(new_reward)
    return new_reward

@router.get("/rewards", response_model=List[RewardResponse], tags=["Gestão da Empresa"])
async def list_company_rewards(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_collaborator_or_admin)):
    """Lista todas as recompensas disponíveis na empresa do utilizador logado."""
    result = await db.execute(select(Reward).filter(Reward.company_id == current_user.company_id))
    return result.scalars().all()

@router.patch("/rewards/{reward_id}", response_model=RewardResponse, tags=["Gestão da Empresa"])
async def update_reward(
    reward_id: int, reward_data: RewardUpdate, current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)
):
    """Atualiza uma recompensa existente."""
    db_reward = await _get_reward_or_404(db, reward_id, current_user.company_id)
    update_data = reward_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reward, key, value)
    
    await db.commit()
    await db.refresh(db_reward)
    return db_reward

@router.delete("/rewards/{reward_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Gestão da Empresa"])
async def delete_reward(
    reward_id: int, current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)
):
    """Apaga uma recompensa."""
    db_reward = await _get_reward_or_404(db, reward_id, current_user.company_id)
    await db.delete(db_reward)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# -----------------------------------------------------------------------------
# 6.5 Relatórios (Apenas Admin)
# -----------------------------------------------------------------------------
@router.get("/reports/summary", response_model=CompanyReport, tags=["Gestão da Empresa"], summary="Obtém um relatório resumido")
async def get_company_summary_report(db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    """Fornece um relatório resumido para a empresa com totais de pontos, clientes e recompensas."""
    company_id = current_admin.company_id
    
    total_points_awarded_query = select(func.coalesce(func.sum(PointTransaction.points), 0)).filter(PointTransaction.company_id == company_id, PointTransaction.points > 0)
    unique_customers_query = select(func.coalesce(func.count(distinct(PointTransaction.client_id)), 0)).filter(PointTransaction.company_id == company_id)
    total_rewards_redeemed_query = select(func.coalesce(func.count(RedeemedReward.id), 0)).filter(RedeemedReward.company_id == company_id)
    
    total_points_awarded = (await db.execute(total_points_awarded_query)).scalar_one()
    unique_customers = (await db.execute(unique_customers_query)).scalar_one()
    total_rewards_redeemed = (await db.execute(total_rewards_redeemed_query)).scalar_one()

    return CompanyReport(
        total_points_awarded=total_points_awarded,
        unique_customers=unique_customers,
        total_rewards_redeemed=total_rewards_redeemed
    )


# =============================================================================
# 7. ENDPOINTS DE PERFIL DE UTILIZADOR (COMUM A TODOS)
# =============================================================================

@router.get("/users/me", response_model=UserResponse, tags=["Perfil do Utilizador"])
async def get_current_user_details(current_user: User = Depends(get_current_active_user)):
    """Retorna os detalhes (nome, email, etc.) do utilizador atualmente autenticado."""
    return current_user

@router.patch("/users/me", response_model=UserResponse, tags=["Perfil do Utilizador"])
async def update_current_user(
    payload: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Permite que o utilizador autenticado atualize o seu próprio nome ou senha."""
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        current_user.name = update_data["name"]
    if "password" in update_data and update_data["password"]:
        current_user.hashed_password = get_password_hash(update_data["password"])

    await db.commit()
    await db.refresh(current_user)
    return current_user
