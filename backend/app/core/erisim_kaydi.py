# -*- coding: utf-8 -*-
"""
[2026-11-05] Erişim kayıtları: kim, ne zaman giriş yaptı; kimin verisine, hangi bölümde eriştiyse. Yalnızca süper admin görür.

Kaynaklar:
  * Girişler — auth uç noktaları `giris_olayi()` çağırır: giris, giris_hatali (yanlış şifre / bilinmeyen e-posta),
    giris_engellendi (çok fazla hatalı deneme), iki_adim_hatali.
  * Oturum açık her istek — `ErisimKaydiAraKatmani`: yanıttan sonra yol şablonu (/yonetim/ogrenci/{ogrenci_id}/rapor),
    hedef öğrenci, durum kodu ve IP kuyruğa bırakılır. Olay: goruntuleme (GET), indirme (dosya yanıtı), islem (yazma).
Yazım arka planda toplu yapılır (istek veritabanını beklemez); kişi ve hedef adları yazım anında kopyalanır.

Hacim: arka planda kendiliğinden yinelenen istekler (bildirim zili, çevrim içi sinyali) yazılmaz; aynı kişinin aynı
sayfayı aynı hedefle TEKRAR_SN içinde yeniden görüntülemesi tek satırdır. İndirme ve işlemler her zaman yazılır.
"""
from __future__ import annotations

import contextvars
import logging
import queue
import re
import threading
import time
import uuid

from sqlalchemy import text

log = logging.getLogger("erisim_kaydi")

IP: contextvars.ContextVar[str | None] = contextvars.ContextVar("erisim_ip", default=None)
_KUYRUK: "queue.Queue[dict]" = queue.Queue(maxsize=50000)
TEKRAR_SN = 600
_son_gorulme: dict[tuple, float] = {}
_kilit = threading.Lock()

# Kişinin bir şeye "girmesi" sayılmayan, arka planda kendiliğinden yinelenen istekler
HARIC = {
    ("POST", "/ogrenci/cevrimici"), ("GET", "/yonetim/cevrimici"),
    ("GET", "/ogrenci/bildirimler"), ("GET", "/yonetim/bildirimler"),
    ("GET", "/yonetim/filiz/ozet"), ("POST", "/istemci-hata"),
}
_ATLA_ONEK = ("/saglik", "/docs", "/openapi", "/redoc", "/pipeline-istemci")
_DOSYA_TURLERI = ("application/pdf", "spreadsheet", "presentation", "wordprocessing", "application/vnd", "text/csv",
                  "application/zip", "application/octet-stream", "image/")

# Yol şablonu → okunur bölüm adı (ilk eşleşen). Eşleşmeyen yolda son anlamlı parça kullanılır.
_BOLUMLER: list[tuple[str, str]] = [
    (r"^/auth/cikis|^/admin/auth/cikis", "Çıkış"),
    (r"/cevap-analizi", "Cevap ayrıntısı"),
    (r"/veli-onayi|/onaylar", "Onay formları"),
    (r"/gorusme", "Rehberlik görüşmeleri"),
    (r"/erken-uyari", "Erken uyarı"),
    (r"/portfolyo", "Portfolyo"),
    (r"/is-hayati-cv|/is-hayati/cv", "CV"),
    (r"/is-hayati", "İş hayatı"),
    (r"/tercih", "Tercih listesi"),
    (r"/hedef", "Hedef ve koçluk"),
    (r"^/koclugu/asistan|/filiz", "Filiz"),
    (r"^/koclugu|^/gelisim-listesi", "Koçluk"),
    (r"/rapor|/tek-bakista|/hazir-raporlar|/veli-sunumu", "Raporlar"),
    (r"/istatistik|/karsilastirma", "İstatistikler"),
    (r"/anket|/tarama", "Anket ve tarama formları"),
    (r"/deneme|/net", "Deneme sınavları"),
    (r"/calisma", "Çalışma takibi"),
    (r"/akran|/sube-dagilimi|/aday", "Şube ve akran analizi"),
    (r"/mezun", "Mezunlar"),
    (r"/kulup", "Kulüpler"),
    (r"/kutuphane", "Kütüphane"),
    (r"/takvim", "Takvim"),
    (r"/koc", "Eğitim koçları"),
    (r"/katman|/degerlendirme|/sorular?\b", "Değerlendirme"),
    (r"/sonuc|/oneri|/listem|/karsilastir", "Sonuçlar ve öneriler"),
    (r"/kvkk|/onay", "KVKK onayı"),
    (r"/profil|/ayarlar|/ben\b|/sifre", "Hesap ve profil"),
    (r"/yetkili|/yoneticiler|/test-hesaplari", "Kullanıcı yönetimi"),
    (r"^/yonetim/ogrenci/\{ogrenci_id\}$", "Öğrenci kartı"),
    (r"/ogrenciler|/giris-listesi|/kayitlar", "Öğrenci listesi"),
    (r"/erisim-kayitlari", "Erişim kayıtları"),
    (r"/audit-log|/hata-kayit", "Sistem kayıtları"),
    (r"^/admin/", "Sistem yönetimi"),
    (r"^/yonetim/okul/\{okul_id\}", "Okul paneli"),
]
_BOLUM_RE = [(re.compile(d), ad) for d, ad in _BOLUMLER]


