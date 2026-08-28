"""
Admin response şemaları.

Bu dosya, sistem_genel_anlatim.md D5/C-madde 6'daki "asla gösterilmeyenler"
kuralının İSTİSNASI — yontem_skorlari, kendall_w, agirlikli_varyans,
etkin_meslek_sayisi gibi alanlar YALNIZCA burada, admin şemalarında
bulunur. app/schemas/ogrenci.py içindeki hiçbir şema bu alanları içermez.
"""
from datetime import datetime

from pydantic import BaseModel


# --- E8 — Sistem Parametreleri ---

class SistemParametresiOut(BaseModel):
    anahtar: str
    deger: str
    aciklama: str | None
    guncelleme_zamani: datetime

    model_config = {"from_attributes": True}


class ParametreGuncelleIstek(BaseModel):
    deger: str


# --- E5 — Bölümler ---

class BolumDurumIstek(BaseModel):
    yeni_durum: str  # 'taslak' | 'test_ediliyor' | 'yayinda'
    gerekce: str


class BolumOut(BaseModel):
    id: int
    ad: str
    durum: str
    test_notu: str | None
    kisa_aciklama: str | None

    model_config = {"from_attributes": True}


class BolumAciklamaIstek(BaseModel):
    kisa_aciklama: str


# --- E7 — Model Yakınsaması / Geçerlilik (admin-only skorlar) ---

class OgrenciBolumUyumDetayOut(BaseModel):
    """Öğrenci şemasındaki (BolumSiralamaSatiri) karşılığının admin versiyonu —
    yontem_skorlari ve kendall_w BURADA VAR, öğrenci şemasında YOK."""
    ogrenci_id: str
    bolum_id: int
    tur_id: int
    toplam_uyum: float
    yontem_skorlari: dict | None
    kendall_w: float | None


# --- E1 — Kontrol Paneli ---

class KontrolPaneliOut(BaseModel):
    toplam_bolum_sayisi: int
    yayinda_bolum_sayisi: int
    tanimli_dal_sayisi: int
    toplam_ogrenci_sayisi: int
    tamamlanan_tur_sayisi: int
    yarida_birakma_orani: float | None  # None = hiç katman oturumu yok


# --- E2 — Pipeline Durumu (STUB) ---

class PipelineDurumuOut(BaseModel):
    durum: str
    aciklama: str


# --- E3 — Katmanlar & Ağırlıklar ---

class KatmanAgirligiOut(BaseModel):
    katman_kod: str
    agirlik: float
    versiyon: int
    aktif_mi: bool


class YeniAgirlikVersiyonuIstek(BaseModel):
    agirliklar: dict[str, float]  # {'K1': 20, 'K2': 15, 'K3': 25, 'K4': 40}


# --- E4 — Dallar ---

class DalOut(BaseModel):
    id: int
    kod: str
    ad: str
    dogrulama_durumu: str

    model_config = {"from_attributes": True}


class DalEkleIstek(BaseModel):
    kod: str
    ad: str
    bagli_degisken_id: int | None = None


class DalDurumIstek(BaseModel):
    yeni_durum: str  # 'taslak' | 'guclu_kanitli' | 'gozden_gecirilmeli'


# --- E6 — Soru Bankası ---

class SoruOut(BaseModel):
    id: int
    katman_kod: str
    soru_tipi: str
    soru_metni: str
    aktif_mi: bool


class SoruEkleIstek(BaseModel):
    katman_id: int
    degisken_id: int | None = None
    soru_tipi: str
    soru_metni: str
    ters_kodlanmis_mi: bool = False
    secenekler: list[str]  # sırasıyla seçenek metinleri (1'den başlayan sıra)


class SoruAktifIstek(BaseModel):
    aktif_mi: bool


# --- Yönetici Yönetimi (super_admin only) ---

class YoneticiEkleIstek(BaseModel):
    ad_soyad: str
    email: str
    sifre: str
    rol: str  # 'super_admin' | 'icerik_editoru'


class RolGuncelleIstek(BaseModel):
    yeni_rol: str


class YoneticiOut(BaseModel):
    id: str
    ad_soyad: str
    email: str
    rol: str
    olusturulma_zamani: datetime


# --- E9 — Audit Log ---

class AuditLogOut(BaseModel):
    id: int
    admin_id: str
    islem: str
    hedef_tablo: str
    hedef_id: str
    gerekce: str | None
    zaman: datetime

    model_config = {"from_attributes": True}


class OgrenciListeOut(BaseModel):
    id: str
    ad_soyad: str
    email: str
    olusturulma_zamani: datetime

    model_config = {"from_attributes": True}
