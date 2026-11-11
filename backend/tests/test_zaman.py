"""
[2026-11-11] "Bugün" Türkiye saatine göredir. Sunucu UTC çalışır; date.today() / datetime.now() Türkiye'de gece
00:00–03:00 arasında dünü verir (öğrencinin gece girdiği kayıt bir gün önceye yazılıyordu). Uygulama kodu tarihi
app.core.zaman'dan (bugun_tr / simdi_tr) almalı; bu test yasak kullanımı yakalar.
"""
import pathlib
import re
from datetime import datetime, timedelta, timezone

YASAK = re.compile(r"(?<![\w.])(date\.today\(\)|_date\.today\(\)|datetime\.(now|today|utcnow)\(\))")


def test_uygulamada_sunucu_saatine_bagli_bugun_yok():
    kok = pathlib.Path(__file__).resolve().parents[1] / "app"
    bulunan = []
    for p in kok.rglob("*.py"):
        if p.name == "zaman.py":   # tek doğru kaynak; açıklamasında yasak kalıplar geçer
            continue
        for i, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            kod = satir.split("#", 1)[0]
            if YASAK.search(kod):
                bulunan.append(f"{p.relative_to(kok.parent)}:{i}: {satir.strip()}")
    assert not bulunan, "Türkiye saati için app.core.zaman.bugun_tr / simdi_tr kullanın:\n" + "\n".join(bulunan)


def test_bugun_tr_gece_yarisindan_sonra_turkiye_gunudur(monkeypatch):
    from app.core import zaman

    class Sabit(datetime):
        @classmethod
        def now(cls, tz=None):
            utc = datetime(2026, 11, 10, 22, 30, tzinfo=timezone.utc)   # Türkiye'de 11 Kasım 01:30
            return utc.astimezone(tz) if tz else utc.replace(tzinfo=None)

    monkeypatch.setattr(zaman, "datetime", Sabit)
    assert zaman.bugun_tr().isoformat() == "2026-11-11"
    assert zaman.simdi_tr().utcoffset() == timedelta(hours=3)
