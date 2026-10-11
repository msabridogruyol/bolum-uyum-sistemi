"""[2026-10-11] Pilot hazırlığı: şifre değişince oturum düşmesi, hesap başına hatalı şifre kilidi, yetkili geçici şifre gizliliği,
öğrenci sınıf kilidi, görüşme notunun okula ait olması, sözlük hata bildirimi."""
import time
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


@pytest.fixture
def ortam(db):
    from app.core.security import erisim_tokeni_uret, sifre_hashle
    ek = uuid.uuid4().hex[:6]
    a = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"PH A {ek}"}).scalar()
    b = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"PH B {ek}"}).scalar()
    oid = uuid.uuid4()
    email = f"{oid.hex[:8]}@ph-test.com"
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sinif, sube, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Pilot Öğrenci', :e, :h, :o, '10. Sınıf', 'A', now(), now())"""),
               {"i": oid, "e": email, "h": sifre_hashle("Eski12345!"), "o": a})
    y1, y2 = uuid.uuid4(), uuid.uuid4()
    from app.core.gizli_metin import sifrele
    for y, ad, gecici in ((y1, "PH Yetkili 1", None), (y2, "PH Yetkili 2", "Gizli-1234")):
        db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, sifre_degistirmeli,
                           gecici_sifre_sifreli, olusturulma_zamani)
                           VALUES (:i, :ad, :e, 'x', 'okul_yetkilisi', :o, TRUE, :sd, :g, now())"""),
                   {"i": y, "ad": ad, "e": f"{y.hex[:8]}@ph-test.com", "o": a, "sd": gecici is not None, "g": sifrele(gecici) if gecici else None})
    db.commit()
    return {"a": a, "b": b, "oid": oid, "email": email, "y1": y1,
            "ogr": {"Authorization": f"Bearer {erisim_tokeni_uret(oid, 'ogrenci')}"},
            "yet": {"Authorization": f"Bearer {erisim_tokeni_uret(y1, 'okul_yetkilisi')}"}}


@db_gerekli
def test_sifre_degisince_eski_oturum_duser_yeni_anahtar_calisir(istemci, ortam):
    assert istemci.get("/ogrenci/profil", headers=ortam["ogr"]).status_code == 200
    time.sleep(1.1)   # iat saniye çözünürlüklü
    r = istemci.post("/ogrenci/profil/sifre-degistir", headers=ortam["ogr"], json={"eski_sifre": "Eski12345!", "yeni_sifre": "Yeni12345!"})
    assert r.status_code == 200 and r.json()["erisim_tokeni"]
    assert istemci.get("/ogrenci/profil", headers=ortam["ogr"]).status_code == 401              # eski anahtar artık geçersiz
    yeni = {"Authorization": f"Bearer {r.json()['erisim_tokeni']}"}
    assert istemci.get("/ogrenci/profil", headers=yeni).status_code == 200                       # bu cihaz devam eder


@db_gerekli
def test_hesap_basina_hatali_sifre_kilidi(istemci, ortam):
    from app.core.hiz_siniri import HESAP_DENEME
    HESAP_DENEME.temizle(ortam["email"])
    for _ in range(8):
        assert istemci.post("/auth/giris", json={"email": ortam["email"], "sifre": "yanlis-sifre"}).status_code == 401
    r = istemci.post("/auth/giris", json={"email": ortam["email"], "sifre": "Eski12345!"})
    assert r.status_code == 429 and "hatalı şifre" in r.json()["detail"]                          # doğru şifre bile beklemeli
    HESAP_DENEME.temizle(ortam["email"])
    assert istemci.post("/auth/giris", json={"email": ortam["email"], "sifre": "Eski12345!"}).status_code == 200


@db_gerekli
def test_yetkili_meslektasinin_gecici_sifresini_goremez(istemci, ortam):
    liste = istemci.get(f"/yonetim/okul/{ortam['a']}/yetkililer", headers=ortam["yet"]).json()
    y2 = next(y for y in liste if y["ad_soyad"] == "PH Yetkili 2")
    assert y2["gecici_sifre"] == "(gizli)" and "Gizli-1234" not in str(liste)


@db_gerekli
def test_okula_bagli_ogrenci_sinifini_degistiremez(istemci, ortam):
    r = istemci.put("/ogrenci/profil", headers=ortam["ogr"], json={"sinif": "12. Sınıf"})
    assert r.status_code == 200 and r.json()["sinif"] == "10. Sınıf"


@db_gerekli
def test_gorusme_notu_yazildigi_okula_aittir(istemci, ortam, db):
    db.execute(text("""INSERT INTO rehberlik_gorusmeleri (okul_id, ogrenci_id, zaman, durum, tur, konu, baslik, notlar, takip_tamam, ogrenciye_goster, olusturan)
                       VALUES (:b, :o, now(), 'yapildi', 'bireysel', 'kariyer', 'Eski okul notu', 'gizli not', FALSE, FALSE, 'Eski okul')"""),
               {"b": ortam["b"], "o": ortam["oid"]})
    db.commit()
    r = istemci.get(f"/yonetim/ogrenci/{ortam['oid']}/gorusmeler", headers=ortam["yet"])
    assert r.status_code == 200 and all(g["baslik"] != "Eski okul notu" for g in r.json()["gorusmeler"])


@db_gerekli
def test_sozluk_hata_bildirimi_gunde_bir(istemci, ortam):
    v = {"terim": "Cevher", "k": "g1", "aciklama": "örnek eksik"}
    assert istemci.post("/ogrenci/sozluk/bildir", headers=ortam["ogr"], json=v).json()["kaydedildi"] is True
    assert istemci.post("/ogrenci/sozluk/bildir", headers=ortam["ogr"], json=v).json()["kaydedildi"] is False


def test_bcrypt_tur_ve_yeniden_karma():
    from app.core.security import BCRYPT_TUR, sifre_hashle, yeniden_karma_gerekli_mi
    assert BCRYPT_TUR >= 10
    assert not yeniden_karma_gerekli_mi(sifre_hashle("x12345678"))
    assert yeniden_karma_gerekli_mi("$2b$12$" + "a" * 53)
