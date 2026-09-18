"""
Koçluk modülü (Bölüm F) — schema.sql BÖLÜM 10
Kaynak: koclugu_karsilastirma_modulu.md F1, F3, F4.2, F5.3, F8

ÖNEMLİ: OgrenciHedefBolum için "tek aktif hedef" kısıtı burada Python
tarafında değil, veritabanı seviyesinde bir partial unique index ile
uygulanır (bkz. bu dosyanın sonundaki Alembic migration notu) — SQLAlchemy
ORM katmanı bu kısıtı garanti etmez, sadece şemaya yansıtır.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class OgrenciHedefBolum(Base):
    __tablename__ = "ogrenci_hedef_bolum"
    # NOT: "aynı öğrenci için aynı anda yalnızca 1 aktif_mi=TRUE satır" kısıtı
    # bir CheckConstraint DEĞİL — PostgreSQL'de yalnızca partial UNIQUE INDEX
    # ile ifade edilebilir (bkz. schema.sql, F8). Alembic migration'da:
    #   CREATE UNIQUE INDEX ux_ogrenci_tek_aktif_hedef
    #       ON ogrenci_hedef_bolum (ogrenci_id) WHERE aktif_mi = TRUE;

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False)
    secim_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    pasif_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # F8 — hedef değişince doldurulur
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class GelisimYorumHavuzu(Base):
    """F3 — 31 değişken × 5 gap aralığı = 150 satır. İçerik henüz yazılmadı (Açık Karar #2)."""
    __tablename__ = "gelisim_yorum_havuzu"
    __table_args__ = (
        CheckConstraint(
            "aralik IN ('belirgin_ustun','ustun','beklenti','altinda','belirgin_altinda')",
            name="ck_gyh_aralik",
        ),
        CheckConstraint(
            "kaynak_tipi IN ('kurs','proje','okuma','staj_deneyim','aliskanlik') OR kaynak_tipi IS NULL",
            name="ck_gyh_kaynak_tipi",
        ),
        CheckConstraint(
            "tahmini_efor IN ('kisa','orta','uzun') OR tahmini_efor IS NULL",
            name="ck_gyh_efor",
        ),
        UniqueConstraint("degisken_id", "aralik", name="uq_gyh_degisken_aralik"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    aralik: Mapped[str] = mapped_column(String, nullable=False)
    durum_tespiti: Mapped[str] = mapped_column(String, nullable=False)
    aksiyon_onerisi: Mapped[str | None] = mapped_column(String)   # yalnızca altında/belirgin_altinda'da dolu
    kaynak_tipi: Mapped[str | None] = mapped_column(String)
    tahmini_efor: Mapped[str | None] = mapped_column(String)


class GelisimKarsilastirmaYorumu(Base):
    """F5.3 — 31 değişken × 5 trend kategorisi = ek 150 satır (Açık Karar #2)."""
    __tablename__ = "gelisim_karsilastirma_yorumu"
    __table_args__ = (
        CheckConstraint(
            "trend IN ('belirgin_gelisim','gelisim','durgun','gerileme','belirgin_gerileme')",
            name="ck_gky_trend",
        ),
        UniqueConstraint("degisken_id", "trend", name="uq_gky_degisken_trend"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    trend: Mapped[str] = mapped_column(String, nullable=False)
    yorum_metni: Mapped[str] = mapped_column(String, nullable=False)


class OgrenciGelisimAksiyonDurumu(Base):
    """F4.2 — öğrencinin kendi işaretlediği aksiyon ilerlemesi (öznel sinyal)."""
    __tablename__ = "ogrenci_gelisim_aksiyon_durumu"
    __table_args__ = (
        CheckConstraint("durum IN ('planlandi','devam_ediyor','tamamlandi')", name="ck_ogad_durum"),
        UniqueConstraint("ogrenci_id", "hedef_bolum_id", "degisken_id", name="uq_ogad_ogrenci_bolum_degisken"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    hedef_bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    durum: Mapped[str] = mapped_column(String, nullable=False, default="planlandi")
    guncelleme_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================================
# AI Koçluk Asistanı (sonradan eklendi)
# ============================================================================

class OgrenciKoclukOturumu(Base):
    __tablename__ = "ogrenci_koclugu_oturumlari"
    __table_args__ = (
        CheckConstraint("durum IN ('aktif','tamamlandi')", name="ck_koclugu_oturum_durum"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    ogrenci_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ogrenciler.id"), nullable=False)
    tur_id: Mapped[int | None] = mapped_column(ForeignKey("ogrenci_degerlendirme_turu.id"))
    baslama_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    bitis_zamani: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    durum: Mapped[str] = mapped_column(String, nullable=False, default="aktif")
    # [NOT] Oturum bitince doldurulur; bir sonraki oturumda ham mesaj
    # geçmişi yerine bu kısa özet modele verilir (maliyet + kalite kontrolü
    # için — bkz. app/core/ai_koc_servisi.py)
    ozet: Mapped[str | None] = mapped_column(String)


class OgrenciKoclukMesaji(Base):
    __tablename__ = "ogrenci_koclugu_mesajlari"
    __table_args__ = (
        CheckConstraint("rol IN ('ogrenci','asistan')", name="ck_koclugu_mesaj_rol"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    oturum_id: Mapped[int] = mapped_column(ForeignKey("ogrenci_koclugu_oturumlari.id"), nullable=False)
    rol: Mapped[str] = mapped_column(String, nullable=False)
    icerik: Mapped[str] = mapped_column(String, nullable=False)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class GelisimKaynakOnerisi(Base):
    """
    [EKLENDİ — genişletilmiş kaynak havuzu] Bölümden BAĞIMSIZ, genel
    kitap/film/rol model/psikolojik yaklaşım/aktivite önerileri. Bölüme
    özel HİÇBİR satır yazılmaz — Filiz (ai_koc_servisi.py) bu genel
    önerileri öğrencinin hedef bölümüne göre YORUMLAYARAK sunar.
    """
    __tablename__ = "gelisim_kaynak_onerileri"
    __table_args__ = (
        CheckConstraint(
            "aralik IN ('belirgin_ustun','ustun','beklenti','altinda','belirgin_altinda')",
            name="ck_gko_aralik",
        ),
        CheckConstraint(
            "kaynak_tipi IN ('kitap','film','rol_model','psikolojik_yaklasim','aktivite')",
            name="ck_gko_kaynak_tipi",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    aralik: Mapped[str] = mapped_column(String, nullable=False)
    kaynak_tipi: Mapped[str] = mapped_column(String, nullable=False)
    baslik: Mapped[str] = mapped_column(String, nullable=False)
    aciklama: Mapped[str] = mapped_column(String, nullable=False)
    sira: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
