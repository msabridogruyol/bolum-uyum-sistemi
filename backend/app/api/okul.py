# -*- coding: utf-8 -*-
"""
[2026-10-09] Okullar — okul kaydı (ad + amblem) ve öğrencinin sol menüsündeki okul rozeti.

GET    /okul/benim                     — öğrenci: kendi okulu + tanıtım bilgileri (amblemi gösterilecekse), yoksa null
GET    /okul/aktif                     — (geriye uyum) ilk gösterilen okul
GET    /admin/okullar                  — süper admin: tüm okullar + öğrenci/okul yetkilisi sayıları
POST   /admin/okullar                  — yeni okul
PUT    /admin/okullar/{id}             — düzenle (ad değişirse öğrenci kayıtlarındaki okul adı da güncellenir)
DELETE /admin/okullar/{id}?hedef_id=   — sil; öğrencisi varsa hedef okula aktarılır (hedef 0 = okul harici)
Öğrenci ve okul yetkilisi işlemleri okul bazlıdır: bkz. app/api/okul_yonetimi.py (/yonetim/...).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin, get_mevcut_ogrenci
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz, simdi
from app.models import AdminKullanici, Okul, Ogrenci

LOGO_EN_FAZLA = 400_000   # data URL karakter sınırı (~300 KB görsel)
IZINLI_BASLANGIC = ("data:image/png", "data:image/jpeg", "data:image/jpg", "data:image/webp", "data:image/svg+xml")

genel_router = APIRouter(prefix="/okul", tags=["Okul"])
admin_router = APIRouter(prefix="/okullar", tags=["admin-okullar"])


class OkulOut(BaseModel):
    id: int
    ad: str
    alt_baslik: str | None = None
    logo: str | None = None
    aktif_mi: bool                    # amblem bu okulun öğrencilerine gösterilsin mi
    # [2026-10-09] Listede sistemdeki öğrenci sayısı; tekil cevaplarda okulun girdiği sayı (boş olabilir → None)
    ogrenci_sayisi: int | None = 0
    yetkili_sayisi: int = 0
    tema_renk: str | None = None

    model_config = {"from_attributes": True}


class KadroKisi(BaseModel):
    gorev: str
    ad: str
    eposta: str | None = None
    telefon: str | None = None


class OkulBilgiOut(BaseModel):
    """[2026-10-09] Öğrencinin gördüğü okul tanıtım penceresi (ve yönetimdeki düzenleme formu)."""
    id: int
    ad: str
    alt_baslik: str | None = None
    logo: str | None = None
    kurulus_yili: int | None = None
    ogrenci_sayisi: int | None = None
    tanitim: str | None = None
    adres: str | None = None
    telefon: str | None = None
    eposta: str | None = None
    web: str | None = None
    kadro: list[KadroKisi] = []
    bilgi_guncelleme_zamani: datetime | None = None
    tema_renk: str | None = None      # [2026-10-09] okul rengi — öğrenci arayüzündeki vurgu çizgileri

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


def _okul(db: Session, okul_id: int) -> Okul:
    okul = db.get(Okul, okul_id)
    if okul is None:
        raise HTTPException(status_code=404, detail="Okul bulunamadı.")
    return okul


@genel_router.get("/benim", response_model=OkulBilgiOut | None)
def benim_okulum(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    if not ogrenci.okul_id:
        return None
    okul = db.get(Okul, ogrenci.okul_id)
    return okul if okul is not None and okul.aktif_mi else None


@genel_router.get("/aktif", response_model=OkulOut | None)
def aktif_okul(db: Session = Depends(get_db)):
    return db.query(Okul).filter(Okul.aktif_mi.is_(True)).order_by(Okul.id).first()


@admin_router.get("", response_model=list[OkulOut])
def okullari_listele(db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    ogr = dict(db.query(Ogrenci.okul_id, func.count(Ogrenci.id)).filter(Ogrenci.okul_id.isnot(None))
               .group_by(Ogrenci.okul_id).all())
    yon = dict(db.query(AdminKullanici.okul_id, func.count(AdminKullanici.id))
               .filter(AdminKullanici.okul_id.isnot(None)).group_by(AdminKullanici.okul_id).all())
    return [OkulOut(id=o.id, ad=o.ad, alt_baslik=o.alt_baslik, logo=o.logo, aktif_mi=o.aktif_mi,
                    ogrenci_sayisi=ogr.get(o.id, 0), yetkili_sayisi=yon.get(o.id, 0))
            for o in db.query(Okul).order_by(Okul.ad).all()]


@admin_router.post("", response_model=OkulOut, status_code=201)
def okul_ekle(istek: OkulIstek, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    ad = (istek.ad or "").strip()
    if not ad:
        raise HTTPException(status_code=400, detail="Okul adı boş olamaz.")
    okul = Okul(ad=ad, alt_baslik=(istek.alt_baslik or "").strip() or None, logo=_logo_dogrula(istek.logo),
                aktif_mi=True if istek.aktif_mi is None else istek.aktif_mi, olusturulma_zamani=simdi())
    db.add(okul)
    db.flush()
    denetim_yaz(db, admin, "okul_ekle", "okullar", okul.id, ad, okul.id)
    db.commit()
    db.refresh(okul)
    return okul


@admin_router.put("/{okul_id}", response_model=OkulOut)
def okul_guncelle(okul_id: int, istek: OkulIstek, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    okul = _okul(db, okul_id)
    ad = (istek.ad or "").strip()
    if not ad:
        raise HTTPException(status_code=400, detail="Okul adı boş olamaz.")
    okul.ad = ad
    db.query(Ogrenci).filter(Ogrenci.okul_id == okul.id).update({Ogrenci.okul: ad}, synchronize_session=False)
    okul.alt_baslik = (istek.alt_baslik or "").strip() or None
    if istek.logo is not None:
        okul.logo = _logo_dogrula(istek.logo)
    if istek.aktif_mi is not None:
        okul.aktif_mi = istek.aktif_mi
    denetim_yaz(db, admin, "okul_guncelle", "okullar", okul.id, ad, okul.id)
    db.commit()
    db.refresh(okul)
    return okul


@admin_router.delete("/{okul_id}", status_code=204)
def okul_sil(okul_id: int, hedef_id: int | None = Query(None), db: Session = Depends(get_db),
             admin: AdminKullanici = Depends(get_mevcut_admin)):
    """Okulun öğrencileri hedef okula (0 = okul harici) aktarılır; okul yetkilisi hesapları okulla birlikte silinir."""
    okul = _okul(db, okul_id)
    sayi = db.query(Ogrenci).filter(Ogrenci.okul_id == okul.id).count()
    if sayi:
        if hedef_id is None or hedef_id == okul_id:
            raise HTTPException(status_code=409, detail=f"Bu okulda {sayi} öğrenci var; silmeden önce aktarılacakları yeri seçin.")
        hedef = _okul(db, hedef_id) if hedef_id else None
        db.query(Ogrenci).filter(Ogrenci.okul_id == okul.id).update(
            {Ogrenci.okul_id: hedef.id if hedef else None, Ogrenci.okul: hedef.ad if hedef else None}, synchronize_session=False)
    yoneticiler = db.query(AdminKullanici).filter(AdminKullanici.okul_id == okul.id).all()
    for y in yoneticiler:
        db.delete(y)
    denetim_yaz(db, admin, "okul_sil", "okullar", okul.id,
                f"{okul.ad} — {sayi} öğrenci aktarıldı, {len(yoneticiler)} okul yetkilisi silindi", okul.id)
    db.delete(okul)
    db.commit()
