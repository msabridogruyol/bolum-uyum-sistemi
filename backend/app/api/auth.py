"""
Kimlik doğrulama uç noktaları — D1.
POST /auth/kayit                 — yeni öğrenci hesabı (KVKK onaylarıyla)
POST /auth/giris                 — e-posta+şifre; gerekiyorsa 2 adımlı doğrulama başlatır
POST /auth/iki-adim/dogrula      — e-postaya gelen kodla girişi tamamlar
POST /auth/iki-adim/tekrar       — yeni kod gönderir
POST /auth/yenile                — refresh token ile yeni access token
POST /auth/sifremi-unuttum       — şifre sıfırlama bağlantısı gönderir (her zaman aynı cevap)
GET  /auth/sifre-sifirla/bilgi   — bağlantı geçerli mi (şifre belirleme ekranı için)
POST /auth/sifre-sifirla         — yeni şifreyi kaydeder
GET  /auth/kvkk-metinleri        — aydınlatma metni ve onay maddeleri
"""
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    sifre_hashle, sifre_dogrula,
    erisim_tokeni_uret, yenileme_tokeni_uret, token_coz, _token_uret,
)
from app.core.katman_servisi import IsKuraliHatasi
from app.core import hesap_guvenligi_servisi as hg
from app.models import Ogrenci, AdminKullanici
from app.schemas.auth import (
    OgrenciKayitIstekV2, GirisIstekV2, GirisCevap, TokenCifti, YenilemeIstek, OgrenciProfil,
    IkiAdimDogrulaIstek, IkiAdimTekrarIstek, SifremiUnuttumIstek, SifreSifirlaIstek, TokenBilgisiOut,
)

router = APIRouter()


def istemci_ip(request: Request) -> str | None:
    ileri = request.headers.get("x-forwarded-for")
    if ileri:
        return ileri.split(",")[0].strip()
    return request.client.host if request.client else None


def _kullanici_tipi(rol: str) -> str:
    return "ogrenci" if rol == "ogrenci" else "yonetim"


def giris_sonucu(db: Session, hesap, rol: str, cihaz_tokeni: str | None) -> GirisCevap:
    """Şifre doğrulandıktan sonra: 2 adım gerekiyorsa kod gönder, gerekmiyorsa token ver."""
    tip = _kullanici_tipi(rol)
    if hg.iki_adim_aktif_mi(db) and not hg.cihaz_guvenilir_mi(db, tip, hesap.id, cihaz_tokeni):
        try:
            hg.dogrulama_kodu_gonder(db, tip, hesap.id, hesap.email, hesap.ad_soyad)
        except IsKuraliHatasi as e:
            db.rollback()
            raise HTTPException(status_code=503, detail=str(e))
        db.commit()
        return GirisCevap(iki_adim_gerekli=True, maskeli_eposta=hg.maskeli_eposta(hesap.email), kullanici_tipi=rol,
                          gecici_token=_token_uret(str(hesap.id), rol, timedelta(minutes=10), "iki_adim"))
    db.commit()
    return GirisCevap(erisim_tokeni=erisim_tokeni_uret(hesap.id, rol), yenileme_tokeni=yenileme_tokeni_uret(hesap.id, rol),
                      kullanici_tipi=rol)


def gecici_tokeni_coz(db: Session, gecici_token: str, izinli_roller: set[str]):
    payload = token_coz(gecici_token)
    if payload is None or payload.get("tip") != "iki_adim" or payload.get("rol") not in izinli_roller:
        raise HTTPException(status_code=401, detail="Doğrulama süresi doldu. Lütfen tekrar giriş yap.")
    try:
        kid = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Doğrulama süresi doldu. Lütfen tekrar giriş yap.")
    rol = payload["rol"]
    hesap = db.get(Ogrenci, kid) if rol == "ogrenci" else db.get(AdminKullanici, kid)
    if hesap is None or (rol != "ogrenci" and hesap.rol != rol):
        raise HTTPException(status_code=401, detail="Doğrulama süresi doldu. Lütfen tekrar giriş yap.")
    return hesap, rol


def iki_adim_tamamla(db: Session, istek: IkiAdimDogrulaIstek, izinli_roller: set[str]) -> GirisCevap:
    hesap, rol = gecici_tokeni_coz(db, istek.gecici_token, izinli_roller)
    tip = _kullanici_tipi(rol)
    try:
        hg.dogrulama_kodunu_kontrol_et(db, tip, hesap.id, istek.kod)
    except IsKuraliHatasi as e:
        db.commit()  # deneme sayısı kaydedilsin
        raise HTTPException(status_code=400, detail=str(e))
    cihaz = hg.cihaz_kaydet(db, tip, hesap.id) if istek.cihazi_hatirla else None
    db.commit()
    return GirisCevap(erisim_tokeni=erisim_tokeni_uret(hesap.id, rol), yenileme_tokeni=yenileme_tokeni_uret(hesap.id, rol),
                      kullanici_tipi=rol, cihaz_tokeni=cihaz)


def kodu_tekrar_gonder(db: Session, istek: IkiAdimTekrarIstek, izinli_roller: set[str]) -> None:
    hesap, rol = gecici_tokeni_coz(db, istek.gecici_token, izinli_roller)
    try:
        hg.dogrulama_kodu_gonder(db, _kullanici_tipi(rol), hesap.id, hesap.email, hesap.ad_soyad, tekrar=True)
    except hg.BeklemeHatasi as e:
        db.rollback()
        raise HTTPException(status_code=429, detail=str(e))
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(e))
    db.commit()


