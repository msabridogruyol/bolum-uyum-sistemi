"""
Kimlik doğrulama yardımcıları — D1: bcrypt şifre hash + JWT (access+refresh).
Kaynak: sistem_genel_anlatim.md D1, veritabani_taslagi.md Bölüm 3
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
import bcrypt

from app.core.config import settings


# [2026-10-11] bcrypt maliyeti 12 → 10 (BCRYPT_TUR ortam değişkeniyle değiştirilebilir; OWASP alt sınırı 10).
# Neden: bir laboratuvarda 30 öğrenci aynı anda girer; düşük işlemcili sunucuda 12 turla doğrulama sırası ~1 dakikayı buluyordu.
# 10 tur ≈ 4 kat hızlı. Eski (12 turluk) karmalar ilk başarılı girişte yeniden karılır (yeniden_karma_gerekli_mi).
import os as _os
BCRYPT_TUR = max(10, min(14, int(_os.getenv("BCRYPT_TUR", "10") or 10)))


def sifre_hashle(duz_sifre: str) -> str:
    return bcrypt.hashpw(duz_sifre.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_TUR)).decode("utf-8")


def yeniden_karma_gerekli_mi(hash_sifre: str | None) -> bool:
    """Karma, güncel tur sayısıyla üretilmemişse True ($2b$12$… → 12)."""
    try:
        return int((hash_sifre or "").split("$")[2]) != BCRYPT_TUR
    except (IndexError, ValueError):
        return False


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


# ----------------------------------------------------------------------------- [2026-10-11] oturumları geçersiz kılma
def token_hesaba_uygun_mu(payload: dict, hesap) -> bool:
    """Anahtar, hesabın oturumları geçersiz kılınmadan ÖNCE verildiyse False (şifre sıfırlandı / değiştirildi)."""
    g = getattr(hesap, "oturum_gecersiz_zamani", None)
    if g is None:
        return True
    try:
        return int(payload.get("iat", 0)) >= int(g.timestamp())
    except (TypeError, ValueError):
        return False


def oturumlari_gecersiz_kil(hesap) -> None:
    """Hesabın şu ana kadar verilmiş tüm erişim / yenileme anahtarlarını geçersiz kılar (commit çağıranda)."""
    hesap.oturum_gecersiz_zamani = datetime.now(timezone.utc)


def yeni_token_cifti(hesap, rol: str) -> dict:
    """Kendi şifresini değiştiren kişinin o anki cihazı oturumda kalsın diye yeni anahtar çifti."""
    return {"erisim_tokeni": erisim_tokeni_uret(hesap.id, rol), "yenileme_tokeni": yenileme_tokeni_uret(hesap.id, rol), "token_tipi": "bearer"}
