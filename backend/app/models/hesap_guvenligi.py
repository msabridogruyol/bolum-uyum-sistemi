"""
[2026-10-04] Hesap güvenliği ve KVKK kayıtları.

- KvkkOnayi            : her onay/geri çekme bir satır (denetim izi). Güncel durum = en son satır.
- DogrulamaKodu        : 2 adımlı doğrulama için e-postaya giden 6 haneli kod (yalnızca özeti saklanır).
- SifreSifirlamaTokeni : "şifremi unuttum" ve rehber daveti bağlantıları (yalnızca özeti saklanır).
- GuvenilirCihaz       : "bu cihazı 30 gün hatırla" — o cihazda tekrar kod istenmez.

kullanici_tipi: 'ogrenci' (ogrenciler tablosu) | 'yonetim' (admin_kullanicilar: yönetici ve rehber öğretmen)
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

_ID = BigInteger().with_variant(Integer, "sqlite")


class KvkkOnayi(Base):
    __tablename__ = "kvkk_onaylari"
    __table_args__ = (
        CheckConstraint("kullanici_tipi IN ('ogrenci','yonetim')", name="ck_kvkk_tip"),
        Index("ix_kvkk_kullanici", "kullanici_tipi", "kullanici_id"),
    )
    id: Mapped[int] = mapped_column(_ID, primary_key=True, autoincrement=True)
    kullanici_tipi: Mapped[str] = mapped_column(String, nullable=False)
    kullanici_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    onay_kodu: Mapped[str] = mapped_column(String, nullable=False)       # aydinlatma, acik_riza_analiz, ...
    metin_surumu: Mapped[str] = mapped_column(String, nullable=False)
    verildi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_adresi: Mapped[str | None] = mapped_column(String)
    zaman: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DogrulamaKodu(Base):
    __tablename__ = "dogrulama_kodlari"
    __table_args__ = (Index("ix_dk_kullanici", "kullanici_tipi", "kullanici_id"),)
    id: Mapped[int] = mapped_column(_ID, primary_key=True, autoincrement=True)
    kullanici_tipi: Mapped[str] = mapped_column(String, nullable=False)
    kullanici_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kod_ozeti: Mapped[str] = mapped_column(String, nullable=False)
    son_kullanma: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deneme_sayisi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kullanildi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SifreSifirlamaTokeni(Base):
    __tablename__ = "sifre_sifirlama_tokenleri"
    __table_args__ = (
        CheckConstraint("amac IN ('sifirlama','davet')", name="ck_sst_amac"),
        Index("ix_sst_ozet", "token_ozeti"),
    )
    id: Mapped[int] = mapped_column(_ID, primary_key=True, autoincrement=True)
    kullanici_tipi: Mapped[str] = mapped_column(String, nullable=False)
    kullanici_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    token_ozeti: Mapped[str] = mapped_column(String, nullable=False)
    amac: Mapped[str] = mapped_column(String, nullable=False, default="sifirlama")
    son_kullanma: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kullanilma_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class GuvenilirCihaz(Base):
    __tablename__ = "guvenilir_cihazlar"
    __table_args__ = (Index("ix_gc_ozet", "cihaz_ozeti"),)
    id: Mapped[int] = mapped_column(_ID, primary_key=True, autoincrement=True)
    kullanici_tipi: Mapped[str] = mapped_column(String, nullable=False)
    kullanici_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cihaz_ozeti: Mapped[str] = mapped_column(String, nullable=False)
    son_kullanma: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
