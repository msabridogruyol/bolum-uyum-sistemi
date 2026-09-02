# -*- coding: utf-8 -*-
"""
Admin — Soru Bankası Detaylı Görünüm (sonradan eklendi)

Bağımsız router — mevcut admin.py'ye dokunmaz. main.py'de admin_guvenlik
ile AYNI şekilde kaydedilir.

GET /admin/sorular-detay          — sayfalanmış, tam detaylı (soru+şıklar) liste
                                     katman_kod, dal_kod, aktif_mi, sayfa filtreleri
GET /admin/sorular-detay/dallar   — K5 filtre menüsü için dal listesi
PUT /admin/sorular-detay/soru/{id}          — soru metnini günceller
PUT /admin/sorular-detay/secenek/{id}       — seçenek metnini günceller
"""

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.api.deps import get_mevcut_admin
from app.models import (
    AdminKullanici, Soru, SoruSecenegi, SjtSecenekDegiskenAgirlik,
    Katman, Degisken, Dal,
)

router = APIRouter(prefix="/sorular-detay", tags=["admin-sorular-detay"])

SAYFA_BOYUTU = 8


# ============================================================================
# Şemalar
# ============================================================================

class SecenekDetayOut(BaseModel):
    id: int
    secenek_sirasi: int
    secenek_metni: str
    sjt_agirliklar: list[dict] = []  # [{"degisken_kod": "M1", "agirlik": 1.0}, ...] — yalnızca SJT'de dolu


class SoruDetayOut(BaseModel):
    id: int
    katman_kod: str
    dal_kod: str | None
    dal_adi: str | None
    soru_tipi: str
    degisken_kod: str | None
    soru_metni: str
    ters_kodlanmis_mi: bool
    aktif_mi: bool
    secenekler: list[SecenekDetayOut]


class SayfalanmisSorularOut(BaseModel):
    sorular: list[SoruDetayOut]
    toplam_soru_sayisi: int
    toplam_sayfa_sayisi: int
    su_anki_sayfa: int


class DalFiltreOut(BaseModel):
    kod: str
    ad: str


class SoruMetniGuncelleIstek(BaseModel):
    soru_metni: str


class SecenekMetniGuncelleIstek(BaseModel):
    secenek_metni: str


# ============================================================================
# Yardımcı — bir sorunun "dal"ını bulur (K1-K4'te hep None; K5'te Likert
# için doğrudan degisken.dal_id, SJT için seçeneklerinin ağırlıklı olduğu
# değişkenlerden biri üzerinden)
# ============================================================================

def _dal_haritasi_olustur(db: Session) -> dict[int, tuple[str, str]]:
    """soru_id -> (dal_kod, dal_adi) haritası, yalnızca K5 soruları için dolu olur."""
    harita: dict[int, tuple[str, str]] = {}

    # Likert: soru.degisken_id -> degisken.dal_id
    likert_satirlari = (
        db.query(Soru.id, Dal.kod, Dal.ad)
        .join(Degisken, Degisken.id == Soru.degisken_id)
        .join(Dal, Dal.id == Degisken.dal_id)
        .filter(Soru.soru_tipi == "likert", Degisken.dal_id.isnot(None))
        .all()
    )
    for soru_id, dal_kod, dal_ad in likert_satirlari:
        harita[soru_id] = (dal_kod, dal_ad)

    # SJT: soru -> seçenekleri -> sjt ağırlıkları -> değişken -> dal (ilk bulunanı kullan)
    sjt_satirlari = (
        db.query(SoruSecenegi.soru_id, Dal.kod, Dal.ad)
        .join(SjtSecenekDegiskenAgirlik, SjtSecenekDegiskenAgirlik.secenek_id == SoruSecenegi.id)
        .join(Degisken, Degisken.id == SjtSecenekDegiskenAgirlik.degisken_id)
        .join(Dal, Dal.id == Degisken.dal_id)
        .filter(Degisken.dal_id.isnot(None))
        .all()
    )
    for soru_id, dal_kod, dal_ad in sjt_satirlari:
        harita.setdefault(soru_id, (dal_kod, dal_ad))

    return harita


# ============================================================================
# Uç noktalar
# ============================================================================

