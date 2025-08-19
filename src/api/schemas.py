# fideliza_backend/src/api/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# --- Esquemas para Clientes ---

class UserInfo(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

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
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class RewardStatusResponse(RewardResponse):
    redeemable: bool
    points_to_redeem: int

class RewardRedeemRequest(BaseModel):
    reward_id: int

class RedeemedRewardResponse(BaseModel):
    id: int
    reward_id: int
    client_id: int
    points_spent: int
    redeemed_at: datetime

    class Config:
        from_attributes = True

# --- Esquemas para Pontuação ---

class PointAdd(BaseModel):
    client_identifier: str

class PointTransactionResponse(BaseModel):
    id: int
    points: int
    client: UserInfo
    awarded_by: UserInfo
    created_at: datetime
    class Config:
        from_attributes = True

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
    id: int
    user_type: str
    company_id: Optional[int] = None
    qr_code_base64: Optional[str] = None
    class Config:
        from_attributes = True

# --- Esquemas para Colaboradores ---

class CollaboratorCreate(UserCreate):
    pass

# --- Esquemas para Autenticação (Token) ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None
    company_id: Optional[int] = None


# --- Esquemas para Empresas ---

class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyAdminCreate(BaseModel):
    company_name: str
    admin_user: UserCreate

class CompanyResponse(CompanyBase):
    id: int
    admin_user_id: Optional[int] = None
    class Config:
        from_attributes = True

# --- NOVOS ESQUEMAS PARA A EXPERIÊNCIA DO CLIENTE ---

class CompanyDetails(CompanyBase):
    """ Schema para listar empresas na tela 'Explorar'. """
    id: int
    logo_url: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

class DashboardData(BaseModel):
    """ Schema para os dados da tela principal (dashboard) do cliente. """
    total_points: int
    last_activity: Optional[PointTransactionResponse] = None
    
    class Config:
        from_attributes = True

# --- Esquemas: Para Consulta de Pontos do Cliente ---

class CompanyInfoForPoints(BaseModel):
    id: int
    name: str

class PointsByCompany(BaseModel):
    total_points: int
    company: CompanyInfoForPoints
    class Config:
        from_attributes = True
