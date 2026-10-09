# -*- coding: utf-8 -*-
"""
[2026-10-09] Okul markası — öğrenci sayfalarının solunda gösterilen okul adı + amblemi.

GET    /okul/aktif                    — herkese açık: gösterilen okul (yoksa null)
GET    /admin/okullar                 — tüm okullar
POST   /admin/okullar                 — yeni okul
PUT    /admin/okullar/{id}            — düzenle
POST   /admin/okullar/{id}/aktif-yap  — gösterilen okul yap (diğerleri pasife alınır)
POST   /admin/okullar/gizle           — hiçbir okulu gösterme
DELETE /admin/okullar/{id}            — sil
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin
from app.core.database import get_db
from app.models import AdminKullanici, AuditLog, Okul

LOGO_EN_FAZLA = 400_000   # data URL karakter sınırı (~300 KB görsel)
IZINLI_BASLANGIC = ("data:image/png", "data:image/jpeg", "data:image/jpg", "data:image/webp", "data:image/svg+xml")

genel_router = APIRouter(prefix="/okul", tags=["Okul"])
admin_router = APIRouter(prefix="/okullar", tags=["admin-okullar"])


class OkulOut(BaseModel):
    id: int
    ad: str
    alt_baslik: str | None = None
    logo: str | None = None
    aktif_mi: bool

    model_config = {"from_attributes": True}


class OkulIstek(BaseModel):
    ad: str
    alt_baslik: str | None = None
    logo: str | None = None          # data URL; boş string → amblemi kaldır
    aktif_mi: bool | None = None


def _logo_dogrula(logo: str | None) -> str | None:
    if logo is None or logo == "":
        return None
    if not logo.startswith(IZINLI_BASLANGIC):
        raise HTTPException(status_code=400, detail="Amblem PNG, JPEG, WEBP veya SVG olmalı.")
    if len(logo) > LOGO_EN_FAZLA:
        raise HTTPException(status_code=400, detail="Amblem çok büyük (en fazla ~300 KB).")
    return logo


def _tek_aktif(db: Session, okul_id: int | None):
    for o in db.query(Okul).filter(Okul.aktif_mi.is_(True)).all():
        if o.id != okul_id:
            o.aktif_mi = False
    db.flush()


def _audit(db: Session, admin: AdminKullanici, islem: str, hedef: int | str, not_: str | None = None):
    db.add(AuditLog(admin_id=admin.id, islem=islem, hedef_tablo="okullar", hedef_id=str(hedef), gerekce=not_))


@genel_router.get("/aktif", response_model=OkulOut | None)
def aktif_okul(db: Session = Depends(get_db)):
    return db.query(Okul).filter(Okul.aktif_mi.is_(True)).order_by(Okul.id.desc()).first()


@admin_router.get("", response_model=list[OkulOut])
def okullari_listele(db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    return db.query(Okul).order_by(Okul.aktif_mi.desc(), Okul.ad).all()


@admin_router.post("", response_model=OkulOut, status_code=201)
def okul_ekle(istek: OkulIstek, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    ad = (istek.ad or "").strip()
    if not ad:
        raise HTTPException(status_code=400, detail="Okul adı boş olamaz.")
    okul = Okul(ad=ad, alt_baslik=(istek.alt_baslik or "").strip() or None,
                logo=_logo_dogrula(istek.logo), aktif_mi=False, olusturulma_zamani=datetime.utcnow())
    db.add(okul)
    db.flush()
    if istek.aktif_mi:
        _tek_aktif(db, okul.id)
        okul.aktif_mi = True
    _audit(db, admin, "okul_ekle", okul.id, ad)
    db.commit()
    db.refresh(okul)
    return okul


@admin_router.put("/{okul_id}", response_model=OkulOut)
def okul_guncelle(okul_id: int, istek: OkulIstek, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    okul = db.get(Okul, okul_id)
    if okul is None:
        raise HTTPException(status_code=404, detail="Okul bulunamadı.")
    ad = (istek.ad or "").strip()
    if not ad:
        raise HTTPException(status_code=400, detail="Okul adı boş olamaz.")
    okul.ad = ad
    okul.alt_baslik = (istek.alt_baslik or "").strip() or None
    if istek.logo is not None:
        okul.logo = _logo_dogrula(istek.logo)
    if istek.aktif_mi is not None:
        if istek.aktif_mi:
            _tek_aktif(db, okul.id)
        okul.aktif_mi = istek.aktif_mi
    _audit(db, admin, "okul_guncelle", okul.id, ad)
    db.commit()
    db.refresh(okul)
    return okul


@admin_router.post("/gizle", status_code=204)
def okul_gosterme(db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    _tek_aktif(db, None)
    _audit(db, admin, "okul_gizle", "-")
    db.commit()


@admin_router.post("/{okul_id}/aktif-yap", response_model=OkulOut)
def okul_aktif_yap(okul_id: int, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    okul = db.get(Okul, okul_id)
    if okul is None:
        raise HTTPException(status_code=404, detail="Okul bulunamadı.")
    _tek_aktif(db, okul.id)
    okul.aktif_mi = True
    _audit(db, admin, "okul_aktif_yap", okul.id, okul.ad)
    db.commit()
    db.refresh(okul)
    return okul


@admin_router.delete("/{okul_id}", status_code=204)
def okul_sil(okul_id: int, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    okul = db.get(Okul, okul_id)
    if okul is None:
        raise HTTPException(status_code=404, detail="Okul bulunamadı.")
    _audit(db, admin, "okul_sil", okul.id, okul.ad)
    db.delete(okul)
    db.commit()