def bolum_adi(sablon: str) -> str:
    for d, ad in _BOLUM_RE:
        if d.search(sablon):
            return ad
    parcalar = [p for p in sablon.split("/") if p and not p.startswith("{")]
    return (parcalar[-1].replace("-", " ").capitalize() if parcalar else "Ana sayfa")[:120]


def sablon_cikar(yol: str, parametreler: dict) -> str:
    """Gerçek yoldaki parametre değerlerini adlarıyla değiştirir (/yonetim/ogrenci/9c1…/rapor → …/{ogrenci_id}/rapor)."""
    if not parametreler:
        return yol
    ters = {str(v): k for k, v in parametreler.items()}
    return "/".join("{" + ters[p] + "}" if p in ters else p for p in yol.split("/"))


def _ekle(satir: dict) -> None:
    try:
        _KUYRUK.put_nowait(satir)
    except queue.Full:
        pass


def giris_olayi(olay: str, hesap=None, rol: str | None = None, eposta: str | None = None) -> None:
    """Giriş olayları (auth uç noktalarından). Hesap bilinmiyorsa (yanlış e-posta) denenen e-posta yazılır."""
    try:
        tip = rol or getattr(hesap, "rol", None) or ("ogrenci" if hesap is not None else "bilinmiyor")
        _ekle({"kullanici_tipi": tip, "kullanici_id": str(hesap.id) if hesap is not None else None,
               "kullanici_eposta": (eposta or getattr(hesap, "email", None) or "")[:254] or None,
               "olay": olay, "bolum": "Giriş", "yontem": "POST", "yol": None, "hedef_ogrenci_id": None,
               "hedef_okul_id": None, "durum_kodu": None, "ip": IP.get(), "parametre": None})
    except Exception:
        log.exception("giriş olayı kuyruğa alınamadı")


def _tekrar_mi(anahtar: tuple) -> bool:
    simdi = time.monotonic()
    with _kilit:
        onceki = _son_gorulme.get(anahtar)
        if onceki is not None and simdi - onceki < TEKRAR_SN:
            return True
        _son_gorulme[anahtar] = simdi
        if len(_son_gorulme) > 50000:      # bellek sınırı: eskileri at
            sinir = simdi - TEKRAR_SN
            for k in [k for k, t in _son_gorulme.items() if t < sinir]:
                _son_gorulme.pop(k, None)
    return False


