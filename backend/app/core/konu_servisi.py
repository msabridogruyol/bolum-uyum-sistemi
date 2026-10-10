# -*- coding: utf-8 -*-
"""
[2026-10-10] Konu takibi listesi (veritabanı).
- Genel liste (okul_id NULL): süper admin ekler / düzenler / siler; tüm okullarda geçerlidir.
- Okula özel konular (okul_id = okul): okul yetkilisi ve süper admin ekler / düzenler / siler.
- Okulda gizleme: okul, genel listedeki bir konuyu kendi öğrencileri için gizleyebilir (okul_konu_gizleme).
Ders yapısı (TYT Türkçe, AYT Fizik …) sabittir: sinav_yapisi.KONU_DERSLERI.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.sinav_yapisi import KONU_DERSLERI


def etkin_konular(db: Session, okul_id: int | None) -> dict[str, list[str]]:
    """Öğrencinin gördüğü liste: gizlenmemiş genel konular + okulun kendi konuları, sıraya göre."""
    rows = db.execute(text("""
        SELECT k.ders, k.ad FROM sinav_konulari k
         WHERE (k.okul_id IS NULL OR k.okul_id = :o)
           AND NOT EXISTS (SELECT 1 FROM okul_konu_gizleme g WHERE g.okul_id = :o AND g.konu_id = k.id)
         ORDER BY k.ders, k.sira, k.id"""), {"o": okul_id or -1}).all()
    d: dict[str, list[str]] = {k: [] for k in KONU_DERSLERI}
    for ders, ad in rows:
        if ders in d and ad not in d[ders]:
            d[ders].append(ad)
    return d


def yonetim_listesi(db: Session, okul_id: int | None) -> list[dict]:
    """Yönetim ekranı: ders ders genel konular (okulda gizli mi?) ve okulun kendi konuları."""
    rows = db.execute(text("""
        SELECT k.id, k.ders, k.ad, k.sira, k.okul_id,
               EXISTS (SELECT 1 FROM okul_konu_gizleme g WHERE g.okul_id = :o AND g.konu_id = k.id) AS gizli
          FROM sinav_konulari k
         WHERE k.okul_id IS NULL OR (CAST(:o AS INTEGER) IS NOT NULL AND k.okul_id = :o)
         ORDER BY k.ders, k.sira, k.id"""), {"o": okul_id}).all()
    dersler = []
    for kod, (oturum, ad, _) in KONU_DERSLERI.items():
        dersler.append({"kod": kod, "oturum": oturum, "ad": ad,
                        "konular": [{"id": r.id, "ad": r.ad, "sira": r.sira, "kaynak": "okul" if r.okul_id else "genel",
                                     "gizli": bool(r.gizli)} for r in rows if r.ders == kod]})
    return dersler
