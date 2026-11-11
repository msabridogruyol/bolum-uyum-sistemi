"""[2026-10-11] Çevrim içi öğrenci listesi: yalnızca kendi okulu, kısa ad, gizlilik tercihi, yönetim kapsamı."""
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


@pytest.fixture
def ortam(db):
    from app.core.security import erisim_tokeni_uret
    ek = uuid.uuid4().hex[:6]
    a = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"CV A {ek}"}).scalar()
    b = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"CV B {ek}"}).scalar()
    k = {}
    for ad, okul, sinif, sube in (("Ali Veli Yılmaz", a, "10. Sınıf", "A"), ("Zeynep Kaya", a, "10. Sınıf", "A"),
                                  ("Mert Demir", a, "11. Sınıf", "B"), ("Ece Can", b, "10. Sınıf", "A"), ("Okulsuz Kişi", None, None, None)):
        i = uuid.uuid4()
        db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sinif, sube, olusturulma_zamani, guncelleme_zamani)
                           VALUES (:i, :ad, :e, 'x', :o, :s, :sb, now(), now())"""),
                   {"i": i, "ad": ad, "e": f"{i.hex[:8]}@cv-test.com", "o": okul, "s": sinif, "sb": sube})
        k[ad.split()[0]] = {"Authorization": f"Bearer {erisim_tokeni_uret(i, 'ogrenci')}"}
    y = uuid.uuid4()
    db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, olusturulma_zamani)
                       VALUES (:i, 'CV Yetkili', :e, 'x', 'okul_yetkilisi', :o, TRUE, now())"""), {"i": y, "e": f"{y.hex[:8]}@cv-test.com", "o": a})
    k["yetkili"] = {"Authorization": f"Bearer {erisim_tokeni_uret(y, 'okul_yetkilisi')}"}
    # [2026-11-11] öğrencide liste okul ayarıyla açılır (varsayılan kapalı); bu testler açık okulda çalışır
    db.execute(text("UPDATE okullar SET ogrenci_cevrimici_acik = TRUE WHERE id IN (:a, :b)"), {"a": a, "b": b})
    db.commit()
    return {"a": a, "b": b, **k}


@db_gerekli
def test_ogrenci_yalnizca_kendi_okulunu_ve_kisa_adi_gorur(istemci, ortam):
    for kim in ("Zeynep", "Mert", "Ece"):
        assert istemci.post("/ogrenci/cevrimici", headers=ortam[kim]).status_code == 200
    r = istemci.post("/ogrenci/cevrimici", headers=ortam["Ali"]).json()
    assert r["toplam"] == 2
    assert r["sinifim"] == [{"ad": "Zeynep K.", "sinif": "10-A"}]
    assert r["digerleri"] == [{"ad": "Mert D.", "sinif": "11-B"}]
    adlar = str(r)
    assert "Ece" not in adlar and "Kaya" not in adlar and "Ali" not in adlar   # başka okul yok, tam soyad yok, kendisi yok


@db_gerekli
def test_gizli_ogrenci_listede_gorunmez_yonetim_sayar(istemci, ortam):
    istemci.post("/ogrenci/cevrimici", headers=ortam["Zeynep"])
    assert istemci.put("/ogrenci/cevrimici/gizlilik", headers=ortam["Zeynep"], json={"gizli": True}).json()["gizli"] is True
    r = istemci.post("/ogrenci/cevrimici", headers=ortam["Ali"]).json()
    assert r["toplam"] == 0 and r["sinifim"] == []
    y = istemci.get("/yonetim/cevrimici", headers=ortam["yetkili"]).json()
    assert y["gizli_sayisi"] == 1 and all(o["ad"] != "Zeynep Kaya" for o in y["ogrenciler"])
    assert any(o["ad"] == "Ali Veli Yılmaz" for o in y["ogrenciler"])   # yönetim tam adı görür


@db_gerekli
def test_yetkili_baska_okulu_goremez_okulsuz_ogrenci_liste_almaz(istemci, ortam):
    assert istemci.get(f"/yonetim/cevrimici?okul_id={ortam['b']}", headers=ortam["yetkili"]).status_code == 403
    istemci.post("/ogrenci/cevrimici", headers=ortam["Ali"])
    r = istemci.post("/ogrenci/cevrimici", headers=ortam["Okulsuz"]).json()
    assert r["toplam"] == 0 and r["sinifim"] == [] and r["digerleri"] == []


@db_gerekli
def test_okul_ayari_kapaliyken_ogrenci_liste_gormez_yetkili_gorur(db, istemci, ortam):
    """[2026-11-11] Varsayılan kapalı: öğrenci listeyi görmez, sinyali yine kaydedilir; yetkili görür ve ayarı açabilir."""
    assert istemci.put(f"/yonetim/okul/{ortam['a']}/ogrenci-cevrimici", headers=ortam["yetkili"], json={"acik": False}).json() == {"ogrenci_cevrimici_acik": False}
    istemci.post("/ogrenci/cevrimici", headers=ortam["Zeynep"])
    r = istemci.post("/ogrenci/cevrimici", headers=ortam["Ali"]).json()
    assert r["goster"] is False and r["toplam"] == 0 and r["sinifim"] == [] and r["digerleri"] == []
    y = istemci.get("/yonetim/cevrimici", headers=ortam["yetkili"]).json()
    assert any(o["ad"] == "Zeynep Kaya" for o in y["ogrenciler"])
    assert istemci.get(f"/yonetim/okul/{ortam['a']}/bilgi", headers=ortam["yetkili"]).json()["ogrenci_cevrimici_acik"] is False
    assert istemci.put(f"/yonetim/okul/{ortam['b']}/ogrenci-cevrimici", headers=ortam["yetkili"], json={"acik": True}).status_code == 403
    istemci.put(f"/yonetim/okul/{ortam['a']}/ogrenci-cevrimici", headers=ortam["yetkili"], json={"acik": True})
    assert istemci.post("/ogrenci/cevrimici", headers=ortam["Ali"]).json()["goster"] is True


@db_gerekli
def test_yeni_okulda_varsayilan_kapali(db):
    o = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES ('CV Varsayılan', TRUE) RETURNING ogrenci_cevrimici_acik")).scalar()
    db.rollback()
    assert o is False
