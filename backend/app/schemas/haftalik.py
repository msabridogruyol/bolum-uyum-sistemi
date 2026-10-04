"""[2026-10-04] Haftalık görevler, seri ve Filiz seviyesi — API şemaları."""
from pydantic import BaseModel


class HaftalikGorevOut(BaseModel):
    id: int
    sira: int
    tur: str
    baslik: str
    aciklama: str | None = None
    link: str | None = None
    durum: str
    elle_tamamlanabilir: bool
    yanit: dict | None = None
    tamamlanma_zamani: str | None = None


class SeriOut(BaseModel):
    guncel: int
    en_uzun: int
    toplam_tamamlanan: int


class GecmisHaftaOut(BaseModel):
    hafta_baslangic: str
    tamamlanan: int
    toplam: int
    seriye_sayildi: bool


class SeviyeOut(BaseModel):
    no: int
    ad: str
    ikon: str
    puan: int
    sonraki_ad: str | None = None
    sonraki_esik: int | None = None
    ilerleme_yuzde: int


class YansitmaSorusuOut(BaseModel):
    anahtar: str
    soru: str


class HaftalikOzetOut(BaseModel):
    hafta_baslangic: str
    hafta_bitis: str
    kalan_gun: int
    gorevler: list[HaftalikGorevOut]
    tamamlanan: int
    toplam: int
    seri_esigi: int
    seri: SeriOut
    gecmis: list[GecmisHaftaOut]
    seviye: SeviyeOut
    yansitma_sorulari: list[YansitmaSorusuOut]


class GorevTamamlaIstek(BaseModel):
    yanit: dict | None = None
