"""
Sistem yönetimi + Doğrulama + İzleme — schema.sql BÖLÜM 7-9
Kaynak: sistem_genel_anlatim.md E8, E3, A7, E9
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SistemParametresi(Base):
    __tablename__ = "sistem_parametreleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anahtar: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    deger: Mapped[str] = mapped_column(String, nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String)
    guncelleme_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    guncelleyen_admin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_kullanicilar.id"))


class KatmanAgirligi(Base):
    __tablename__ = "katman_agirliklari"
    __table_args__ = (
        UniqueConstraint("versiyon", "katman_id", name="uq_ka_versiyon_katman"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    versiyon: Mapped[int] = mapped_column(Integer, nullable=False)
    katman_id: Mapped[int] = mapped_column(ForeignKey("katmanlar.id"), nullable=False)
    agirlik: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class GecerlilikSonucu(Base):
    """A7 — soru güvenilirlik testi (kör eşleştirme) ham sonuçları."""
    __tablename__ = "gecerlilik_sonuclari"
    __table_args__ = (
        CheckConstraint("model IN ('model_a','model_b','model_c')", name="ck_gs_model"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    soru_id: Mapped[int] = mapped_column(ForeignKey("sorular.id"), nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    tahmin_edilen_degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    gercek_degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    eslesme_skoru: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class GecerlilikOzeti(Base):
    __tablename__ = "gecerlilik_ozet"
    __table_args__ = (
        CheckConstraint("guven_seviyesi IN ('yuksek','dusuk')", name="ck_go_guven"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    soru_id: Mapped[int] = mapped_column(ForeignKey("sorular.id"), nullable=False, unique=True)
    dogruluk_orani: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    guven_seviyesi: Mapped[str] = mapped_column(String, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    admin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_kullanicilar.id"), nullable=False)
    islem: Mapped[str] = mapped_column(String, nullable=False)
    hedef_tablo: Mapped[str] = mapped_column(String, nullable=False)
    hedef_id: Mapped[str] = mapped_column(String, nullable=False)
    gerekce: Mapped[str | None] = mapped_column(String)
    zaman: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
