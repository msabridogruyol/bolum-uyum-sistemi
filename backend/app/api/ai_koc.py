# -*- coding: utf-8 -*-
"""
AI Koçluk Asistanı — API uç noktaları

POST /koclugu/asistan/oturum/baslat        — yeni oturum başlatır (varsa aktif olanı döner)
POST /koclugu/asistan/oturum/{id}/mesaj    — mesaj gönderir, asistan cevabını döner
POST /koclugu/asistan/oturum/{id}/bitir    — oturumu kapatır, özet çıkarır
GET  /koclugu/asistan/gecmis               — geçmiş oturum özetlerini listeler
"""
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.api.deps import get_mevcut_ogrenci
from app.models import Ogrenci, OgrenciKoclukOturumu, OgrenciKoclukMesaji
from app.core.ai_koc_servisi import (
    sistem_promptu_olustur, openai_ile_konus, oturumu_ozetle,
    AsistanKullanilamiyorHatasi, MAKSIMUM_TUR,
)

router = APIRouter(prefix="/asistan", tags=["ai-koc"])


class OturumOut(BaseModel):
    oturum_id: int
    durum: str


class MesajIstek(BaseModel):
    mesaj: str


class MesajCevap(BaseModel):
    asistan_yaniti: str
    oturum_kapandi_mi: bool = False


class GecmisOturumOut(BaseModel):
    oturum_id: int
    baslama_zamani: datetime
    ozet: str | None


@router.post("/oturum/baslat", response_model=OturumOut)
def oturum_baslat(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    aktif = (
        db.query(OgrenciKoclukOturumu)
        .filter(OgrenciKoclukOturumu.ogrenci_id == ogrenci.id, OgrenciKoclukOturumu.durum == "aktif")
        .first()
    )
    if aktif:
        return OturumOut(oturum_id=aktif.id, durum=aktif.durum)

    yeni = OgrenciKoclukOturumu(ogrenci_id=ogrenci.id, durum="aktif")
    db.add(yeni)
    db.commit()
    db.refresh(yeni)
    return OturumOut(oturum_id=yeni.id, durum=yeni.durum)


@router.post("/oturum/{oturum_id}/mesaj", response_model=MesajCevap)
def mesaj_gonder(
    oturum_id: int,
    istek: MesajIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    oturum = db.get(OgrenciKoclukOturumu, oturum_id)
    if oturum is None or oturum.ogrenci_id != ogrenci.id:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı.")
    if oturum.durum != "aktif":
        raise HTTPException(status_code=400, detail="Bu oturum kapatılmış, yeni bir oturum başlatın.")
    if not istek.mesaj.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    onceki_mesajlar = (
        db.query(OgrenciKoclukMesaji)
        .filter(OgrenciKoclukMesaji.oturum_id == oturum.id)
        .order_by(OgrenciKoclukMesaji.olusturulma_zamani)
        .all()
    )
    mesaj_gecmisi = [
        {"role": "user" if m.rol == "ogrenci" else "assistant", "content": m.icerik}
        for m in onceki_mesajlar
    ]
    mesaj_gecmisi.append({"role": "user", "content": istek.mesaj.strip()})

    onceki_oturum = (
        db.query(OgrenciKoclukOturumu)
        .filter(
            OgrenciKoclukOturumu.ogrenci_id == ogrenci.id,
            OgrenciKoclukOturumu.durum == "tamamlandi",
            OgrenciKoclukOturumu.id != oturum.id,
        )
        .order_by(OgrenciKoclukOturumu.bitis_zamani.desc())
        .first()
    )
    onceki_ozet = onceki_oturum.ozet if onceki_oturum else None

    sistem_promptu = sistem_promptu_olustur(db, ogrenci, onceki_ozet)

    try:
        yanit = openai_ile_konus(sistem_promptu, mesaj_gecmisi)
    except AsistanKullanilamiyorHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))

    db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="ogrenci", icerik=istek.mesaj.strip()))
    db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="asistan", icerik=yanit))
    db.commit()

    toplam_mesaj = len(onceki_mesajlar) + 2
    kapandi = False
    if toplam_mesaj >= MAKSIMUM_TUR:
        _oturumu_kapat_ve_ozetle(db, oturum, sistem_promptu, mesaj_gecmisi + [{"role": "assistant", "content": yanit}])
        kapandi = True

    return MesajCevap(asistan_yaniti=yanit, oturum_kapandi_mi=kapandi)


@router.post("/oturum/{oturum_id}/bitir", status_code=204)
def oturumu_bitir(
    oturum_id: int,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    oturum = db.get(OgrenciKoclukOturumu, oturum_id)
    if oturum is None or oturum.ogrenci_id != ogrenci.id:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı.")
    if oturum.durum != "aktif":
        return

    mesajlar = (
        db.query(OgrenciKoclukMesaji)
        .filter(OgrenciKoclukMesaji.oturum_id == oturum.id)
        .order_by(OgrenciKoclukMesaji.olusturulma_zamani)
        .all()
    )
    mesaj_gecmisi = [
        {"role": "user" if m.rol == "ogrenci" else "assistant", "content": m.icerik}
        for m in mesajlar
    ]
    sistem_promptu = sistem_promptu_olustur(db, ogrenci, None)
    _oturumu_kapat_ve_ozetle(db, oturum, sistem_promptu, mesaj_gecmisi)


def _oturumu_kapat_ve_ozetle(db: Session, oturum: OgrenciKoclukOturumu, sistem_promptu: str, mesaj_gecmisi: list[dict]):
    ozet = oturumu_ozetle(sistem_promptu, mesaj_gecmisi) if mesaj_gecmisi else None
    oturum.durum = "tamamlandi"
    oturum.bitis_zamani = datetime.now(timezone.utc)
    oturum.ozet = ozet
    db.commit()


@router.get("/gecmis", response_model=list[GecmisOturumOut])
def gecmis_oturumlari_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    oturumlar = (
        db.query(OgrenciKoclukOturumu)
        .filter(OgrenciKoclukOturumu.ogrenci_id == ogrenci.id, OgrenciKoclukOturumu.durum == "tamamlandi")
        .order_by(OgrenciKoclukOturumu.bitis_zamani.desc())
        .limit(20)
        .all()
    )
    return [
        GecmisOturumOut(oturum_id=o.id, baslama_zamani=o.baslama_zamani, ozet=o.ozet)
        for o in oturumlar
    ]
