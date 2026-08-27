"""
İçerik yapısı tabloları — schema.sql BÖLÜM 2
Kaynak: sistem_genel_anlatim.md B), D2, D3, A6, E4, E5
"""
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Katman(Base):
    __tablename__ = "katmanlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kod: Mapped[str] = mapped_column(String, nullable=False, unique=True)          # 'K1'..'K5'
    ad: Mapped[str] = mapped_column(String, nullable=False)
    sira: Mapped[int] = mapped_column(Integer, nullable=False)
    normalizasyon_agirligi: Mapped[float | None] = mapped_column(Numeric(5, 2))    # K5 için NULL
    kosullu_mu: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tetikleyici_katman_id: Mapped[int | None] = mapped_column(ForeignKey("katmanlar.id"))


class Degisken(Base):
    __tablename__ = "degiskenler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    katman_id: Mapped[int] = mapped_column(ForeignKey("katmanlar.id"), nullable=False)
    kod: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    ad: Mapped[str] = mapped_column(String, nullable=False)
    aciklama: Mapped[str | None] = mapped_column(String)
    sira: Mapped[int] = mapped_column(Integer, nullable=False)
    # [EKSİK/EKLENDİ] — sistem_genel_anlatim.md "Ertelenen Konular #1"
    # ("K5 sorularının şema bağlantısı henüz tasarlanmadı") burada çözüldü.
    # Belgenin kendi önerisi "sorular.dal_degisken_id" idi; bunun yerine
    # degiskenler.dal_id tercih edildi çünkü D3'teki "K5'in yeni sorularının
    # yeni DEĞİŞKENLER olarak tanımlanıp K1-K4 ile birebir aynı mekanizmayla
    # işlenmesi" ilkesine daha uygun — soru değil, değişken dala bağlanıyor;
    # soru zaten degisken_id üzerinden bunu miras alıyor. Yalnızca K5
    # katmanına ait değişkenlerde dolu olur, K1-K4'te NULL kalır.
    dal_id: Mapped[int | None] = mapped_column(ForeignKey("dallar.id"))
    # [EKSİK/EKLENDİ] Bazı değişkenlerde öğrencinin bölüm beklentisinden
    # yüksek puan alması İYİ DEĞİL — tam tersi tercih edilir (örn. P4
    # Nevrotiklik: düşük olması istenir). F2/F5 hesaplamaları bu bayrağa
    # göre gap/trend yönünü çevirir. D4 buna ihtiyaç duymaz (mutlak fark kullanır).
    ters_yonlu: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Soru(Base):
    __tablename__ = "sorular"
    __table_args__ = (
        CheckConstraint("soru_tipi IN ('likert','sjt')", name="ck_soru_tipi"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    katman_id: Mapped[int] = mapped_column(ForeignKey("katmanlar.id"), nullable=False)
    degisken_id: Mapped[int | None] = mapped_column(ForeignKey("degiskenler.id"))  # SJT'de NULL
    soru_tipi: Mapped[str] = mapped_column(String, nullable=False)
    soru_metni: Mapped[str] = mapped_column(String, nullable=False)
    ters_kodlanmis_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aktif_mi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SoruSecenegi(Base):
    __tablename__ = "soru_secenekleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    soru_id: Mapped[int] = mapped_column(ForeignKey("sorular.id"), nullable=False)
    secenek_sirasi: Mapped[int] = mapped_column(Integer, nullable=False)
    secenek_metni: Mapped[str] = mapped_column(String, nullable=False)


class SjtSecenekDegiskenAgirlik(Base):
    __tablename__ = "sjt_secenek_degisken_agirlik"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    secenek_id: Mapped[int] = mapped_column(ForeignKey("soru_secenekleri.id"), nullable=False)
    degisken_id: Mapped[int] = mapped_column(ForeignKey("degiskenler.id"), nullable=False)
    agirlik: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)


class Bolum(Base):
    __tablename__ = "bolumler"
    __table_args__ = (
        CheckConstraint("durum IN ('taslak','test_ediliyor','yayinda')", name="ck_bolum_durum"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ad: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    osym_puan_turu: Mapped[str | None] = mapped_column(String)
    kisa_aciklama: Mapped[str | None] = mapped_column(String)                       # D5 Katman-2 "Keşfet" için
    durum: Mapped[str] = mapped_column(String, nullable=False, default="taslak")
    test_notu: Mapped[str | None] = mapped_column(String)
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Dal(Base):
    __tablename__ = "dallar"
    __table_args__ = (
        CheckConstraint("dogrulama_durumu IN ('taslak','guclu_kanitli','gozden_gecirilmeli')", name="ck_dal_durum"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kod: Mapped[str] = mapped_column(String, nullable=False, unique=True)          # 'D01'..
    ad: Mapped[str] = mapped_column(String, nullable=False)
    bagli_degisken_id: Mapped[int | None] = mapped_column(ForeignKey("degiskenler.id"))
    dogrulama_durumu: Mapped[str] = mapped_column(String, nullable=False, default="taslak")
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class BolumDalEslesme(Base):
    __tablename__ = "bolum_dal_eslesme"
    __table_args__ = (
        CheckConstraint("dogrulama_durumu IN ('guclu_kanitli','gozden_gecirilmeli')", name="ck_bde_durum"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False, unique=True)
    dal_id: Mapped[int] = mapped_column(ForeignKey("dallar.id"), nullable=False)
    kaynak1_model_a_dal_id: Mapped[int | None] = mapped_column(ForeignKey("dallar.id"))
    kaynak1_model_b_dal_id: Mapped[int | None] = mapped_column(ForeignKey("dallar.id"))
    kaynak1_model_c_dal_id: Mapped[int | None] = mapped_column(ForeignKey("dallar.id"))
    kaynak2_kumeleme_dal_id: Mapped[int | None] = mapped_column(ForeignKey("dallar.id"))
    dogrulama_durumu: Mapped[str] = mapped_column(String, nullable=False, default="gozden_gecirilmeli")


class BolumKumelemeSonucu(Base):
    __tablename__ = "bolum_kumeleme_sonuclari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bolum_id: Mapped[int] = mapped_column(ForeignKey("bolumler.id"), nullable=False)
    kume_no: Mapped[int] = mapped_column(Integer, nullable=False)
    silhouette_skoru: Mapped[float | None] = mapped_column(Numeric(5, 4))
    olusturulma_zamani: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
