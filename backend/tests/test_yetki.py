"""[2026-10-11] Kritik uçlarda yetki sınırları (gerçek uygulama, PostgreSQL; veriler işlem sonunda geri alınır)."""
import pytest

from tests.conftest import db_gerekli

YONETIM_UCLARI = [
    ("GET", "/admin/parametreler"),
    ("GET", "/admin/hata-kayitlari"),
    ("GET", "/admin/audit-log"),
    ("GET", "/yonetim/okul/{okul_a}/ogrenciler"),
    ("GET", "/yonetim/test-hesaplari"),
    ("POST", "/admin/sorular/toplu"),
]


def _yol(sablon, kisiler):
    return sablon.format(okul_a=kisiler["okul_a"], okul_b=kisiler["okul_b"])


@db_gerekli
@pytest.mark.parametrize("metod,yol", YONETIM_UCLARI)
def test_tokensiz_yonetim_uclari_401(istemci, kisiler, metod, yol):
    r = istemci.request(metod, _yol(yol, kisiler), json={} if metod == "POST" else None)
    assert r.status_code == 401


@db_gerekli
@pytest.mark.parametrize("metod,yol", YONETIM_UCLARI)
def test_ogrenci_yonetim_uclarina_giremez(istemci, kisiler, metod, yol):
    r = istemci.request(metod, _yol(yol, kisiler), headers=kisiler["ogrenci"], json={"satirlar": []} if metod == "POST" else None)
    assert r.status_code in (401, 403)


@db_gerekli
@pytest.mark.parametrize("yol", ["/admin/parametreler", "/admin/hata-kayitlari", "/yonetim/test-hesaplari"])
def test_okul_yetkilisi_super_admin_uclarina_giremez(istemci, kisiler, yol):
    assert istemci.get(yol, headers=kisiler["yetkili"]).status_code in (401, 403)


@db_gerekli
@pytest.mark.parametrize("yol", [
    "/yonetim/okul/{okul_b}/ogrenciler",
    "/yonetim/okul/{okul_b}/istatistik",
])
def test_okul_yetkilisi_baska_okula_403(istemci, kisiler, yol):
    r = istemci.get(_yol(yol, kisiler), headers=kisiler["yetkili"])
    assert r.status_code == 403


@db_gerekli
def test_okul_yetkilisi_kendi_okuluna_girer(istemci, kisiler):
    r = istemci.get(_yol("/yonetim/okul/{okul_a}/ogrenciler", kisiler), headers=kisiler["yetkili"])
    assert r.status_code == 200


@db_gerekli
def test_okul_yetkilisi_baska_okula_toplu_ogrenci_ekleyemez(istemci, kisiler):
    r = istemci.post(_yol("/yonetim/okul/{okul_b}/ogrenciler", kisiler), headers=kisiler["yetkili"],
                     json={"ogrenciler": [{"ad_soyad": "X Y", "email": "x@y.invalid"}]})
    assert r.status_code == 403


@db_gerekli
def test_super_admin_hata_kayitlarina_girer(istemci, kisiler):
    r = istemci.get("/admin/hata-kayitlari", headers=kisiler["super"])
    assert r.status_code == 200 and "gruplar" in r.json() and "ozet" in r.json()


@db_gerekli
def test_toplu_yukleme_satir_siniri_413(istemci, kisiler):
    satir = {"katman_kod": "K1", "a_degisken_kod": "A", "b_degisken_kod": "B", "soru_metni": "s", "a_ucu_etiketi": "a", "b_ucu_etiketi": "b"}
    r = istemci.post("/admin/kutup-sorulari/toplu", headers=kisiler["super"], json={"satirlar": [satir] * 20_001})
    assert r.status_code == 413 and "20.000" in r.json()["detail"]


@db_gerekli
def test_yanitlarda_istek_kimligi_basligi(istemci):
    r = istemci.get("/saglik")
    assert r.status_code == 200 and r.headers.get("x-istek-kimligi")