# ----------------------------------------------------------------------------- kayıt / giriş
@router.post("/kayit", response_model=OgrenciProfil, status_code=status.HTTP_201_CREATED)
def kayit_ol(istek: OgrenciKayitIstekV2, request: Request, db: Session = Depends(get_db)):
    email = istek.email.strip()
    mevcut = db.query(Ogrenci).filter(func.lower(Ogrenci.email) == email.lower()).first()
    if mevcut is not None:
        raise HTTPException(status_code=400, detail="Bu e-posta ile zaten bir hesap var.")

    ogrenci = Ogrenci(ad_soyad=istek.ad_soyad.strip(), email=email, sifre_hash=sifre_hashle(istek.sifre))
    db.add(ogrenci)
    db.flush()
    if istek.kvkk is not None:
        try:
            hg.kvkk_kaydet(db, "ogrenci", ogrenci.id, istek.kvkk, istemci_ip(request), tam_kayit=True)
        except IsKuraliHatasi as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    db.refresh(ogrenci)
    return OgrenciProfil(id=str(ogrenci.id), ad_soyad=ogrenci.ad_soyad, email=ogrenci.email)


@router.post("/giris", response_model=GirisCevap)
def giris_yap(istek: GirisIstekV2, db: Session = Depends(get_db)):
    """Öğrenci ve rehber öğretmenler bu sayfadan giriş yapar."""
    hata = HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")
    email = istek.email.strip().lower()

    ogrenci = db.query(Ogrenci).filter(func.lower(Ogrenci.email) == email).first()
    if ogrenci is not None and sifre_dogrula(istek.sifre, ogrenci.sifre_hash):
        return giris_sonucu(db, ogrenci, "ogrenci", istek.cihaz_tokeni)

    rehber = db.query(AdminKullanici).filter(func.lower(AdminKullanici.email) == email, AdminKullanici.rol == "rehber").first()
    if rehber is not None and sifre_dogrula(istek.sifre, rehber.sifre_hash):
        if getattr(rehber, "aktif_mi", True) is False:
            raise HTTPException(status_code=403, detail="Hesabın yönetim tarafından devre dışı bırakılmış.")
        return giris_sonucu(db, rehber, "rehber", istek.cihaz_tokeni)
    raise hata


@router.post("/iki-adim/dogrula", response_model=GirisCevap)
def iki_adim_dogrula(istek: IkiAdimDogrulaIstek, db: Session = Depends(get_db)):
    return iki_adim_tamamla(db, istek, {"ogrenci", "rehber"})


@router.post("/iki-adim/tekrar", status_code=204)
def iki_adim_tekrar(istek: IkiAdimTekrarIstek, db: Session = Depends(get_db)):
    kodu_tekrar_gonder(db, istek, {"ogrenci", "rehber"})


@router.post("/yenile", response_model=TokenCifti)
def token_yenile(istek: YenilemeIstek, db: Session = Depends(get_db)):
    hata = HTTPException(status_code=401, detail="Geçersiz yenileme tokeni.")

    payload = token_coz(istek.yenileme_tokeni)
    if payload is None or payload.get("tip") != "refresh":
        raise hata
    try:
        kid = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise hata

    rol = payload.get("rol", "ogrenci")
    if rol == "ogrenci":
        hesap = db.get(Ogrenci, kid)
    elif rol == "rehber":
        hesap = db.get(AdminKullanici, kid)
        if hesap is not None and hesap.rol != "rehber":
            hesap = None
    else:
        raise hata
    if hesap is None:
        raise hata
    return TokenCifti(erisim_tokeni=erisim_tokeni_uret(hesap.id, rol), yenileme_tokeni=yenileme_tokeni_uret(hesap.id, rol))


# ----------------------------------------------------------------------------- şifre sıfırlama
SIFIRLAMA_MESAJI = {"mesaj": "Bu e-posta adresi kayıtlıysa şifre sıfırlama bağlantısı gönderildi. Gelen kutunu (ve spam klasörünü) kontrol et."}


@router.post("/sifremi-unuttum")
def sifremi_unuttum(istek: SifremiUnuttumIstek, request: Request, db: Session = Depends(get_db)):
    hg.sifirlama_baglantisi_gonder(db, istek.email, "ogrenci", request.headers.get("origin"))
    db.commit()
    return SIFIRLAMA_MESAJI


@router.get("/sifre-sifirla/bilgi", response_model=TokenBilgisiOut)
def sifre_sifirlama_bilgisi(token: str, db: Session = Depends(get_db)):
    try:
        return TokenBilgisiOut(**hg.token_bilgisi(db, token))
    except IsKuraliHatasi as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sifre-sifirla")
def sifreyi_sifirla(istek: SifreSifirlaIstek, db: Session = Depends(get_db)):
    try:
        hg.sifreyi_sifirla(db, istek.token, istek.yeni_sifre)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    return {"mesaj": "Şifren güncellendi. Yeni şifrenle giriş yapabilirsin."}


# ----------------------------------------------------------------------------- KVKK
@router.get("/kvkk-metinleri")
def kvkk_metinlerini_getir():
    return hg.kvkk_metinleri()
