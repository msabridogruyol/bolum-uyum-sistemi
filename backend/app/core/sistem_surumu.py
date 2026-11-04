"""[2026-11-04] Kullanıcı kuralı: sistemin güncellenme tarihi (gün.ay.yıl saat:dakika:saniye) ekranda görünmeli.

* Sunucu: açılışta kod sürümü sistem_surumleri tablosuna yazılır (yalnızca ilk görüldüğünde). Sürüm Render'da
  RENDER_GIT_COMMIT; yoksa app/ altındaki .py/.json dosyalarının özeti (yerel geliştirme).
* Arayüz: Vite derleme anı (__YAYIN_ZAMANI__); arayüz ikisinden yenisini "Son güncelleme" olarak gösterir.
* Gece bakımı: son bakımın başlangıç / bitişi (gece_bakim_kaydi).
"""
from __future__ import annotations

import hashlib
import logging
import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text

log = logging.getLogger("sistem_surumu")
_KOK = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def kod_surumu() -> str:
    commit = (os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT") or "").strip()
    if commit:
        return commit[:40]
    h = hashlib.sha1()
    for p in sorted(_KOK.rglob("*")):
        if p.suffix in (".py", ".json", ".sql") and "__pycache__" not in p.parts and p.is_file():
            h.update(str(p.relative_to(_KOK)).encode())
            h.update(p.read_bytes())
    return "yerel-" + h.hexdigest()[:16]


def surumu_kaydet(engine) -> None:
    try:
        with engine.begin() as b:
            b.execute(text("SET LOCAL lock_timeout = '3s'"))
            b.execute(text("INSERT INTO sistem_surumleri (surum) VALUES (:s) ON CONFLICT (surum) DO NOTHING"), {"s": kod_surumu()})
    except Exception:
        log.warning("sistem sürümü kaydedilemedi", exc_info=True)


def surum_bilgisi(db) -> dict:
    """Herkese açık: yalnızca zamanlar (kod özeti / commit gösterilmez)."""
    r = db.execute(text("SELECT ilk_calisma FROM sistem_surumleri WHERE surum = :s"), {"s": kod_surumu()}).first()
    if r is None:   # açılış kaydı yapılamadıysa (ör. veritabanı geç açıldı) ilk sorguda yazılır
        from app.core.database import engine
        surumu_kaydet(engine)
        r = db.execute(text("SELECT ilk_calisma FROM sistem_surumleri WHERE surum = :s"), {"s": kod_surumu()}).first()
    b = db.execute(text("""SELECT baslama, bitis, durum FROM gece_bakim_kaydi
                            WHERE durum <> 'calisiyor' ORDER BY gun DESC LIMIT 1""")).first()
    return {
        "sunucu_guncelleme": r[0].isoformat() if r else None,
        "son_gece_bakimi": {"baslama": b[0].isoformat() if b and b[0] else None,
                            "bitis": b[1].isoformat() if b and b[1] else None, "durum": b[2] if b else None} if b else None,
    }
