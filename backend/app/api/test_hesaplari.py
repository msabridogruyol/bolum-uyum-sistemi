# -*- coding: utf-8 -*-
"""
[2026-10-10] Test hesapları — YALNIZCA SÜPER ADMİN.

GET    /yonetim/test-hesaplari                          — test öğrencileri + test okul yetkilileri + okul listesi
POST   /yonetim/test-hesaplari                          — yeni test hesabı (öğrenci | okul_yetkilisi)
POST   /yonetim/test-hesaplari/{tip}/{id}/baglanti      — giriş bağlantısı üret (süreli; eskisini geçersiz kılar)
DELETE /yonetim/test-hesaplari/{tip}/{id}/baglanti      — bağlantıyı iptal et
POST   /yonetim/test-hesaplari/{tip}/{id}/sifre         — yeni şifre (2 adımsız normal giriş için)
POST   /yonetim/test-hesaplari/ogrenci/{id}/senaryo     — ilerlemeyi senaryoya göre kur (gerçek akışla cevaplar)
DELETE /yonetim/test-hesaplari/{tip}/{id}               — test hesabını sil
POST   /auth/test-giris                                 — bağlantı anahtarıyla giriş (herkese açık uç; yalnızca test hesapları)

Güvenlik: bağlantı anahtarı rastgele 32 karakter, veritabanında yalnızca SHA-256 özeti tutulur, süresi dolar,
yalnızca test_hesabi=True hesaplarda çalışır ve her üretim/iptal/giriş Audit Log'a yazılır.
"""
import re
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz, gecici_sifre, ogrenciyi_sil, olay_yaz, simdi
from app.core.katman_servisi import IsKuraliHatasi
from app.core.security import erisim_tokeni_uret, sifre_hashle, yenileme_tokeni_uret
from app.core.test_hesabi_servisi import (
    ASAMA_ADI, anahtar_ozeti, giris_anahtari_uret, ilerleme_ozeti, ilerlemeyi_sifirla, senaryo_uygula,
)
from app.models import AdminKullanici, Bolum, Ogrenci, Okul

router = APIRouter(prefix="/yonetim/test-hesaplari", tags=["Test hesapları (süper admin)"])
giris_router = APIRouter(tags=["Kimlik Doğrulama"])

TIPLER = {"ogrenci", "okul_yetkilisi"}


class YeniTestIstek(BaseModel):
    tip: str
    ad_soyad: str = Field(min_length=3, max_length=80)
    okul_id: int | None = None
    sinif: str | None = "11"


class BaglantiIstek(BaseModel):
    saat: int = 24


class SenaryoIstek(BaseModel):
    asama: str = "tamamlandi"
    yarim: bool = False
    egilim: str = "rastgele"            # rastgele | dengeli | bolum
    egilim_bolum_id: int | None = None
    gun_once: int = 3
    yeni_tur_hazir: bool = False
    onceki_tur: bool = False
    hedef: str = "otomatik"             # yok | otomatik | <bolum_id>
    tamamlanan_adim: int = 0
    listem_otomatik: bool = True
    tohum: int | None = None


class TestGirisIstek(BaseModel):
    anahtar: str = Field(min_length=10, max_length=100)


def _hesap(db: Session, tip: str, hesap_id: str):
    if tip not in TIPLER:
        raise HTTPException(status_code=404, detail="Geçersiz hesap tipi.")
    try:
        h = db.get(Ogrenci if tip == "ogrenci" else AdminKullanici, uuid.UUID(hesap_id))
    except ValueError:
        h = None
    if h is None or not getattr(h, "test_hesabi", False):
        raise HTTPException(status_code=404, detail="Test hesabı bulunamadı.")
    return h


def _baglanti_durumu(h) -> dict:
    bitis = h.test_giris_bitis
    gecerli = bool(h.test_giris_anahtari and bitis and bitis > simdi())
    return {"baglanti_var": gecerli, "baglanti_bitis": bitis if gecerli else None}


