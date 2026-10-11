"""[2026-10-11] Yükleme boyut sınırları — veritabanı gerektirmez."""
import base64
import io

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from app.core.yukleme_siniri import (GovdeBoyutuAraKatmani, MB, TABLO_EN_FAZLA_SATIR, base64_coz, satir_siniri)


def _uygulama(sinir=1000, yol_sinirlari=None):
    app = FastAPI()

    @app.post("/yukle")
    async def yukle(request: Request):
        return {"uzunluk": len(await request.body())}

    @app.post("/json")
    def json_uc(veri: dict):
        return {"anahtar": len(veri)}

    @app.post("/istemci-hata")
    async def ih(request: Request):
        return {"uzunluk": len(await request.body())}

    return GovdeBoyutuAraKatmani(app, en_fazla=sinir, yol_sinirlari=yol_sinirlari if yol_sinirlari is not None else {"/istemci-hata": 100})


def test_content_length_asiminda_413():
    c = TestClient(_uygulama())
    r = c.post("/yukle", content=b"x" * 1001)
    assert r.status_code == 413
    assert "İstek çok büyük" in r.json()["detail"]
    assert c.post("/yukle", content=b"x" * 1000).json() == {"uzunluk": 1000}


def test_akista_sayarak_413_content_length_yok():
    c = TestClient(_uygulama())

    def parcalar():
        for _ in range(5):
            yield b"y" * 300            # toplam 1500 > 1000; chunked, Content-Length yok

    r = c.post("/yukle", content=parcalar())
    assert r.status_code == 413


def test_akista_413_fastapi_govde_ayristirmada():
    """FastAPI JSON gövdesini okurken oluşan hatayı 400'e sarar; ara katman bunu 413'e çevirmeli."""
    c = TestClient(_uygulama())

    def parcalar():
        yield b'{"a": "' + b"z" * 600
        yield b"z" * 600 + b'"}'

    r = c.post("/json", content=parcalar(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_yol_ozel_sinir():
    c = TestClient(_uygulama())
    assert c.post("/istemci-hata", content=b"a" * 101).status_code == 413
    assert c.post("/istemci-hata", content=b"a" * 100).status_code == 200


def test_get_istegi_etkilenmez():
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})
    c = TestClient(GovdeBoyutuAraKatmani(app, en_fazla=1))
    assert c.get("/").status_code == 200


def test_base64_coz_sinir():
    veri = b"a" * 2000
    assert base64_coz(base64.b64encode(veri).decode(), en_fazla_bayt=2000) == veri
    assert base64_coz("data:text/csv;base64," + base64.b64encode(veri).decode(), en_fazla_bayt=2000) == veri
    with pytest.raises(HTTPException) as e:
        base64_coz(base64.b64encode(veri).decode(), en_fazla_bayt=1000)
    assert e.value.status_code == 413 and "en fazla" in e.value.detail


def test_satir_siniri():
    satir_siniri(TABLO_EN_FAZLA_SATIR)
    with pytest.raises(HTTPException) as e:
        satir_siniri(TABLO_EN_FAZLA_SATIR + 1)
    assert e.value.status_code == 413 and "20.000" in e.value.detail


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def test_tablo_dosyasi_csv_satir_siniri():
    from app.api.okul_yonetimi import _dosyadan_satirlar
    baslik = "ad;soyad\n"
    tamam = baslik + "".join(f"Ad{i};Soyad{i}\n" for i in range(TABLO_EN_FAZLA_SATIR))
    assert len(_dosyadan_satirlar("x.csv", _b64(tamam.encode()))) == TABLO_EN_FAZLA_SATIR + 1
    fazla = tamam + "Fazla;Satir\n"
    with pytest.raises(HTTPException) as e:
        _dosyadan_satirlar("x.csv", _b64(fazla.encode()))
    assert e.value.status_code == 413


def test_tablo_dosyasi_bayt_siniri():
    from app.api.okul_yonetimi import _dosyadan_satirlar
    with pytest.raises(HTTPException) as e:
        _dosyadan_satirlar("x.csv", _b64(b"a;b\n" * (10 * MB // 4 + 10)))
    assert e.value.status_code == 413 and "10 MB" in e.value.detail


def test_tablo_dosyasi_excel_satir_siniri():
    openpyxl = pytest.importorskip("openpyxl")
    from app.api.okul_yonetimi import _dosyadan_satirlar
    wb = openpyxl.Workbook(write_only=True)
    ws = wb.create_sheet()
    ws.append(["Ad", "Soyad"])
    for i in range(TABLO_EN_FAZLA_SATIR + 5):
        ws.append([f"Ad{i}", f"S{i}"])
    bio = io.BytesIO()
    wb.save(bio)
    with pytest.raises(HTTPException) as e:
        _dosyadan_satirlar("x.xlsx", _b64(bio.getvalue()))
    assert e.value.status_code == 413
