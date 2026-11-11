# -*- coding: utf-8 -*-
"""[2026-10-10] Katmanların öğrenciye gösterilen adları. Veritabanında ad yalnızca "K1" gibi kod olabildiği için
kod yerine anlaşılır ad kullanılır (veritabanında anlamlı bir ad varsa o korunur). Adlar değerlendirme ekranındakilerle aynıdır."""

KATMAN_ADI = {
    "K1": "Değerler / Motivasyon", "K2": "Kişilik & Çalışma Tarzı", "K3": "İş Ortamı & Profesyonel Yetkinlik",
    "K4": "Alan Eğilimi & Bilişsel Stil", "K5": "İş türü tercihleri",
}


def katman_adi(kod: str | None, ad: str | None = None) -> str:
    if ad and ad.strip() and ad.strip().upper() != (kod or "").upper():
        return ad.strip()
    return KATMAN_ADI.get((kod or "").upper(), boyut_kodu(kod) or "")


def boyut_kodu(kod):
    """[2026-11-11] Kullanıcı kararı: ekranda "Katman" yerine "Boyut", K1–K5 yerine B1–B5. Sistemdeki kod (K1…K5) değişmez;
    yalnızca kullanıcıya gösterilen metin çevrilir."""
    import re
    return re.sub(r"^K([1-5])(?![0-9A-Za-z])", r"B\1", kod) if isinstance(kod, str) else kod
