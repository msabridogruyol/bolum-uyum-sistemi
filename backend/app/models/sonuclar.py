"""
Sonuçlar (tur bazlı) — schema.sql BÖLÜM 6
Kaynak: sistem_genel_anlatim.md D3, D4
"""
import uuid
from datetime import datetime
from sqlalchemy import Integer, BigInteger, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class OgrenciBolumUyumSkoru(Base):
    """
    D4 — TOPLAM_UYUM. `yontem_skorlari` ve `kendall_w` YALNIZCA admin API
    şemasında döner (bkz. D5 "öğrenciye asla gösterilmeyenler" kuralı,
    Bölüm C madde 6 — API response ayrımı backend seviyesinde uygulanmalı).
    """
    __tablename__ = "ogrenci_bolum_uyum_skorlari"
    __table_args__ = (
        UniqueConstraint("ogrenci_id", "tur_id", "bolum_id", name="uq_obus_ogrenci_tur_bolum"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False)
    toplam_uyum: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    yontem_skorlari: Mapped[dict | None] = mapped_column(JSON)   # admin-only — 10 ÇKKV sonucu [DÜZELTME: JSONB->JSON, taşınabilirlik]
    kendall_w: Mapped[float | None] = mapped_column(Numeric(4, 3))  # admin-only
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class OgrenciDalUyumSkoru(Base):
    __tablename__ = "ogrenci_dal_uyum_skorlari"
    __table_args__ = (
        UniqueConstraint("ogrenci_id", "tur_id", "dal_id", "bolum_id", name="uq_odus_ogrenci_tur_dal_bolum"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    dal_id: Mapped[int] = mapped_column(ForeignKey("dallar.id"), nullable=False)
    bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False)
    dal_ici_uyum: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
