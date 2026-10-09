"""
Kimlik tabloları — schema.sql BÖLÜM 1
Kaynak: sistem_genel_anlatim.md D1, veritabani_taslagi.md Bölüm 3
"""
import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, CheckConstraint, BigInteger, Integer
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
    okul: Mapped[str | None] = mapped_column(String, nullable=True)   # okullar.ad kopyası (istatistikler için); öğrenci girmez
    # [2026-10-09] Öğrencinin okulu yönetimden atanır (Okullar sayfası); öğrenci serbest metin girmez.
    okul_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("okullar.id", ondelete="SET NULL"), nullable=True)
    sube: Mapped[str | None] = mapped_column(String, nullable=True)
    # [2026-10-09] Yönetimden açılan hesaplar geçici şifreyle başlar; ilk girişte öğrenci kendi şifresini belirler.
    sifre_degistirmeli: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    son_giris_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
        # [2026-10-09] 3 yetki seviyesi: süper admin (tüm sistem) / okul yetkilisi (yalnızca kendi okulu) / öğrenci
        CheckConstraint("rol IN ('super_admin','okul_yetkilisi')", name="ck_admin_rol"),
        CheckConstraint("rol <> 'okul_yetkilisi' OR okul_id IS NOT NULL", name="ck_admin_okul"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_soyad: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    sifre_hash: Mapped[str] = mapped_column(String, nullable=False)
    rol: Mapped[str] = mapped_column(String, nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    okul_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("okullar.id", ondelete="CASCADE"), nullable=True)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sifre_degistirmeli: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    son_giris_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OgrenciHesapOlayi(Base):
    """[2026-10-09] Öğrenci hesabının olay kaydı: hesap açıldı, giriş, hatalı giriş, şifre sıfırlandı ..."""
    __tablename__ = "ogrenci_hesap_olaylari"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id", ondelete="CASCADE"), nullable=False)
    olay: Mapped[str] = mapped_column(String, nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String)
    yapan: Mapped[str | None] = mapped_column(String)
    ip: Mapped[str | None] = mapped_column(String)
    zaman: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
