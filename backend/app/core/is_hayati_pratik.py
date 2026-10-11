# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı — Zor Günler, Okulda Öğretilmeyenler ve Mülakat Pratiği sekmelerinin ortak yardımcıları.

İçerik dosyaları (app/data):
  zor_gunler.json          — {"alanlar": {"U01": {"ad", "senaryolar": [5]}}, "meslekler": {"meslek adı": [2]}}
  is_hayati_dersler.json   — {"dersler": [{kod, baslik, kartlar, sinav, kaynaklar, son_kontrol}]}
  is_hayati_mulakat.json   — {"star", "kontrol", "kategoriler", "alanlar": {"U01": [sorular]}}
Bölümün üst alanı K5 dallar tablosundaki 'U..' kodudur (bolum_dal_eslesme).
"""
import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

_VERI = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=None)
def veri(dosya: str) -> dict:
    try:
        return json.loads((_VERI / dosya).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def meslek_anahtari(ad: str | None) -> str:
    """Simülasyonla aynı anahtar: ad.strip().lower() (bkz. meslek_senaryolari.senaryo_bul)."""
    return (ad or "").strip().lower()


def bolum_alani(db: Session, bolum_id: int) -> dict | None:
    r = db.execute(text("""SELECT d.kod, d.ad FROM bolum_dal_eslesme e JOIN dallar d ON d.id = e.dal_id
                            WHERE e.bolum_id = :b AND d.kod LIKE 'U%' LIMIT 1"""), {"b": bolum_id}).first()
    return {"kod": r.kod, "ad": r.ad} if r else None


def bolum_meslekleri(db: Session, bolum_id: int) -> tuple[str | None, list[str]]:
    r = db.execute(text("SELECT ad, detay FROM bolumler WHERE id = :i AND durum = 'yayinda'"), {"i": bolum_id}).first()
    if r is None:
        return None, []
    d = r.detay if isinstance(r.detay, dict) else json.loads(r.detay or "{}")
    return r.ad, [m.get("ad") for m in (d.get("meslekler") or []) if m.get("ad")]
