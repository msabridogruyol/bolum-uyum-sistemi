# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı → 'gercek' sekmesi (Beklenti ve Gerçek).

  GET  /ogrenci/is-hayati/gercek/{bolum_id}   — karşılaştırılabilir gerçek göstergeler + öğrencinin önceki denemeleri
  POST /ogrenci/is-hayati/gercek/{bolum_id}   — {tahminler: {...}} kaydeder; gerçek verinin o anki özetini de saklar

Tahmin alanları (hepsi isteğe bağlı; yalnızca gerçek verisi olan göstergeler sorulur):
  istihdam_orani (0–100, %), is_bulma_suresi_ay (0–120), alan_uyum_orani (0–100, %), ilk_net_maas (TL, 0–10.000.000)
Hiçbir değer uydurulmaz: gösterge verisi yoksa `deger: null` ve `veri_yok: true` döner. Kazanç TL değil yalnızca grup ise grup döner.
Tablo: is_hayati_beklentiler (göç 0055_is_hayati_beklenti). Bağlama: app/api/is_hayati.py otomatik ekler.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import is_hayati_servisi as ihs
from app.core.database import get_db
from app.models import Ogrenci

ogrenci_router = APIRouter()

SINIRLAR = {"istihdam_orani": (0, 100), "is_bulma_suresi_ay": (0, 120), "alan_uyum_orani": (0, 100), "ilk_net_maas": (0, 10_000_000)}


class TahminGirdi(BaseModel):
    tahminler: dict[str, float | None] = Field(default_factory=dict)


def _yil_asgari_net(db: Session, yil) -> dict | None:
    """Veri yılındaki asgari ücretin (net) yıl içi ortalaması — dönemler ay ağırlıklı (yürürlük tarihine göre)."""
    if not yil:
        return None
    rows = db.execute(text("SELECT donem, net, brut, yururluk_tarihi, kaynak FROM asgari_ucret "
                           "WHERE EXTRACT(YEAR FROM yururluk_tarihi) = :y ORDER BY yururluk_tarihi"), {"y": int(yil)}).mappings().all()
    if not rows:
        return None
    aylar = [r["yururluk_tarihi"].month for r in rows] + [13]
    toplam = sum(float(r["net"]) * (aylar[i + 1] - aylar[i]) for i, r in enumerate(rows))
    ay = 13 - aylar[0]
    return {"yil": int(yil), "net_ortalama": round(toplam / ay, 2), "donemler": [r["donem"] for r in rows],
            "kaynak": "; ".join(dict.fromkeys(r["kaynak"] for r in rows if r["kaynak"]))}


def gercek_ozet(db: Session, bolum_id: int) -> dict | None:
    v = ihs.bolum_verisi(db, bolum_id)
    if v is None:
        return None
    i = v["istihdam"] or {}
    kaynak = {"kaynak": i.get("kaynak"), "yil": i.get("veri_yili"), "program": i.get("program_adi_kaynak"), "tahmin": False}

    def gosterge(kod, ad, birim):
        d = i.get(kod)
        return {"kod": kod, "ad": ad, "birim": birim, "deger": d, "veri_yok": d is None, **kaynak}

    gostergeler = [gosterge("istihdam_orani", "Mezunların kayıtlı çalışma oranı", "%"),
                   gosterge("is_bulma_suresi_ay", "İlk işi bulma süresi", "ay"),
                   gosterge("alan_uyum_orani", "Alanında çalışma oranı", "%")]

    asgari = v["asgari"]
    kazanc = {"kod": "ilk_net_maas", "ad": "İlk net maaş", "birim": "TL", "asgari": asgari, **kaynak,
              "deger": i.get("kazanc_tl"), "kazanc_grubu": i.get("kazanc_grubu"), "kazanc_grubu_ad": i.get("kazanc_grubu_ad"),
              "yil_asgari": None, "asgari_kat": None, "meslek_tahmini": None}
    if kazanc["deger"] is not None:
        ya = _yil_asgari_net(db, i.get("veri_yili"))
        kazanc["yil_asgari"] = ya
        if ya and ya["net_ortalama"]:
            kazanc["asgari_kat"] = round(kazanc["deger"] / ya["net_ortalama"], 2)
    # Bölüm mesleklerinin TÜİK meslek grubu ortalamasından güncellenmiş TAHMİNİ net kazancı (ilk maaş değil, ortalama)
    tah = [m for m in v["kazanc"]["meslekler"] if m.get("guncel_tahmin_net_tl")]
    if tah:
        degerler = sorted(m["guncel_tahmin_net_tl"] for m in tah)
        kazanc["meslek_tahmini"] = {
            "min": degerler[0], "max": degerler[-1], "meslek_sayisi": len(tah), "tahmin": True,
            "veri_yili": tah[0].get("veri_yili"), "kaynak": tah[0].get("kaynak"), "donem": tah[0].get("guncel_donem"),
            "aciklama": v["kazanc"]["aciklama"]}
    kazanc["veri_yok"] = kazanc["deger"] is None and not kazanc["kazanc_grubu"] and not kazanc["meslek_tahmini"]
    return {"bolum": v["bolum"], "gostergeler": gostergeler, "kazanc": kazanc, "asgari": asgari,
            "istihdam_var": v["istihdam"] is not None}


