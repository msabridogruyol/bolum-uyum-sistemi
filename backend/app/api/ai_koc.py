# -*- coding: utf-8 -*-
"""
AI Koçluk Asistanı — API uç noktaları

GET  /koclugu/asistan/durum                 — asistan aktif mi, bugün kalan mesaj hakkı
POST /koclugu/asistan/oturum/baslat        — yeni oturum başlatır (varsa aktif olanı döner, mesajlarıyla)
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
    asistan_aktif_mi, kriz_mesaji_mi, KRIZ_YANITI, GUNLUK_MESAJ_LIMITI_VARSAYILAN,
)
from app.core.katman_servisi import parametre_oku

router = APIRouter(prefix="/asistan", tags=["ai-koc"])


class OturumMesajiOut(BaseModel):
    rol: str
    icerik: str


class OturumOut(BaseModel):
    oturum_id: int
    durum: str
    mesajlar: list[OturumMesajiOut] = []


class MesajIstek(BaseModel):
    mesaj: str
    sayfa: str | None = None  # [2026-10-04] öğrencinin o an bulunduğu sayfa (bağlam için)


class AsistanDurumOut(BaseModel):
    aktif: bool
    gunluk_limit: int
    bugun_gonderilen: int
    kalan: int


def _gunluk_limit(db: Session) -> int:
    try:
        return max(1, int(parametre_oku(db, "filiz_gunluk_mesaj_limiti", str(GUNLUK_MESAJ_LIMITI_VARSAYILAN))))
    except (TypeError, ValueError):
        return GUNLUK_MESAJ_LIMITI_VARSAYILAN


def _bugun_gonderilen(db: Session, ogrenci: Ogrenci) -> int:
    """Türkiye saatine göre bugün öğrencinin gönderdiği mesaj sayısı."""
    from app.core.haftalik_servisi import TR_SAAT
    simdi = datetime.now(timezone.utc).astimezone(TR_SAAT)
    gun_basi = simdi.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    return (
        db.query(OgrenciKoclukMesaji)
        .join(OgrenciKoclukOturumu, OgrenciKoclukOturumu.id == OgrenciKoclukMesaji.oturum_id)
        .filter(OgrenciKoclukOturumu.ogrenci_id == ogrenci.id, OgrenciKoclukMesaji.rol == "ogrenci",
                OgrenciKoclukMesaji.olusturulma_zamani >= gun_basi.replace(tzinfo=None))
        .count()
    )


@router.get("/durum", response_model=AsistanDurumOut)
def asistan_durumu(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    limit, gonderilen = _gunluk_limit(db), _bugun_gonderilen(db, ogrenci)
    return AsistanDurumOut(aktif=asistan_aktif_mi(), gunluk_limit=limit, bugun_gonderilen=gonderilen, kalan=max(0, limit - gonderilen))


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
        mesajlar = (
            db.query(OgrenciKoclukMesaji)
            .filter(OgrenciKoclukMesaji.oturum_id == aktif.id)
            .order_by(OgrenciKoclukMesaji.olusturulma_zamani, OgrenciKoclukMesaji.id)
            .all()
        )
        return OturumOut(oturum_id=aktif.id, durum=aktif.durum,
                         mesajlar=[OturumMesajiOut(rol=m.rol, icerik=m.icerik) for m in mesajlar])

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
    metin = istek.mesaj.strip()[:2000]
    if not metin:
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    # [2026-10-04] Kriz ifadesi: model çağrılmaz, güvenli yönlendirme cevabı verilir (limit ve anahtardan bağımsız)
    if kriz_mesaji_mi(metin):
        db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="ogrenci", icerik=metin))
        db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="asistan", icerik=KRIZ_YANITI))
        db.commit()
        return MesajCevap(asistan_yaniti=KRIZ_YANITI, oturum_kapandi_mi=False)

    if _bugun_gonderilen(db, ogrenci) >= _gunluk_limit(db):
        raise HTTPException(status_code=429, detail="Bugünlük mesaj hakkın doldu. Yarın yine konuşalım! 🌱")

    onceki_mesajlar = (
        db.query(OgrenciKoclukMesaji)
        .filter(OgrenciKoclukMesaji.oturum_id == oturum.id)
        .order_by(OgrenciKoclukMesaji.olusturulma_zamani, OgrenciKoclukMesaji.id)
        .all()
    )
    mesaj_gecmisi = [
        {"role": "user" if m.rol == "ogrenci" else "assistant", "content": m.icerik}
        for m in onceki_mesajlar
    ]
    mesaj_gecmisi.append({"role": "user", "content": metin})

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

    sistem_promptu = sistem_promptu_olustur(db, ogrenci, onceki_ozet, istek.sayfa)

    try:
        yanit = openai_ile_konus(sistem_promptu, mesaj_gecmisi)
    except AsistanKullanilamiyorHatasi as e:
        raise HTTPException(status_code=503, detail=str(e))

    db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="ogrenci", icerik=metin))
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
