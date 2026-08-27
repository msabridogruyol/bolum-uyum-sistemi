"""
Hesaplama çıktıları (statik) — schema.sql BÖLÜM 4
Kaynak: sistem_genel_anlatim.md A4, A5 — offline pipeline'ın nihai ürünü
"""
from datetime import datetime
from sqlalchemy import Integer, BigInteger, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BolumAgirligi(Base):
    __tablename__ = "bolum_agirliklari"
    __table_args__ = (
        UniqueConstraint("bolum_id", "degisken_id", "versiyon", name="uq_bolum_agirlik_versiyon"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    agirlik_degeri: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)     # A5 — ORTALAMA(A,B,C)
    yakinsama_skoru: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)    # A5 — STD_SAPMA(A,B,C)
    agirlikli_varyans: Mapped[float | None] = mapped_column(Numeric(6, 4))           # A4 — güvenilirlik göstergesi
    etkin_meslek_sayisi: Mapped[int | None] = mapped_column(Integer)                 # A4 — güvenilirlik göstergesi
    versiyon: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
