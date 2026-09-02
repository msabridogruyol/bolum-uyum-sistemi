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


class DalDetayOut(BaseModel):
    id: int
    kod: str
    ad: str
    dogrulama_durumu: str
    bolum_sayisi: int
    degisken_sayisi: int
    soru_sayisi: int
    coklu_kaynakli_mi: bool  # kaynak1 (model) VE kaynak2 (kümeleme) ikisi de dolu mu


@router.get("/dallar-detay", response_model=list[DalDetayOut])
def dallari_detayli_listele(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    from app.models import BolumDalEslesme

    dallar = db.query(Dal).order_by(Dal.kod).all()

    bolum_sayilari = dict(
        db.query(BolumDalEslesme.dal_id, func.count(BolumDalEslesme.id))
        .group_by(BolumDalEslesme.dal_id).all()
    )
    degisken_sayilari = dict(
        db.query(Degisken.dal_id, func.count(Degisken.id))
        .filter(Degisken.dal_id.isnot(None))
        .group_by(Degisken.dal_id).all()
    )
    # bir dalın soru sayısı = o dala bağlı değişkenlerin (likert) + o değişkenlere
    # ağırlıklı seçeneği olan sorularının (sjt) birleşimi — basitlik için
    # değişken bazlı likert soru sayımı + benzersiz sjt soru sayımı toplanır
    degisken_id_to_dal = dict(
        db.query(Degisken.id, Degisken.dal_id).filter(Degisken.dal_id.isnot(None)).all()
    )
    likert_soru_sayilari: dict[int, int] = {}
    for degisken_id, adet in db.query(Soru.degisken_id, func.count(Soru.id)).filter(
        Soru.soru_tipi == "likert", Soru.degisken_id.in_(degisken_id_to_dal.keys())
    ).group_by(Soru.degisken_id).all():
        dal_id = degisken_id_to_dal[degisken_id]
        likert_soru_sayilari[dal_id] = likert_soru_sayilari.get(dal_id, 0) + adet

    sjt_soru_id_by_dal: dict[int, set] = {}
    sjt_satirlari = (
        db.query(SoruSecenegi.soru_id, Degisken.dal_id)
        .join(SjtSecenekDegiskenAgirlik, SjtSecenekDegiskenAgirlik.secenek_id == SoruSecenegi.id)
        .join(Degisken, Degisken.id == SjtSecenekDegiskenAgirlik.degisken_id)
        .filter(Degisken.dal_id.isnot(None))
        .all()
    )
    for soru_id, dal_id in sjt_satirlari:
        sjt_soru_id_by_dal.setdefault(dal_id, set()).add(soru_id)

    sonuc = []
    for d in dallar:
        soru_sayisi = likert_soru_sayilari.get(d.id, 0) + len(sjt_soru_id_by_dal.get(d.id, set()))
        coklu_kaynakli = False
        eslesme = db.query(BolumDalEslesme).filter(BolumDalEslesme.dal_id == d.id).first()
        if eslesme and eslesme.kaynak2_kumeleme_dal_id and any([
            eslesme.kaynak1_model_a_dal_id, eslesme.kaynak1_model_b_dal_id, eslesme.kaynak1_model_c_dal_id,
        ]):
            coklu_kaynakli = True
        sonuc.append(DalDetayOut(
            id=d.id, kod=d.kod, ad=d.ad, dogrulama_durumu=d.dogrulama_durumu,
            bolum_sayisi=bolum_sayilari.get(d.id, 0),
            degisken_sayisi=degisken_sayilari.get(d.id, 0),
            soru_sayisi=soru_sayisi,
            coklu_kaynakli_mi=coklu_kaynakli,
        ))
    return sonuc


class OzetOut(BaseModel):
    toplam: int
    likert_sayisi: int
    sjt_sayisi: int
    aktif_sayisi: int
    pasif_sayisi: int
    degisken_bazli: list[dict]  # [{"degisken_kod": "D1", "soru_sayisi": 3}, ...]


class DegiskenFiltreOut(BaseModel):
    kod: str
    ad: str


@router.get("/degiskenler", response_model=list[DegiskenFiltreOut])
def katman_degiskenleri_listele(
    katman_kod: str,
    dal_kod: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """Filtre menüsü için — bir katmandaki (K5'te isteğe bağlı bir dal içindeki) değişkenler."""
    sorgu = (
        db.query(Degisken.kod, Degisken.ad)
        .join(Katman, Katman.id == Degisken.katman_id)
        .filter(Katman.kod == katman_kod)
    )
    if dal_kod:
        sorgu = sorgu.join(Dal, Dal.id == Degisken.dal_id).filter(Dal.kod == dal_kod)
    satirlar = sorgu.order_by(Degisken.sira).all()
    return [DegiskenFiltreOut(kod=k, ad=a) for k, a in satirlar]


@router.get("/ozet", response_model=OzetOut)
def katman_ozeti_getir(
    katman_kod: str,
    dal_kod: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """Bir katmanın (K5'te isteğe bağlı bir dalın) özet istatistikleri."""
    sorgu = db.query(Soru).join(Katman, Katman.id == Soru.katman_id).filter(Katman.kod == katman_kod)
    tum_sorular = sorgu.all()

    if dal_kod:
        dal_haritasi = _dal_haritasi_olustur(db)
        tum_sorular = [s for s in tum_sorular if dal_haritasi.get(s.id, (None, None))[0] == dal_kod]

    degisken_kodlari = dict(db.query(Degisken.id, Degisken.kod).all())
    degisken_sayaci: dict[str, int] = {}
    for s in tum_sorular:
        if s.degisken_id and s.degisken_id in degisken_kodlari:
            kod = degisken_kodlari[s.degisken_id]
            degisken_sayaci[kod] = degisken_sayaci.get(kod, 0) + 1

    return OzetOut(
        toplam=len(tum_sorular),
        likert_sayisi=sum(1 for s in tum_sorular if s.soru_tipi == "likert"),
        sjt_sayisi=sum(1 for s in tum_sorular if s.soru_tipi == "sjt"),
        aktif_sayisi=sum(1 for s in tum_sorular if s.aktif_mi),
        pasif_sayisi=sum(1 for s in tum_sorular if not s.aktif_mi),
        degisken_bazli=[{"degisken_kod": k, "soru_sayisi": v} for k, v in sorted(degisken_sayaci.items())],
    )


@router.get("", response_model=SayfalanmisSorularOut)
def sorulari_detayli_listele(
    katman_kod: str | None = None,
    dal_kod: str | None = None,
    degisken_kod: str | None = None,
    soru_tipi: str | None = None,
    aktif_mi: bool | None = None,
    arama: str | None = None,
    sayfa: int = 1,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sorgu = db.query(Soru, Katman.kod).join(Katman, Katman.id == Soru.katman_id)
    if katman_kod:
        sorgu = sorgu.filter(Katman.kod == katman_kod)
    if aktif_mi is not None:
        sorgu = sorgu.filter(Soru.aktif_mi == aktif_mi)
    if soru_tipi:
        sorgu = sorgu.filter(Soru.soru_tipi == soru_tipi)
    if arama and arama.strip():
        sorgu = sorgu.filter(Soru.soru_metni.ilike(f"%{arama.strip()}%"))
    if degisken_kod:
        sorgu = sorgu.join(Degisken, Degisken.id == Soru.degisken_id).filter(Degisken.kod == degisken_kod)

    tum_satirlar = sorgu.order_by(Soru.id).all()
    dal_haritasi = _dal_haritasi_olustur(db) if (katman_kod == "K5" or dal_kod) else {}

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
