"""
[2026-11-05] Gelişim listesi (haftalık görevlerin yerine; ayrıntı: app/core/gelisim_listesi.py).
GET    /gelisim-listesi                          — alanlar, maddeler, durumlar, kayıtlar, isteğe bağlı maddeler, Filiz seviyesi
POST   /gelisim-listesi/adim/{kod}/kayit         — "şu tarihte şunu yaptım" kaydı {tarih, aciklama}
DELETE /gelisim-listesi/kayit/{id}               — kendi kaydını sil
POST   /gelisim-listesi/adim/{kod}/durum         — {durum: bekliyor | devam_ediyor | tamamlandi}
POST   /gelisim-listesi/oz-degerlendirme         — isteğe bağlı 3 soru {yanit}
GET    /gelisim-listesi/oz-degerlendirmeler      — geçmiş öz değerlendirmeler (eski haftalık yansıtmalar dahil)
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import gelisim_listesi as gl
from app.core.database import get_db
from app.core.katman_servisi import IsKuraliHatasi
from app.models import Ogrenci
from app.schemas.girdi import GirdiModeli

router = APIRouter()


class KayitIstek(GirdiModeli):
    tarih: date
    aciklama: str = Field(min_length=1, max_length=1000)


class DurumIstek(GirdiModeli):
    durum: str = Field(pattern="^(bekliyor|devam_ediyor|tamamlandi)$")


class OzDegerlendirmeIstek(GirdiModeli):
    yanit: dict


def _yanit(db: Session, ogrenci: Ogrenci) -> dict:
    v = gl.liste(db, ogrenci)
    db.commit()
    return v


@router.get("")
def liste(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    return _yanit(db, ogrenci)


@router.post("/adim/{kod}/kayit")
def kayit_ekle(kod: str, istek: KayitIstek, db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    try:
        gl.kayit_ekle(db, ogrenci, kod, istek.tarih, istek.aciklama)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(400, str(e))
    return _yanit(db, ogrenci)


@router.delete("/kayit/{kayit_id}")
def kayit_sil(kayit_id: int, db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    try:
        gl.kayit_sil(db, ogrenci, kayit_id)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(404, str(e))
    return _yanit(db, ogrenci)


@router.post("/adim/{kod}/durum")
def durum(kod: str, istek: DurumIstek, db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    try:
        gl.durum_degistir(db, ogrenci, kod, istek.durum)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(400, str(e))
    return _yanit(db, ogrenci)


@router.post("/oz-degerlendirme")
def oz_degerlendirme(istek: OzDegerlendirmeIstek, db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    try:
        gl.oz_degerlendirme_kaydet(db, ogrenci, istek.yanit)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(400, str(e))
    return _yanit(db, ogrenci)


@router.get("/oz-degerlendirmeler")
def oz_degerlendirmeler(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    return {"kayitlar": gl.oz_degerlendirmeler(db, ogrenci),
            "sorular": [{"anahtar": a, "soru": s} for a, s in gl.OZ_DEGERLENDIRME_SORULARI]}
