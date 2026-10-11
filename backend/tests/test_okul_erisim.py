"""[2026-10-11] Okul sistemi aç / kapat ve tek giriş ekranı (gerçek uygulama, PostgreSQL; veriler geri alınır)."""
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


@pytest.fixture
def sifreli(db, kisiler):
    """kisiler'deki hesaplara bilinen şifre ve e-posta verir."""
    from app.core.security import sifre_hashle
    h = sifre_hashle("DenemeSifre!1")
    ek = uuid.uuid4().hex[:6]
    e = {"ogr": f"ogr.{ek}@filizyol-test.com", "yet": f"yet.{ek}@filizyol-test.com", "sup": f"sup.{ek}@filizyol-test.com"}
    db.execute(text("UPDATE ogrenciler SET sifre_hash=:h, email=:e WHERE okul_id=:o"), {"h": h, "e": e["ogr"], "o": kisiler["okul_a"]})
    db.execute(text("UPDATE admin_kullanicilar SET sifre_hash=:h, email=:e WHERE okul_id=:o AND rol='okul_yetkilisi'"),
               {"h": h, "e": e["yet"], "o": kisiler["okul_a"]})
    db.execute(text("UPDATE admin_kullanicilar SET sifre_hash=:h, email=:e WHERE email LIKE 'super_admin.%@test.invalid' "
                    "AND id = (SELECT id FROM admin_kullanicilar WHERE email LIKE 'super_admin.%@test.invalid' ORDER BY olusturulma_zamani DESC LIMIT 1)"),
               {"h": h, "e": e["sup"]})
    db.commit()
    return e


def _giris(istemci, email, yol="/auth/giris"):
    return istemci.post(yol, json={"email": email, "sifre": "DenemeSifre!1"})


@db_gerekli
def test_okul_yetkilisi_ana_giris_ekranindan_girer(istemci, sifreli, monkeypatch):
    monkeypatch.setenv("IKI_ADIM_KAPALI", "1")
    from app.core import config
    monkeypatch.setattr(config.settings, "IKI_ADIM_KAPALI", "1", raising=False)
    r = _giris(istemci, sifreli["yet"])
    assert r.status_code == 200, r.text
    assert r.json()["kullanici_tipi"] == "okul_yetkilisi" and r.json()["erisim_tokeni"]
    ben = istemci.get("/yonetim/ben", headers={"Authorization": f"Bearer {r.json()['erisim_tokeni']}"})
    assert ben.status_code == 200


@db_gerekli
def test_okul_yetkilisi_yonetim_girisinden_giremez(istemci, sifreli):
    r = _giris(istemci, sifreli["yet"], "/admin/auth/giris")
    assert r.status_code == 403 and "ana giriş" in r.json()["detail"]


@db_gerekli
def test_ogrenci_girisi_degismedi(istemci, sifreli, monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "IKI_ADIM_KAPALI", "1", raising=False)
    r = _giris(istemci, sifreli["ogr"])
    assert r.status_code == 200 and r.json()["kullanici_tipi"] == "ogrenci"


@db_gerekli
def test_yanlis_sifre_ayni_mesaj(istemci, sifreli):
    for e in (sifreli["yet"], sifreli["ogr"], "yok@filizyol-test.com"):
        r = istemci.post("/auth/giris", json={"email": e, "sifre": "yanlis-sifre-123"})
        assert r.status_code == 401 and r.json()["detail"] == "E-posta veya şifre hatalı."


@db_gerekli
def test_okul_kapatilinca_giris_ve_oturum_423(istemci, kisiler, sifreli, monkeypatch):
    from app.core import config
    monkeypatch.setattr(config.settings, "IKI_ADIM_KAPALI", "1", raising=False)
    r = istemci.put(f"/admin/okullar/{kisiler['okul_a']}/erisim", headers=kisiler["super"], json={"acik": False, "mesaj": "Dönem arası bakım."})
    assert r.status_code == 200 and r.json()["erisim_acik"] is False

    for e in (sifreli["ogr"], sifreli["yet"]):
        r = _giris(istemci, e)
        assert r.status_code == 423 and r.json()["detail"] == "Dönem arası bakım."
    # açık oturumlar da kapanır
    assert istemci.get("/ogrenci/profil", headers=kisiler["ogrenci"]).status_code == 423
    assert istemci.get(f"/yonetim/okul/{kisiler['okul_a']}/ozet", headers=kisiler["yetkili"]).status_code == 423
    # süper admin etkilenmez
    assert istemci.get(f"/yonetim/okul/{kisiler['okul_a']}/ozet", headers=kisiler["super"]).status_code == 200

    r = istemci.put(f"/admin/okullar/{kisiler['okul_a']}/erisim", headers=kisiler["super"], json={"acik": True})
    assert r.status_code == 200 and r.json()["erisim_acik"] is True and r.json()["kapali_mesaji"] is None
    assert istemci.get("/ogrenci/profil", headers=kisiler["ogrenci"]).status_code == 200


@db_gerekli
def test_bos_mesajda_varsayilan(istemci, kisiler):
    from app.core.okul_erisim import VARSAYILAN_MESAJ
    istemci.put(f"/admin/okullar/{kisiler['okul_a']}/erisim", headers=kisiler["super"], json={"acik": False, "mesaj": "  "})
    r = istemci.get("/ogrenci/profil", headers=kisiler["ogrenci"])
    assert r.status_code == 423 and r.json()["detail"] == VARSAYILAN_MESAJ


@db_gerekli
def test_baska_okul_etkilenmez_ve_yetkili_kapatamaz(istemci, kisiler):
    r = istemci.put(f"/admin/okullar/{kisiler['okul_a']}/erisim", headers=kisiler["yetkili"], json={"acik": False})
    assert r.status_code in (401, 403)
    istemci.put(f"/admin/okullar/{kisiler['okul_b']}/erisim", headers=kisiler["super"], json={"acik": False})
    assert istemci.get("/ogrenci/profil", headers=kisiler["ogrenci"]).status_code == 200


@db_gerekli
def test_okul_yetkilisi_iki_adimli_dogrulamayi_ana_ekrandan_tamamlar(istemci, sifreli, monkeypatch):
    import re
    from app.core import eposta_servisi as ep
    monkeypatch.setenv("TEST_EPOSTA_KAYDI", "1")
    ep.GONDERILENLER.clear()
    r = _giris(istemci, sifreli["yet"])
    assert r.status_code == 200 and r.json()["iki_adim_gerekli"] is True
    kod = re.search(r"\b(\d{6})\b", ep.GONDERILENLER[-1]["metin"]).group(1)
    r = istemci.post("/auth/iki-adim/dogrula", json={"gecici_token": r.json()["gecici_token"], "kod": kod, "cihazi_hatirla": False})
    assert r.status_code == 200, r.text
    assert r.json()["kullanici_tipi"] == "okul_yetkilisi" and r.json()["erisim_tokeni"]
