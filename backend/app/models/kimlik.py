"""
Kimlik tabloları — schema.sql BÖLÜM 1
Kaynak: sistem_genel_anlatim.md D1, veritabani_taslagi.md Bölüm 3
"""
import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, CheckConstraint, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Ogrenci(Base):
    __tablename__ = "ogrenciler"
    __table_args__ = (
        CheckConstraint(
            "cinsiyet IN ('kadin','erkek','belirtmek_istemiyorum','diger') OR cinsiyet IS NULL",
            name="ck_ogrenci_cinsiyet",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_soyad: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    sifre_hash: Mapped[str] = mapped_column(String, nullable=False)  # bcrypt/argon2
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    guncelleme_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Profil alanları (sonradan eklendi) ---
    okul: Mapped[str | None] = mapped_column(String, nullable=True)
    sinif: Mapped[str | None] = mapped_column(String, nullable=True)
    dogum_tarihi: Mapped[date | None] = mapped_column(Date, nullable=True)
    # NOT: dogum_tarihi/cinsiyet KVKK açısından hassas — veli onayı akışı ayrıca kurulmalı.
    cinsiyet: Mapped[str | None] = mapped_column(String, nullable=True)
    ilgi_alanlari: Mapped[str | None] = mapped_column(String, nullable=True)
    hedef_universite: Mapped[str | None] = mapped_column(String, nullable=True)
    hedef_meslek_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("meslekler.id"), nullable=True)
    profil_foto_base64: Mapped[str | None] = mapped_column(String, nullable=True)


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
