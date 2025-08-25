from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- Esquemas para Clientes ---

class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

# --- Esquemas para Relatórios ---

class CompanyReport(BaseModel):
    total_points_awarded: int
    total_rewards_redeemed: int
    unique_customers: int

# --- Esquemas para Recompensas ---

class RewardBase(BaseModel):
    name: str
    description: Optional[str] = None
    points_required: int = Field(gt=0, description="Os pontos necessários devem ser maiores que zero")

class RewardCreate(RewardBase):
    pass

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

# --- Esquemas para Pontuação ---

class PointAdd(BaseModel):
    client_identifier: str

class PointTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    points: int
    client: UserInfo
    awarded_by: UserInfo
    created_at: datetime

# --- Esquemas para Usuários ---

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_type: str
    company_id: Optional[int] = None
    qr_code_base64: Optional[str] = None

# --- Esquemas para Colaboradores ---

class CollaboratorCreate(UserCreate):
    pass

# --- Esquemas para Autenticação (Token) ---

# Em schemas.py
class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None
    company_id: Optional[int] = None

# Em schemas.py
class PasswordReset(BaseModel):
    token: str
    new_password: str

# --- Esquemas para Empresas ---

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

# --- NOVOS ESQUEMAS PARA A EXPERIÊNCIA DO CLIENTE ---

class CompanyDetails(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    logo_url: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DashboardData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_points: int
    last_activity: Optional[PointTransactionResponse] = None
    qr_code_base64: Optional[str] = None # <-- Adicione esta linha

# --- Esquemas: Para Consulta de Pontos do Cliente ---

class CompanyInfoForPoints(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class PointsByCompany(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_points: int
    company: CompanyInfoForPoints
