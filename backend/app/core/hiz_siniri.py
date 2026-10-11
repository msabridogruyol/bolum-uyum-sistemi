"""
[2026-10-11] İstek sıklığı sınırlama (rate limiting) — ek paket yok, süreç içi (in-memory) token bucket.

Kademeler (varsayılanlar; sistem_parametreleri'nden değiştirilebilir, 60 sn'de bir yeniden okunur):
  kimlik       — giriş, 2 adımlı kod, şifre sıfırlama/davet kabul, kayıt, test girişi: IP başına 120/dk ve 2000/saat
  + hesap başına — [2026-10-11] HESAP_DENEME: aynı e-postaya 15 dakikada 8 hatalı şifre → o hesap 15 dk kilitlenir (IP'den bağımsız)
  agir         — dosya yükleme / önizleme, toplu yükleme, PDF / Excel üretimi, Filiz AI mesajı (öğrenci + yönetim): kişi (yoksa IP) başına 20/dk ve 300/saat
  istemci_hata — POST /istemci-hata (kimliksiz): IP başına 10/dk ve 60/saat
  genel        — diğer tüm API: kişi (yoksa IP) başına 300/dk
  muaf         — OPTIONS, /saglik, /docs, /openapi.json, /redoc, /favicon.ico
[2026-10-11] Kimlik kademesi neden 120/dk? Okullarda bir sınıfın / laboratuvarın tamamı aynı dış IP'den (NAT) aynı anda giriş
yapar; 20/dk'lık eski sınır 30 kişilik bir laboratuvarı kilitliyordu. Kaba kuvvete karşı asıl koruma artık HESAP başına
(HESAP_DENEME: e-posta başına hatalı şifre sayacı); IP tavanı yalnızca parola püskürtme / e-posta bombardımanına karşı. Kimlikli isteklerde anahtar kullanıcıdır (JWT sub),
böylece aynı okul IP'sinin arkasındaki öğrenciler genel kademede birbirinin kotasını tüketmez.

SINIRLAMALAR (bilinçli):
  * Sayaçlar SÜREÇ İÇİDİR. Render'da birden çok örnek (instance) ya da birden çok uvicorn işçisi çalışırsa her biri kendi
    sayacını tutar; etkin sınır ≈ sınır × örnek sayısı olur ve yeniden başlatmada sayaçlar sıfırlanır. Ölçek büyürse
    sayaçlar Redis'e (INCR + EXPIRE) ya da Postgres'e taşınmalıdır; bu modülde arayüz (KovaSinirlayici.dene) aynı kalır.
  * İstemci IP'si X-Forwarded-For'un İLK değeridir (app.api.auth.istemci_ip ile aynı kalıp). Vercel yeniden yazma
    katmanı bu başlığı gerçek istemci IP'siyle değiştirir; Render adresine doğrudan gelen istekte başlık sahte olabilir.
  * Sınırlayıcı ya da parametre okuma hata verirse istek GEÇER (fail-open): sınırlama erişilebilirliği bozmamalı.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from typing import Callable

from app.core.security import token_coz

MUAF_YOLLAR = {"/saglik", "/docs", "/openapi.json", "/redoc", "/favicon.ico", "/docs/oauth2-redirect"}

# (anahtar, varsayılan) — sistem_parametreleri.anahtar
VARSAYILAN = {
    "hiz_siniri": "acik",                     # "kapali" → tamamen devre dışı
    "hiz_siniri_kimlik_dakika": "120",          # [2026-10-11] 20 → 120: bir laboratuvar (30–40 öğrenci) aynı IP'den aynı anda girer
    "hiz_siniri_kimlik_saat": "2000",           # 150 → 2000
    "hiz_siniri_agir_dakika": "20",
    "hiz_siniri_agir_saat": "300",
    "hiz_siniri_genel_dakika": "300",
    "hiz_siniri_istemci_hata_dakika": "10",
    "hiz_siniri_istemci_hata_saat": "60",
}

_KIMLIK = re.compile(
    r"^/(auth|admin/auth)/(giris|kayit|test-giris|iki-adim/dogrula|iki-adim/tekrar|sifremi-unuttum|sifre-sifirla|sifre-sifirla/bilgi)/?$"
)
_AGIR_GET = [
    re.compile(r"/(pdf|excel|rapor|sablon|deneme-sablonu)/?$"),                # PDF / Excel / şablon üretimi
]
_AGIR = [                                                                       # yalnızca POST / PUT
    re.compile(r"/(onizle|deneme-onizle|okul-denemeleri)/?$"),                 # dosya önizleme / deneme kaydı
    re.compile(r"^/yonetim/okul/\d+/ogrenciler/?$"),                           # toplu öğrenci oluşturma
    re.compile(r"^/admin/is-hayati/(baglanti/indir|dosya/oku|istihdam/|kazanc/)"),
    re.compile(r"^/admin/(sorular/toplu|pipeline/yukle|kutup-sorulari/toplu|meslekler/toplu-yukle|"
               r"bolumler/toplu-aciklama|soru-gecerlilik/yukle)/?$"),
    re.compile(r"^/koclugu/asistan/oturum/[^/]+/mesaj/?$"),                             # Filiz AI (dış API maliyeti)
    re.compile(r"^/yonetim/filiz/sor/?$"),                                              # [2026-10-11] Filiz yönetim asistanı (AI modu)
]


def kademe_bul(metod: str, yol: str) -> str | None:
    """None → sınırlama yok (muaf)."""
    if metod == "OPTIONS" or yol in MUAF_YOLLAR:
        return None
    if yol.rstrip("/") == "/istemci-hata":
        return "istemci_hata"
    if _KIMLIK.match(yol):
        return "kimlik"
    if metod == "GET" and any(d.search(yol) for d in _AGIR_GET):
        return "agir"
    if metod in ("POST", "PUT") and any(d.search(yol) for d in _AGIR):
        return "agir"
    return "genel"


def kurallar(kademe: str, p: dict) -> list[tuple[int, float]]:
    """[(en_fazla_istek, saniye), ...] — 0 ya da negatif değer o kuralı kapatır."""
    def i(anahtar):
        try:
            return int(float(p.get(anahtar, VARSAYILAN[anahtar])))
        except (TypeError, ValueError):
            return int(VARSAYILAN[anahtar])

    if kademe == "kimlik":
        k = [(i("hiz_siniri_kimlik_dakika"), 60.0), (i("hiz_siniri_kimlik_saat"), 3600.0)]
    elif kademe == "agir":
        k = [(i("hiz_siniri_agir_dakika"), 60.0), (i("hiz_siniri_agir_saat"), 3600.0)]
    elif kademe == "istemci_hata":
        k = [(i("hiz_siniri_istemci_hata_dakika"), 60.0), (i("hiz_siniri_istemci_hata_saat"), 3600.0)]
    else:
        k = [(i("hiz_siniri_genel_dakika"), 60.0)]
    return [(n, s) for n, s in k if n > 0]


class HesapDenemeSayaci:
    """[2026-10-11] Hesap (e-posta) başına hatalı şifre sayacı — IP'den bağımsız kaba kuvvet koruması.
    Pencere içinde `en_fazla` hatalı denemeden sonra hesap `pencere` saniye kilitli kalır; doğru şifre sayacı sıfırlar.
    Süreç içidir (KovaSinirlayici ile aynı sınırlama)."""

    def __init__(self, en_fazla: int = 8, pencere: float = 900.0, saat: Callable[[], float] = time.monotonic):
        self.en_fazla, self.pencere, self._saat = en_fazla, pencere, saat
        self._kayit: dict[str, list[float]] = {}
        self._kilit = threading.Lock()

    def _guncel(self, anahtar: str, simdi: float) -> list[float]:
        l = [t for t in self._kayit.get(anahtar, []) if simdi - t < self.pencere]
        if l:
            self._kayit[anahtar] = l
        else:
            self._kayit.pop(anahtar, None)
        return l

    def bekleme(self, anahtar: str) -> float:
        """0 → deneyebilir; >0 → kaç saniye sonra."""
        simdi = self._saat()
        with self._kilit:
            l = self._guncel(anahtar, simdi)
            return max(0.0, self.pencere - (simdi - l[-self.en_fazla])) if len(l) >= self.en_fazla else 0.0

    def hatali(self, anahtar: str) -> None:
        simdi = self._saat()
        with self._kilit:
            if len(self._kayit) > 50_000:
                self._kayit.clear()
            self._guncel(anahtar, simdi)
            self._kayit.setdefault(anahtar, []).append(simdi)

    def temizle(self, anahtar: str) -> None:
        with self._kilit:
            self._kayit.pop(anahtar, None)


HESAP_DENEME = HesapDenemeSayaci()


def hesap_kilit_kontrol(email: str) -> None:
    """Giriş uçlarında şifre kontrolünden ÖNCE çağrılır; kilitliyse 429."""
    from fastapi import HTTPException
    b = HESAP_DENEME.bekleme(email)
    if b > 0:
        dk = max(1, math.ceil(b / 60))
        raise HTTPException(status_code=429, detail=f"Bu hesap için çok fazla hatalı şifre denendi. Güvenliğin için {dk} dakika sonra tekrar dene "
                                                    "ya da \"Şifremi unuttum\" ile yeni şifre al.")


class KovaSinirlayici:
    """Token bucket: her (anahtar, kural) için kapasite = sınır, dolum hızı = sınır / süre.
    dene() izin verilirse 0, verilmezse kaç saniye sonra tekrar denenebileceğini döner (hiçbir kova tüketilmez)."""

    def __init__(self, en_fazla_anahtar: int = 100_000, saat: Callable[[], float] = time.monotonic):
        self._kovalar: dict[tuple, list[float]] = {}   # (anahtar, sınır, süre) → [jeton, son_zaman]
        self._kilit = threading.Lock()
        self._saat = saat
        self._en_fazla = en_fazla_anahtar
        self._son_temizlik = saat()

    def dene(self, anahtar: str, kurallar_: list[tuple[int, float]]) -> float:
        if not kurallar_:
            return 0.0
        simdi = self._saat()
        with self._kilit:
            self._temizle(simdi)
            durumlar = []
            bekle = 0.0
            for sinir, sure in kurallar_:
                k = (anahtar, sinir, sure)
                kova = self._kovalar.get(k)
                hiz = sinir / sure
                if kova is None:
                    kova = [float(sinir), simdi]
                    self._kovalar[k] = kova
                else:
                    kova[0] = min(float(sinir), kova[0] + (simdi - kova[1]) * hiz)
                    kova[1] = simdi
                if kova[0] < 1.0:
                    bekle = max(bekle, (1.0 - kova[0]) / hiz)
                durumlar.append(kova)
            if bekle > 0:
                return bekle
            for kova in durumlar:
                kova[0] -= 1.0
            return 0.0

    def _temizle(self, simdi: float) -> None:
        # Dolmuş (uzun süre boşta kalmış) kovalar bellekte tutulmaz; sahte IP seline karşı üst sınır.
        if simdi - self._son_temizlik < 60 and len(self._kovalar) < self._en_fazla:
            return
        self._son_temizlik = simdi
        for k in [k for k, v in self._kovalar.items() if simdi - v[1] >= k[2]]:
            del self._kovalar[k]
        if len(self._kovalar) >= self._en_fazla:   # hâlâ çoksa (saldırı) — fail-open: sıfırla
            self._kovalar.clear()

    def sifirla(self) -> None:
        with self._kilit:
            self._kovalar.clear()


def _istemci_ip(scope) -> str:
    for ad, deger in scope.get("headers") or []:
        if ad == b"x-forwarded-for":
            ilk = deger.decode("latin-1").split(",")[0].strip()
            if ilk:
                return ilk
    istemci = scope.get("client")
    return istemci[0] if istemci else "bilinmiyor"


def _kullanici_anahtari(scope) -> str | None:
    for ad, deger in scope.get("headers") or []:
        if ad == b"authorization":
            d = deger.decode("latin-1")
            if d.startswith("Bearer "):
                p = token_coz(d[7:].strip())
                if p and p.get("sub"):
                    return f"{p.get('rol', '?')}:{p['sub']}"
            return None
    return None


def _parametreleri_db_den_oku() -> dict:
    from sqlalchemy import text
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        satirlar = db.execute(text("SELECT anahtar, deger FROM sistem_parametreleri WHERE anahtar LIKE 'hiz_siniri%'")).all()
        return {a: d for a, d in satirlar}
    finally:
        db.close()


class HizSiniriAraKatmani:
    """Saf ASGI ara katmanı. Aşımda 429 + Retry-After + Türkçe mesaj."""

    def __init__(self, app, sinirlayici: KovaSinirlayici | None = None,
                 parametre_kaynagi: Callable[[], dict] | None = _parametreleri_db_den_oku, yenileme_sn: float = 60.0):
        self.app = app
        self.sinirlayici = sinirlayici or KovaSinirlayici()
        self._kaynak = parametre_kaynagi
        self._yenileme = yenileme_sn
        self._param = dict(VARSAYILAN)
        self._param_zamani = -1e9

    async def _parametreler(self) -> dict:
        simdi = time.monotonic()
        if self._kaynak is not None and simdi - self._param_zamani >= self._yenileme:
            self._param_zamani = simdi   # hata olsa da her istekte yeniden denenmesin
            try:
                import anyio
                okunan = await anyio.to_thread.run_sync(self._kaynak)
                self._param = {**VARSAYILAN, **(okunan or {})}
            except Exception:
                pass
        return self._param

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        kademe = kademe_bul(scope.get("method", "GET"), scope.get("path", ""))
        if kademe is None:
            return await self.app(scope, receive, send)
        try:
            p = await self._parametreler()
            if str(p.get("hiz_siniri", "acik")).strip().lower() == "kapali":
                return await self.app(scope, receive, send)
            ip = _istemci_ip(scope)
            if kademe in ("kimlik", "istemci_hata"):
                anahtar = f"ip:{ip}"
            else:
                anahtar = _kullanici_anahtari(scope) or f"ip:{ip}"
            bekle = self.sinirlayici.dene(f"{kademe}|{anahtar}", kurallar(kademe, p))
        except Exception:
            bekle = 0.0   # fail-open
        if bekle <= 0:
            return await self.app(scope, receive, send)

        sn = max(1, math.ceil(bekle))
        sure = f"{sn} saniye" if sn < 120 else f"{math.ceil(sn / 60)} dakika"
        mesaj = {
            "kimlik": f"Çok fazla giriş/doğrulama denemesi yapıldı. Lütfen {sure} sonra tekrar deneyin.",
            "agir": f"Bu işlemi çok sık yaptınız (dosya yükleme / rapor üretimi). Lütfen {sure} sonra tekrar deneyin.",
        }.get(kademe, f"Çok fazla istek gönderildi. Lütfen {sure} sonra tekrar deneyin.")
        govde = json.dumps({"detail": mesaj, "kademe": kademe}, ensure_ascii=False).encode("utf-8")
        await send({"type": "http.response.start", "status": 429, "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(govde)).encode()),
            (b"retry-after", str(sn).encode()),
        ]})
        await send({"type": "http.response.body", "body": govde})
