# -*- coding: utf-8 -*-
"""
[2026-10-11] Sistem Sözlüğü — veritabanından gelen terimler (sözlükte aranabilsin diye).

GET /ogrenci/sozluk/ek
  bolumler   : [{id, ad, t}]                 — 301 bölüm, açıklama = detay.ozet
  meslekler  : [{ad, t, bolumler:[{id, ad}]}] — bölüm detaylarındaki meslekler (tekil ada göre birleştirilir)
  ozellikler : [{ad, t, katman}]             — değerlendirmede ölçülen özellikler (açıklaması olanlar)

Kişisel veri yok; içerik herkese aynı. Yanıt süreç içinde önbelleğe alınır (içerik yönetim ekranından güncellenince
ONBELLEK_SN içinde tazelenir). Durumu 'aktif' olmayan bölümler dahil edilmez.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.models import Ogrenci

router = APIRouter(prefix="/ogrenci/sozluk", tags=["Sözlük"])

ONBELLEK_SN = 600
_onbellek: dict = {"zaman": 0.0, "veri": None}


def _veri(db: Session) -> dict:
    bolumler, meslekler = [], {}
    rows = db.execute(text("SELECT id, ad, detay, durum FROM bolumler ORDER BY ad")).all()
    for r in rows:
        if r.durum and r.durum not in ("aktif", "yayinda"):
            continue
        d = r.detay or {}
        ozet = (d.get("ozet") or "").strip()
        if ozet:
            bolumler.append({"id": r.id, "ad": r.ad, "t": ozet})
        for m in d.get("meslekler") or []:
            if not isinstance(m, dict) or not (m.get("ad") or "").strip():
                continue
            ad = m["ad"].strip()
            k = meslekler.setdefault(ad, {"ad": ad, "t": (m.get("aciklama") or "").strip(), "bolumler": []})
            if not k["t"] and m.get("aciklama"):
                k["t"] = m["aciklama"].strip()
            if all(b["id"] != r.id for b in k["bolumler"]):
                k["bolumler"].append({"id": r.id, "ad": r.ad})
    ozellikler = [{"ad": r.ad, "t": r.aciklama.strip(), "katman": r.katman} for r in db.execute(text(
        "SELECT d.ad, d.aciklama, k.kod AS katman FROM degiskenler d LEFT JOIN katmanlar k ON k.id = d.katman_id "
        "WHERE coalesce(d.aciklama, '') <> '' ORDER BY d.ad")).all()]
    return {"bolumler": bolumler, "meslekler": [m for m in meslekler.values() if m["t"]], "ozellikler": ozellikler}


@router.get("/ek")
def sozluk_ek(response: Response, db: Session = Depends(get_db), _o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if _onbellek["veri"] is None or time.time() - _onbellek["zaman"] > ONBELLEK_SN:
        _onbellek["veri"] = _veri(db)
        _onbellek["zaman"] = time.time()
    response.headers["Cache-Control"] = "private, max-age=600"
    return _onbellek["veri"]