@router.get("")
def test_hesaplari(db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    okullar = {o.id: o.ad for o in db.query(Okul).order_by(Okul.ad).all()}
    ogr = db.query(Ogrenci).filter(Ogrenci.test_hesabi.is_(True)).order_by(Ogrenci.olusturulma_zamani.desc()).all()
    yet = db.query(AdminKullanici).filter(AdminKullanici.test_hesabi.is_(True)).order_by(AdminKullanici.olusturulma_zamani.desc()).all()
    return {
        "ogrenciler": [{"id": str(o.id), "ad_soyad": o.ad_soyad, "email": o.email, "okul_id": o.okul_id,
                        "okul_ad": okullar.get(o.okul_id, "Okul harici"), "sinif": o.sinif,
                        "ilerleme": ilerleme_ozeti(db, o), "son_giris_zamani": o.son_giris_zamani, **_baglanti_durumu(o)}
                       for o in ogr],
        "yetkililer": [{"id": str(y.id), "ad_soyad": y.ad_soyad, "email": y.email, "okul_id": y.okul_id,
                        "okul_ad": okullar.get(y.okul_id, "—"), "son_giris_zamani": y.son_giris_zamani, **_baglanti_durumu(y)}
                       for y in yet],
        "okullar": [{"id": k, "ad": v} for k, v in okullar.items()],
        "asamalar": [{"kod": k, "ad": v} for k, v in ASAMA_ADI.items()],
    }


def _kvkk_onayla(db: Session, tip: str, hesap_id) -> None:
    from app.core import hesap_guvenligi_servisi as hg
    from app.core.kvkk_metinleri import TUM_KODLAR
    try:
        hg.kvkk_kaydet(db, tip, hesap_id, {k: True for k in TUM_KODLAR}, "test-hesabi", tam_kayit=True)
    except Exception:
        pass   # KVKK tablosu bu ortamda yoksa hesap yine açılır


@router.post("", status_code=201)
def test_hesabi_ac(istek: YeniTestIstek, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    if istek.tip not in TIPLER:
        raise HTTPException(status_code=400, detail="Hesap tipi öğrenci ya da okul yetkilisi olmalı.")
    okul = db.get(Okul, istek.okul_id) if istek.okul_id else None
    if istek.tip == "okul_yetkilisi" and okul is None:
        raise HTTPException(status_code=400, detail="Okul yetkilisi için okul seçin.")
    ad = re.sub(r"\s+", " ", istek.ad_soyad).strip()
    ek = secrets.token_hex(3)
    sifre = gecici_sifre()
    if istek.tip == "ogrenci":
        h = Ogrenci(ad_soyad=ad, email=f"test.ogrenci.{ek}@test.filizyol.app", sifre_hash=sifre_hashle(sifre),
                    okul_id=okul.id if okul else None, okul=okul.ad if okul else None, sinif=(istek.sinif or "11")[:10],
                    sifre_degistirmeli=False, test_hesabi=True, olusturulma_zamani=simdi())
        db.add(h); db.flush()
        _kvkk_onayla(db, "ogrenci", h.id)
        olay_yaz(db, h.id, "hesap_acildi", "Test hesabı", admin.ad_soyad)
    else:
        h = AdminKullanici(ad_soyad=ad, email=f"test.yetkili.{ek}@test.filizyol.app", sifre_hash=sifre_hashle(sifre),
                           rol="okul_yetkilisi", okul_id=okul.id, aktif_mi=True, sifre_degistirmeli=False,
                           test_hesabi=True, olusturulma_zamani=simdi())
        db.add(h); db.flush()
        _kvkk_onayla(db, "yonetim", h.id)
    denetim_yaz(db, admin, "test_hesabi_ac", "ogrenciler" if istek.tip == "ogrenci" else "admin_kullanicilar", h.id,
                f"{istek.tip}: {ad} <{h.email}>", okul.id if okul else None)
    db.commit()
    return {"id": str(h.id), "tip": istek.tip, "ad_soyad": ad, "email": h.email, "sifre": sifre}


@router.post("/{tip}/{hesap_id}/baglanti")
def baglanti_uret(tip: str, hesap_id: str, istek: BaglantiIstek, db: Session = Depends(get_db),
                  admin: AdminKullanici = Depends(get_mevcut_admin)):
    h = _hesap(db, tip, hesap_id)
    anahtar = giris_anahtari_uret(h, istek.saat)
    denetim_yaz(db, admin, "test_baglanti_uret", tip, h.id, f"{h.ad_soyad}: {istek.saat} saat geçerli", h.okul_id)
    db.commit()
    return {"yol": f"/test-giris?k={anahtar}", "bitis": h.test_giris_bitis}


@router.delete("/{tip}/{hesap_id}/baglanti", status_code=204)
def baglanti_iptal(tip: str, hesap_id: str, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    h = _hesap(db, tip, hesap_id)
    h.test_giris_anahtari, h.test_giris_bitis = None, None
    denetim_yaz(db, admin, "test_baglanti_iptal", tip, h.id, h.ad_soyad, h.okul_id)
    db.commit()


@router.post("/{tip}/{hesap_id}/sifre")
def sifre_yenile(tip: str, hesap_id: str, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    h = _hesap(db, tip, hesap_id)
    sifre = gecici_sifre()
    h.sifre_hash = sifre_hashle(sifre)
    h.sifre_degistirmeli = False
    denetim_yaz(db, admin, "test_sifre_yenile", tip, h.id, h.ad_soyad, h.okul_id)
    db.commit()
    return {"email": h.email, "sifre": sifre}


@router.post("/ogrenci/{hesap_id}/senaryo")
def senaryo(hesap_id: str, istek: SenaryoIstek, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    o = _hesap(db, "ogrenci", hesap_id)
    if istek.egilim == "bolum" and (not istek.egilim_bolum_id or db.get(Bolum, istek.egilim_bolum_id) is None):
        raise HTTPException(status_code=400, detail="Eğilim için bölüm seçin.")
    try:
        ozet = senaryo_uygula(db, o, istek.model_dump())
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    denetim_yaz(db, admin, "test_senaryo", "ogrenciler", o.id, f"{o.ad_soyad}: {ozet['asama']}", o.okul_id)
    db.commit()
    return {**ozet, "ilerleme": ilerleme_ozeti(db, o)}


@router.delete("/{tip}/{hesap_id}", status_code=204)
def test_hesabi_sil(tip: str, hesap_id: str, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_admin)):
    h = _hesap(db, tip, hesap_id)
    etiket, okul_id, hid = f"{h.ad_soyad} <{h.email}>", h.okul_id, h.id
    try:
        if tip == "ogrenci":
            ilerlemeyi_sifirla(db, h)           # bağlı tüm kayıtlar (CASCADE eksik olsa da) önce temizlenir
            from sqlalchemy import text
            with db.begin_nested():
                db.execute(text("DELETE FROM ogrenci_hesap_olaylari WHERE ogrenci_id = :id"), {"id": h.id})
            ogrenciyi_sil(db, h)
        else:
            _yonetici_baglarini_coz(db, h.id, admin.id)
            db.delete(h)
        db.flush()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Test hesabı silinemedi: {type(e).__name__}: {str(e).splitlines()[0][:200]}")
    denetim_yaz(db, admin, "test_hesabi_sil", tip, hid, etiket, okul_id)
    db.commit()


def _yonetici_baglarini_coz(db: Session, silinen_id, yapan_id) -> None:
    """admin_kullanicilar'a bağlı kayıtlar (audit_log, meslek_dili, parametreler …): bağ NULL yapılır;
    sütun NULL olamıyorsa kayıt silmeyi yapan süper admine devredilir (kayıt kaybolmaz)."""
    from sqlalchemy import text
    baglar = db.execute(text("""
        SELECT c.conrelid::regclass::text AS tablo, a.attname AS sutun, a.attnotnull AS zorunlu
        FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
        WHERE c.contype = 'f' AND c.confrelid = 'admin_kullanicilar'::regclass""")).all()
    for tablo, sutun, zorunlu in baglar:
        deger = yapan_id if zorunlu else None
        with db.begin_nested():
            db.execute(text(f'UPDATE {tablo} SET "{sutun}" = :d WHERE "{sutun}" = :id'), {"d": deger, "id": silinen_id})


# ----------------------------------------------------------------------------- bağlantıyla giriş
@giris_router.post("/auth/test-giris")
def test_giris(istek: TestGirisIstek, db: Session = Depends(get_db)):
    hata = HTTPException(status_code=401, detail="Bu test bağlantısı geçersiz ya da süresi dolmuş. Süper adminden yeni bağlantı isteyin.")
    ozet = anahtar_ozeti(istek.anahtar.strip())
    o = db.query(Ogrenci).filter(Ogrenci.test_giris_anahtari == ozet, Ogrenci.test_hesabi.is_(True)).first()
    h = o or db.query(AdminKullanici).filter(AdminKullanici.test_giris_anahtari == ozet,
                                             AdminKullanici.test_hesabi.is_(True)).first()
    if h is None or not h.test_giris_bitis or h.test_giris_bitis <= simdi():
        raise hata
    if o is None and h.aktif_mi is False:
        raise hata
    rol = "ogrenci" if o is not None else h.rol
    h.son_giris_zamani = simdi()
    if o is not None:
        olay_yaz(db, o.id, "giris", "Test bağlantısıyla", "Test")
    db.commit()
    return {"kapsam": "ogrenci" if o is not None else "admin", "kullanici_tipi": rol, "ad_soyad": h.ad_soyad,
            "erisim_tokeni": erisim_tokeni_uret(h.id, rol), "yenileme_tokeni": yenileme_tokeni_uret(h.id, rol)}
