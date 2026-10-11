# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı → "Okulda Öğretilmeyenler" sekmesi (prefix: /ogrenci/is-hayati, modül kapısı is_hayati otomatik).

Kısa dersler (3–6 kart + 3–5 soruluk mini sınav + kaynaklar). Hukuki/sayısal bilgiler resmî kaynaktan kontrol edilmiştir;
her dersin "son_kontrol" tarihi vardır. Bordro dersindeki tutar örneği UYDURULMAZ: asgari_ucret tablosundaki güncel
dönemden hesaplanır ve yalnızca hesap tablodaki net tutarla tutarlıysa gösterilir.

  GET  /dersler                 — ders listesi (kartlar + sorular, doğru cevaplar hariç) + ilerleme + bordro örneği
  POST /dersler/{kod}/sinav     — cevaplar → puan, doğru cevaplar ve açıklamalar; en iyi puan saklanır
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import is_hayati_pratik as ihp
from app.core import is_hayati_servisi as ihs
from app.core.database import get_db
from app.models import Ogrenci

ogrenci_router = APIRouter()
DOSYA = "is_hayati_dersler.json"

# Asgari ücret bordrosunda işçiden yapılan kesinti oranları (SGK primi işçi payı + işsizlik sigortası işçi payı).
# Kaynak: 5510 sayılı Kanun (SGK) ve 4447 sayılı İşsizlik Sigortası Kanunu oranları; 2026 bordro parametreleriyle kontrol edildi.
SGK_ISCI = 0.14
ISSIZLIK_ISCI = 0.01


def bordro_ornegi(asgari: dict | None) -> dict | None:
    if not asgari or not asgari.get("brut") or not asgari.get("net"):
        return None
    brut = asgari["brut"]
    sgk, iss = round(brut * SGK_ISCI, 2), round(brut * ISSIZLIK_ISCI, 2)
    net = round(brut - sgk - iss, 2)
    tutarli = abs(net - asgari["net"]) < 1
    return {"donem": asgari["donem"], "brut": brut, "sgk_isci": sgk if tutarli else None, "issizlik_isci": iss if tutarli else None,
            "gelir_vergisi": 0 if tutarli else None, "damga_vergisi": 0 if tutarli else None, "net": asgari["net"],
            "hesap_tutarli": tutarli, "kaynak": asgari.get("kaynak")}


def _dersler() -> list[dict]:
    return ihp.veri(DOSYA).get("dersler") or []


@ogrenci_router.get("/dersler")
def dersler(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    ilerleme = {r.ders_kod: {"puan": r.sinav_puani, "toplam": r.sinav_toplam, "deneme": r.deneme,
                             "zaman": r.tamamlanma_zamani.isoformat()} for r in db.execute(text(
        "SELECT ders_kod, sinav_puani, sinav_toplam, deneme, tamamlanma_zamani FROM is_hayati_ders_ilerleme WHERE ogrenci_id = :o"),
        {"o": o.id}).all()}
    liste = []
    for d in _dersler():
        liste.append({**{k: v for k, v in d.items() if k != "sinav"},
                      "sinav": [{"soru": s["soru"], "secenekler": s["secenekler"]} for s in d.get("sinav") or []],
                      "ilerleme": ilerleme.get(d["kod"])})
    return {"dersler": liste, "bordro": bordro_ornegi(ihs.guncel_asgari(db)),
            "not": ihp.veri(DOSYA).get("genel_not"), "tamamlanan": sum(1 for d in liste if d["ilerleme"])}


class SinavIstek(BaseModel):
    cevaplar: list[int | None] = Field(default_factory=list, max_length=10)


@ogrenci_router.post("/dersler/{kod}/sinav")
def sinav(kod: str, istek: SinavIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    d = next((x for x in _dersler() if x["kod"] == kod), None)
    if d is None:
        raise HTTPException(404, "Ders bulunamadı.")
    sorular = d.get("sinav") or []
    if len(istek.cevaplar) != len(sorular):
        raise HTTPException(400, "Tüm soruları cevapla.")
    sonuc = [{"dogru": s["dogru"], "dogru_mu": c == s["dogru"], "aciklama": s.get("aciklama")} for s, c in zip(sorular, istek.cevaplar)]
    puan = sum(1 for x in sonuc if x["dogru_mu"])
    db.execute(text("""
        INSERT INTO is_hayati_ders_ilerleme (ogrenci_id, ders_kod, sinav_puani, sinav_toplam, deneme)
        VALUES (:o, :k, :p, :t, 1)
        ON CONFLICT (ogrenci_id, ders_kod) DO UPDATE SET
            sinav_puani = GREATEST(COALESCE(is_hayati_ders_ilerleme.sinav_puani, 0), EXCLUDED.sinav_puani),
            sinav_toplam = EXCLUDED.sinav_toplam, deneme = is_hayati_ders_ilerleme.deneme + 1,
            tamamlanma_zamani = now()
    """), {"o": o.id, "k": kod, "p": puan, "t": len(sorular)})
    db.commit()
    return {"puan": puan, "toplam": len(sorular), "sonuc": sonuc}
