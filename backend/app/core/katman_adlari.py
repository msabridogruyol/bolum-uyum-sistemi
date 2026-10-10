# -*- coding: utf-8 -*-
"""[2026-10-10] Katmanların öğrenciye gösterilen adları. Veritabanında ad yalnızca "K1" gibi kod olabildiği için
kod yerine anlaşılır ad kullanılır (veritabanında anlamlı bir ad varsa o korunur)."""

KATMAN_ADI = {
    "K1": "Değerlerin", "K2": "Kişiliğin", "K3": "İş becerilerin", "K4": "İlgi ve eğilimlerin", "K5": "Sana özel alanlar",
}


def katman_adi(kod: str | None, ad: str | None = None) -> str:
    if ad and ad.strip() and ad.strip().upper() != (kod or "").upper():
        return ad.strip()
    return KATMAN_ADI.get((kod or "").upper(), kod or "")
