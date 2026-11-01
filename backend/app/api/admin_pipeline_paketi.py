# -*- coding: utf-8 -*-
"""
[2026-11-01] Süper admin: pipeline sayacı, "bu bilgisayara kur" dosyası ve kayıtlı bilgisayarlar.
Ayrıntı: app/core/pipeline_paketi.py

GET    /admin/pipeline-paketi/durum             — sayaç, depo durumu, bilgisayarlar, son veri sürümleri
POST   /admin/pipeline-paketi/kurulum-dosyasi   — 24 saat geçerli, tek kullanımlık kurulum dosyası (.ps1)
DELETE /admin/pipeline-paketi/cihazlar/{id}     — bilgisayarın erişimini kaldır
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_super_admin
from app.core import pipeline_depo as depo
from app.core import pipeline_paketi as pp
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici

router = APIRouter(prefix="/admin/pipeline-paketi", tags=["Admin — Pipeline kurulumu ve sayaç"])

_API_DESENI = re.compile(r"^(https://[A-Za-z0-9.\-]+(:\d+)?|http://(localhost|127\.0\.0\.1)(:\d+)?)(/[A-Za-z0-9._~\-/]*)?$")


@router.get("/durum")
def durum(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    kod = pp.kod_manifesti()
    return {"sayac": pp.sayac_durumu(db), "depo_hazir": depo.hazir_mi(), "kod_surumu": pp.kod_surumu(kod),
            "kod_dosya_sayisi": len(kod), "cihazlar": pp.cihazlar(db), "surumler": pp.surumler(db)}


class KurulumIstek(BaseModel):
    cihaz_adi: str = Field(..., min_length=2, max_length=60)
    api_adresi: str = Field(..., max_length=300)


@router.post("/kurulum-dosyasi")
def kurulum_dosyasi(istek: KurulumIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    ad = re.sub(r"[^\w .\-]", "", istek.cihaz_adi, flags=re.UNICODE).strip()
    if len(ad) < 2:
        raise HTTPException(422, "Bilgisayar adı en az 2 harf olmalı (harf, rakam, boşluk, nokta, tire).")
    if not _API_DESENI.match(istek.api_adresi.strip()):
        raise HTTPException(422, "Sistem adresi geçersiz.")
    ham = pp.kurulum_anahtari_olustur(db, yon, ad)
    denetim_yaz(db, yon, "pipeline_kurulum_dosyasi", "pipeline_anahtarlari", ad,
                f"'{ad}' bilgisayarı için pipeline kurulum dosyası indirildi (24 saat geçerli, tek kullanımlık)")
    db.commit()
    icerik = pp.kurulum_dosyasi(istek.api_adresi.strip(), ham, ad)
    return Response(icerik.encode("utf-8"), media_type="application/octet-stream",
                    headers={"Content-Disposition": 'attachment; filename="pipeline_kurulum.ps1"'})


@router.delete("/cihazlar/{cihaz_id}", status_code=204)
def cihaz_kaldir(cihaz_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    try:
        ad = pp.cihazi_iptal_et(db, cihaz_id)
    except pp.PaketHatasi as e:
        db.rollback()
        raise HTTPException(404, str(e))
    denetim_yaz(db, yon, "pipeline_cihaz_kaldirma", "pipeline_anahtarlari", cihaz_id, f"'{ad}' bilgisayarının pipeline erişimi kaldırıldı")
    db.commit()
