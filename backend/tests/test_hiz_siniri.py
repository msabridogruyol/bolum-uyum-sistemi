"""[2026-10-11] İstek sıklığı sınırı — veritabanı gerektirmez."""
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.hiz_siniri import HizSiniriAraKatmani, KovaSinirlayici, VARSAYILAN, kademe_bul, kurallar
from app.core.security import erisim_tokeni_uret


class Saat:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_kova_sinir_ve_dolum():
    saat = Saat()
    s = KovaSinirlayici(saat=saat)
    k = [(3, 60.0)]
    assert [s.dene("a", k) for _ in range(3)] == [0, 0, 0]
    bekle = s.dene("a", k)
    assert 19 < bekle <= 20.01           # 3/dk → bir jeton 20 sn'de dolar
    assert s.dene("b", k) == 0           # başka anahtar etkilenmez
    saat.t += 20.0
    assert s.dene("a", k) == 0
    assert s.dene("a", k) > 0


def test_kova_coklu_kural_hepsi_gecerli():
    saat = Saat()
    s = KovaSinirlayici(saat=saat)
    k = [(10, 60.0), (12, 3600.0)]
    for _ in range(10):
        assert s.dene("x", k) == 0
    assert s.dene("x", k) > 0            # dakika kuralı
    saat.t += 60
    assert s.dene("x", k) == 0 and s.dene("x", k) == 0
    bekle = s.dene("x", k)               # saat kuralı (12) doldu
    assert bekle > 60


def test_kova_reddedilen_istek_jeton_tuketmez():
    saat = Saat()
    s = KovaSinirlayici(saat=saat)
    k = [(1, 10.0), (100, 60.0)]
    assert s.dene("y", k) == 0
    for _ in range(50):
        assert s.dene("y", k) > 0
    saat.t += 10
    assert s.dene("y", k) == 0           # 100'lük kova reddedilenlerle boşalmamış olmalı


def test_kova_bellek_temizligi():
    saat = Saat()
    s = KovaSinirlayici(saat=saat, en_fazla_anahtar=50)
    for i in range(200):
        s.dene(f"ip{i}", [(5, 60.0)])
    assert len(s._kovalar) <= 50


@pytest.mark.parametrize("metod,yol,beklenen", [
    ("POST", "/auth/giris", "kimlik"),
    ("POST", "/admin/auth/giris", "kimlik"),
    ("POST", "/auth/iki-adim/dogrula", "kimlik"),
    ("POST", "/admin/auth/sifremi-unuttum", "kimlik"),
    ("GET", "/auth/sifre-sifirla/bilgi", "kimlik"),
    ("POST", "/auth/sifre-sifirla", "kimlik"),
    ("POST", "/auth/test-giris", "kimlik"),
    ("POST", "/auth/kayit", "kimlik"),
    ("POST", "/auth/yenile", "genel"),
    ("POST", "/yonetim/okul/5/onizle", "agir"),
    ("POST", "/yonetim/okul/5/ogrenciler", "agir"),
    ("GET", "/yonetim/okul/5/ogrenciler", "genel"),
    ("POST", "/yonetim/okul/5/deneme-onizle", "agir"),
    ("GET", "/yonetim/okul/5/okul-denemeleri", "genel"),
    ("POST", "/admin/is-hayati/dosya/oku", "agir"),
    ("POST", "/admin/sorular/toplu", "agir"),
    ("POST", "/admin/pipeline/yukle", "agir"),
    ("GET", "/yonetim/okul/3/istatistik/excel", "agir"),
    ("GET", "/ogrenci/portfolyo/pdf", "agir"),
    ("GET", "/ogrenci/rapor", "agir"),
    ("GET", "/yonetim/anket-sablonlari", "genel"),
    ("POST", "/koclugu/asistan/oturum/abc/mesaj", "agir"),
    ("POST", "/istemci-hata", "istemci_hata"),
    ("GET", "/ogrenci/profil", "genel"),
    ("GET", "/saglik", None),
    ("OPTIONS", "/auth/giris", None),
    ("GET", "/openapi.json", None),
])
def test_kademe_bul(metod, yol, beklenen):
    assert kademe_bul(metod, yol) == beklenen


