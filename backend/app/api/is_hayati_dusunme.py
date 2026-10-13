"""
[2026-10-13] İş Hayatı → "Düşünme Atölyesi" sekmesi (prefix: /ogrenci/is-hayati, modül kapısı is_hayati otomatik).

Okulda doğrudan öğretilmeyen düşünme araçları, yaparak: kök neden (5 Neden), korelasyon ≠ nedensellik, algoritmik düşünme,
ikiye bölerek arama. Her modül: günlük hayattan bir durum → öğrencinin aracı bilmeden ilk denemesi → aracın tanıtımı →
aynı araç okulda → aynı araç iş hayatında → "bu hafta dene". Zekâ testi değildir; sonuçlar yalnızca öğrencinin kendisine görünür.
Mülakat Simülasyonu'nda bir düşünme aracını kullanan sorular (mulakat_simulasyonu.json → soru.arac) seçili bölüm için listelenir.

  GET  /dusunme?bolum_id=   — araçlar (tüm içerik), öğrencinin ilerlemesi, seçili bölümün mülakatında aracı kullanan sorular
  POST /dusunme/{kod}       — modül bitti: ilk deneme ve son soruların sonucu (öğrenci + araç başına tek satır, üzerine yazılır)
  POST /dusunme-deney       — "Öğrenmeyi öğren" deneyi: 1. ölçüm (aynı oturum) ya da en erken 12 saat sonra 2. ölçüm

İçerik: app/data/dusunme_atolyesi.json.
"""
import json
from datetime import datetime, timedelta, timezone

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
    return {"araclar": [{**a, "mulakat": mulakat.get(a["kod"], [])} for a in araclar()], "ilerleme": ilerleme,
            "deney": _deney(db, o)}


# ---- "Öğrenmeyi öğren" deneyi: tekrar okuma ile kendini sınamanın aynı gün ve ertesi gün karşılaştırması ---------------------
IKINCI_OLCUM_SAAT = 12


def _deney(db: Session, o: Ogrenci) -> dict | None:
    r = db.execute(text("""SELECT sinama_listesi, olcum1, olcum1_zamani, olcum2, olcum2_zamani FROM is_hayati_ogrenme_deneyi
                            WHERE ogrenci_id = :o"""), {"o": o.id}).first()
    if r is None:
        return None
    acilis = r.olcum1_zamani + timedelta(hours=IKINCI_OLCUM_SAAT)
    simdi = datetime.now(timezone.utc)
    return {"sinama_listesi": r.sinama_listesi, "olcum1": r.olcum1, "olcum1_zamani": r.olcum1_zamani.isoformat(),
            "olcum2": r.olcum2, "olcum2_zamani": r.olcum2_zamani.isoformat() if r.olcum2_zamani else None,
            "ikinci_hazir": r.olcum2 is None and simdi >= acilis,
            "kalan_saat": None if r.olcum2 is not None or simdi >= acilis else max(1, round((acilis - simdi).total_seconds() / 3600))}


class DeneyIstek(BaseModel):
    asama: int = Field(..., ge=1, le=2)
    okuma: int = Field(..., ge=0, le=20)      # tekrar okuyarak çalışılan listeden doğru sayısı
    sinama: int = Field(..., ge=0, le=20)     # kendini sınayarak çalışılan listeden doğru sayısı
    toplam: int = Field(..., ge=1, le=20)     # liste başına öğe sayısı
    sinama_listesi: int = Field(1, ge=1, le=2)


@ogrenci_router.post("/dusunme-deney")
def deney_kaydet(istek: DeneyIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if max(istek.okuma, istek.sinama) > istek.toplam:
        raise HTTPException(400, "Geçersiz sonuç.")
    olcum = json.dumps({"okuma": istek.okuma, "sinama": istek.sinama, "toplam": istek.toplam})
    if istek.asama == 1:   # deney (yeniden) başlar: 2. ölçüm sıfırlanır
        db.execute(text("""
            INSERT INTO is_hayati_ogrenme_deneyi (ogrenci_id, sinama_listesi, olcum1) VALUES (:o, :l, CAST(:m AS JSONB))
            ON CONFLICT (ogrenci_id) DO UPDATE SET sinama_listesi = EXCLUDED.sinama_listesi, olcum1 = EXCLUDED.olcum1,
                   olcum1_zamani = now(), olcum2 = NULL, olcum2_zamani = NULL"""), {"o": o.id, "l": istek.sinama_listesi, "m": olcum})
    else:
        d = _deney(db, o)
        if d is None or not d["ikinci_hazir"]:
            raise HTTPException(400, "İkinci ölçüm, ilk ölçümden en az 12 saat sonra yapılabilir.")
        db.execute(text("UPDATE is_hayati_ogrenme_deneyi SET olcum2 = CAST(:m AS JSONB), olcum2_zamani = now() WHERE ogrenci_id = :o"),
                   {"o": o.id, "m": olcum})
    db.commit()
    return _deney(db, o)


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
