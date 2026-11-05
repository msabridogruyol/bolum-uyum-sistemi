"""
[2026-10-04 → 2026-11-05] Haftalık görevler KALDIRILDI (kullanıcı kararı: lise öğrencisi için fazla; süreli değil, gelişim
alanlarına göre yapılacaklar listesi). Yerine: app/core/gelisim_listesi.py. Bu modülde yalnızca başka yerlerin kullandığı
Türkiye saati yardımcıları kalır. Eski ogrenci_haftalik_gorev tablosu geçmiş kayıt olarak durur (seviye ve eski yansıtma
cevapları için okunur), yeni satır yazılmaz.
"""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

try:
    TR_SAAT = ZoneInfo("Europe/Istanbul")
except Exception:  # sunucuda saat dilimi verisi yoksa: Türkiye 2016'dan beri sabit UTC+3
    TR_SAAT = timezone(timedelta(hours=3))


def bugun_tr(simdi: datetime | None = None) -> date:
    return (simdi or datetime.now(timezone.utc)).astimezone(TR_SAAT).date()


def hafta_baslangici(gun: date) -> date:
    return gun - timedelta(days=gun.weekday())  # Pazartesi
