"""
[2026-10-13] İş Hayatı → "Düşünme Atölyesi" sekmesi (prefix: /ogrenci/is-hayati, modül kapısı is_hayati otomatik).

Okulda doğrudan öğretilmeyen düşünme araçları, yaparak: kök neden (5 Neden), korelasyon ≠ nedensellik, algoritmik düşünme,
ikiye bölerek arama. Her modül: günlük hayattan bir durum → öğrencinin aracı bilmeden ilk denemesi → aracın tanıtımı →
aynı araç okulda → aynı araç iş hayatında → "bu hafta dene". Zekâ testi değildir; sonuçlar yalnızca öğrencinin kendisine görünür.
Mülakat Simülasyonu'nda bir düşünme aracını kullanan sorular (mulakat_simulasyonu.json → soru.arac) seçili bölüm için listelenir.

  GET  /dusunme?bolum_id=   — araçlar (tüm içerik), öğrencinin ilerlemesi, seçili bölümün mülakatında aracı kullanan sorular
  POST /dusunme/{kod}       — modül bitti: ilk deneme ve son soruların sonucu (öğrenci + araç başına tek satır, üzerine yazılır)

İçerik: app/data/dusunme_atolyesi.json.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import is_hayati_pratik as ihp
from app.core.database import get_db
from app.models import Ogrenci

ogrenci_router = APIRouter()
DOSYA = "dusunme_atolyesi.json"


def araclar() -> list[dict]:
    return ihp.veri(DOSYA).get("araclar") or []


def arac_ozeti(kod: str | None) -> dict | None:
    """Mülakat Simülasyonu'nda soru etiketi için: {kod, ad, ikon}."""
    a = next((x for x in araclar() if x.get("kod") == kod), None) if kod else None
    return {"kod": a["kod"], "ad": a["ad"], "ikon": a.get("ikon")} if a else None


def _mulakat_sorulari(db: Session, bolum_id: int | None) -> dict[str, list[dict]]:
    if not bolum_id:
        return {}
    ad, _m = ihp.bolum_meslekleri(db, bolum_id)
    ic = ((ihp.veri("mulakat_simulasyonu.json").get("bolumler") or {}).get(" ".join((ad or "").split())) or {})
    sonuc: dict[str, list[dict]] = {}
    for q in ic.get("sorular") or []:
        if q.get("arac"):
            sonuc.setdefault(q["arac"], []).append({"konu": q.get("konu"), "soru": q.get("soru")})
    return sonuc


@ogrenci_router.get("/dusunme")
def dusunme(bolum_id: int | None = Query(None), db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    ilerleme = {r.arac_kod: {"ilk": r.ilk, "son": r.son, "deneme": r.deneme, "zaman": r.tamamlanma_zamani.isoformat()}
                for r in db.execute(text("""SELECT arac_kod, ilk, son, deneme, tamamlanma_zamani FROM is_hayati_dusunme
                                             WHERE ogrenci_id = :o"""), {"o": o.id}).all()}
    mulakat = _mulakat_sorulari(db, bolum_id)
    return {"araclar": [{**a, "mulakat": mulakat.get(a["kod"], [])} for a in araclar()], "ilerleme": ilerleme}


class DusunmeIstek(BaseModel):
    ilk_dogru: int = Field(0, ge=0, le=50)
    ilk_toplam: int = Field(0, ge=0, le=50)
    okulda: bool | None = None
    iste: bool | None = None


@ogrenci_router.post("/dusunme/{kod}")
def dusunme_bitir(kod: str, istek: DusunmeIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if not any(a.get("kod") == kod for a in araclar()):
        raise HTTPException(404, "Bu düşünme aracı bulunamadı.")
    if istek.ilk_dogru > istek.ilk_toplam:
        raise HTTPException(400, "Geçersiz sonuç.")
    ilk = {"dogru": istek.ilk_dogru, "toplam": istek.ilk_toplam}
    son = {"okulda": istek.okulda, "iste": istek.iste}
    r = db.execute(text("""
        INSERT INTO is_hayati_dusunme (ogrenci_id, arac_kod, ilk, son) VALUES (:o, :k, CAST(:i AS JSONB), CAST(:s AS JSONB))
        ON CONFLICT (ogrenci_id, arac_kod) DO UPDATE SET ilk = EXCLUDED.ilk, son = EXCLUDED.son,
               deneme = is_hayati_dusunme.deneme + 1, tamamlanma_zamani = now()
        RETURNING deneme"""), {"o": o.id, "k": kod, "i": json.dumps(ilk), "s": json.dumps(son)}).first()
    db.commit()
    return {"kod": kod, "ilk": ilk, "son": son, "deneme": r.deneme}
