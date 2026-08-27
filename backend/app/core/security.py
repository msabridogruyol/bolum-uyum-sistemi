"""
Kimlik doğrulama yardımcıları — D1: bcrypt şifre hash + JWT (access+refresh).
Kaynak: sistem_genel_anlatim.md D1, veritabani_taslagi.md Bölüm 3
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
import bcrypt

from app.core.config import settings


def sifre_hashle(duz_sifre: str) -> str:
    return bcrypt.hashpw(duz_sifre.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def sifre_dogrula(duz_sifre: str, hash_sifre: str) -> bool:
    return bcrypt.checkpw(duz_sifre.encode("utf-8"), hash_sifre.encode("utf-8"))


def _token_uret(konu: str, rol: str, sure: timedelta, tip: str) -> str:
    simdi = datetime.now(timezone.utc)
    payload = {
        "sub": konu,       # kullanıcı id'si (UUID string)
        "rol": rol,        # 'ogrenci' | 'super_admin' | 'icerik_editoru'
        "tip": tip,        # 'access' | 'refresh'
        "iat": simdi,
        "exp": simdi + sure,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def erisim_tokeni_uret(kullanici_id: uuid.UUID, rol: str) -> str:
    return _token_uret(
        str(kullanici_id), rol,
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES), "access",
    )


def yenileme_tokeni_uret(kullanici_id: uuid.UUID, rol: str) -> str:
    return _token_uret(
        str(kullanici_id), rol,
        timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS), "refresh",
    )


def token_coz(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
