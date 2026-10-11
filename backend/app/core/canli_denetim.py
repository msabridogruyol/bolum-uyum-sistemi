# -*- coding: utf-8 -*-
"""
[2026-10-11] Canlı güvenlik / yapılandırma denetimi — Kontrol Paneli "Güvenlik Durumu" kartının üst satırları ve açılış günlüğü.
Statik kod denetiminden farklı olarak bu maddeler çalışan sunucunun gerçek ayarlarına bakar.
Gizli değerlerin kendisi asla döndürülmez; yalnızca "ayarlı mı / yeterince uzun mu" bilgisi.
"""
from __future__ import annotations

import logging

from app.core.config import settings

_log = logging.getLogger("guvenlik")
VARSAYILAN_JWT = "CHANGE_ME_IN_PRODUCTION"


def jwt_anahtari_zayif_mi() -> bool:
    k = settings.JWT_SECRET_KEY or ""
    return k == VARSAYILAN_JWT or len(k) < 32


def maddeler() -> list[dict]:
    from app.core.eposta_servisi import eposta_yapilandirildi_mi
    from app.core.security import BCRYPT_TUR
    m = []
    if jwt_anahtari_zayif_mi():
        m.append({"baslik": "Oturum imza anahtarı (JWT_SECRET_KEY)", "durum": "kritik",
                  "detay": "Varsayılan ya da 32 karakterden kısa. Bu anahtarı bilen herkes sahte oturum açabilir. "
                           "Render → Environment → JWT_SECRET_KEY alanına 64+ karakterlik rastgele bir değer girin (tüm oturumlar bir kez kapanır)."})
    else:
        m.append({"baslik": "Oturum imza anahtarı (JWT_SECRET_KEY)", "durum": "iyi", "detay": "Ayarlı ve yeterince uzun."})
    m.append({"baslik": "E-posta gönderimi", "durum": "iyi" if eposta_yapilandirildi_mi() else "dikkat",
              "detay": "Yapılandırılmış (şifre sıfırlama ve 2 adımlı doğrulama çalışır)." if eposta_yapilandirildi_mi()
              else "Yapılandırılmamış: şifremi unuttum e-postaları ve 2 adımlı doğrulama çalışmaz."})
    m.append({"baslik": "Şifre saklama", "durum": "iyi", "detay": f"bcrypt, {BCRYPT_TUR} tur; eski karmalar ilk girişte yenilenir."})
    m.append({"baslik": "Şifre değişince oturumlar", "durum": "iyi",
              "detay": "Şifre sıfırlanınca o hesabın tüm açık oturumları düşer; kendi değiştirince diğer cihazlar düşer."})
    m.append({"baslik": "Hatalı şifre koruması", "durum": "iyi",
              "detay": "Hesap başına 15 dakikada 8 hatalı denemede 15 dk kilit (IP'den bağımsız); giriş IP başına 120/dk."})
    return m


def acilista_uyar() -> None:
    if jwt_anahtari_zayif_mi():
        _log.critical("GÜVENLİK: JWT_SECRET_KEY varsayılan ya da kısa! Sahte oturum açılabilir. Ortam değişkenini hemen ayarlayın.")
