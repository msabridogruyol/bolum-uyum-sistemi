# -*- coding: utf-8 -*-
"""
[2026-10-11] İş Hayatı → 'gelecek' sekmesi (Gelecekte Bu Meslek): yapay zekâ ve otomasyonun meslek grupları üzerindeki etkisi.

  GET /ogrenci/is-hayati/gelecek/{bolum_id}

Veri: meslek_grubu_ai_etkisi (göç 0058; tohum = ILO Working Paper 140, 2025, Tablo A1) → düzey, açıklama, kaynak, sayfa, yıl,
4 haneli meslek dağılımı. Nitel içerik (değişen görevler, değer kazanan beceriler, lisede yapılabilecekler, ölçek, uyarı, WEF notları):
app/data/ai_etkisi_gruplar.json. Meslek → ISCO: meslek_isco tablosu (2 hane; satır yoksa 1 haneli ana gruba düşer).
Süper admin düzenlemesi: admin_is_hayati.py'deki genel /admin/is-hayati/kayit/{tablo} uçları — tablo tanımı aşağıda TABLOLAR'a eklenir.
"""
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
_JSON = Path(__file__).resolve().parents[1] / "data" / "ai_etkisi_gruplar.json"

DUZEY_ADI = {"yuksek": "En çok değişecek", "orta": "Kısmen değişecek", "dusuk": "Az değişecek", "belirsiz": "Belirsiz"}
DUZEY_SIRA = {"dusuk": 1, "orta": 2, "yuksek": 3, "belirsiz": 0}
_ILO_MESLEK_SINIRI = 8   # öğrenciye gösterilen 4 haneli meslek sayısı (grubun en çok maruz kalanlarından)


@lru_cache(maxsize=1)
def ai_verisi() -> dict:
    try:
        return json.loads(_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"gruplar": {}}


def _json(v, bos):
    if v is None:
        return bos
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except Exception:
        return bos


def _satirlar(db: Session) -> dict:
    """isco_kodu → en yeni veri yılındaki satır."""
    rows = db.execute(text("""SELECT DISTINCT ON (isco_kodu) * FROM meslek_grubu_ai_etkisi
                              ORDER BY isco_kodu, veri_yili DESC, id DESC""")).mappings().all()
    return {r["isco_kodu"]: dict(r) for r in rows}


def _grup(kod: str, satir: dict | None) -> dict:
    v = ai_verisi()
    nitel = (v.get("gruplar") or {}).get(kod) or {}
    if satir is None:
        return {"kod": kod, "ad": ihs.isco_adi(kod), "duzey": None, "duzey_ad": None, "sira": None, "veri_var": False,
                "degisen_gorevler": nitel.get("degisen_gorevler") or [], "deger_kazanan": nitel.get("deger_kazanan") or [],
                "lisede": nitel.get("lisede") or []}
    meslekler = _json(satir.get("meslekler"), [])
    duzey = satir.get("duzey") or "belirsiz"
    return {
        "kod": kod, "ad": ihs.isco_adi(kod) or nitel.get("ad"), "veri_var": True,
        "duzey": duzey, "duzey_ad": DUZEY_ADI.get(duzey, duzey), "sira": DUZEY_SIRA.get(duzey),
        "puan": float(satir["puan"]) if satir.get("puan") is not None else None,
        "aciklama": satir.get("aciklama"), "kaynak": satir.get("kaynak"), "kaynak_bolum": satir.get("kaynak_bolum"),
        "veri_yili": satir.get("veri_yili"),
        "dagilim": _json(satir.get("dagilim"), {}),
        "meslek_sayisi": len(meslekler),
        "ilo_meslekleri": meslekler[:_ILO_MESLEK_SINIRI],
        "degisen_gorevler": nitel.get("degisen_gorevler") or [], "deger_kazanan": nitel.get("deger_kazanan") or [],
        "lisede": nitel.get("lisede") or [],
        "tahmin": False,
    }


