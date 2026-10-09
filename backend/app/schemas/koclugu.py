"""Bölüm F — Koçluk modülü request/response şemaları."""
from pydantic import BaseModel


class HedefSecIstek(BaseModel):
    bolum_id: int
    onay: bool = False


class AktifHedefOut(BaseModel):
    bolum_id: int
    bolum_adi: str
    secim_zamani: str


class GapSatiriOut(BaseModel):
    degisken_id: int
    degisken_kod: str | None = None
    degisken_adi: str
    katman_kod: str | None = None
    katman_adi: str | None = None
    # [2026-10-03] Ekrandaki karşılaştırma bu GÖRELİ değerlerle çizilir (katman içinde 50 = profilinin ortası).
    # Kategori de aynı ölçekten hesaplandığı için grafik ile "güçlü/gelişime açık" etiketi çelişmez.
    ogrenci_goreli: float | None = None
    bolum_goreli: float | None = None
    aksiyon_durumu: str | None = None   # planlandi | devam_ediyor | tamamlandi | None
    nedir: str | None = None            # [2026-10-03] özelliğin öğrenci dilinde açıklaması
    ogrenci_puan: float
    bolum_beklenen: float
    gap: float
    kategori: str
    oncelik_skoru: float
    durum_tespiti: str | None
    aksiyon_onerisi: str | None
    kaynak_tipi: str | None
    tahmini_efor: str | None


class YolHaritasiOut(BaseModel):
    simdi: list[GapSatiriOut]
    bu_donem: list[GapSatiriOut]
    uzun_vadede: list[GapSatiriOut]
    efor_belirsiz: list[GapSatiriOut]


class AksiyonDurumIstek(BaseModel):
    durum: str  # 'planlandi' | 'devam_ediyor' | 'tamamlandi'


class KarsilastirmaSatiriOut(BaseModel):
    degisken_id: int
    degisken_adi: str
    eski_puan: float
    yeni_puan: float
    degisim: float
    trend: str
    yorum_metni: str | None


# ============================= [2026-10-03] Detaylı gelişim planı ============================= #

class PlanAdimiOut(BaseModel):
    kod: str
    degisken_kod: str
    degisken_adi: str
    asama: str
    baslik: str
    aciklama: str
    tur: str
    tur_etiket: str
    sure: str
    olcut: str
    durum: str | None = None
    nasil: list[str] = []        # [2026-10-09] "Nasıl yaparsın?" — adım adım
    kontrol: list[str] = []      # "Nasıl anlarsın?" — kontrol listesi
    ipucu: str | None = None


class PlanAsamasiOut(BaseModel):
    kod: str
    baslik: str
    alt: str
    adimlar: list[PlanAdimiOut]
    tamamlanan: int
    toplam: int
    once_oncekine_odaklan: bool


class OdakAlaniOut(BaseModel):
    degisken_id: int
    degisken_kod: str
    degisken_adi: str
    kategori: str
    oncelik_sirasi: int
    nedir: str
    neden_onemli: str
    durum_tespiti: str | None = None


class GucluYonOut(BaseModel):
    degisken_id: int
    degisken_kod: str
    degisken_adi: str
    kategori: str
    nedir: str
    neden_onemli: str
    adimlar: list[PlanAdimiOut]


class SonrakiAlanOut(BaseModel):
    degisken_id: int
    degisken_adi: str
    kategori: str


class PlanIlerlemeOut(BaseModel):
    toplam: int
    tamamlanan: int
    devam_eden: int


class GelisimPlaniOut(BaseModel):
    hedef_bolum_adi: str
    odak_alanlari: list[OdakAlaniOut]
    sonraki_alanlar: list[SonrakiAlanOut]
    asamalar: list[PlanAsamasiOut]
    guclu_yonler: list[GucluYonOut]
    siradaki_adim: PlanAdimiOut | None = None
    ilerleme: PlanIlerlemeOut


class AdimDurumIstek(BaseModel):
    durum: str | None = None   # 'planlandi' | 'devam_ediyor' | 'tamamlandi' | null (işareti kaldır)
