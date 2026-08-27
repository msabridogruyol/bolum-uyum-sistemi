"""
Admin kimlik doğrulaması — öğrenciden AYRI bir giriş akışı.
Kaynak: veritabani_taslagi.md 3.3, sistem_genel_anlatim.md E) bölümü.

NOT: Admin kayıt (self-servis) uç noktası KASITLI OLARAK yok — admin
hesapları öğrenci gibi herkese açık bir formdan oluşturulmaz (E9'da
"Öğrenciler & Audit Log" yönetimi admin panelinden yapılır, ama ilk
admin hesabı bir seed script/migration ile oluşturulmalı — bu backend
iskeletinin kapsamı dışında bırakıldı, AÇIK KARAR).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import sifre_dogrula, erisim_tokeni_uret, yenileme_tokeni_uret
from app.models import AdminKullanici
from app.schemas.auth import GirisIstek, TokenCifti

router = APIRouter()


@router.post("/giris", response_model=TokenCifti)
def admin_giris_yap(istek: GirisIstek, db: Session = Depends(get_db)):
    hata = HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")
    admin = db.query(AdminKullanici).filter(AdminKullanici.email == istek.email).first()
    if admin is None or not sifre_dogrula(istek.sifre, admin.sifre_hash):
        raise hata
    return TokenCifti(
        erisim_tokeni=erisim_tokeni_uret(admin.id, admin.rol),
        yenileme_tokeni=yenileme_tokeni_uret(admin.id, admin.rol),
    )
