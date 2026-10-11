# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı → 'yol' sekmesi (Mesleğe Giden Yol).

  GET /ogrenci/is-hayati/yol/{bolum_id}

İçerik: app/data/meslege_yol.json (anahtar: bolumler.ad). Birleştirme: alan şablonu (17 K5 üst alanı) → düzenlenmiş meslek
şablonu (öğretmenlik, sağlık meslek mensubu, SMMM, TMMOB oda kaydı) → bölüme özgü kayıt. '{SURE}' bölümün öğrenim süresiyle
doldurulur. Ek olarak bölüm detayındaki meslek kartlarının "nasıl olunur" metinleri döner (içerik ekibinin yazdığı metinler).
JSON'da bölüm yoksa (yeni bölüm) K5 bağlarından ana alan bulunur ve yalnızca alan şablonu gösterilir.
"""
import copy
import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import is_hayati_servisi as ihs
from app.core.database import get_db
from app.models import Ogrenci

ogrenci_router = APIRouter()
_JSON = Path(__file__).resolve().parents[1] / "data" / "meslege_yol.json"
_ALANLAR = ("adimlar", "basamaklar", "zorlayanlar", "neden_seviyor", "hazirlik")


@lru_cache(maxsize=1)
def yol_verisi() -> dict:
    try:
        return json.loads(_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"alanlar": {}, "sablonlar": {}, "bolumler": {}}


def _ana_alan(db: Session, bolum_id: int) -> str | None:
    r = db.execute(text("""SELECT dl.kod FROM bolum_k5_baglari bk JOIN degiskenler d ON d.id = bk.degisken_id
                             JOIN dallar dl ON dl.id = d.dal_id WHERE bk.bolum_id = :b ORDER BY bk.bag DESC, d.id LIMIT 1"""),
                   {"b": bolum_id}).first()
    return r.kod if r else None


def _sure_doldur(o, sure: str | None):
    if isinstance(o, dict):
        return {k: _sure_doldur(v, sure) for k, v in o.items()}
    if isinstance(o, list):
        return [_sure_doldur(v, sure) for v in o]
    if isinstance(o, str) and "{SURE}" in o:
        return o.replace("{SURE}", sure or "programa göre")
    return o


def yol_birlestir(ad: str, alan_kodu: str | None, sure: str | None) -> dict:
    v = yol_verisi()
    kayit = v["bolumler"].get(ad) or {}
    alan_kodu = kayit.get("alan") or alan_kodu
    alan = copy.deepcopy(v["alanlar"].get(alan_kodu) or {})
    katmanlar = []
    if alan.get("sablon"):
        katmanlar.append(v["sablonlar"].get(alan["sablon"]) or {})
    if kayit.get("sablon") and kayit.get("sablon") != alan.get("sablon"):
        katmanlar.append(v["sablonlar"].get(kayit["sablon"]) or {})
    katmanlar.append(kayit)
    sonuc = {k: alan.get(k) or [] for k in _ALANLAR}
    kaynaklar, duzenleme = [], []
    for kat in katmanlar:
        for k in _ALANLAR:
            if kat.get(k):
                sonuc[k] = copy.deepcopy(kat[k])
        for kay in kat.get("kaynaklar") or []:
            if kay not in kaynaklar:
                kaynaklar.append(kay)
        if kat.get("baslik"):
            duzenleme.append(kat["baslik"])
    return _sure_doldur({
        **sonuc,
        "alan": {"kod": alan_kodu, "ad": alan.get("ad")},
        "ozel": kayit.get("ozel"),
        "regule": bool(kayit.get("regule")),
        "oda_kaydi": bool(kayit.get("oda_kaydi")),
        "duzenleme": duzenleme,
        "temel_bolum": ihs.tr_baslik(kayit["temel_bolum"]) if kayit.get("temel_bolum") else None,
        "kaynaklar": kaynaklar,
        "son_kontrol": kayit.get("son_kontrol") or (v.get("son_kontrol") if kaynaklar else None),
        "bolume_ozel_kayit": bool(kayit),
    }, sure)


@ogrenci_router.get("/yol/{bolum_id}")
def yol(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    r = db.execute(text("SELECT id, ad, detay FROM bolumler WHERE id = :i AND durum = 'yayinda'"), {"i": bolum_id}).first()
    if r is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    d = r.detay if isinstance(r.detay, dict) else json.loads(r.detay or "{}")
    sure = d.get("ogrenim_suresi")
    alan_kodu = None if r.ad in yol_verisi()["bolumler"] else _ana_alan(db, r.id)
    sonuc = yol_birlestir(r.ad, alan_kodu, sure)
    meslekler = [{"ad": m.get("ad"), "nasil_olunur": m.get("nasil_olunur")}
                 for m in (d.get("meslekler") or []) if isinstance(m, dict) and m.get("ad") and m.get("nasil_olunur")]
    return {"bolum": {"id": r.id, "ad": ihs.tr_baslik(r.ad), "ogrenim_suresi": sure}, **sonuc, "meslekler": meslekler[:8]}
