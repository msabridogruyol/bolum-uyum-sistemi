# -*- coding: utf-8 -*-
"""
[2026-10-11] Günlük aktiflik kaydı — öğrencinin sistemi açtığı günler (ogrenci_aktif_gunler).

gune_isle(db, ogrenci_id): bugünü (Türkiye saati) işaretler; aynı gün ikinci kez çağrılırsa bir şey yapmaz.
Çağrıldığı yerler: başarılı giriş (auth._giris_kaydet) ve öğrenci sayfası açıkken gelen "buradayım" sinyali
(cevrimici.buradayim — en fazla 45 sn'de bir). Böylece "beni hatırla" ile açık kalan oturumlar da sayılır.
Hata sessizce yutulur: aktiflik kaydı asıl isteği asla bozmamalı.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.orm import Session

TR = ZoneInfo("Europe/Istanbul")
_log = logging.getLogger(__name__)


def bugun_tr() -> date:
    return datetime.now(TR).date()


def gune_isle(db: Session, ogrenci_id) -> None:
    try:
        with db.begin_nested():
            db.execute(text("INSERT INTO ogrenci_aktif_gunler (ogrenci_id, gun) VALUES (:o, :g) ON CONFLICT DO NOTHING"),
                       {"o": ogrenci_id, "g": bugun_tr()})
    except Exception as e:   # tablo henüz yoksa vb.
        _log.debug("aktif gün yazılamadı: %s", e)


def aktiflik_ozeti(db: Session, ogrenci_id, gun: int = 30) -> dict:
    """Son `gun` gün: aktif gün sayısı, son aktif gün, güncel seri ve gün gün işaret listesi (eskiden yeniye)."""
    from datetime import timedelta
    bugun = bugun_tr()
    bas = bugun - timedelta(days=gun - 1)
    try:
        gunler = {r[0] for r in db.execute(text(
            "SELECT gun FROM ogrenci_aktif_gunler WHERE ogrenci_id = :o AND gun >= :b"), {"o": ogrenci_id, "b": bas}).all()}
        son = db.execute(text("SELECT max(gun) FROM ogrenci_aktif_gunler WHERE ogrenci_id = :o"), {"o": ogrenci_id}).scalar()
    except Exception:
        db.rollback()
        gunler, son = set(), None
    seri, g = 0, bugun if bugun in gunler else bugun - timedelta(days=1)
    while g in gunler:
        seri += 1
        g -= timedelta(days=1)
    return {"gun": gun, "aktif_gun": len(gunler), "son_aktif": son.isoformat() if son else None, "seri": seri,
            "takvim": [{"gun": (bas + timedelta(days=i)).isoformat(), "aktif": (bas + timedelta(days=i)) in gunler} for i in range(gun)]}
