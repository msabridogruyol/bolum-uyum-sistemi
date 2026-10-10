# -*- coding: utf-8 -*-
"""
[2026-10-10] Akran eşleştirme, şube dağılımı önerisi ve aday öğrenci şube uyumu (rehber / okul yetkilisi).
Sonuçlar yalnızca yönetim tarafında görünür; öğrenciye gösterilmez.
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_yonetimi import _okul_kapsami, _ogrenci_kapsami, _sinif_metni
from app.core.akran_servisi import aday_uyumu, benzer_akranlar, sube_dagilimi
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz, olay_yaz, yapan_etiketi
from app.models import AdminKullanici, Ogrenci

router = APIRouter(prefix="/yonetim", tags=["Akran ve şube"])


def _okul_ogrencileri(db: Session, okul_id: int):
    q = db.query(Ogrenci)
    return q.filter(Ogrenci.okul_id.is_(None) if okul_id == 0 else Ogrenci.okul_id == okul_id).all()


@router.get("/ogrenci/{ogrenci_id}/akranlar")
def akranlar(ogrenci_id: str, kapsam: str = "okul", db: Session = Depends(get_db),
             yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """kapsam: okul (tüm okul) | sinif (aynı sınıf düzeyi)"""
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    havuz = _okul_ogrencileri(db, o.okul_id or 0)
    if kapsam == "sinif" and o.sinif:
        havuz = [x for x in havuz if x.sinif == o.sinif]
    havuz = [x for x in havuz if x.sinif != "Aday" or x.id == o.id]
    return benzer_akranlar(db, str(o.id), [(x.id, x.ad_soyad, _sinif_metni(x)) for x in havuz], n=5)


class DagilimIstek(BaseModel):
    sinif: str
    subeler: list[str] = Field(min_length=1, max_length=20)
    mod: str = "dengeli"                     # dengeli | benzer
    adaylar_dahil: bool = False              # 'Aday' öğrencileri de bu sınıfa dağıt
    cinsiyet_dengele: bool = True


def _subeler(ham: list[str]) -> list[str]:
    s = []
    for x in ham:
        x = re.sub(r"\s+", "", str(x or "")).upper()[:3]
        if x and x not in s:
            s.append(x)
    if not s:
        raise HTTPException(status_code=400, detail="En az bir şube adı girin.")
    return s


@router.post("/okul/{okul_id}/sube-dagilimi")
def dagilim_onerisi(okul_id: int, istek: DagilimIstek, db: Session = Depends(get_db),
                    yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    if istek.mod not in ("dengeli", "benzer"):
        raise HTTPException(status_code=400, detail="Geçersiz mod.")
    subeler = _subeler(istek.subeler)
    hepsi = _okul_ogrencileri(db, okul_id)
    secilen = [x for x in hepsi if x.sinif == istek.sinif or (istek.adaylar_dahil and x.sinif == "Aday")]
    if not secilen:
        raise HTTPException(status_code=400, detail="Bu sınıfta öğrenci yok.")
    ogr = [{"id": str(x.id), "ad_soyad": x.ad_soyad, "sube": x.sube if x.sinif != "Aday" else "Aday",
            "cinsiyet": x.cinsiyet} for x in secilen]
    sonuc = sube_dagilimi(db, ogr, subeler, istek.mod, istek.cinsiyet_dengele)
    sonuc["sinif"] = istek.sinif
    degisen = sum(1 for g in sonuc["subeler"] for o in g["ogrenciler"] if o["eski_sube"] != g["sube"])
    sonuc["degisecek"] = degisen
    return sonuc


class Atama(BaseModel):
    id: str
    sube: str


class UygulaIstek(BaseModel):
    sinif: str
    atamalar: list[Atama] = Field(min_length=1, max_length=2000)


@router.post("/okul/{okul_id}/sube-dagilimi/uygula")
def dagilimi_uygula(okul_id: int, istek: UygulaIstek, db: Session = Depends(get_db),
                    yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    from app.api.okul_yonetimi import SINIFLAR
    if istek.sinif not in SINIFLAR or istek.sinif == "Aday":
        raise HTTPException(status_code=400, detail="Geçersiz sınıf.")
    say = 0
    for a in istek.atamalar:
        o = _ogrenci_kapsami(db, yon, a.id)
        if (o.okul_id or 0) != okul_id:
            raise HTTPException(status_code=403, detail="Öğrenci bu okulda değil.")
        sube = _subeler([a.sube])[0]
        if (o.sinif, o.sube) != (istek.sinif, sube):
            eski = _sinif_metni(o) or "—"
            o.sinif, o.sube = istek.sinif, sube
            olay_yaz(db, o.id, "bilgi_guncellendi", f"sınıf/şube: {eski} → {_sinif_metni(o)} (şube dağılımı)", yapan_etiketi(yon))
            say += 1
    if say:
        denetim_yaz(db, yon, "sube_dagilimi", "ogrenciler", istek.sinif, f"{istek.sinif}: {say} öğrencinin şubesi güncellendi", okul_id or None)
    db.commit()
    return {"guncellenen": say}


@router.get("/okul/{okul_id}/adaylar")
def adaylar(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    from app.api.okul_yonetimi import _durum, _ilerleme
    il = _ilerleme(db, okul_id)
    sonuc = []
    for o in sorted([x for x in _okul_ogrencileri(db, okul_id) if x.sinif == "Aday"], key=lambda x: x.ad_soyad.lower()):
        kod, etiket = _durum(o, il.get(o.id) or {})
        sonuc.append({"id": str(o.id), "ad_soyad": o.ad_soyad, "email": o.email, "ogrenci_no": o.ogrenci_no,
                      "durum": kod, "durum_etiket": etiket})
    return sonuc


@router.get("/ogrenci/{ogrenci_id}/aday-uyumu")
def aday_sube_uyumu(ogrenci_id: str, sinif: str = "9. Sınıf", db: Session = Depends(get_db),
                    yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    sinif_ogr = [{"id": str(x.id), "ad_soyad": x.ad_soyad, "sube": x.sube, "etiket": _sinif_metni(x)}
                 for x in _okul_ogrencileri(db, o.okul_id or 0) if x.sinif == sinif and x.id != o.id]
    sonuc = aday_uyumu(db, str(o.id), sinif_ogr)
    sonuc["sinif"] = sinif
    sonuc["sinif_ogrenci"] = len(sinif_ogr)
    return sonuc