@router.get("/dallar", response_model=list[DalFiltreOut])
def dal_filtre_listesi(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    dallar = db.query(Dal).order_by(Dal.kod).all()
    return [DalFiltreOut(kod=d.kod, ad=d.ad) for d in dallar]


@router.get("", response_model=SayfalanmisSorularOut)
def sorulari_detayli_listele(
    katman_kod: str | None = None,
    dal_kod: str | None = None,
    aktif_mi: bool | None = None,
    sayfa: int = 1,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sorgu = db.query(Soru, Katman.kod).join(Katman, Katman.id == Soru.katman_id)
    if katman_kod:
        sorgu = sorgu.filter(Katman.kod == katman_kod)
    if aktif_mi is not None:
        sorgu = sorgu.filter(Soru.aktif_mi == aktif_mi)

    tum_satirlar = sorgu.order_by(Soru.id).all()
    dal_haritasi = _dal_haritasi_olustur(db) if (katman_kod == "K5" or dal_kod) else {}

    # dal_kod filtresi Python tarafında uygulanıyor (haritalama SQL join'e taşınabilir
    # ama K5 soru sayısı küçük olduğu için performans sorun değil)
    if dal_kod:
        tum_satirlar = [(s, kk) for s, kk in tum_satirlar if dal_haritasi.get(s.id, (None, None))[0] == dal_kod]

    toplam = len(tum_satirlar)
    toplam_sayfa = max(1, (toplam + SAYFA_BOYUTU - 1) // SAYFA_BOYUTU)
    sayfa = max(1, min(sayfa, toplam_sayfa))
    baslangic = (sayfa - 1) * SAYFA_BOYUTU
    sayfa_satirlari = tum_satirlar[baslangic:baslangic + SAYFA_BOYUTU]

    soru_idler = [s.id for s, _ in sayfa_satirlari]
    degisken_kodlari = dict(db.query(Degisken.id, Degisken.kod).all())

    tum_secenekler = (
        db.query(SoruSecenegi)
        .filter(SoruSecenegi.soru_id.in_(soru_idler))
        .order_by(SoruSecenegi.soru_id, SoruSecenegi.secenek_sirasi)
        .all()
    )
    secenek_idler = [sec.id for sec in tum_secenekler]
    agirliklar = (
        db.query(SjtSecenekDegiskenAgirlik, Degisken.kod)
        .join(Degisken, Degisken.id == SjtSecenekDegiskenAgirlik.degisken_id)
        .filter(SjtSecenekDegiskenAgirlik.secenek_id.in_(secenek_idler))
        .all()
    )
    agirlik_by_secenek: dict[int, list[dict]] = {}
    for a, degisken_kod in agirliklar:
        agirlik_by_secenek.setdefault(a.secenek_id, []).append(
            {"degisken_kod": degisken_kod, "agirlik": float(a.agirlik)}
        )

    secenekler_by_soru: dict[int, list[SecenekDetayOut]] = {}
    for sec in tum_secenekler:
        secenekler_by_soru.setdefault(sec.soru_id, []).append(SecenekDetayOut(
            id=sec.id, secenek_sirasi=sec.secenek_sirasi, secenek_metni=sec.secenek_metni,
            sjt_agirliklar=agirlik_by_secenek.get(sec.id, []),
        ))

    sonuc = []
    for s, katman_kodu in sayfa_satirlari:
        dal_kodu, dal_adi = dal_haritasi.get(s.id, (None, None))
        sonuc.append(SoruDetayOut(
            id=s.id, katman_kod=katman_kodu, dal_kod=dal_kodu, dal_adi=dal_adi,
            soru_tipi=s.soru_tipi, degisken_kod=degisken_kodlari.get(s.degisken_id),
            soru_metni=s.soru_metni, ters_kodlanmis_mi=s.ters_kodlanmis_mi, aktif_mi=s.aktif_mi,
            secenekler=secenekler_by_soru.get(s.id, []),
        ))

    return SayfalanmisSorularOut(
        sorular=sonuc, toplam_soru_sayisi=toplam,
        toplam_sayfa_sayisi=toplam_sayfa, su_anki_sayfa=sayfa,
    )


@router.put("/soru/{soru_id}", status_code=204)
def soru_metnini_guncelle(
    soru_id: int,
    istek: SoruMetniGuncelleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    soru = db.get(Soru, soru_id)
    if soru is None:
        raise HTTPException(status_code=404, detail="Soru bulunamadı.")
    if not istek.soru_metni.strip():
        raise HTTPException(status_code=400, detail="Soru metni boş olamaz.")
    soru.soru_metni = istek.soru_metni.strip()
    db.commit()


@router.put("/secenek/{secenek_id}", status_code=204)
def secenek_metnini_guncelle(
    secenek_id: int,
    istek: SecenekMetniGuncelleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    secenek = db.get(SoruSecenegi, secenek_id)
    if secenek is None:
        raise HTTPException(status_code=404, detail="Seçenek bulunamadı.")
    if not istek.secenek_metni.strip():
        raise HTTPException(status_code=400, detail="Seçenek metni boş olamaz.")
    secenek.secenek_metni = istek.secenek_metni.strip()
    db.commit()
