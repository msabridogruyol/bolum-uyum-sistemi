# -*- coding: utf-8 -*-
"""
[2026-10-09] Meslek dili (jargon) sözlüğü — hangi sürümün gösterileceğine karar verir.

Öncelik: okula özel sürüm (okul yetkilisi düzenledi) → genel sürüm (süper admin düzenledi)
         → varsayılan içerik (backend/app/core/meslek_jargonu.json, anahtar = bölüm adı).
"""
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Bolum, MeslekDili

_YOL = Path(__file__).resolve().parent / "meslek_jargonu.json"


def _ad_anahtar(ad: str) -> str:
    return (ad or "").replace("i", "İ").replace("ı", "I").upper().replace(" ", "")


try:
    _VARSAYILAN = {_ad_anahtar(k): v for k, v in json.loads(_YOL.read_text(encoding="utf-8")).items()}
except (OSError, ValueError):
    _VARSAYILAN = {}


def varsayilan_terimler(bolum_adi: str) -> list:
    return _VARSAYILAN.get(_ad_anahtar(bolum_adi), [])


def kayit_getir(db: Session, bolum_id: int, okul_id: int | None) -> MeslekDili | None:
    q = db.query(MeslekDili).filter(MeslekDili.bolum_id == bolum_id)
    q = q.filter(MeslekDili.okul_id.is_(None)) if not okul_id else q.filter(MeslekDili.okul_id == okul_id)
    return q.first()


def etkin_surum(db: Session, bolum: Bolum, okul_id: int | None) -> dict:
    """kaynak: 'okul' | 'genel' | 'varsayilan'"""
    if okul_id:
        k = kayit_getir(db, bolum.id, okul_id)
        if k is not None:
            return {"terimler": k.terimler or [], "kaynak": "okul", "guncelleyen_ad": k.guncelleyen_ad, "guncelleme_zamani": k.guncelleme_zamani}
    k = kayit_getir(db, bolum.id, None)
    if k is not None:
        return {"terimler": k.terimler or [], "kaynak": "genel", "guncelleyen_ad": k.guncelleyen_ad, "guncelleme_zamani": k.guncelleme_zamani}
    return {"terimler": varsayilan_terimler(bolum.ad), "kaynak": "varsayilan", "guncelleyen_ad": None, "guncelleme_zamani": None}
