"""
Kimlik tabloları — schema.sql BÖLÜM 1
Kaynak: sistem_genel_anlatim.md D1, veritabani_taslagi.md Bölüm 3
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Ogrenci(Base):
    __tablename__ = "ogrenciler"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_soyad: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    sifre_hash: Mapped[str] = mapped_column(String, nullable=False)  # bcrypt/argon2
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    guncelleme_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    # NOT: yaş/doğum tarihi bilinçli olarak yok — KVKK/veli onayı ertelendi
    # (sistem_genel_anlatim.md, Ertelenen Konular #2)


class AdminKullanici(Base):
    __tablename__ = "admin_kullanicilar"
    __table_args__ = (
        CheckConstraint("rol IN ('super_admin','icerik_editoru')", name="ck_admin_rol"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_soyad: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    sifre_hash: Mapped[str] = mapped_column(String, nullable=False)
    rol: Mapped[str] = mapped_column(String, nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
