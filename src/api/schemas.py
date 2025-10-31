"""
# Schemas da API (Pydantic)

Este módulo define os modelos Pydantic usados para validar requests, formatar responses
e documentar payloads de utilizadores, empresas, pontos, recompensas e relatórios.

## Secções
- Reutilizáveis (UserInfo, CompanyInfo)
- Utilizador e autenticação
- Empresa
- Pontos e transações
- Recompensas e resgates
- Relatórios e dashboard

Notas:
- Modelos que são construídos a partir de objetos ORM definem `model_config = ConfigDict(from_attributes=True)`.
- Restrições (ex.: `points_required > 0`) são aplicadas via `Field`.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

# SCHEMAS BASE E REUTILIZÁVEIS


class UserInfo(BaseModel):
    """Informações resumidas de um utilizador.

    Attributes:
        id: Identificador do utilizador.
        name: Nome de exibição do utilizador.
    """

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CompanyInfo(BaseModel):
    """Informações resumidas de uma empresa.

    Attributes:
        id: Identificador da empresa.
        name: Nome da empresa.
    """

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


# SCHEMAS DE UTILIZADOR E AUTENTICAÇÃO


class UserBase(BaseModel):
    """Campos base de utilizador."""
    email: EmailStr = Field(description="Endereço de e-mail do utilizador.")
    name: str = Field(description="Nome de exibição do utilizador.")


class UserCreate(UserBase):
    """Payload para criação de utilizador.

    Attributes:
        password: Senha em texto (será validada/hashada no backend).
    """
    password: str = Field(description="Senha em texto que será validada e armazenada com hash.")


class UserUpdate(BaseModel):
    """Atualização parcial de utilizador.

    Attributes:
        name: Novo nome (opcional).
        email: Novo email (opcional).
        password: Nova senha em texto (opcional).
    """
    name: Optional[str] = Field(default=None, description="Novo nome do utilizador.")
    email: Optional[EmailStr] = Field(default=None, description="Novo e-mail do utilizador.")
    password: Optional[str] = Field(default=None, description="Nova senha do utilizador.")


class UserResponse(UserBase):
    """Representação completa de utilizador em respostas.

    Attributes:
        id: Identificador do utilizador.
        user_type: Tipo/role do utilizador (ADMIN, CLIENT, COLLABORATOR).
        company_id: ID da empresa associada (quando aplicável).
        qr_code_base64: PNG do QR codificado em base64 (opcional).
    """

    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Identificador do utilizador.")
    user_type: str = Field(description="Tipo/role do utilizador: ADMIN, CLIENT ou COLLABORATOR.")
    company_id: Optional[int] = Field(default=None, description="ID da empresa associada, quando aplicável.")
    qr_code_base64: Optional[str] = Field(default=None, description="Imagem PNG em base64 do QR do utilizador.")


class CollaboratorCreate(UserCreate):
    """Alias de ``UserCreate`` utilizado para criação de colaboradores."""


class Token(BaseModel):
    """Resposta de autenticação (token de acesso)."""
    access_token: str = Field(description="Token JWT de acesso.")
    token_type: str = Field(description="Tipo do token, tipicamente 'bearer'.")


class TokenData(BaseModel):
    """Dados mínimos derivados do token JWT.

    Attributes:
        email: Email do utilizador (sub).
        user_type: Tipo do utilizador.
        company_id: Empresa associada (quando aplicável).
    """
    email: Optional[str] = Field(default=None, description="Email (claim 'sub') do token.")
    user_type: Optional[str] = Field(default=None, description="Tipo do utilizador associado ao token.")
    company_id: Optional[int] = Field(default=None, description="Empresa associada ao utilizador.")


class PasswordRecoveryRequest(BaseModel):
    """Requisição para iniciar recuperação de senha."""
    email: EmailStr = Field(description="E-mail do utilizador para envio do link de recuperação.")
    app_type: str = Field(default="client", description="Origem do pedido: 'client' ou 'gestao'.")


class PasswordReset(BaseModel):
    """Conclusão da recuperação de senha."""
    token: str = Field(description="Token de recuperação fornecido por e-mail.")
    new_password: str = Field(description="Nova senha do utilizador.")


# SCHEMAS DE EMPRESA


class CompanyBase(BaseModel):
    """Campos base de empresa."""
    name: str = Field(description="Nome da empresa.")


class CompanyCreate(CompanyBase):
    """Payload de criação de empresa."""


class CompanyAdminCreate(BaseModel):
    """Criação de empresa com utilizador administrador inicial.

    Attributes:
        company_name: Nome da empresa a ser criada.
        admin_user: Dados do utilizador administrador.
    """
    company_name: str = Field(description="Nome da empresa a ser criada.")
    admin_user: UserCreate = Field(description="Dados do utilizador administrador inicial.")


class CompanyResponse(CompanyBase):
    """Representação de empresa em respostas."""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Identificador da empresa.")
    admin_user_id: Optional[int] = Field(default=None, description="ID do utilizador admin associado.")


class CompanyDetails(CompanyBase):
    """Detalhes estendidos de empresa."""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Identificador da empresa.")
    logo_url: Optional[str] = Field(default=None, description="URL do logotipo da empresa.")
    address: Optional[str] = Field(default=None, description="Endereço da empresa.")
    category: Optional[str] = Field(default=None, description="Categoria de atuação.")
    latitude: Optional[float] = Field(default=None, description="Latitude da localização.")
    longitude: Optional[float] = Field(default=None, description="Longitude da localização.")


class CompanyUpdate(BaseModel):
    """Atualização parcial de empresa.

    Attributes:
        userName: Atualiza também ``users.name`` do admin associado.
    """
    name: Optional[str] = Field(default=None, description="Novo nome da empresa.")
    address: Optional[str] = Field(default=None, description="Novo endereço da empresa.")
    category: Optional[str] = Field(default=None, description="Nova categoria.")
    logo_url: Optional[str] = Field(default=None, description="Novo URL do logotipo.")
    userName: Optional[str] = Field(default=None, description="Novo nome do utilizador admin (reflete em users.name).")


# SCHEMAS DE PONTUAÇÃO E TRANSAÇÕES


class PointAdd(BaseModel):
    """Adição de pontos a um cliente.

    Attributes:
        client_identifier: Identificador do cliente (ex.: ID do QR).
        points: Quantidade de pontos a adicionar (default: 1).
    """
    client_identifier: str = Field(description="Identificador do cliente (ex.: ID contido no QR).")
    points: int = Field(default=1, description="Quantidade de pontos a adicionar.")


class PointTransactionResponse(BaseModel):
    """Transação de pontos (crédito/débito) retornada pela API.

    Attributes:
        id: Identificador da transação.
        points: Pontos (positivo crédito; negativo resgate).
        created_at: Data/hora da transação.
        client: Informações do cliente.
        awarded_by: Quem concedeu/lançou a transação.
    """

    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Identificador da transação.")
    points: int = Field(description="Pontos lançados: positivo (crédito), negativo (resgate).")
    created_at: datetime = Field(description="Data/hora da transação.")
    client: Optional[UserInfo] = Field(default=None, description="Cliente relacionado (resumido).")
    awarded_by: Optional[UserInfo] = Field(default=None, description="Quem lançou a transação (resumido).")


class PointsByCompany(BaseModel):
    """Total de pontos do cliente por empresa."""
    model_config = ConfigDict(from_attributes=True)
    total_points: int = Field(description="Total de pontos do cliente nesta empresa.")
    company: CompanyInfo = Field(description="Informações da empresa.")


# SCHEMAS DE PRÉMIOS E RECOMPENSAS


class RewardBase(BaseModel):
    """Campos base de recompensa."""
    name: str = Field(description="Nome da recompensa.")
    description: Optional[str] = Field(default=None, description="Descrição opcional da recompensa.")
    points_required: int = Field(
        gt=0, description="Os pontos necessários devem ser maiores que zero"
    )


class RewardCreate(RewardBase):
    """Payload de criação de recompensa."""


class RewardUpdate(BaseModel):
    """Atualização parcial de recompensa."""
    name: Optional[str] = Field(default=None, description="Novo nome da recompensa.")
    description: Optional[str] = Field(default=None, description="Nova descrição.")
    points_required: Optional[int] = Field(default=None, gt=0, description="Novo total de pontos necessários (se informado).")


class RewardResponse(RewardBase):
    """Recompensa com metadados de propriedade/tempo."""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Identificador da recompensa.")
    company_id: int = Field(description="Empresa dona da recompensa.")
    created_at: datetime = Field(description="Data/hora de criação.")


class RewardStatusResponse(RewardResponse):
    """Estado da recompensa para um cliente."""
    redeemable: bool = Field(description="Indica se o cliente pode resgatar agora.")
    points_to_redeem: int = Field(description="Pontos que faltam para resgatar (0 se já pode).")


class RewardRedeemRequest(BaseModel):
    """Pedido de resgate de recompensa."""
    reward_id: int = Field(description="Identificador da recompensa a ser resgatada.")


class RedeemedRewardResponse(BaseModel):
    """Recompensa já resgatada (histórico)."""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Identificador do registro de resgate.")
    reward_id: int = Field(description="Recompensa resgatada.")
    client_id: int = Field(description="Cliente que resgatou.")
    points_spent: int = Field(description="Pontos gastos no resgate.")
    redeemed_at: datetime = Field(description="Data/hora do resgate.")


# SCHEMAS DE RELATÓRIOS E DASHBOARD


class CompanyReport(BaseModel):
    """Métricas agregadas da empresa."""
    total_points_awarded: int = Field(description="Soma dos pontos concedidos (créditos).")
    total_rewards_redeemed: int = Field(description="Quantidade de recompensas resgatadas.")
    unique_customers: int = Field(description="Contagem de clientes únicos.")


class DashboardData(BaseModel):
    """Payload do dashboard (cliente/admin)."""
    model_config = ConfigDict(from_attributes=True)
    total_points: int = Field(description="Total de pontos do cliente em todas as empresas.")
    last_activity: Optional[PointTransactionResponse] = Field(default=None, description="Última transação do cliente.")
    qr_code_base64: Optional[str] = Field(default=None, description="QR do cliente em base64.")
