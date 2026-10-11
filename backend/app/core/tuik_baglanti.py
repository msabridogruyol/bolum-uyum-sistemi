# -*- coding: utf-8 -*-
"""
[2026-10-10] TÜİK Veri Portalı'ndan bağlantıyla dosya indirme + yıllık güncelleme hatırlatması.

TÜİK'in herkese açık bir API'si yok (web servisi yalnızca resmî kurumlara protokolle). Bu yüzden süper admin
portaldaki tablonun indirme bağlantısını yapıştırır; dosya burada indirilip mevcut yükleme akışına
(sütun eşleştirme → önizleme → kaydet) verilir.

Güvenlik (SSRF): yalnızca https ve *.tuik.gov.tr alan adları; her yönlendirme de aynı kurala tabi; çözülen IP
özel/yerel olamaz; en fazla 25 MB, 30 sn; yalnızca xlsx / xls / csv içeriği.
"""
import base64
import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

IZINLI_ALAN = "tuik.gov.tr"
EN_FAZLA_BAYT = 25 * 1024 * 1024
ZAMAN_ASIMI = 30


class BaglantiHatasi(ValueError):
    pass


def _alan_uygun_mu(url: str) -> urllib.parse.ParseResult:
    u = urllib.parse.urlparse((url or "").strip())
    if u.scheme != "https":
        raise BaglantiHatasi("Bağlantı https:// ile başlamalı.")
    host = (u.hostname or "").lower().rstrip(".")
    if not (host == IZINLI_ALAN or host.endswith("." + IZINLI_ALAN)):
        raise BaglantiHatasi("Yalnızca TÜİK (tuik.gov.tr) bağlantıları kabul edilir.")
    if u.port not in (None, 443):
        raise BaglantiHatasi("Bağlantıda farklı bir port kullanılamaz.")
    try:
        adresler = {ai[4][0] for ai in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)}
    except socket.gaierror:
        raise BaglantiHatasi("TÜİK sunucusuna ulaşılamadı (alan adı çözülemedi).")
    for a in adresler:
        ip = ipaddress.ip_address(a)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise BaglantiHatasi("Bağlantı geçersiz bir adrese yönleniyor.")
    return u


class _GuvenliYonlendirme(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _alan_uygun_mu(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _dosya_adi(url: str, yanit) -> str:
    cd = yanit.headers.get("Content-Disposition") or ""
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="?([^";]+)"?', cd)
    if m:
        return urllib.parse.unquote(m.group(1)).strip()
    son = urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
    return son or "tuik_tablosu"


def _tur_belirle(ad: str, bas: bytes) -> str:
    if bas.startswith(b"PK"):
        return ".xlsx"
    if bas.startswith(b"\xd0\xcf\x11\xe0"):
        raise BaglantiHatasi("Dosya eski Excel (.xls) biçiminde. Excel'de açıp .xlsx olarak kaydedin ve aşağıdan yükleyin.")
    metin = bas[:2048]
    if b"\x00" in metin or metin.lstrip().lower().startswith((b"<!doctype", b"<html")):
        raise BaglantiHatasi("Bağlantı bir tablo dosyası değil (web sayfası döndü). Portaldaki 'indir' bağlantısını kopyalayın.")
    return ".csv"


