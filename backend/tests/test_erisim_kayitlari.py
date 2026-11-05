"""
[2026-11-05] Erişim kayıtları: kim, ne zaman giriş yaptı; kimin verisine, hangi bölümde eriştiyse (yalnızca süper admin görür).
"""
from sqlalchemy import text

from app.core import erisim_kaydi as ek
from tests.conftest import db_gerekli


def test_sablon_ve_bolum():
    assert ek.sablon_cikar("/yonetim/ogrenci/9c1/rapor", {"ogrenci_id": "9c1"}) == "/yonetim/ogrenci/{ogrenci_id}/rapor"
    assert ek.sablon_cikar("/yonetim/okul/12/ogrenciler", {"okul_id": 12}) == "/yonetim/okul/{okul_id}/ogrenciler"
    assert ek.bolum_adi("/yonetim/ogrenci/{ogrenci_id}/cevap-analizi") == "Cevap ayrıntısı"
    assert ek.bolum_adi("/yonetim/ogrenci/{ogrenci_id}") == "Öğrenci kartı"
    assert ek.bolum_adi("/yonetim/ogrenci/{ogrenci_id}/gorusmeler") == "Rehberlik görüşmeleri"
    assert ek.bolum_adi("/yonetim/okul/{okul_id}/ogrenciler") == "Öğrenci listesi"
    assert ek.bolum_adi("/bilinmeyen/bir-sayfa") == "Bir sayfa"


def _kayitlar(db, **kosul):
    ek.bosalt(db)
    nerede = " AND ".join(f"{k} = :{k}" for k in kosul)
    return db.execute(text(f"SELECT * FROM erisim_kayitlari WHERE {nerede} ORDER BY id"), kosul).mappings().all()


def _ogr(db, kisiler):
    return db.execute(text("SELECT id, email FROM ogrenciler WHERE okul_id = :o"), {"o": kisiler["okul_a"]}).one()


@db_gerekli
def test_giris_olaylari(db, kisiler, istemci):
    from app.core.security import sifre_hashle
    oid, _ = _ogr(db, kisiler)
    eposta = f"ogr.{str(oid)[:8]}@filizyol-test.com"
    db.execute(text("UPDATE ogrenciler SET sifre_hash = :h, email = :e WHERE id = :i"),
               {"h": sifre_hashle("Dogru-Sifre-1"), "e": eposta, "i": oid})
    db.commit()
    assert istemci.post("/auth/giris", json={"email": eposta, "sifre": "yanlis-sifre"}).status_code == 401
    r = istemci.post("/auth/giris", json={"email": eposta, "sifre": "Dogru-Sifre-1"})
    assert r.status_code == 200, r.text
    olaylar = [k["olay"] for k in _kayitlar(db, kullanici_id=oid)]
    assert olaylar[:2] == ["giris_hatali", "giris"]
    k = _kayitlar(db, kullanici_id=oid)[1]
    assert k["kullanici_tipi"] == "ogrenci" and k["kullanici_ad"] == "Test Öğrenci" and k["okul_id"] == kisiler["okul_a"]

    # Kayıtlı olmayan e-posta: kişi bilinmez, denenen e-posta yazılır
    istemci.post("/auth/giris", json={"email": "yok.boyle.biri@filizyol-test.com", "sifre": "x12345678"})
    k = _kayitlar(db, kullanici_eposta="yok.boyle.biri@filizyol-test.com")
    assert k and k[-1]["olay"] == "giris_hatali" and k[-1]["kullanici_tipi"] == "bilinmiyor" and k[-1]["kullanici_id"] is None


