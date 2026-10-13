"""
[2026-10-13] "Gelecekteki sana mektup": öğrenci bugünkü kendini anlatan bir mektup yazar; mektup mühürlenir ve seçtiği gün
e-postasına gelir (okul e-postası mezuniyetten sonra kapanabileceği için isteğe bağlı kişisel e-posta da eklenebilir).

Gizlilik:
  * Metin ve kişisel e-posta Fernet ile şifreli saklanır (anahtar JWT gizli anahtarından türetilir; veritabanı tek başına sızsa
    bile okunamaz). Okul / yönetim ekranı ya da ucu yoktur; yapay zekâya (Filiz) gönderilmez; kayıt günlüğüne metin yazılmaz.
  * Öğrenci mektubunu teslim gününe kadar göremez (zaman kapsülü); istediği an silebilir ya da teslim tarihini değiştirebilir.
  * Teslim günü geldiğinde mektup hesapta da açılır (e-posta yapılandırılmamışsa ya da gönderilemezse bile okunabilir).
Teslim: main.py'deki arka plan döngüsü (açılışta ve 6 saatte bir) teslim_et() çağırır.
"""
import base64
import hashlib
import logging
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

log = logging.getLogger("gelecek_mektup")
EN_AZ_GUN, EN_COK_YIL = 30, 10
EN_KISA, EN_UZUN = 40, 5000
EN_COK_BEKLEYEN = 3
def turkiye_bugun() -> date:
    """Türkiye saatine göre bugünün tarihi (sunucu UTC çalışır)."""
    return datetime.now(ZoneInfo("Europe/Istanbul")).date()


EPOSTA_RX = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")


def _f() -> Fernet:
    anahtar = hashlib.sha256((settings.JWT_SECRET_KEY + "|gelecek-mektup|v1").encode()).digest()
    return Fernet(base64.urlsafe_b64encode(anahtar))


def sifrele(metin: str | None) -> str | None:
    return _f().encrypt(metin.encode()).decode() if metin else None


def coz(sifreli: str | None) -> str | None:
    if not sifreli:
        return None
    try:
        return _f().decrypt(sifreli.encode()).decode()
    except (InvalidToken, ValueError):
        return None


def maskele(eposta: str | None) -> str | None:
    if not eposta or "@" not in eposta:
        return None
    ad, alan = eposta.split("@", 1)
    return f"{ad[:2]}{'•' * max(1, min(6, len(ad) - 2))}@{alan}"


def _sinif_no(sinif: str | None) -> int | None:
    m = re.match(r"\s*(\d{1,2})", sinif or "")
    return int(m.group(1)) if m and 9 <= int(m.group(1)) <= 12 else None


def tarih_secenekleri(sinif: str | None, bugun: date | None = None) -> list[dict]:
    """Öğrencinin sınıfına göre anlamlı teslim günleri. Mezuniyet: lise son sınıfın bittiği yılın 30 Haziran'ı."""
    bugun = bugun or turkiye_bugun()
    egitim_yili_sonu = bugun.year + (1 if bugun.month >= 7 else 0)
    secenekler = []
    n = _sinif_no(sinif)
    if n:
        mezuniyet = date(egitim_yili_sonu + (12 - n), 6, 30)
        secenekler.append({"kod": "mezuniyet", "ad": "Liseden mezun olduğun gün", "tarih": mezuniyet.isoformat()})
        secenekler.append({"kod": "universite", "ad": "Üniversitenin ilk haftası", "tarih": date(mezuniyet.year, 10, 1).isoformat()})
    for yil, ad in ((1, "Bir yıl sonra"), (5, "Beş yıl sonra")):
        try:
            t = bugun.replace(year=bugun.year + yil)
        except ValueError:   # 29 Şubat
            t = bugun.replace(year=bugun.year + yil, day=28)
        secenekler.append({"kod": f"{yil}yil", "ad": ad, "tarih": t.isoformat()})
    return [s for s in secenekler if (date.fromisoformat(s["tarih"]) - bugun).days >= EN_AZ_GUN]


def tarih_gecerli_mi(t: date, bugun: date | None = None) -> bool:
    bugun = bugun or turkiye_bugun()
    return EN_AZ_GUN <= (t - bugun).days <= EN_COK_YIL * 366


def teslim_et(db: Session, bugun: date | None = None) -> dict:
    """Teslim günü gelmiş bekleyen mektupları e-postayla gönderir. Dönen: {gonderildi, hata, eposta_yok}."""
    from app.core import eposta_servisi as ep
    bugun = bugun or turkiye_bugun()
    sayac = {"gonderildi": 0, "hata": 0, "eposta_yok": 0}
    satirlar = db.execute(text("""
        SELECT m.id, m.metin_sifreli, m.kisisel_eposta_sifreli, m.olusturulma_zamani, o.ad_soyad, o.email, o.test_hesabi
          FROM gelecek_mektuplari m JOIN ogrenciler o ON o.id = m.ogrenci_id
         WHERE m.durum = 'bekliyor' AND m.teslim_tarihi <= :b ORDER BY m.teslim_tarihi LIMIT 200"""), {"b": bugun}).all()
    yapilandirildi = ep.eposta_yapilandirildi_mi()
    for r in satirlar:
        alicilar = [a for a in dict.fromkeys([coz(r.kisisel_eposta_sifreli), (r.email or "").strip()]) if a]
        metin = coz(r.metin_sifreli)
        if r.test_hesabi or not alicilar or not metin or not yapilandirildi:
            durum = "eposta_yok"
        else:
            konu, html, duz = ep.gelecek_mektup_epostasi(r.ad_soyad, r.olusturulma_zamani.strftime("%d.%m.%Y"), metin)
            basarili = any([ep.eposta_gonder(a, konu, html, duz) for a in alicilar])   # noqa: C419 — liste: her adrese gönderilsin
            durum = "gonderildi" if basarili else "hata"
        sayac[durum] += 1
        db.execute(text("UPDATE gelecek_mektuplari SET durum = :d, gonderim_zamani = now() WHERE id = :i"), {"d": durum, "i": r.id})
        db.commit()
    return sayac


def arka_planda_teslim() -> None:
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        s = teslim_et(db)
        if any(s.values()):
            log.info("Gelecek mektupları teslim: %s", s)
    except Exception as hata:
        log.error("Gelecek mektupları teslim hatası: %s: %s", type(hata).__name__, hata)
        db.rollback()
    finally:
        db.close()
