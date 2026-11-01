# -*- coding: utf-8 -*-
"""
[2026-11-01] Veri Kaynakları (süper admin): sistemdeki dış verilerin varlığı, dönemi, son güncellemesi ve kontrol kaydı.

GET  /admin/veri-kaynaklari                   — tüm kaynaklar, durum ve son 5 kontrol
POST /admin/veri-kaynaklari/{kod}/kontrol     — "kontrol ettim, güncel" / "güncelledim" / "sorun var" kaydı (not isteğe bağlı)
GET  /admin/veri-kaynaklari/{kod}/gecmis      — o kaynağın kontrol geçmişi (son 50)
Ayrıntı: app/core/veri_kaynaklari.py
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_super_admin
from app.core import veri_kaynaklari as vk
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici

router = APIRouter(prefix="/admin/veri-kaynaklari", tags=["Admin — Veri Kaynakları"])


class KontrolIstek(BaseModel):
    sonuc: str = Field(..., pattern="^(guncel|guncellendi|sorun)$")
    notlar: str | None = Field(None, max_length=1000)


@router.get("")
def kaynaklar(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    return vk.liste(db)


@router.post("/{kod}/kontrol")
def kontrol(kod: str, istek: KontrolIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    if kod not in {k[0] for k in vk.KAYNAKLAR}:
        raise HTTPException(404, "Böyle bir veri kaynağı yok.")
    if istek.sonuc == "sorun" and not (istek.notlar or "").strip():
        raise HTTPException(422, "Sorunu kısaca yazın.")
    r = vk.kontrol_kaydet(db, kod, istek.sonuc, istek.notlar, yon)
    denetim_yaz(db, yon, "veri_kaynagi_kontrol", "veri_kaynagi_kontrolleri", r["id"],
                f"{kod}: {vk.SONUCLAR[istek.sonuc]}" + (f" · {istek.notlar.strip()[:200]}" if (istek.notlar or "").strip() else ""))
    db.commit()
    return r


@router.get("/{kod}/gecmis")
def gecmis(kod: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    if kod not in {k[0] for k in vk.KAYNAKLAR}:
        raise HTTPException(404, "Böyle bir veri kaynağı yok.")
    return {"kod": kod, "kontroller": vk.gecmis(db, kod)}
