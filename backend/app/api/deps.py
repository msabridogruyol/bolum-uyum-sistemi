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
    Herhangi bir admin rolü (super_admin veya icerik_editoru) kabul eder.
    Yalnızca super_admin gerektiren işlemler için get_mevcut_super_admin kullanın.
    """
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") not in ("super_admin", "icerik_editoru"):
        raise _YETKISIZ

    try:
        admin_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _YETKISIZ

    admin = db.get(AdminKullanici, admin_id)
    if admin is None:
        raise _YETKISIZ
    return admin


def get_mevcut_super_admin(
    admin: AdminKullanici = Depends(get_mevcut_admin),
) -> AdminKullanici:
    if admin.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca super_admin rolüne açık.")
    return admin
