"""[2026-11-04] Okul özet raporları için kısa süreli önbellek (20.000 öğrencili okulda istatistik / tek bakışta / rapor yorumu
her açılışta 5–8 sn hesaplanıyordu).

Bu sayfalar o anki okul özetini gösterir; birkaç dakikalık gecikme anlamı değiştirmez. Sonuç fonksiyon + argümanlarla
(veritabanı oturumu hariç) en çok OZET_SURESI_SN saniye süreç içinde tutulur; aynı anda gelen aynı istekler tek hesabı
bekler. Dönen veri her çağırana kopyalanır (çağıran değiştirse de önbellek bozulmaz). Öğrenciye özel ekranlar ve rehberin
işlem yaptığı listeler (öğrenci listesi, erken uyarı, görüşmeler) önbelleğe alınmaz.
"""
from __future__ import annotations

import copy
import functools
import threading
import time

OZET_SURESI_SN = 300
_EN_FAZLA = 256
_veri: dict = {}
_kilitler: dict = {}
_ana = threading.Lock()


def ozet_onbellegi(fn=None, *, haric: tuple = (), kopyala: bool = True):
    """@ozet_onbellegi ya da @ozet_onbellegi(haric=("yonetici",)): anahtar, fonksiyonun parametrelerinden (db ve `haric`
    dışındakiler) kurulur. `haric` parametreler sonucu değiştirmeyen ama hesap için gereken nesnelerdir (ör. yetki
    denetiminden geçmiş yönetici)."""
    import inspect

    def bezeyici(f):
        imza = inspect.signature(f)

        @functools.wraps(f)
        def sarici(*args, **kwargs):
            b = imza.bind(*args, **kwargs)
            b.apply_defaults()
            anahtar = (f.__module__, f.__qualname__,
                       tuple((k, v) for k, v in b.arguments.items() if k != "db" and k not in haric))
            try:
                hash(anahtar)
            except TypeError:   # hashlenemeyen argüman (ör. küme) → önbelleksiz
                return f(*args, **kwargs)
            with _ana:
                kilit = _kilitler.setdefault(anahtar, threading.Lock())
            with kilit:
                k = _veri.get(anahtar)
                if k is not None and time.monotonic() - k[0] < OZET_SURESI_SN:
                    return copy.deepcopy(k[1]) if kopyala else k[1]
                sonuc = f(*args, **kwargs)
                with _ana:
                    if len(_veri) >= _EN_FAZLA:
                        for eski in sorted(_veri, key=lambda a: _veri[a][0])[: _EN_FAZLA // 2]:
                            _veri.pop(eski, None)
                            _kilitler.pop(eski, None)
                    _veri[anahtar] = (time.monotonic(), sonuc)
                return copy.deepcopy(sonuc) if kopyala else sonuc
        return sarici
    return bezeyici(fn) if fn is not None else bezeyici


def hepsini_bosalt() -> None:
    with _ana:
        _veri.clear()


class YazmadaBosaltAraKatmani:
    """Yönetim (/yonetim, /admin) tarafında başarılı her değişiklik isteğinden sonra özet önbelleği boşaltılır: rehber öğrenci
    ekleyince, sınıf atayınca vb. panel hemen güncel görünür. Öğrenci işlemleri (cevap, görev) boşaltmaz; okul özetleri
    öğrenci tarafındaki değişikliği en geç OZET_SURESI_SN sonra gösterir."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") in ("GET", "HEAD", "OPTIONS") or \
                not str(scope.get("path", "")).startswith(("/yonetim", "/admin")):
            return await self.app(scope, receive, send)

        async def gonder(mesaj):
            if mesaj["type"] == "http.response.start" and mesaj.get("status", 500) < 400:
                hepsini_bosalt()
            await send(mesaj)
        await self.app(scope, receive, gonder)
