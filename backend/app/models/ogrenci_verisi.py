"""
Öğrenci verisi (dinamik, tur bazlı) — schema.sql BÖLÜM 5
Kaynak: sistem_genel_anlatim.md D2, D2c (tur/yeniden değerlendirme mekanizması)
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Numeric, Boolean, DateTime, ForeignKey, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class OgrenciDegerlendirmeTuru(Base):
    """D2c — her tam K1-K4 turu ayrı bir kayıt; öğrenci geçmişi asla üzerine yazılmaz."""
    __tablename__ = "ogrenci_degerlendirme_turu"
    __table_args__ = (
        CheckConstraint("durum IN ('devam_ediyor','tamamlandi')", name="ck_odt_durum"),
        UniqueConstraint("ogrenci_id", "tur_no", name="uq_odt_ogrenci_tur"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_no: Mapped[int] = mapped_column(Integer, nullable=False)
    baslama_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    tamamlanma_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    durum: Mapped[str] = mapped_column(String, nullable=False, default="devam_ediyor")
    # [EKLENDİ] Güvenlik/tutarlılık altyapısı — kontrol soruları + tam ekran/
    # sekme olaylarından hesaplanan birleşik güven skoru (bkz. guvenlik_servisi.py).
    guven_skoru: Mapped[float | None] = mapped_column(Numeric(5, 2))
    sonuc_gecerli_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    gecersizlik_nedeni: Mapped[str | None] = mapped_column(String)


class OgrenciKatmanOturumu(Base):
    __tablename__ = "ogrenci_katman_oturumlari"
    __table_args__ = (
        CheckConstraint(
            "durum IN ('baslamadi','devam_ediyor','yarida_birakildi','tamamlandi')",
            name="ck_oko_durum",
        ),
        UniqueConstraint("ogrenci_id", "tur_id", "katman_id", name="uq_oko_ogrenci_tur_katman"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    katman_id: Mapped[int] = mapped_column(ForeignKey("katmanlar.id"), nullable=False)
    durum: Mapped[str] = mapped_column(String, nullable=False, default="baslamadi")
    kilitlenen_soru_id_listesi: Mapped[list[int] | None] = mapped_column(JSON)  # [DÜZELTME] ARRAY(Integer) yerine JSON — SQLite/PostgreSQL taşınabilirliği için, işlevsel olarak eşdeğer
    baslama_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tamamlanma_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OgrenciDalOturumu(Base):
    __tablename__ = "ogrenci_dal_oturumlari"
    __table_args__ = (
        CheckConstraint("durum IN ('baslamadi','devam_ediyor','tamamlandi')", name="ck_odo_durum"),
        UniqueConstraint("ogrenci_id", "tur_id", "dal_id", name="uq_odo_ogrenci_tur_dal"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    dal_id: Mapped[int] = mapped_column(ForeignKey("dallar.id"), nullable=False)
    durum: Mapped[str] = mapped_column(String, nullable=False, default="baslamadi")
    baslama_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tamamlanma_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OgrenciDegiskenSkoru(Base):
    __tablename__ = "ogrenci_degisken_skorlari"
    __table_args__ = (
        CheckConstraint("puan >= 0 AND puan <= 100", name="ck_ods_puan_araligi"),
        UniqueConstraint("ogrenci_id", "tur_id", "degisken_id", name="uq_ods_ogrenci_tur_degisken"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    puan: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class OgrenciCevap(Base):
    """
    [EKSİK/EKLENDİ] — schema.sql'de yoktu. D2'deki katman akışının çalışması
    için öğrencinin HAM (soru bazlı) cevaplarının, katman tamamlanıp
    ogrenci_degisken_skorlari'na agregatif olarak yazılana kadar bir yerde
    tutulması gerekiyor — aksi halde "kaldığı yerden devam et" (D4) ve çoklu
    sorudan tek değişken puanı üretme (D2) mekanizmaları çalışamaz.
    """
    __tablename__ = "ogrenci_cevaplar"
    __table_args__ = (
        UniqueConstraint("ogrenci_id", "tur_id", "soru_id", name="uq_oc_ogrenci_tur_soru"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    soru_id: Mapped[int] = mapped_column(ForeignKey("sorular.id"), nullable=False)
    secenek_id: Mapped[int] = mapped_column(ForeignKey("soru_secenekleri.id"), nullable=False)
    cevap_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class GuvenlikOlayi(Base):
    """
    [EKLENDİ] Güvenlik/tutarlılık altyapısı — tam ekrandan çıkma, sekme
    değiştirme, pencere odağı kaybı gibi olayları loglar. guvenlik_servisi.py
    bu tabloyu sayarak güven skorunun "olay" bileşenini hesaplar.
    """
    __tablename__ = "guvenlik_olaylari"
    __table_args__ = (
        CheckConstraint(
            "olay_tipi IN ("
            "'tam_ekrandan_cikti','tam_ekrana_geri_donuldu',"
            "'sekme_degisti','sekmeye_geri_donuldu',"
            "'pencere_odagi_kaybedildi','pencere_odagi_geri_kazanildi',"
            "'kamera_izni_reddedildi','kamera_desteklenmiyor'"
            ")",
            name="ck_go_olay_tipi",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    olay_tipi: Mapped[str] = mapped_column(String, nullable=False)
    katman_kod: Mapped[str | None] = mapped_column(String)
    olay_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class GuvenlikFotografi(Base):
    """
    [EKLENDİ] Periyodik kimlik doğrulama fotoğraflarının referansı — asıl
    dosya Supabase Storage'da, burada yalnızca yol/zaman/bağlam tutulur.
    """
    __tablename__ = "guvenlik_fotograflari"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"), nullable=False)
    depolama_yolu: Mapped[str] = mapped_column(String, nullable=False)
    katman_kod: Mapped[str | None] = mapped_column(String)
    cekim_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
