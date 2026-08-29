"""
Öğrenci katman akışı (D2) response/request şemaları.

KRİTİK KURAL (sistem_genel_anlatim.md D5, Bölüm C madde 6): Bu dosyadaki
şemalar öğrenci API uç noktalarında kullanılır — model bilgisi, benzerlik/
yakınsama skorları, agirlikli_varyans, etkin_meslek_sayisi, yontem_skorlari,
Kendall's W gibi alanlar burada YOK ve asla eklenmemeli. Bu alanlar
YALNIZCA app/schemas/admin.py içindeki (henüz yazılmadı) ayrı şemalarda
bulunabilir.
"""
from datetime import datetime, date
from pydantic import BaseModel


class KatmanOut(BaseModel):
    id: int
    kod: str
    ad: str
    sira: int
    normalizasyon_agirligi: float | None
    kosullu_mu: bool
    durum: str  # 'baslamadi' | 'devam_ediyor' | 'tamamlandi' — öğrencinin bu katmandaki ilerlemesi

    model_config = {"from_attributes": True}


class SecenekOut(BaseModel):
    id: int
    secenek_sirasi: int
    secenek_metni: str

    model_config = {"from_attributes": True}


class SoruOut(BaseModel):
    id: int
    soru_tipi: str
    soru_metni: str
    secenekler: list[SecenekOut] = []

    model_config = {"from_attributes": True}


class KatmanBaslatCevap(BaseModel):
    tur_id: int
    katman_oturum_id: int
    sorular: list[SoruOut]


class CevapIstek(BaseModel):
    soru_id: int
    secenek_id: int


class KatmanSonucSatiri(BaseModel):
    degisken_id: int
    degisken_adi: str
    puan: float
    # --- Gelişim yorumu (sonradan eklendi, opsiyonel — geriye dönük uyumlu) ---
    durum_tespiti: str | None = None
    aksiyon_onerisi: str | None = None
    kaynak_tipi: str | None = None
    tahmini_efor: str | None = None


class KatmanTamamlamaCevap(BaseModel):
    katman_kodu: str
    sonuclar: list[KatmanSonucSatiri]
    tum_katmanlar_tamamlandi_mi: bool


class TurDurumOut(BaseModel):
    tur_id: int
    tur_no: int
    durum: str
    baslama_zamani: datetime
    tamamlanma_zamani: datetime | None

    model_config = {"from_attributes": True}


# --- Genel Durum Özeti (sidebar/ilerleme göstergesi için) ---

class DurumOzetiOut(BaseModel):
    tur_no: int | None                      # hiç tur başlamadıysa None
    tur_tamamlandi_mi: bool
    tamamlanan_katman_sayisi: int
    toplam_ana_katman_sayisi: int
    k5_acilan_dal_sayisi: int
    k5_tamamlanan_dal_sayisi: int
    sonraki_tur_tarihi: str | None          # ISO tarih, tur tamamlandıysa dolu


# --- D5 Katman 2 — Keşfet ---

class KesfetSonucOut(BaseModel):
    bolum_id: int
    bolum_adi: str
    kisa_aciklama: str | None
    toplam_uyum: float | None  # None = öğrenci henüz K1-K4'ü tamamlamadı
    katman_ortalamalari: dict[str, float]

class BolumSiralamaSatiri(BaseModel):
    """
    D5 — yalnızca öğrenciye gösterilenler. yontem_skorlari ve kendall_w
    BİLİNÇLİ OLARAK burada YOK (sistem_genel_anlatim.md D5, "asla
    gösterilmeyenler" listesi) — bu alanlar yalnızca admin şemasında olmalı.
    """
    bolum_id: int
    bolum_adi: str
    toplam_uyum: float

    model_config = {"from_attributes": True}

class DalAdayOut(BaseModel):
    dal_kodu: str
    dal_adi: str
    puan: float


class K5DurumOut(BaseModel):
    esik: float
    acilan: list[DalAdayOut]
    ilgi_gosterilen: list[DalAdayOut]


class DalBaslatCevap(BaseModel):
    dal_oturum_id: int
    sorular: list[SoruOut]


class DalTamamlamaCevap(BaseModel):
    dal_kodu: str
    sonuclar: list[KatmanSonucSatiri]


# ============================================================================
# Profil (sonradan eklendi)
# ============================================================================
# NOT (hukuki): dogum_tarihi/cinsiyet KVKK açısından hassas veri sayılabilir,
# veli onayı akışı ayrıca kurulmalıdır — bu şema yalnızca teknik alt yapıdır.

class ProfilOut(BaseModel):
    ad_soyad: str
    email: str
    okul: str | None
    sinif: str | None
    dogum_tarihi: date | None
    cinsiyet: str | None
    ilgi_alanlari: str | None
    hedef_universite: str | None
    hedef_meslek_id: int | None
    hedef_meslek_adi: str | None  # join ile doldurulur, hedef_meslek_id NULL ise None
    profil_foto_base64: str | None

    model_config = {"from_attributes": True}


class ProfilGuncelleIstek(BaseModel):
    ad_soyad: str | None = None
    okul: str | None = None
    sinif: str | None = None
    dogum_tarihi: date | None = None
    cinsiyet: str | None = None  # 'kadin' | 'erkek' | 'belirtmek_istemiyorum' | 'diger'
    ilgi_alanlari: str | None = None
    hedef_universite: str | None = None
    hedef_meslek_id: int | None = None


class SifreDegistirIstek(BaseModel):
    eski_sifre: str
    yeni_sifre: str  # min 8 karakter — router'da doğrulanır


class ProfilFotoIstek(BaseModel):
    foto_base64: str  # "data:image/png;base64,..." formatında, tam data URI


class MeslekAramaSonucu(BaseModel):
    id: int
    ad: str

    model_config = {"from_attributes": True}


class KatmanGecmisSonucOut(BaseModel):
    """Bir katman daha önce tamamlanmışsa, sonucunu tekrar sorgulamak için."""
    katman_kodu: str
    tamamlandi_mi: bool
    sonuclar: list[KatmanSonucSatiri]


class BolumOrnekMeslekOut(BaseModel):
    """Keşfet ekranında bir bölümün altında gösterilecek örnek meslekler —
    a2_meslek_bolum_eslesme_aday.csv'den (3 modelin ortalaması) türetildi."""
    meslek_adi: str
    benzerlik_skoru: float
