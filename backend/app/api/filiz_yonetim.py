# -*- coding: utf-8 -*-
"""
[2026-10-11] Filiz — yönetim paneli asistanı uç noktaları (okul yetkilisi + süper admin).

  GET  /yonetim/filiz/ozet  — balon için günün bulguları (yalnızca sayılar, öğrenci adı yok) + hazır soru çipleri
  POST /yonetim/filiz/sor   — {metin} → kural tabanlı cevap (SSS, niyet bağlantıları, durum özeti, öneriler)
  GET  /yonetim/filiz/sss   — okul yetkilisi SSS'i (Sistem Hakkında & SSS sayfası bunu gösterir; tek kaynak)

Kapsam: okul yetkilisi YALNIZCA kendi okulunu görür (okul_id istemciden alınmaz, hesaptan gelir) ve /ozet, /sor
okulun paketinde 'filiz' modülü açıksa çalışır; süper admin her zaman. Yapay zekâ servisi çağrılmaz, sorular kaydedilmez
(app/core/filiz_yonetim_rehber.py).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.core.database import get_db
from app.core.filiz_yonetim_rehber import filiz_ozeti, sss_listesi, yanitla
from app.models import AdminKullanici

router = APIRouter(prefix="/yonetim/filiz", tags=["Filiz — yönetim asistanı"])


def _filiz_acik(db: Session, yon: AdminKullanici) -> None:
    if yon.rol == "super_admin":
        return
    from app.core.paketler import okul_modulleri
    if not yon.okul_id or "filiz" not in okul_modulleri(db, yon.okul_id):
        raise HTTPException(403, "Filiz okulunuzun paketinde açık değil.")


@router.get("/ozet")
def ozet(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _filiz_acik(db, yon)
    return filiz_ozeti(db, yon)


class SoruIstek(BaseModel):
    metin: str = Field(..., max_length=500)


@router.post("/sor")
def sor(istek: SoruIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _filiz_acik(db, yon)
    return yanitla(db, yon, istek.metin)


@router.get("/sss")
def sss(yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    return {"sss": sss_listesi(yon.rol, yon.okul_id)}
