"""FastAPI dependency'leri — JWT doğrulama, DB session, mevcut kullanıcı."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import token_coz
from app.models import Ogrenci, AdminKullanici

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/giris")

_YETKISIZ = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Geçersiz veya süresi dolmuş oturum.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_mevcut_ogrenci(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Ogrenci:
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") != "ogrenci":
        raise _YETKISIZ

    try:
        ogrenci_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _YETKISIZ

    ogrenci = db.get(Ogrenci, ogrenci_id)
    if ogrenci is None:
        raise _YETKISIZ
    return ogrenci


def get_mevcut_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminKullanici:
    """
    [2026-10-09] Sistem yönetimi uç noktaları (içerik, pipeline, parametreler...) — YALNIZCA süper admin.
    Okul yetkilisi bu uç noktalara erişemez; onun uç noktaları get_mevcut_yonetim + okul kapsamı kullanır.
    """
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") != "super_admin":
        raise _YETKISIZ

    try:
        admin_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _YETKISIZ

    admin = db.get(AdminKullanici, admin_id)
    if admin is None or admin.rol != "super_admin" or admin.aktif_mi is False:
        raise _YETKISIZ
    return admin


YONETIM_ROLLERI = ("super_admin", "okul_yetkilisi")


def get_mevcut_yonetim(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminKullanici:
    """[2026-10-09] Süper admin veya okul yetkilisi. Okul kapsamı uç noktanın içinde ayrıca denetlenir."""
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") not in YONETIM_ROLLERI:
        raise _YETKISIZ
    try:
        kid = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _YETKISIZ
    hesap = db.get(AdminKullanici, kid)
    if hesap is None or hesap.rol not in YONETIM_ROLLERI or hesap.aktif_mi is False or hesap.rol != payload.get("rol"):
        raise _YETKISIZ
    return hesap


def get_mevcut_super_admin(
    admin: AdminKullanici = Depends(get_mevcut_admin),
) -> AdminKullanici:
    if admin.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca super_admin rolüne açık.")
    return admin
