# fideliza_backend/src/database/models.py
import datetime
import qrcode
import io
import base64
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from typing import List

class Base(DeclarativeBase):
    pass

# NOVO: Tabela para o histórico de prémios resgatados
class RedeemedReward(Base):
    __tablename__ = "redeemed_rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    reward_id: Mapped[int] = mapped_column(ForeignKey("rewards.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    
    # ID do admin/colaborador que autorizou o resgate (pode ser nulo se for automático)
    authorized_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    redeemed_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    # Relacionamentos
    reward: Mapped["Reward"] = relationship(foreign_keys=[reward_id])
    client: Mapped["User"] = relationship(foreign_keys=[client_id])
    authorized_by: Mapped["User"] = relationship(foreign_keys=[authorized_by_id])


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    points_required: Mapped[int] = mapped_column(Integer, nullable=False)
    
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)

    company: Mapped["Company"] = relationship()
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    points: Mapped[int] = mapped_column(Integer, default=1)
    
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    awarded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)

    client: Mapped["User"] = relationship(foreign_keys=[client_id])
    company: Mapped["Company"] = relationship()
    awarded_by: Mapped["User"] = relationship(foreign_keys=[awarded_by_id])


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    qr_code_base64: Mapped[str] = mapped_column(Text, nullable=True)
    user_type: Mapped[str] = mapped_column(String, default="CLIENT", nullable=False)
    
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="users", foreign_keys=[company_id])

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def generate_qr_code(self):
        if self.id is None:
            return
        qr_content = str(self.id)
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img_buffer = io.BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_buffer, format="PNG")
        self.qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', type='{self.user_type}')>"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    users: Mapped[List["User"]] = relationship(back_populates="company", foreign_keys=[User.company_id])
    admin: Mapped["User"] = relationship(foreign_keys=[admin_user_id])

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"
