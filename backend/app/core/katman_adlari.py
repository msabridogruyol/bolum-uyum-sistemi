# -*- coding: utf-8 -*-
"""[2026-10-10] Katmanların öğrenciye gösterilen adları. Veritabanında ad yalnızca "K1" gibi kod olabildiği için
kod yerine anlaşılır ad kullanılır (veritabanında anlamlı bir ad varsa o korunur). Adlar değerlendirme ekranındakilerle aynıdır."""

KATMAN_ADI = {
    "K1": "Değerler / Motivasyon", "K2": "Kişilik & Çalışma Tarzı", "K3": "İş Ortamı & Profesyonel Yetkinlik",
    "K4": "Alan Eğilimi & Bilişsel Stil", "K5": "Derinleşme",
}


def katman_adi(kod: str | None, ad: str | None = None) -> str:
    if ad and ad.strip() and ad.strip().upper() != (kod or "").upper():
        return ad.strip()
    return KATMAN_ADI.get((kod or "").upper(), kod or "")
