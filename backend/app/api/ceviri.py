# -*- coding: utf-8 -*-
"""
[2026-10-12] Çoklu dil uçları.

PUT  /ogrenci/profil/dil   {dil}             — öğrencinin kendi dil tercihi
PUT  /yonetim/ben/dil      {dil}             — okul yetkilisi / süper admin kendi dil tercihi
POST /ceviri/icerik        {dil, metinler[]} — sistem içeriğinin çevirisi (yalnızca içerik havuzundaki metinler;
                                                 app/core/ceviri_servisi.py). Giriş gerekmez: içerik herkese aynı, kişisel veri yok.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.ceviri_servisi import DILLER, icerik_cevir
from app.core.database import get_db
from app.models import AdminKullanici, Ogrenci

router = APIRouter(tags=["Çoklu dil"])


class DilIstek(BaseModel):
    dil: str = Field(min_length=2, max_length=5)


def _dil(d: str) -> str:
    d = d.strip().lower()
    if d not in DILLER:
        raise HTTPException(status_code=400, detail="Bu dil desteklenmiyor.")
    return d   # NULL = hiç seçilmedi; 'tr' açıkça Türkçe seçildi


@router.put("/ogrenci/profil/dil")
def ogrenci_dil(istek: DilIstek, db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    ogrenci.dil = _dil(istek.dil)
    db.commit()
    return {"dil": ogrenci.dil}


@router.put("/yonetim/ben/dil")
def yonetim_dil(istek: DilIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    yon.dil = _dil(istek.dil)
    db.commit()
    return {"dil": yon.dil}


class IcerikIstek(BaseModel):
    dil: str = Field(min_length=2, max_length=5)
    metinler: list[str] = Field(max_length=200)


@router.post("/ceviri/icerik")
def icerik(istek: IcerikIstek, db: Session = Depends(get_db)):
    # Genel hız sınırı (HizSiniriAraKatmani) uygulanır; havuz sınırlı olduğundan yapay zekâ maliyeti de sınırlıdır.
    dil = istek.dil.strip().lower()
    if dil not in DILLER:
        raise HTTPException(status_code=400, detail="Bu dil desteklenmiyor.")
    metinler = [m[:4000] for m in istek.metinler if isinstance(m, str)]
    return {"ceviriler": icerik_cevir(db, metinler, dil)}