@ogrenci_router.get("/gelecek/{bolum_id}")
def gelecek(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    r = db.execute(text("SELECT id, ad, detay FROM bolumler WHERE id = :i AND durum = 'yayinda'"), {"i": bolum_id}).first()
    if r is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    d = r.detay if isinstance(r.detay, dict) else json.loads(r.detay or "{}")
    adlar = [m.get("ad") for m in (d.get("meslekler") or []) if isinstance(m, dict) and m.get("ad")]
    harita = ihs.meslek_isco_haritasi(db, adlar)
    satirlar = _satirlar(db)

    meslekler, gruplar, eksik = [], {}, []
    for ad in adlar:
        kod, guven = harita.get(ihs.tr_kucuk(ad), (None, None))
        veri_kodu = kod if kod in satirlar else (kod[:1] if kod and kod[:1] in satirlar else None)
        meslekler.append({"meslek": ad, "isco_kodu": kod, "isco_guven": guven, "grup_kodu": veri_kodu or kod,
                          "grup_duzeyi": None if not veri_kodu else ("alt_ana_grup" if len(veri_kodu) == 2 else "ana_grup")})
        anahtar = veri_kodu or kod
        if anahtar and anahtar not in gruplar:
            gruplar[anahtar] = _grup(anahtar, satirlar.get(veri_kodu) if veri_kodu else None)
        if not kod:
            eksik.append(ad)

    v = ai_verisi()
    sirali = sorted(gruplar.values(), key=lambda g: (-(g.get("sira") or 0), g["kod"]))
    kaynaklar = []
    if v.get("kaynak"):
        kaynaklar.append({"ad": v["kaynak"].get("atif"), "url": v["kaynak"].get("url")})
    if v.get("genel"):
        kaynaklar.append({"ad": v["genel"].get("kisa"), "url": v["genel"].get("url")})
    return {
        "bolum": {"id": r.id, "ad": ihs.tr_baslik(r.ad)},
        "uyari": v.get("uyari"),
        "olcek": v.get("olcek"),
        "duzey_kurali": v.get("duzey_kurali"),
        "duzey_adlari": DUZEY_ADI,
        "meslekler": meslekler,
        "gruplar": sirali,
        "genel": v.get("genel"),
        "kaynaklar": kaynaklar,
        "son_kontrol": v.get("son_kontrol"),
        "eslesmeyen": eksik,
        "veri_yok": not any(g.get("veri_var") for g in sirali),
    }


# ---------------------------------------------------------------- süper admin: genel kayıt uçlarına tablo tanımı ekle
def _admin_tablosunu_kaydet():
    from app.api import admin_is_hayati as aih

    def _duzey_ai(v):
        t = aih._metin(v, True, 20)
        if t not in DUZEY_ADI:
            raise ValueError("dusuk / orta / yuksek / belirsiz")
        return t

    aih.TABLOLAR.setdefault("meslek_grubu_ai_etkisi", {
        "ad": "Yapay zekâ etkisi (meslek grubu)", "sira": "isco_kodu, veri_yili DESC", "ara": ["isco_kodu", "aciklama", "kaynak"],
        "guncelleme": True,
        "alanlar": {"isco_kodu": aih._isco, "duzey": _duzey_ai, "puan": lambda v: aih._sayi(v, False, 0, 1),
                    "aciklama": lambda v: aih._metin(v, False, 2000), "kaynak": lambda v: aih._metin(v, True, 600),
                    "kaynak_bolum": lambda v: aih._metin(v, False, 200), "veri_yili": aih._yil},
    })


try:
    _admin_tablosunu_kaydet()
except Exception:  # admin modülü yüklenemezse öğrenci ucu yine çalışsın
    import logging
    logging.getLogger(__name__).exception("meslek_grubu_ai_etkisi admin tablosu kaydedilemedi")
