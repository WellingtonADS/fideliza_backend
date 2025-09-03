from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# =============================================================================
# SCHEMAS BASE E REUTILIZÁVEIS
# =============================================================================

class UserInfo(BaseModel):
    """Schema simplificado para informações de utilizador em respostas."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class CompanyInfo(BaseModel):
    """Schema simplificado para informações de empresa em respostas."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

# =============================================================================
# SCHEMAS DE UTILIZADOR E AUTENTICAÇÃO
# =============================================================================

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    """Schema de resposta completo para um utilizador."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_type: str
    company_id: Optional[int] = None
    qr_code_base64: Optional[str] = None

class CollaboratorCreate(UserCreate):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None
    company_id: Optional[int] = None

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr
    app_type: str = 'client'

class PasswordReset(BaseModel):
    token: str
    new_password: str

# =============================================================================
# SCHEMAS DE EMPRESA
# =============================================================================

class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyAdminCreate(BaseModel):
    company_name: str
    admin_user: UserCreate

class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    admin_user_id: Optional[int] = None

class CompanyDetails(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    logo_url: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# NOVO SCHEMA PARA ATUALIZAÇÃO DA EMPRESA
class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    logo_url: Optional[str] = None

# =============================================================================
# SCHEMAS DE PONTUAÇÃO E TRANSAÇÕES
# =============================================================================

class PointAdd(BaseModel):
    client_identifier: str
    points: int = 1

class PointTransactionResponse(BaseModel):
    """Schema unificado para resposta de transação de pontos."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    points: int
    created_at: datetime
    client: Optional[UserInfo] = None
    awarded_by: Optional[UserInfo] = None

class PointsByCompany(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_points: int
    company: CompanyInfo

# =============================================================================
# SCHEMAS DE PRÉMIOS E RECOMPENSAS
# =============================================================================

class RewardBase(BaseModel):
    name: str
    description: Optional[str] = None
    points_required: int = Field(gt=0, description="Os pontos necessários devem ser maiores que zero")

class RewardCreate(RewardBase):
    pass

# NOVO SCHEMA PARA ATUALIZAÇÃO DE PRÉMIO
class RewardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    points_required: Optional[int] = Field(None, gt=0)


class RewardResponse(RewardBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    created_at: datetime

class RewardStatusResponse(RewardResponse):
    redeemable: bool
    points_to_redeem: int

class RewardRedeemRequest(BaseModel):
    reward_id: int

class RedeemedRewardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reward_id: int
    client_id: int
    points_spent: int
    redeemed_at: datetime

# =============================================================================
# SCHEMAS DE RELATÓRIOS E DASHBOARD
# =============================================================================

class CompanyReport(BaseModel):
    total_points_awarded: int
    total_rewards_redeemed: int
    unique_customers: int

class DashboardData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_points: int
    last_activity: Optional[PointTransactionResponse] = None
    qr_code_base64: Optional[str] = None

