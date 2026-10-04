"""
Admin kimlik doğrulaması — öğrenciden AYRI bir giriş akışı.
Kaynak: veritabani_taslagi.md 3.3, sistem_genel_anlatim.md E) bölümü.

NOT: Admin kayıt (self-servis) uç noktası KASITLI OLARAK yok.
[2026-10-04] 2 adımlı doğrulama + şifremi unuttum eklendi. Rehber öğretmenler bu sayfadan değil,
öğrenci giriş sayfasından girer.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import sifre_dogrula
from app.core import hesap_guvenligi_servisi as hg
from app.models import AdminKullanici
from app.schemas.auth import GirisIstekV2, GirisCevap, IkiAdimDogrulaIstek, IkiAdimTekrarIstek, SifremiUnuttumIstek
from app.api.auth import giris_sonucu, iki_adim_tamamla, kodu_tekrar_gonder, SIFIRLAMA_MESAJI

router = APIRouter()
YONETIM_ROLLERI = {"super_admin", "icerik_editoru"}


@router.post("/giris", response_model=GirisCevap)
def admin_giris_yap(istek: GirisIstekV2, db: Session = Depends(get_db)):
    hata = HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")
    admin = db.query(AdminKullanici).filter(func.lower(AdminKullanici.email) == istek.email.strip().lower()).first()
    if admin is None or admin.rol not in YONETIM_ROLLERI or not sifre_dogrula(istek.sifre, admin.sifre_hash):
        raise hata
    return giris_sonucu(db, admin, admin.rol, istek.cihaz_tokeni)


@router.post("/iki-adim/dogrula", response_model=GirisCevap)
def admin_iki_adim_dogrula(istek: IkiAdimDogrulaIstek, db: Session = Depends(get_db)):
    return iki_adim_tamamla(db, istek, YONETIM_ROLLERI)


@router.post("/iki-adim/tekrar", status_code=204)
def admin_iki_adim_tekrar(istek: IkiAdimTekrarIstek, db: Session = Depends(get_db)):
    kodu_tekrar_gonder(db, istek, YONETIM_ROLLERI)


@router.post("/sifremi-unuttum")
def admin_sifremi_unuttum(istek: SifremiUnuttumIstek, request: Request, db: Session = Depends(get_db)):
    hg.sifirlama_baglantisi_gonder(db, istek.email, "yonetim", request.headers.get("origin"))
    db.commit()
    return SIFIRLAMA_MESAJI
