from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Moto(Base):
    __tablename__ = "motos"
    id: Mapped[int] = mapped_column(primary_key=True)
    modelo: Mapped[str] = mapped_column(String(120))
    marca: Mapped[str] = mapped_column(String(40))
    ano: Mapped[int | None] = mapped_column(Integer)
    preco: Mapped[float] = mapped_column(Float)
    cidade: Mapped[str | None] = mapped_column(String(80))
    url: Mapped[str] = mapped_column(String(500), unique=True)  # evita duplicados
    descricao: Mapped[str | None] = mapped_column(Text)
    km: Mapped[int | None] = mapped_column(Integer)
    data_publicacao: Mapped[str | None] = mapped_column(String(40))
    fotos: Mapped[str | None] = mapped_column(Text)
    valor_fipe: Mapped[float | None] = mapped_column(Float)
    desconto: Mapped[float | None] = mapped_column(Float)
    score: Mapped[int | None] = mapped_column(Integer)
    lucro_estimado: Mapped[float | None] = mapped_column(Float)
    classificacao: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
