# -*- coding: utf-8 -*-
"""[2026-10-11] Sunucu kilitlenmesi düzeltmeleri (10.000 öğrencilik simülasyonda bulundu).

1. Ziyaret kaydı istek yolunda veritabanına dokunmaz; kaydı kuyruğa bırakır.
2. Eşzamanlı istek sınırı aynı anda işlenen istek sayısını tavanda tutar, fazlası bekler (hata almaz).
Veritabansız birim testleri: küçük Starlette uygulamaları.
"""
import asyncio

import httpx
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


def _uygulama(gecikme=0.0, sayac=None):
    async def uc(request):
        if sayac is not None:
            sayac["simdi"] += 1
            sayac["en_fazla"] = max(sayac["en_fazla"], sayac["simdi"])
        await asyncio.sleep(gecikme)
        if sayac is not None:
            sayac["simdi"] -= 1
        return JSONResponse({"ok": True}, status_code=201)
    return Starlette(routes=[Route("/x", uc), Route("/saglik", uc)])


def test_ziyaret_kaydi_istek_yolunda_veritabanina_dokunmaz(monkeypatch):
    import app.main as m

    def patla(*a, **k):
        raise AssertionError("istek yolunda SessionLocal çağrıldı")
    monkeypatch.setattr(m, "SessionLocal", patla)
    while not m._ZIYARET_KUYRUGU.empty():
        m._ZIYARET_KUYRUGU.get_nowait()

    async def calis():
        uyg = m.ZiyaretKaydiMiddleware(_uygulama())
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=uyg), base_url="http://t") as c:
            r = await c.get("/x")
            await c.get("/saglik")          # hariç yol: kaydedilmez
        return r
    r = asyncio.run(calis())
    assert r.status_code == 201
    kayit = m._ZIYARET_KUYRUGU.get_nowait()
    assert kayit == {"yol": "/x", "metod": "GET", "tip": "anonim", "durum": 201}
    assert m._ZIYARET_KUYRUGU.empty()


def test_es_zamanli_istek_siniri_tavani_asmaz_ve_hepsi_tamamlanir():
    import app.main as m
    sayac = {"simdi": 0, "en_fazla": 0}

    async def calis():
        uyg = m.EsZamanliIstekSiniri(_uygulama(gecikme=0.02, sayac=sayac), sinir=3)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=uyg), base_url="http://t") as c:
            return await asyncio.gather(*[c.get("/x") for _ in range(20)])
    yanitlar = asyncio.run(calis())
    assert all(r.status_code == 201 for r in yanitlar)
    assert sayac["en_fazla"] == 3


def test_sinir_havuz_kapasitesinin_altinda():
    from app.core.database import HAVUZ_KAPASITESI
    import app.main as m
    katman = next(mw for mw in m.app.user_middleware if mw.cls is m.EsZamanliIstekSiniri)
    sinir = (getattr(katman, "kwargs", None) or getattr(katman, "options", {}))["sinir"]
    assert 1 <= sinir <= HAVUZ_KAPASITESI - 5


@pytest.mark.parametrize("dosya", ["0062_performans_indeksleri"])
def test_indeks_gocu_otomatik_listede(dosya):
    from app.core.sema_guncelleme import OTOMATIK
    assert dosya in OTOMATIK
