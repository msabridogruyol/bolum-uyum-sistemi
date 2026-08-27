"""
Meslek verisi tabloları — schema.sql BÖLÜM 3
Kaynak: sistem_genel_anlatim.md A1, A2, A2b, A3, A4b
"""
from datetime import datetime
from sqlalchemy import String, BigInteger, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Meslek(Base):
    __tablename__ = "meslekler"
    __table_args__ = (
        CheckConstraint("kaynak IN ('tmss_resmi','ek_guncel')", name="ck_meslek_kaynak"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    isco_kodu: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    ad: Mapped[str] = mapped_column(String, nullable=False)
    alt_grup_kodu: Mapped[str] = mapped_column(String, nullable=False)
    alt_grup_adi: Mapped[str] = mapped_column(String, nullable=False)
    ana_grup_kodu: Mapped[str] = mapped_column(String, nullable=False)
    kaynak: Mapped[str] = mapped_column(String, nullable=False, default="tmss_resmi")


class Kategori(Base):
    __tablename__ = "kategoriler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    aciklama: Mapped[str] = mapped_column(String, nullable=False)


class AltGrupKategoriEslesme(Base):
    __tablename__ = "alt_grup_kategori_eslesme"
    __table_args__ = (
        CheckConstraint("guven_seviyesi IN ('yuksek','dusuk')", name="ck_agke_guven"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alt_grup_kodu: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    kategori_id: Mapped[int] = mapped_column(ForeignKey("kategoriler.id"), nullable=False)
    model_a_skor: Mapped[float | None] = mapped_column(Numeric(5, 4))
    model_b_skor: Mapped[float | None] = mapped_column(Numeric(5, 4))
    model_c_skor: Mapped[float | None] = mapped_column(Numeric(5, 4))
    guven_seviyesi: Mapped[str] = mapped_column(String, nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MeslekBolumEslesmeAday(Base):
    """A2 ham çıktısı — model bazlı meslek↔bölüm benzerlik skorları (E7 için)."""
    __tablename__ = "meslek_bolum_eslesme_aday"
    __table_args__ = (
        CheckConstraint("model IN ('model_a','model_b','model_c')", name="ck_mbea_model"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    meslek_id: Mapped[int] = mapped_column(ForeignKey("meslekler.id"), nullable=False)
    bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    benzerlik_skoru: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MeslekDegiskenSkoru(Base):
    """A3 ham çıktısı — model bazlı meslek↔değişken skorları (E7 için)."""
    __tablename__ = "meslek_degisken_skorlari"
    __table_args__ = (
        CheckConstraint("model IN ('model_a','model_b','model_c')", name="ck_mds_model"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    meslek_id: Mapped[int] = mapped_column(ForeignKey("meslekler.id"), nullable=False)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    skor: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