def indir(url: str) -> dict:
    """Bağlantıdaki tabloyu indirir; {dosya_adi, icerik_base64, boyut} döner (mevcut /dosya/oku akışına verilir)."""
    _alan_uygun_mu(url)
    acici = urllib.request.build_opener(_GuvenliYonlendirme())
    istek = urllib.request.Request(url.strip(), headers={"User-Agent": "Filizyol/1.0 (istatistik verisi icin)"})
    try:
        with acici.open(istek, timeout=ZAMAN_ASIMI) as y:
            uzunluk = y.headers.get("Content-Length")
            if uzunluk and uzunluk.isdigit() and int(uzunluk) > EN_FAZLA_BAYT:
                raise BaglantiHatasi("Dosya 25 MB'tan büyük.")
            veri = y.read(EN_FAZLA_BAYT + 1)
            ad = _dosya_adi(y.geturl(), y)
    except BaglantiHatasi:
        raise
    except urllib.error.HTTPError as e:
        raise BaglantiHatasi(f"TÜİK sunucusu dosyayı vermedi (HTTP {e.code}). Bağlantının güncel olduğunu kontrol edin.")
    except (urllib.error.URLError, TimeoutError, OSError):
        raise BaglantiHatasi("TÜİK sunucusuna bağlanılamadı ya da yanıt zaman aşımına uğradı. Dosyayı indirip elle yükleyebilirsiniz.")
    if len(veri) > EN_FAZLA_BAYT:
        raise BaglantiHatasi("Dosya 25 MB'tan büyük.")
    if not veri:
        raise BaglantiHatasi("Bağlantıdan boş dosya geldi.")
    uzanti = _tur_belirle(ad, veri[:4096])
    if not ad.lower().endswith((".xlsx", ".xls", ".csv")):
        ad = re.sub(r"[^\w.\-]+", "_", ad)[:80] + uzanti
    return {"dosya_adi": ad, "icerik_base64": base64.b64encode(veri).decode(), "boyut": len(veri)}


# ----------------------------------------------------------------------------- yıllık hatırlatma
HATIRLATMA_AY_GUN = (7, 15)   # TÜİK Yükseköğretim İstihdam Göstergeleri genellikle Temmuz'da yayımlanır


def guncelleme_durumu(db, bugun: date | None = None) -> dict:
    """Beklenen veri yılı (bugün 15 Temmuz'u geçtiyse geçen yıl, değilse iki yıl önce) yüklü mü?"""
    from sqlalchemy import text
    bugun = bugun or date.today()
    beklenen = bugun.year - 1 if (bugun.month, bugun.day) >= HATIRLATMA_AY_GUN else bugun.year - 2
    son = db.execute(text("SELECT MAX(veri_yili) FROM istihdam_gostergeleri")).scalar()
    return {"son_veri_yili": son, "beklenen_veri_yili": beklenen, "guncel": son is not None and son >= beklenen}


def hatirlat(db, bugun: date | None = None) -> bool:
    """Beklenen yılın verisi yoksa süper adminlere yılda bir kez bildirim gönderir (tek_seferlik_gocler işaretiyle)."""
    from sqlalchemy import text
    from app.core.bildirim import bildir
    d = guncelleme_durumu(db, bugun)
    if d["guncel"]:
        return False
    isaret = f"tuik_hatirlatma_{d['beklenen_veri_yili']}"
    eklendi = db.execute(text("INSERT INTO tek_seferlik_gocler (ad) VALUES (:a) ON CONFLICT (ad) DO NOTHING RETURNING ad"),
                         {"a": isaret}).first()
    if not eklendi:
        db.rollback()
        return False
    idler = [r[0] for r in db.execute(text(
        "SELECT id FROM admin_kullanicilar WHERE rol = 'super_admin' AND COALESCE(aktif_mi, TRUE)")).all()]
    son = d["son_veri_yili"]
    bildir(db, "yonetim", idler, "sistem",
           f"TÜİK {d['beklenen_veri_yili']} istihdam verisi yayımlanmış olabilir",
           (f"Sistemdeki son Yükseköğretim İstihdam Göstergeleri {son} yılına ait. " if son else
            "Sistemde henüz Yükseköğretim İstihdam Göstergeleri yok. ")
           + "TÜİK Veri Portalı'ndaki tablonun indirme bağlantısını İş Hayatı Verileri ekranına yapıştırarak güncelleyebilirsiniz.",
           link="/admin/is-hayati-verileri", eposta=True)
    db.commit()
    return True