def test_kurallar_parametreden():
    assert kurallar("kimlik", VARSAYILAN) == [(20, 60.0), (150, 3600.0)]
    assert kurallar("genel", {**VARSAYILAN, "hiz_siniri_genel_dakika": "5"}) == [(5, 60.0)]
    assert kurallar("genel", {**VARSAYILAN, "hiz_siniri_genel_dakika": "0"}) == []       # 0 → kapalı
    assert kurallar("agir", {**VARSAYILAN, "hiz_siniri_agir_dakika": "abc"})[0] == (20, 60.0)   # bozuk değer → varsayılan


def _uygulama(param):
    async def tamam(request):
        return JSONResponse({"ok": True})
    app = Starlette(routes=[Route(y, tamam, methods=["GET", "POST", "OPTIONS"])
                            for y in ("/auth/giris", "/saglik", "/ogrenci/profil")])
    return HizSiniriAraKatmani(app, parametre_kaynagi=lambda: param)


def test_ara_katman_429_retry_after_turkce():
    c = TestClient(_uygulama({"hiz_siniri_kimlik_dakika": "3", "hiz_siniri_kimlik_saat": "100"}))
    for _ in range(3):
        assert c.post("/auth/giris", headers={"X-Forwarded-For": "1.2.3.4, 10.0.0.1"}).status_code == 200
    r = c.post("/auth/giris", headers={"X-Forwarded-For": "1.2.3.4, 10.0.0.1"})
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) >= 1
    assert "tekrar deneyin" in r.json()["detail"] and "giriş" in r.json()["detail"]
    # Farklı IP (X-Forwarded-For'un ilk değeri) etkilenmez
    assert c.post("/auth/giris", headers={"X-Forwarded-For": "5.6.7.8"}).status_code == 200


def test_ara_katman_muaf_yollar():
    c = TestClient(_uygulama({"hiz_siniri_kimlik_dakika": "1", "hiz_siniri_genel_dakika": "1"}))
    for _ in range(5):
        assert c.get("/saglik").status_code == 200
        assert c.options("/auth/giris").status_code == 200


def test_ara_katman_kullanici_bazli_anahtar():
    """Aynı IP (okul NAT'ı) arkasındaki iki öğrenci genel kademede birbirinin kotasını tüketmez."""
    import uuid
    c = TestClient(_uygulama({"hiz_siniri_genel_dakika": "2"}))
    t1 = {"Authorization": f"Bearer {erisim_tokeni_uret(uuid.uuid4(), 'ogrenci')}", "X-Forwarded-For": "9.9.9.9"}
    t2 = {"Authorization": f"Bearer {erisim_tokeni_uret(uuid.uuid4(), 'ogrenci')}", "X-Forwarded-For": "9.9.9.9"}
    assert c.get("/ogrenci/profil", headers=t1).status_code == 200
    assert c.get("/ogrenci/profil", headers=t1).status_code == 200
    assert c.get("/ogrenci/profil", headers=t1).status_code == 429
    assert c.get("/ogrenci/profil", headers=t2).status_code == 200


def test_ara_katman_kapali_parametresi():
    c = TestClient(_uygulama({"hiz_siniri": "kapali", "hiz_siniri_kimlik_dakika": "1"}))
    for _ in range(5):
        assert c.post("/auth/giris").status_code == 200


def test_ara_katman_parametre_hatasinda_varsayilan():
    def bozuk():
        raise RuntimeError("veritabanı yok")
    async def tamam(request):
        return JSONResponse({"ok": True})
    app = HizSiniriAraKatmani(Starlette(routes=[Route("/auth/giris", tamam, methods=["POST"])]), parametre_kaynagi=bozuk)
    c = TestClient(app)
    kodlar = [c.post("/auth/giris").status_code for _ in range(21)]
    assert kodlar[:20] == [200] * 20 and kodlar[20] == 429      # varsayılan 20/dk
