# -*- coding: utf-8 -*-
"""
Admin — Güvenlik/Tutarlılık Genel Bakış (sonradan eklendi)
GET /admin/guvenlik/turlar                — tüm turların güven skoru + olay özeti (filtrelenebilir)
GET /admin/guvenlik/turlar/{tur_id}        — bir turun tüm olayları + fotoğrafları (detay)
"""

from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from app.models import (
    OgrenciDegerlendirmeTuru, Ogrenci, GuvenlikOlayi, GuvenlikFotografi,
)


# ============================================================================
# Şemalar
# ============================================================================

class GuvenlikTurOzetOut(BaseModel):
    tur_id: int
    ogrenci_id: str
    ogrenci_adi: str
    ogrenci_email: str
    tur_no: int
    durum: str
    guven_skoru: float | None
    sonuc_gecerli_mi: bool
    gecersizlik_nedeni: str | None
    olay_sayisi: int
    kritik_olay_sayisi: int  # tam_ekrandan_cikti + sekme_degisti + kamera sorunları
    fotograf_sayisi: int
    tamamlanma_zamani: str | None


class GuvenlikOlayOut(BaseModel):
    id: int
    olay_tipi: str
    katman_kod: str | None
    olay_zamani: str


class GuvenlikFotografOut(BaseModel):
    id: int
    foto_base64: str
    katman_kod: str | None
    cekim_zamani: str


class GuvenlikTurDetayOut(BaseModel):
    ozet: GuvenlikTurOzetOut
    olaylar: list[GuvenlikOlayOut]
    fotograflar: list[GuvenlikFotografOut]


KRITIK_OLAY_TIPLERI = {
    "tam_ekrandan_cikti", "sekme_degisti",
    "kamera_izni_reddedildi", "kamera_desteklenmiyor",
}


# ============================================================================
# Uç noktalar — bu iki fonksiyonu admin.py'deki router'a ekleyin
# (aşağıdaki @router.get satırlarını olduğu gibi admin router'ınıza taşıyın)
# ============================================================================

def guvenlik_turlarini_listele_impl(
    yalniz_gecersiz: bool,
    en_az_kritik_olay: int,
    db: Session,
):
    turlar = db.query(OgrenciDegerlendirmeTuru).filter(
        OgrenciDegerlendirmeTuru.durum == "tamamlandi"
    ).all()
    if not turlar:
        return []

    tur_idler = [t.id for t in turlar]

    olay_satirlari = (
        db.query(GuvenlikOlayi.tur_id, GuvenlikOlayi.olay_tipi, func.count(GuvenlikOlayi.id))
        .filter(GuvenlikOlayi.tur_id.in_(tur_idler))
        .group_by(GuvenlikOlayi.tur_id, GuvenlikOlayi.olay_tipi)
        .all()
    )
    olay_sayilari: dict[int, int] = {}
    kritik_sayilari: dict[int, int] = {}
    for tur_id, olay_tipi, adet in olay_satirlari:
        olay_sayilari[tur_id] = olay_sayilari.get(tur_id, 0) + adet
        if olay_tipi in KRITIK_OLAY_TIPLERI:
            kritik_sayilari[tur_id] = kritik_sayilari.get(tur_id, 0) + adet

    fotograf_sayilari = dict(
        db.query(GuvenlikFotografi.tur_id, func.count(GuvenlikFotografi.id))
        .filter(GuvenlikFotografi.tur_id.in_(tur_idler))
        .group_by(GuvenlikFotografi.tur_id)
        .all()
    )

    ogrenciler = {o.id: o for o in db.query(Ogrenci).filter(Ogrenci.id.in_([t.ogrenci_id for t in turlar])).all()}

    sonuc = []
    for t in turlar:
        o = ogrenciler.get(t.ogrenci_id)
        kritik = kritik_sayilari.get(t.id, 0)
        if yalniz_gecersiz and t.sonuc_gecerli_mi:
            continue
        if kritik < en_az_kritik_olay:
            continue
        sonuc.append(GuvenlikTurOzetOut(
            tur_id=t.id,
            ogrenci_id=str(t.ogrenci_id),
            ogrenci_adi=o.ad_soyad if o else "?",
            ogrenci_email=o.email if o else "?",
            tur_no=t.tur_no,
            durum=t.durum,
            guven_skoru=float(t.guven_skoru) if t.guven_skoru is not None else None,
            sonuc_gecerli_mi=t.sonuc_gecerli_mi,
            gecersizlik_nedeni=t.gecersizlik_nedeni,
            olay_sayisi=olay_sayilari.get(t.id, 0),
            kritik_olay_sayisi=kritik,
            fotograf_sayisi=fotograf_sayilari.get(t.id, 0),
            tamamlanma_zamani=t.tamamlanma_zamani.isoformat() if t.tamamlanma_zamani else None,
        ))

    # en düşük güven skoru en üstte (en dikkat gerektiren en önce görünsün)
    sonuc.sort(key=lambda s: (s.guven_skoru if s.guven_skoru is not None else 999))
    return sonuc


def guvenlik_tur_detayini_getir_impl(tur_id: int, db: Session):
    tur = db.get(OgrenciDegerlendirmeTuru, tur_id)
    if tur is None:
        raise HTTPException(status_code=404, detail="Tur bulunamadı.")

    ogrenci = db.get(Ogrenci, tur.ogrenci_id)

    olaylar = (
        db.query(GuvenlikOlayi)
        .filter(GuvenlikOlayi.tur_id == tur_id)
        .order_by(GuvenlikOlayi.olay_zamani)
        .all()
    )
    fotograflar = (
        db.query(GuvenlikFotografi)
        .filter(GuvenlikFotografi.tur_id == tur_id)
        .order_by(GuvenlikFotografi.cekim_zamani)
        .all()
    )

    kritik = sum(1 for o in olaylar if o.olay_tipi in KRITIK_OLAY_TIPLERI)

    ozet = GuvenlikTurOzetOut(
        tur_id=tur.id,
        ogrenci_id=str(tur.ogrenci_id),
        ogrenci_adi=ogrenci.ad_soyad if ogrenci else "?",
        ogrenci_email=ogrenci.email if ogrenci else "?",
        tur_no=tur.tur_no,
        durum=tur.durum,
        guven_skoru=float(tur.guven_skoru) if tur.guven_skoru is not None else None,
        sonuc_gecerli_mi=tur.sonuc_gecerli_mi,
        gecersizlik_nedeni=tur.gecersizlik_nedeni,
        olay_sayisi=len(olaylar),
        kritik_olay_sayisi=kritik,
        fotograf_sayisi=len(fotograflar),
        tamamlanma_zamani=tur.tamamlanma_zamani.isoformat() if tur.tamamlanma_zamani else None,
    )

    return GuvenlikTurDetayOut(
        ozet=ozet,
        olaylar=[
            GuvenlikOlayOut(id=o.id, olay_tipi=o.olay_tipi, katman_kod=o.katman_kod, olay_zamani=o.olay_zamani.isoformat())
            for o in olaylar
        ],
        fotograflar=[
            GuvenlikFotografOut(id=f.id, foto_base64=f.depolama_yolu, katman_kod=f.katman_kod, cekim_zamani=f.cekim_zamani.isoformat())
            for f in fotograflar
        ],
    )
