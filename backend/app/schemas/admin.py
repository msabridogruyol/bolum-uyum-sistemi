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


class BolumTopluAciklamaSatiri(BaseModel):
    ad: str
    kisa_aciklama: str


class BolumTopluAciklamaIstek(BaseModel):
    satirlar: list[BolumTopluAciklamaSatiri]


class BolumTopluAciklamaSonucu(BaseModel):
    guncellenen: int
    eslesmeyenler: list[str]


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
    degisken_kod: str | None = None
    degisken_adi: str | None = None
    soru_tipi: str
    soru_metni: str
    aktif_mi: bool


# --- A7 — Soru Geçerlilik Testi (sonradan eklendi) ---

class SoruGecerlilikSonucuGiris(BaseModel):
    soru_id: int
    gercek_degisken_kod: str
    model_a_tahmin: str
    model_a_dogru: bool
    model_a_benzerlik: float
    model_b_tahmin: str
    model_b_dogru: bool
    model_b_benzerlik: float
    model_c_tahmin: str
    model_c_dogru: bool
    model_c_benzerlik: float


class SoruGecerlilikYuklemeIstek(BaseModel):
    sonuclar: list[SoruGecerlilikSonucuGiris]


class SoruGecerlilikSonucuOut(BaseModel):
    soru_id: int
    soru_metni: str
    katman_kod: str
    gercek_degisken_kod: str
    model_a_tahmin: str
    model_a_dogru: bool
    model_b_tahmin: str
    model_b_dogru: bool
    model_c_tahmin: str
    model_c_dogru: bool
    kac_model_dogru: int
    ortalama_benzerlik: float
    test_zamani: datetime


class SoruGecerlilikOzetOut(BaseModel):
    toplam_soru: int
    tam_dogru: int          # 3/3 model doğru
    kismi_dogru: int        # 1-2/3 model doğru
    hic_dogru_degil: int    # 0/3 model doğru
    sonuclar: list[SoruGecerlilikSonucuOut]


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


class OgrenciDetayOut(BaseModel):
    id: str
    ad_soyad: str
    email: str
    okul: str | None
    hedef_bolum_adi: str | None
    hedef_bolum_uyum_orani: float | None
    olusturulma_zamani: datetime


class OkulSayisiOut(BaseModel):
    okul: str
    sayi: int


class HedefBolumSayisiOut(BaseModel):
    bolum_adi: str
    sayi: int


class OgrenciIstatistikleriOut(BaseModel):
    toplam_ogrenci: int
    hedefi_olan_ogrenci: int
    ortalama_hedef_uyum_orani: float | None
    en_cok_okul: list[OkulSayisiOut]
    en_cok_hedeflenen_bolum: list[HedefBolumSayisiOut]
    ogrenciler: list[OgrenciDetayOut]


# --- Detaylı/Kademeli İstatistikler (sonradan eklendi) ---

class BolumKademeIstatistigiOut(BaseModel):
    bolum_id: int
    bolum_adi: str
    hedefleyen_sayisi: int
    yetiyor_sayisi: int       # uyum >= 70
    sinirda_sayisi: int       # 40 <= uyum < 70
    yetmiyor_sayisi: int      # uyum < 40
    henuz_hesaplanmadi_sayisi: int  # K1-K4 bitmediği için uyum yok
    ortalama_uyum: float | None


class OkulKirilimOut(BaseModel):
    okul: str
    ogrenci_sayisi: int
    hedefi_olan_sayisi: int
    ortalama_uyum: float | None


class SinifKirilimOut(BaseModel):
    sinif: str
    ogrenci_sayisi: int
    hedefi_olan_sayisi: int
    ortalama_uyum: float | None


class DetayliIstatistiklerOut(BaseModel):
    bolumler: list[BolumKademeIstatistigiOut]
    okullar: list[OkulKirilimOut]
    siniflar: list[SinifKirilimOut]


# --- Pipeline Sonuçları (sonradan eklendi) ---
# Bilgisayarınızda çalışan pipeline'ın çıktısını (CSV) admin panelinden
# yükleyip, canlıya yansımadan ÖNCE önizleyip onaylamanızı sağlar.

class PipelineTaslakSatiri(BaseModel):
    bolum_adi: str
    degisken_kod: str
    agirlik_degeri: float
    yakinsama_skoru: float | None = None
    agirlikli_varyans: float | None = None
    etkin_meslek_sayisi: int | None = None


class PipelineYuklemeIstek(BaseModel):
    satirlar: list[PipelineTaslakSatiri]


class PipelineBolumAralikOut(BaseModel):
    bolum_adi: str
    min_deger: float
    max_deger: float
    aralik: float


class PipelineYuklemeSonucu(BaseModel):
    yukleme_grubu: str
    toplam_satir: int
    eslesen_satir: int
    eslesmeyen_satirlar: list[str]  # "bolum_adi / degisken_kod" formatında, teşhis için
    bolum_sayisi: int
    ortalama_aralik: float
    en_duz_10: list[PipelineBolumAralikOut]


class PipelineTaslakGrubuOut(BaseModel):
    yukleme_grubu: str
    yuklenme_zamani: datetime
    toplam_satir: int
    bolum_sayisi: int
    ortalama_aralik: float
    durum: str


# --- Kullanım İstatistikleri (sonradan eklendi) ---

class GunlukZiyaretOut(BaseModel):
    tarih: str  # ISO tarih (YYYY-MM-DD)
    sayi: int


class SayfaZiyaretOut(BaseModel):
    yol: str
    sayi: int


class KullanimIstatistikleriOut(BaseModel):
    bugun_toplam: int
    son_7_gun_toplam: int
    ogrenci_ziyaret: int
    admin_ziyaret: int
    anonim_ziyaret: int
    gunluk_dagilim: list[GunlukZiyaretOut]  # son 7 gün
    en_cok_ziyaret_edilen: list[SayfaZiyaretOut]  # ilk 5
