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
    degisken_adi: str
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