def istek_kaydi(scope: dict, payload: dict, durum: int, icerik_turu: str) -> None:
    yontem = scope.get("method", "")
    yol = scope.get("path", "")
    if yontem in ("OPTIONS", "HEAD") or yol.startswith(_ATLA_ONEK):
        return
    parametreler = scope.get("path_params") or {}
    sablon = sablon_cikar(yol, parametreler)[:255]
    if (yontem, sablon) in HARIC:
        return
    rol = payload.get("rol")
    kid = payload.get("sub")
    hedef = None
    if rol == "ogrenci":
        hedef = kid
    elif parametreler.get("ogrenci_id"):
        hedef = str(parametreler["ogrenci_id"])
    try:
        hedef = str(uuid.UUID(str(hedef))) if hedef else None
    except ValueError:
        hedef = None
    if yontem == "GET":
        olay = "indirme" if any(t in icerik_turu for t in _DOSYA_TURLERI) else "goruntuleme"
    else:
        olay = "islem"
    if olay == "goruntuleme" and _tekrar_mi((kid, sablon, hedef, tuple(sorted((k, str(v)) for k, v in parametreler.items())), durum >= 400)):
        return
    okul_param = parametreler.get("okul_id")
    try:
        okul_param = int(okul_param) if okul_param is not None else None
    except (TypeError, ValueError):
        okul_param = None
    ek = None
    for k in ("gorusme_id", "portfolyo_id"):
        if parametreler.get(k) is not None:
            ek = (k, str(parametreler[k]))
    _ekle({"kullanici_tipi": rol or "bilinmiyor", "kullanici_id": kid, "kullanici_eposta": None, "olay": olay,
           "bolum": bolum_adi(sablon), "yontem": yontem[:10], "yol": sablon, "hedef_ogrenci_id": hedef,
           "hedef_okul_id": okul_param, "durum_kodu": durum, "ip": IP.get(), "parametre": ek})


# ----------------------------------------------------------------------------- yazım
_EKLE_SQL = text("""
INSERT INTO erisim_kayitlari (zaman, kullanici_tipi, kullanici_id, kullanici_ad, kullanici_eposta, okul_id, olay, bolum,
                              yontem, yol, hedef_ogrenci_id, hedef_ad, hedef_okul_id, durum_kodu, ip)
VALUES (:zaman, :kullanici_tipi, CAST(:kullanici_id AS uuid), :kullanici_ad, :kullanici_eposta, :okul_id, :olay, :bolum,
        :yontem, :yol, CAST(:hedef_ogrenci_id AS uuid), :hedef_ad, :hedef_okul_id, :durum_kodu, :ip)
""")


def _uuidler(degerler) -> list[str]:
    out = []
    for d in degerler:
        try:
            out.append(str(uuid.UUID(str(d))))
        except (TypeError, ValueError):
            pass
    return list(set(out))


def _yaz(db, satirlar: list[dict]) -> int:
    """Adları ve okulları toplu çözüp satırları ekler. Çağıran commit eder."""
    from datetime import datetime, timezone
    # gorusme_id / portfolyo_id → öğrenci
    for tablo, anahtar in (("rehberlik_gorusmeleri", "gorusme_id"), ("portfolyo_kayitlari", "portfolyo_id")):
        idler = sorted({int(s["parametre"][1]) for s in satirlar
                        if s.get("parametre") and s["parametre"][0] == anahtar and s["parametre"][1].isdigit()})
        if idler:
            try:
                with db.begin_nested():
                    eslesme = {str(r[0]): str(r[1]) for r in db.execute(
                        text(f"SELECT id, ogrenci_id FROM {tablo} WHERE id = ANY(:i)"), {"i": idler})}
                for s in satirlar:
                    if s.get("parametre") and s["parametre"][0] == anahtar and not s.get("hedef_ogrenci_id"):
                        s["hedef_ogrenci_id"] = eslesme.get(s["parametre"][1])
            except Exception:
                pass
    ogr_idler = _uuidler([s["kullanici_id"] for s in satirlar if s["kullanici_tipi"] == "ogrenci"]
                         + [s["hedef_ogrenci_id"] for s in satirlar if s.get("hedef_ogrenci_id")])
    yon_idler = _uuidler([s["kullanici_id"] for s in satirlar if s["kullanici_tipi"] in ("okul_yetkilisi", "super_admin")])
    ogr, yon = {}, {}
    if ogr_idler:
        ogr = {str(r[0]): (r[1], r[2], r[3]) for r in db.execute(
            text("SELECT id, ad_soyad, okul_id, email FROM ogrenciler WHERE id = ANY(CAST(:i AS uuid[]))"), {"i": ogr_idler})}
    if yon_idler:
        yon = {str(r[0]): (r[1], r[2], r[3]) for r in db.execute(
            text("SELECT id, ad_soyad, okul_id, email FROM admin_kullanicilar WHERE id = ANY(CAST(:i AS uuid[]))"), {"i": yon_idler})}
    simdi = datetime.now(timezone.utc)
    kayit = []
    for s in satirlar:
        kim = (ogr if s["kullanici_tipi"] == "ogrenci" else yon).get(str(s.get("kullanici_id")))
        hedef = ogr.get(str(s.get("hedef_ogrenci_id"))) if s.get("hedef_ogrenci_id") else None
        kayit.append({
            "zaman": s.get("zaman") or simdi, "kullanici_tipi": s["kullanici_tipi"][:20],
            "kullanici_id": s.get("kullanici_id"),
            "kullanici_ad": kim[0] if kim else None, "kullanici_eposta": s.get("kullanici_eposta") or (kim[2] if kim else None),
            "okul_id": kim[1] if kim else None, "olay": s["olay"], "bolum": s.get("bolum"), "yontem": s.get("yontem"),
            "yol": s.get("yol"), "hedef_ogrenci_id": s.get("hedef_ogrenci_id"),
            "hedef_ad": hedef[0] if hedef else None,
            "hedef_okul_id": s.get("hedef_okul_id") if s.get("hedef_okul_id") is not None else (hedef[1] if hedef else None),
            "durum_kodu": s.get("durum_kodu"), "ip": (s.get("ip") or "")[:64] or None,
        })
    if kayit:
        db.execute(_EKLE_SQL, kayit)
    return len(kayit)


