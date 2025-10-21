# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, distinct
from sqlalchemy.orm import selectinload
from datetime import timedelta, datetime, timezone
from typing import List
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from jose import jwt, JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

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
    get_current_collaborator_or_admin
)
from ...core.config import settings

# Configuração do FastMail
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

# Configuração do rate limiter com key_func sensível a testes
def _key_func(request):
    # Se um header de teste existir, usa-o como chave de rate limit para isolar casos de teste
    test_id = request.headers.get("X-Test-Id") if request and hasattr(request, 'headers') else None
    if test_id:
        return test_id
    return get_remote_address(request)

limiter = Limiter(key_func=_key_func)

router = APIRouter()

# =============================================================================
# 1. ACESSO PÚBLICO E AUTENTICAÇÃO
# =============================================================================

@router.get("/", tags=["Status"], summary="Verifica o estado da API")
def read_root():
    """Endpoint inicial para verificar se a API está a funcionar."""
    return {"message": "Bem-vindo à API do Fideliza+"}

@router.post("/token", response_model=Token, tags=["Autenticação"], summary="Autentica um utilizador")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Autentica um utilizador e retorna um token JWT."""
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de utilizador ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Migração transparente: se o hash não estiver no formato atual, re-hash com pbkdf2 e salva
    try:
        if not user.hashed_password.startswith("$pbkdf2-sha256$"):
            user.hashed_password = get_password_hash(form_data.password)
            db.add(user)
            await db.commit()
    except Exception:
        pass

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_type": user.user_type, "company_id": user.company_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/request-password-recovery", status_code=status.HTTP_200_OK, tags=["Autenticação"])
async def request_password_recovery(
    payload: PasswordRecoveryRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Inicia o processo de recuperação de senha.
    """
    result = await db.execute(select(User).filter(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user:
        # Gera um token de acesso de curta duração (ex: 15 minutos) para a recuperação
        password_reset_token = create_access_token(
            data={"sub": user.email, "purpose": "password-reset"},
            expires_delta=timedelta(minutes=15)
        )

        if payload.app_type == 'gestao':
            scheme = settings.GESTAO_APP_SCHEME
            android_pkg = settings.ANDROID_GESTAO_PACKAGE
            web_base = settings.GESTAO_WEB_RESET_URL
        else: # 'client'
            scheme = settings.CLIENT_APP_SCHEME
            android_pkg = settings.ANDROID_CLIENT_PACKAGE
            web_base = settings.CLIENT_WEB_RESET_URL

        # Deep link padrão (scheme://path?token=...)
        deep_link = f"{scheme}://reset-password?token={password_reset_token}"
        # Intent link Android com fallback para web
        intent_link = (
            f"intent://reset-password?token={password_reset_token}#Intent;"
            f"scheme={scheme};package={android_pkg};end"
        )
        # Web fallback (GitHub Pages). Passamos também qual app e open=1 para autoabrir
        web_link = f"{web_base}?token={password_reset_token}&app={payload.app_type}&open=1"

        # Prepara o e-mail em HTML com links clicáveis
        html_body = f"""
        <p>Olá {user.name},</p>
        <p>Você solicitou a redefinição da sua senha.</p>
        <p>Para redefinir sua senha, escolha uma das opções abaixo:</p>
        <ul>
            <li>Pelo navegador (fallback): <a href='{web_link}' target='_blank'>{web_link}</a></li>
            <li>Pelo app (scheme): <a href='{deep_link}'>{deep_link}</a></li>
            <li>Android (intent): <a href='{intent_link}'>{intent_link}</a></li>
        </ul>
        <p>Se você não solicitou isto, por favor ignore este e-mail.</p>
        <p>Obrigado,<br/>Equipa Fideliza+</p>
        """
        message = MessageSchema(
                subject="Recuperação de Senha - Fideliza+",
                recipients=[user.email],
                body=html_body,
                subtype=MessageType.html
        )

        # Envia o e-mail em segundo plano
        fm = FastMail(conf)
        background_tasks.add_task(fm.send_message, message)
    
    # Retornamos sempre a mesma mensagem para não revelar se um e-mail existe ou não
    return {"message": "Se existir uma conta com este e-mail, um link de recuperação foi enviado."}


@router.post("/reset-password", status_code=status.HTTP_200_OK, tags=["Autenticação"])
async def reset_password(
    payload: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    Permite redefinir a senha de um usuário com base em um token válido.
    """
    try:
        # Decodifica e valida o token recebido
        token_data = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Verifica o propósito do token
        if token_data.get("purpose") != "password-reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido para redefinição de senha."
            )

        # Verifica se o token expirou
        exp = token_data.get("exp")
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token expirado."
            )

        # Verifica se o e-mail no token corresponde a um usuário ativo
        email = token_data.get("sub")
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )

        # Atualiza a senha do usuário
        user.hashed_password = get_password_hash(payload.new_password)
        db.add(user)
        await db.commit()

        return {"message": "Senha redefinida com sucesso."}

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao validar o token: {str(e)}"
        )

# =============================================================================
# 2. REGISTO DE NOVAS CONTAS
# =============================================================================

@router.post("/register/client/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Registo"], summary="Regista um novo cliente")
@limiter.limit("5/minute")
async def register_client(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Cria um novo utilizador do tipo 'CLIENTE'.
    Verifica se o email já existe antes de criar.
    Valida a força da senha.
    """
    # Verifica se o email já está registrado
    result = await db.execute(select(User).filter(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já registado")

    # Valida a força da senha
    if len(user.password) < 8 or not any(char.isdigit() for char in user.password) or not any(char.isalpha() for char in user.password):
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter pelo menos 8 caracteres, incluindo letras e números."
        )

    # Cria o novo usuário
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
@limiter.limit("5/minute")
async def register_company_and_admin(
    request: Request,
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
# 3. EXPERIÊNCIA DO CLIENTE
# =============================================================================

@router.get("/companies", response_model=List[CompanyDetails], tags=["Experiência do Cliente"], summary="Lista todas as empresas parceiras")
async def get_all_companies(db: AsyncSession = Depends(get_db)):
    """
    Endpoint público para obter uma lista de todas as empresas parceiras.
    Alimenta a tela "Explorar Lojas" no aplicativo do cliente.
    """
    result = await db.execute(select(Company))
    companies = result.scalars().all()
    return companies

@router.get("/dashboard", response_model=DashboardData, tags=["Experiência do Cliente"], summary="Obtém os dados do dashboard do cliente")
async def get_client_dashboard(
    current_user: User = Depends(get_current_active_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para o dashboard do cliente.
    Retorna o total de pontos e a última atividade de pontuação.
    Acessível apenas por 'CLIENTE'.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Acesso restrito a clientes. Faça login com uma conta de CLIENTE no app Fideliza Cliente. "
                "Se você é administrador, use o app Fideliza Gestão."
            ),
        )

    # Calcula o total de pontos do cliente em todas as empresas
    total_points_query = select(func.sum(PointTransaction.points)).where(PointTransaction.client_id == current_user.id)
    total_points_result = await db.execute(total_points_query)
    total_points = total_points_result.scalar_one_or_none() or 0

    # Busca a última transação de pontos
    last_transaction_query = (
        select(PointTransaction)
        .where(PointTransaction.client_id == current_user.id)
        .order_by(PointTransaction.created_at.desc())
        .limit(1)
        .options(
            selectinload(PointTransaction.client),
            selectinload(PointTransaction.awarded_by)
        )
    )
    last_transaction_result = await db.execute(last_transaction_query)
    last_transaction = last_transaction_result.scalar_one_or_none()

    return DashboardData(
        total_points=total_points,
        last_activity=last_transaction,
        qr_code_base64=current_user.qr_code_base64
    )
    
@router.get("/points/my-points", response_model=List[PointsByCompany], tags=["Experiência do Cliente"], summary="Obtém os pontos do cliente por empresa")
@limiter.limit("10/minute")
async def get_my_points(
    request: Request,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Retorna o total de pontos que o cliente logado possui, agrupado por empresa.
    Acessível apenas por 'CLIENTE'.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(
            status_code=403,
            detail=(
                "Apenas clientes podem consultar seus pontos. Faça login com uma conta de CLIENTE no app Fideliza Cliente. "
                "Se você é administrador, use o app Fideliza Gestão."
            ),
        )
        
    query = (
        select(func.sum(PointTransaction.points).label("total_points"), Company)
        .join(Company, PointTransaction.company_id == Company.id)
        .filter(PointTransaction.client_id == current_user.id)
        .group_by(Company.id)
    )
    result = await db.execute(query)
    return [{"total_points": total, "company": company} for total, company in result.all()]

@router.get(
    "/points/my-transactions/{company_id}",
    response_model=List[PointTransactionResponse],
    summary="Obtém as transações do cliente para uma empresa específica",
    tags=["Experiência do Cliente"]
)
@limiter.limit("10/minute")
async def get_my_transactions_for_company(
    request: Request,
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retorna o histórico de transações do cliente logado para uma empresa específica.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(
            status_code=403,
            detail=(
                "Apenas clientes podem acessar este histórico. Faça login com uma conta de CLIENTE no app Fideliza Cliente. "
                "Se você é administrador, use o app Fideliza Gestão."
            ),
        )

    query = (
        select(PointTransaction)
        .where(
            PointTransaction.client_id == current_user.id,
            PointTransaction.company_id == company_id
        )
        .options(selectinload(PointTransaction.awarded_by))
        .order_by(PointTransaction.created_at.desc())
    )
    result = await db.execute(query)
    transactions = result.scalars().all()
    return transactions

@router.get("/rewards/my-status", response_model=List[RewardStatusResponse], tags=["Experiência do Cliente"], summary="Verifica o estado das recompensas para o cliente")
@limiter.limit("10/minute")
async def get_my_rewards_status(
    request: Request,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    Mostra ao cliente todas as recompensas das empresas onde ele tem pontos,
    indicando se já pode resgatar ou quantos pontos faltam.
    Acessível apenas por 'CLIENTE'.
    """
    if current_user.user_type != 'CLIENT':
        raise HTTPException(
            status_code=403,
            detail=(
                "Apenas clientes podem consultar o estado de recompensas. Faça login com uma conta de CLIENTE no app Fideliza Cliente. "
                "Se você é administrador, use o app Fideliza Gestão."
            ),
        )
    
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

@router.post("/rewards/redeem", response_model=RedeemedRewardResponse, status_code=status.HTTP_201_CREATED, tags=["Experiência do Cliente"], summary="Resgata uma recompensa")
@limiter.limit("5/minute")
async def redeem_reward(
    request: Request,
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
        raise HTTPException(
            status_code=403,
            detail=(
                "Apenas clientes podem resgatar recompensas. Faça login com uma conta de CLIENTE no app Fideliza Cliente. "
                "Se você é administrador, use o app Fideliza Gestão."
            ),
        )
        
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
    
    db.add_all([spend_transaction, new_redeemed_reward])
    await db.commit()
    
    return new_redeemed_reward

# =============================================================================
# 4. GESTÃO DA EMPRESA (ADMINS E COLABORADORES)
# =============================================================================

@router.get("/companies/me", response_model=CompanyDetails, tags=["Gestão da Empresa"], summary="Obtém detalhes da empresa do admin")
@limiter.limit("10/minute")
async def get_my_company_details(request: Request, current_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    """Obtém os detalhes da empresa do administrador logado."""
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    return company

@router.patch("/companies/me", response_model=CompanyDetails, tags=["Gestão da Empresa"], summary="Atualiza detalhes da empresa do admin")
@limiter.limit("5/minute")
async def update_my_company_details(
    request: Request,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza os detalhes da empresa do administrador logado."""
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    update_data = company_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)

    # Atualiza o nome do usuário na tabela 'users'
    if "userName" in update_data:
        current_user.name = update_data["userName"]
        db.add(current_user)

    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company

@router.post("/collaborators/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Gestão da Empresa"], summary="Cria um novo colaborador")
@limiter.limit("5/minute")
async def create_collaborator(
    request: Request,
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

    # Valida a força da senha
    if len(collaborator.password) < 8 or not any(char.isdigit() for char in collaborator.password) or not any(char.isalpha() for char in collaborator.password):
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter pelo menos 8 caracteres, incluindo letras e números."
        )

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

@router.get("/collaborators/", response_model=List[UserResponse], tags=["Gestão da Empresa"], summary="Lista os colaboradores da empresa")
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

@router.patch("/collaborators/{collaborator_id}", response_model=UserResponse, tags=["Gestão da Empresa"], summary="Atualiza um colaborador")
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

@router.delete("/collaborators/{collaborator_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Gestão da Empresa"], summary="Exclui um colaborador")
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

@router.post("/points/add", response_model=PointTransactionResponse, status_code=status.HTTP_201_CREATED, tags=["Gestão da Empresa"], summary="Adiciona pontos a um cliente")
async def add_points_to_client(
    payload: PointAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    """Adiciona uma quantidade específica de pontos a um cliente."""
    try:
        client_id = int(payload.client_identifier)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Identificador do cliente inválido.")

    client = await db.get(User, client_id)
    if not client or client.user_type != 'CLIENT':
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    new_transaction = PointTransaction(
        client_id=client.id,
        company_id=current_user.company_id,
        awarded_by_id=current_user.id,
        points=payload.points
    )
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)

    result = await db.execute(
        select(PointTransaction).where(PointTransaction.id == new_transaction.id)
        .options(selectinload(PointTransaction.client), selectinload(PointTransaction.awarded_by))
    )
    return result.scalar_one()

@router.get("/points/transactions/", response_model=List[PointTransactionResponse], tags=["Gestão da Empresa"], summary="Lista as transações de pontos da empresa")
async def list_company_point_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_collaborator_or_admin)
):
    """Lista as transações de pontos da empresa do utilizador logado."""
    query = (
        select(PointTransaction)
        .where(PointTransaction.company_id == current_user.company_id)
        .options(selectinload(PointTransaction.client), selectinload(PointTransaction.awarded_by))
        .order_by(PointTransaction.created_at.desc())
    )
    result = await db.execute(query)
    transactions = result.scalars().all()
    return transactions
    
@router.post("/rewards/", response_model=RewardResponse, status_code=status.HTTP_201_CREATED, tags=["Gestão da Empresa"], summary="Cria uma nova recompensa")
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

@router.get("/rewards/", response_model=List[RewardResponse], tags=["Gestão da Empresa"], summary="Lista as recompensas da empresa")
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

@router.patch("/rewards/{reward_id}", response_model=RewardResponse, tags=["Gestão da Empresa"], summary="Atualiza uma recompensa")
async def update_reward(
    reward_id: int,
    reward_data: RewardUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza um prémio existente."""
    db_reward = await db.get(Reward, reward_id)
    if not db_reward or db_reward.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prémio não encontrado")

    update_data = reward_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reward, key, value)

    db.add(db_reward)
    await db.commit()
    await db.refresh(db_reward)
    return db_reward

@router.delete("/rewards/{reward_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Gestão da Empresa"], summary="Exclui uma recompensa")
async def delete_reward(
    reward_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Apaga um prémio."""
    db_reward = await db.get(Reward, reward_id)
    if not db_reward or db_reward.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prémio não encontrado")

    await db.delete(db_reward)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/reports/summary", response_model=CompanyReport, tags=["Gestão da Empresa"], summary="Obtém um relatório resumido da empresa")
@limiter.limit("5/minute")
async def get_company_summary_report(
    request: Request,
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
    
# =============================================================================
# 5. PERFIL DE UTILIZADOR (COMUM A TODOS)
# =============================================================================

@router.get("/users/me", response_model=UserResponse, tags=["Perfil do Utilizador"], summary="Obtém detalhes do utilizador logado")
async def get_current_user_details(current_user: User = Depends(get_current_active_user)):
    """Retorna os detalhes do utilizador atualmente autenticado."""
    return current_user

@router.patch("/users/me", response_model=UserResponse, tags=["Perfil do Utilizador"], summary="Atualiza o perfil do utilizador logado")
async def update_current_user(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