def _denemeler(db: Session, ogrenci_id, bolum_id: int) -> list[dict]:
    rows = db.execute(text("SELECT id, tahminler, gercek, zaman FROM is_hayati_beklentiler WHERE ogrenci_id = :o AND bolum_id = :b "
                           "ORDER BY zaman DESC LIMIT 10"), {"o": ogrenci_id, "b": bolum_id}).mappings().all()
    out = []
    for r in rows:
        t = r["tahminler"] if isinstance(r["tahminler"], dict) else json.loads(r["tahminler"] or "{}")
        g = r["gercek"] if isinstance(r["gercek"], dict) or r["gercek"] is None else json.loads(r["gercek"])
        out.append({"id": r["id"], "tahminler": t, "gercek": g, "zaman": r["zaman"].isoformat()})
    return out


TOPLULUK_EN_AZ = 5   # en az bu kadar öğrencinin tahmini yoksa topluluk ortancası gösterilmez (gizlilik + anlamlılık)


def _topluluk(db: Session, bolum_id: int) -> dict:
    """Bu bölüm için tahmin yapan öğrencilerin (her öğrencinin İLK denemesi) ortancası — 'çoğu öğrenci …' cümlesinin tek dayanağı."""
    out = {}
    for kod in SINIRLAR:
        r = db.execute(text("""WITH ilk AS (SELECT DISTINCT ON (ogrenci_id) (tahminler ->> :k)::numeric AS v
                                              FROM is_hayati_beklentiler WHERE bolum_id = :b AND tahminler ? :k
                                             ORDER BY ogrenci_id, zaman)
                               SELECT COUNT(*) AS n, percentile_cont(0.5) WITHIN GROUP (ORDER BY v) AS ortanca FROM ilk"""),
                       {"k": kod, "b": bolum_id}).first()
        if r and r.n >= TOPLULUK_EN_AZ:
            out[kod] = {"n": r.n, "ortanca": round(float(r.ortanca), 1)}
    return out


@ogrenci_router.get("/gercek/{bolum_id}")
def gercek_getir(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    g = gercek_ozet(db, bolum_id)
    if g is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    return {**g, "denemeler": _denemeler(db, o.id, bolum_id), "topluluk": _topluluk(db, bolum_id)}


@ogrenci_router.post("/gercek/{bolum_id}")
def gercek_kaydet(bolum_id: int, girdi: TahminGirdi, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    g = gercek_ozet(db, bolum_id)
    if g is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    temiz = {}
    # Yalnızca karşılaştırılabilecek göstergeler kaydedilir (verisi olmayan göstergede tahmin sorulmaz)
    karsilastirilir = {x["kod"] for x in g["gostergeler"] if not x["veri_yok"]}
    if not g["kazanc"]["veri_yok"]:
        karsilastirilir.add("ilk_net_maas")
    for k, v in (girdi.tahminler or {}).items():
        if k not in SINIRLAR or v is None or k not in karsilastirilir:
            continue
        lo, hi = SINIRLAR[k]
        if not (lo <= float(v) <= hi):
            raise HTTPException(422, f"'{k}' {lo}–{hi} aralığında olmalı.")
        temiz[k] = round(float(v), 2)
    if not temiz:
        raise HTTPException(422, "En az bir tahmin gir.")
    ozet = {"gostergeler": {x["kod"]: x["deger"] for x in g["gostergeler"]},
            "kazanc_tl": g["kazanc"]["deger"], "kazanc_grubu": g["kazanc"]["kazanc_grubu"], "asgari_kat": g["kazanc"]["asgari_kat"],
            "asgari_net": (g["asgari"] or {}).get("net"), "asgari_donem": (g["asgari"] or {}).get("donem"),
            "kaynak": g["kazanc"]["kaynak"], "yil": g["kazanc"]["yil"]}
    db.execute(text("INSERT INTO is_hayati_beklentiler (ogrenci_id, bolum_id, tahminler, gercek) "
                    "VALUES (:o, :b, CAST(:t AS JSONB), CAST(:g AS JSONB))"),
               {"o": o.id, "b": bolum_id, "t": json.dumps(temiz), "g": json.dumps(ozet, default=str)})
    db.commit()
    return {**g, "denemeler": _denemeler(db, o.id, bolum_id), "topluluk": _topluluk(db, bolum_id)}
