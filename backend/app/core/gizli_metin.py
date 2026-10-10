# -*- coding: utf-8 -*-
"""[2026-10-10] Geçici şifrelerin GERİ ÇÖZÜLEBİLİR biçimde saklanması (rehberin tabloda görebilmesi için).
Fernet (AES-128-CBC + HMAC) — anahtar JWT gizli anahtarından türetilir; veritabanı tek başına sızsa bile okunamaz.
Yalnızca GEÇİCİ şifreler saklanır; kişi kendi şifresini belirlediği anda silinir."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _f() -> Fernet:
    anahtar = hashlib.sha256((settings.JWT_SECRET_KEY + "|gecici-sifre|v1").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(anahtar))


def sifrele(metin: str | None) -> str | None:
    return _f().encrypt(metin.encode()).decode() if metin else None


def coz(sifreli: str | None) -> str | None:
    if not sifreli:
        return None
    try:
        return _f().decrypt(sifreli.encode()).decode()
    except (InvalidToken, ValueError):
        return None
