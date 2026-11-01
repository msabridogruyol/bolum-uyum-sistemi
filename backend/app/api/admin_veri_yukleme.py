# -*- coding: utf-8 -*-
"""
[2026-11-01] Pipeline çıktılarını admin panelinden yükleme (yalnızca süper admin). Ayrıntı: app/core/veri_yukleme.py

POST /admin/veri-yukleme/{tur}/onizle          — dosya metni → önizleme (canlıya hiçbir şey yazılmaz)
POST /admin/veri-yukleme/{tur}/uygula          — önce mevcut hâl yedeklenir, sonra dosya canlıya yazılır
GET  /admin/veri-yukleme/{tur}/yedekler        — son 10 yedek
POST /admin/veri-yukleme/yedekler/{id}/geri-yukle — o yedeğe dön (dönmeden önceki hâl de yedeklenir)
tur: k5_baglari | ornek_meslekler
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_super_admin
from app.core import veri_yukleme as vy
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici

router = APIRouter(prefix="/admin/veri-yukleme", tags=["Admin — Pipeline veri yükleme"])


class DosyaIstek(BaseModel):
    metin: str = Field(..., max_length=8_000_000)
    dosya_adi: str | None = Field(None, max_length=200)


def _tur(tur: str) -> str:
    if tur not in vy.TURLER:
        raise HTTPException(404, "Bilinmeyen veri türü.")
    return tur


def _ayristir(tur: str, istek: DosyaIstek) -> list[dict]:
    try:
        return vy.ayristir(tur, istek.metin)
    except vy.VeriHatasi as e:
        raise HTTPException(422, str(e))


@router.post("/{tur}/onizle")
def onizle(tur: str, istek: DosyaIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    tur = _tur(tur)
    return vy.onizle(db, tur, _ayristir(tur, istek))


@router.post("/{tur}/uygula")
def uygula(tur: str, istek: DosyaIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    tur = _tur(tur)
    satirlar = _ayristir(tur, istek)
    try:
        r = vy.uygula(db, tur, satirlar, yon, istek.dosya_adi)
    except vy.VeriHatasi as e:
        db.rollback()
        raise HTTPException(422, str(e))
    tablo = "bolum_k5_baglari" if tur == "k5_baglari" else "bolum_ornek_meslekler"
    denetim_yaz(db, yon, "pipeline_veri_yukleme", tablo, r["yedek_id"],
                f"{vy.TURLER[tur]}: {r['yazilan']} satır, {r['bolum_sayisi']} bölüm canlıya alındı ({istek.dosya_adi or 'dosya'}); "
                f"önceki hâl yedek #{r['yedek_id']}")
    db.commit()
    return r


@router.get("/{tur}/yedekler")
def yedekler(tur: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    return {"tur": _tur(tur), "yedekler": vy.yedekler(db, tur)}


@router.post("/yedekler/{yedek_id}/geri-yukle")
def geri_yukle(yedek_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    try:
        r = vy.geri_yukle(db, yedek_id, yon)
    except vy.VeriHatasi as e:
        db.rollback()
        raise HTTPException(404, str(e))
    denetim_yaz(db, yon, "pipeline_veri_geri_yukleme", "veri_yedekleri", yedek_id,
                f"{vy.TURLER.get(r['tur'], r['tur'])}: yedek #{yedek_id} geri yüklendi ({r['yazilan']} satır); önceki hâl yedek #{r['yedek_id']}")
    db.commit()
    return r