def _al(en_cok: int = 5000) -> list[dict]:
    satirlar = []
    try:
        while len(satirlar) < en_cok:
            s = _KUYRUK.get_nowait()
            s.setdefault("zaman", None)
            satirlar.append(s)
    except queue.Empty:
        pass
    return satirlar


def bosalt(db=None) -> int:
    """Kuyruktakileri hemen yazar (liste ekranı açılırken ve testlerde). db verilirse onun işlemi kullanılır."""
    satirlar = _al()
    if not satirlar:
        return 0
    if db is not None:
        try:
            with db.begin_nested():
                return _yaz(db, satirlar)
        except Exception:
            log.exception("erişim kayıtları yazılamadı")
            return 0
    from app.core.database import SessionLocal
    s = SessionLocal()
    try:
        n = _yaz(s, satirlar)
        s.commit()
        return n
    except Exception:
        s.rollback()
        log.exception("erişim kayıtları yazılamadı")
        return 0
    finally:
        s.close()


def _yazici() -> None:
    while True:
        time.sleep(3)
        try:
            bosalt()
        except Exception:
            pass


def yaziciyi_baslat() -> None:
    threading.Thread(target=_yazici, name="erisim-kaydi-yazici", daemon=True).start()


class ErisimKaydiAraKatmani:
    """Saf ASGI ara katmanı. IP'yi bağlam değişkenine koyar (giriş olayları için); yanıttan sonra oturum açık isteği kuyruğa
    bırakır. Kayıt hatası asıl isteği asla bozmaz."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        basliklar = {}
        try:
            basliklar = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers") or []}
            ileri = basliklar.get("x-forwarded-for")
            ip = ileri.split(",")[0].strip() if ileri else ((scope.get("client") or [None])[0])
            IP.set(ip)
        except Exception:
            pass
        yanit = {"kod": 500, "tur": ""}

        async def yakala(mesaj):
            if mesaj["type"] == "http.response.start":
                yanit["kod"] = mesaj["status"]
                for k, v in mesaj.get("headers") or []:
                    if k.lower() == b"content-type":
                        yanit["tur"] = v.decode("latin-1").lower()
            await send(mesaj)
        try:
            await self.app(scope, receive, yakala)
        finally:
            try:
                yetki = basliklar.get("authorization", "")
                if yetki.startswith("Bearer "):
                    from app.core.security import token_coz
                    payload = token_coz(yetki[7:].strip())
                    if payload and payload.get("tip") == "access" and payload.get("sub"):
                        istek_kaydi(scope, payload, yanit["kod"], yanit["tur"])
            except Exception:
                pass
