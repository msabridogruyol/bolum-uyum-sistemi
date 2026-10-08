"""
[2026-10-08] Bölüm bilgi kartı (her sayfadaki açılır pencere) için herkese açık, salt-okunur uç noktalar.
GET /bolumler/{bolum_id}/bilgi           — tanıtım (özet, dersler, meslekler...) + üst/alt alan
GET /bolumler/{bolum_id}/universiteler   — YÖK Atlas: üniversiteler, kontenjan, taban puan, başarı sırası
GET /bolumler/ada-gore?ad=...            — sadece bölüm adı bilinen ekranlar için id bulma
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Bolum, BolumDalEslesme, Dal
from app.core.yokatlas_servisi import bolum_universiteleri

router = APIRouter()


def _bolum(db: Session, bolum_id: int) -> Bolum:
    b = db.get(Bolum, bolum_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")
    return b


@router.get("/ada-gore")
def bolum_ada_gore(ad: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    b = db.query(Bolum).filter(Bolum.ad == ad.strip()).first()
    if b is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")
    return {"bolum_id": b.id, "ad": b.ad}


@router.get("/{bolum_id}/bilgi")
def bolum_bilgi(bolum_id: int, db: Session = Depends(get_db)):
    b = _bolum(db, bolum_id)
    e = db.query(BolumDalEslesme).filter(BolumDalEslesme.bolum_id == b.id).first()
    dal = db.get(Dal, e.dal_id) if e else None
    return {
        "bolum_id": b.id, "ad": b.ad, "kisa_aciklama": b.kisa_aciklama, "detay": b.detay,
        "ust_alan": dal.ad if dal and dal.kod.startswith("U") else None,
        "alt_alan": getattr(e, "alt_alan", None) if e else None,
    }


@router.get("/{bolum_id}/universiteler")
def bolum_universite_listesi(bolum_id: int, db: Session = Depends(get_db)):
    return bolum_universiteleri(db, _bolum(db, bolum_id))
