# -*- coding: utf-8 -*-
"""
[2026-11-11] Türkiye saatine göre "bugün" ve "şimdi".

Sunucu (Render) UTC çalışır: date.today() / datetime.now() Türkiye'de gece 00:00–03:00 arasında DÜNÜ verir. Öğrencinin
o saatlerde girdiği kayıt bir gün önceye yazılıyor, "bugün" tarihli giriş "ileri tarih" sayılıp reddediliyordu.
Uygulama kodunda tarih / saat bu modülden alınır; tests/test_zaman.py date.today() ve parametresiz datetime.now()
kullanımına izin vermez.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

TR = ZoneInfo("Europe/Istanbul")


def simdi_tr() -> datetime:
    """Türkiye saatiyle şimdi (saat dilimi bilgili)."""
    return datetime.now(TR)


def bugun_tr() -> date:
    """Türkiye saatiyle bugünün tarihi."""
    return simdi_tr().date()