@db_gerekli
def test_yonetici_erisimi_hedef_ogrenciyle(db, kisiler, istemci):
    oid, _ = _ogr(db, kisiler)
    yol = f"/yonetim/ogrenci/{oid}/veli-onayi"
    assert istemci.get(yol, headers=kisiler["yetkili"]).status_code == 200
    assert istemci.get(yol, headers=kisiler["yetkili"]).status_code == 200      # 10 dk içinde aynı sayfa: tek satır
    k = _kayitlar(db, hedef_ogrenci_id=oid, kullanici_tipi="okul_yetkilisi")
    assert len(k) == 1
    k = k[0]
    assert k["olay"] == "goruntuleme" and k["bolum"] == "Onay formları" and k["yol"] == "/yonetim/ogrenci/{ogrenci_id}/veli-onayi"
    assert k["hedef_ad"] == "Test Öğrenci" and k["hedef_okul_id"] == kisiler["okul_a"] and k["kullanici_ad"] == "Test okul_yetkilisi"
    assert k["durum_kodu"] == 200 and k["ip"]

    # Dosya indirme her zaman yazılır
    assert istemci.get(f"/yonetim/okul/{kisiler['okul_a']}/onaylar/form", headers=kisiler["yetkili"]).status_code == 200
    k = _kayitlar(db, yol="/yonetim/okul/{okul_id}/onaylar/form")
    assert k and k[-1]["olay"] == "indirme" and k[-1]["hedef_okul_id"] == kisiler["okul_a"]

    # Yetkisiz deneme de görünür (başka okulun verisi → 403)
    assert istemci.get(f"/yonetim/okul/{kisiler['okul_b']}/onaylar", headers=kisiler["yetkili"]).status_code == 403
    k = _kayitlar(db, hedef_okul_id=kisiler["okul_b"])
    assert k and k[-1]["durum_kodu"] == 403


@db_gerekli
def test_ogrenci_istegi_ve_gurultu(db, kisiler, istemci):
    oid, _ = _ogr(db, kisiler)
    istemci.get("/ogrenci/veli-onayi", headers=kisiler["ogrenci"])
    istemci.get("/ogrenci/bildirimler", headers=kisiler["ogrenci"])       # arka plan yoklaması: yazılmaz
    k = _kayitlar(db, kullanici_id=oid)
    assert [x["yol"] for x in k] == ["/ogrenci/veli-onayi"]
    assert k[0]["hedef_ogrenci_id"] == oid and k[0]["kullanici_tipi"] == "ogrenci"


@db_gerekli
def test_yalnizca_super_admin_gorur(db, kisiler, istemci):
    oid, _ = _ogr(db, kisiler)
    istemci.get(f"/yonetim/ogrenci/{oid}/veli-onayi", headers=kisiler["yetkili"])
    assert istemci.get("/admin/erisim-kayitlari", headers=kisiler["yetkili"]).status_code in (401, 403)
    assert istemci.get("/admin/erisim-kayitlari", headers=kisiler["ogrenci"]).status_code in (401, 403)
    r = istemci.get(f"/admin/erisim-kayitlari?hedef_ogrenci_id={oid}&kullanici_tipi=okul_yetkilisi", headers=kisiler["super"])
    assert r.status_code == 200, r.text
    v = r.json()
    assert v["toplam"] >= 1 and all(x["hedef_ogrenci_id"] == str(oid) for x in v["kayitlar"])
    assert v["kayitlar"][0]["olay_etiket"] == "Görüntüleme" and v["kayitlar"][0]["okul_ad"]
    # Yetkilinin listeyi açma denemesi de kayıtlı
    r = istemci.get("/admin/erisim-kayitlari?yalniz_hata=true&kullanici_tipi=okul_yetkilisi", headers=kisiler["super"])
    assert any(x["yol"] == "/admin/erisim-kayitlari" for x in r.json()["kayitlar"])
    r = istemci.get("/admin/erisim-kayitlari/csv", headers=kisiler["super"])
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv") and "Hedef öğrenci" in r.text
    assert istemci.get("/admin/erisim-kayitlari?bas=2026-11-05&bit=2026-11-01", headers=kisiler["super"]).status_code == 400
