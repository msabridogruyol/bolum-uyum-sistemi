"""
Kimlik doğrulama uç noktaları — D1.
POST /auth/kayit    — yeni öğrenci hesabı
POST /auth/giris    — email+şifre ile giriş, access+refresh token döner
POST /auth/yenile   — refresh token ile yeni access token
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    sifre_hashle, sifre_dogrula,
    erisim_tokeni_uret, yenileme_tokeni_uret, token_coz,
)
from app.models import Ogrenci
from app.schemas.auth import OgrenciKayitIstek, GirisIstek, TokenCifti, YenilemeIstek, OgrenciProfil

router = APIRouter()


@router.post("/kayit", response_model=OgrenciProfil, status_code=status.HTTP_201_CREATED)
def kayit_ol(istek: OgrenciKayitIstek, db: Session = Depends(get_db)):
    mevcut = db.query(Ogrenci).filter(Ogrenci.email == istek.email).first()
    if mevcut is not None:
        raise HTTPException(status_code=400, detail="Bu e-posta ile zaten bir hesap var.")

    ogrenci = Ogrenci(
        ad_soyad=istek.ad_soyad,
        email=istek.email,
        sifre_hash=sifre_hashle(istek.sifre),
    )
    db.add(ogrenci)
    db.commit()
    db.refresh(ogrenci)
    return OgrenciProfil(id=str(ogrenci.id), ad_soyad=ogrenci.ad_soyad, email=ogrenci.email)


@router.post("/giris", response_model=TokenCifti)
def giris_yap(istek: GirisIstek, db: Session = Depends(get_db)):
    hata = HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    ogrenci = db.query(Ogrenci).filter(Ogrenci.email == istek.email).first()
    if ogrenci is None or not sifre_dogrula(istek.sifre, ogrenci.sifre_hash):
        raise hata

    return TokenCifti(
        erisim_tokeni=erisim_tokeni_uret(ogrenci.id, "ogrenci"),
        yenileme_tokeni=yenileme_tokeni_uret(ogrenci.id, "ogrenci"),
    )


@router.post("/yenile", response_model=TokenCifti)
def token_yenile(istek: YenilemeIstek, db: Session = Depends(get_db)):
    hata = HTTPException(status_code=401, detail="Geçersiz yenileme tokeni.")

    payload = token_coz(istek.yenileme_tokeni)
    if payload is None or payload.get("tip") != "refresh":
        raise hata

    try:
        ogrenci_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise hata

    ogrenci = db.get(Ogrenci, ogrenci_id)
    if ogrenci is None:
        raise hata

    return TokenCifti(
        erisim_tokeni=erisim_tokeni_uret(ogrenci.id, "ogrenci"),
        yenileme_tokeni=yenileme_tokeni_uret(ogrenci.id, "ogrenci"),
    )
