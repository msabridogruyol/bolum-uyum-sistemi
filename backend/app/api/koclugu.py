"""
Bölüm F — Koçluk modülü uç noktaları.
POST /koclugu/hedef              — hedef seç/değiştir (onay akışı, F8)
GET  /koclugu/hedef               — aktif hedefi getir
GET  /koclugu/hedef/gelisim       — gap analizi + gelişim kartları (F2-F3)
GET  /koclugu/hedef/yol-haritasi  — 3 aşamalı gelişim planı (F4)
POST /koclugu/hedef/aksiyon       — bir gelişim aksiyonunun durumunu güncelle (F4.2)
GET  /koclugu/karsilastirma       — tur bazlı önceki/güncel karşılaştırma (F5)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.core.katman_servisi import IsKuraliHatasi, son_tur_getir
from app.core.koclugu_servisi import (
    aktif_hedef_getir, hedef_sec, gap_analizi_hesapla, yol_haritasi_olustur,
    aksiyon_durumu_guncelle, tur_karsilastirmasi_hesapla,
)
from app.models import Ogrenci, Bolum
from app.schemas.koclugu import (
    HedefSecIstek, AktifHedefOut, GapSatiriOut, YolHaritasiOut,
    AksiyonDurumIstek, KarsilastirmaSatiriOut,
)

router = APIRouter()


@router.post("/hedef", response_model=AktifHedefOut)
def hedefi_sec(
    istek: HedefSecIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    try:
        hedef = hedef_sec(db, ogrenci, istek.bolum_id, onay=istek.onay)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))  # 409 — onay gerektiren çakışma
    db.commit()
    bolum = db.get(Bolum, hedef.bolum_id)
    return AktifHedefOut(bolum_id=hedef.bolum_id, bolum_adi=bolum.ad, secim_zamani=hedef.secim_zamani.isoformat())


@router.get("/hedef", response_model=AktifHedefOut | None)
def aktif_hedefi_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        return None
    bolum = db.get(Bolum, hedef.bolum_id)
    return AktifHedefOut(bolum_id=hedef.bolum_id, bolum_adi=bolum.ad, secim_zamani=hedef.secim_zamani.isoformat())


def _gap_satirlarini_hazirla(db: Session, ogrenci: Ogrenci):
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        raise HTTPException(status_code=400, detail="Henüz bir hedef bölümün yok.")
    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi as e:
        raise HTTPException(status_code=400, detail=str(e))
    if tur.durum != "tamamlandi":
        raise HTTPException(status_code=400, detail="K1-K4 tamamlanmadan gelişim analizi hesaplanamaz.")
    return gap_analizi_hesapla(db, ogrenci, tur, hedef.bolum_id)


def _gap_satiri_to_out(s) -> GapSatiriOut:
    kart = s.gelisim_karti
    return GapSatiriOut(
        degisken_id=s.degisken.id, degisken_adi=s.degisken.ad,
        ogrenci_puan=s.ogrenci_puan, bolum_beklenen=s.bolum_beklenen,
        gap=round(s.gap, 2), kategori=s.kategori, oncelik_skoru=round(s.oncelik_skoru, 2),
        durum_tespiti=kart.durum_tespiti if kart else None,
        aksiyon_onerisi=kart.aksiyon_onerisi if kart else None,
        kaynak_tipi=kart.kaynak_tipi if kart else None,
        tahmini_efor=kart.tahmini_efor if kart else None,
    )


@router.get("/hedef/gelisim", response_model=list[GapSatiriOut])
def gelisim_analizi_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    satirlar = _gap_satirlarini_hazirla(db, ogrenci)
    return [_gap_satiri_to_out(s) for s in satirlar]


@router.get("/hedef/yol-haritasi", response_model=YolHaritasiOut)
def yol_haritasini_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    satirlar = _gap_satirlarini_hazirla(db, ogrenci)
    harita = yol_haritasi_olustur(satirlar)
    return YolHaritasiOut(**{k: [_gap_satiri_to_out(s) for s in v] for k, v in harita.items()})


@router.post("/hedef/aksiyon/{degisken_id}", status_code=204)
def aksiyon_durumunu_guncelle(
    degisken_id: int,
    istek: AksiyonDurumIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        raise HTTPException(status_code=400, detail="Henüz bir hedef bölümün yok.")
    try:
        aksiyon_durumu_guncelle(db, ogrenci, hedef.bolum_id, degisken_id, istek.durum)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()


@router.get("/karsilastirma", response_model=list[KarsilastirmaSatiriOut] | None)
def tur_karsilastirmasini_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """F5.4 — ilk tur davranışı: en az 2 tamamlanmış tur yoksa null döner (frontend F5'i gizler)."""
    satirlar = tur_karsilastirmasi_hesapla(db, ogrenci)
    if satirlar is None:
        return None
    return [
        KarsilastirmaSatiriOut(
            degisken_id=s.degisken.id, degisken_adi=s.degisken.ad,
            eski_puan=s.eski_puan, yeni_puan=s.yeni_puan, degisim=round(s.degisim, 2),
            trend=s.trend, yorum_metni=s.yorum.yorum_metni if s.yorum else None,
        )
        for s in satirlar
    ]
