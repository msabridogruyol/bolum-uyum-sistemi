"""
[2026-11-06] Kullanıcı bildirimi: "test hesabında sorun var, okulu silince verileri silinmiyor".
Okullar › sil test / demo öğrencilerini gerçek öğrenciler gibi "okul harici"ye aktarıyordu (bütün verileriyle).
Şimdi: demo okul tümüyle silinir; gerçek okuldaki test öğrencileri aktarılmaz, silinir; yetkililerin güvenlik kayıtları da silinir.
"""
import uuid

from sqlalchemy import text

from tests.conftest import db_gerekli

pytestmark = db_gerekli


def _say(db, sql, **p):
    return db.execute(text(sql), p).scalar()


def _kvkk_ekle(db, tip, kid):
    db.execute(text("""INSERT INTO kvkk_onaylari (kullanici_tipi, kullanici_id, onay_kodu, verildi, metin_surumu, zaman)
                       VALUES (:t, :i, 'aydinlatma', TRUE, 'test', now())"""), {"t": tip, "i": kid})


def test_demo_okul_okullar_ekranindan_tumuyle_silinir(db, kisiler, istemci):
    r = istemci.post("/yonetim/test-hesaplari/demo-okul", headers=kisiler["super"], json={"okul_adi": "Silme Demo", "ogrenci_sayisi": 2})
    assert r.status_code == 201, r.text
    oid = r.json()["okul_id"]
    ogr = [x[0] for x in db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": oid})]
    yet = [x[0] for x in db.execute(text("SELECT id FROM admin_kullanicilar WHERE okul_id = :o"), {"o": oid})]
    assert len(ogr) == 2 and len(yet) == 1
    db.execute(text("INSERT INTO ogrenci_hesap_olaylari (ogrenci_id, olay, zaman) VALUES (:i, 'giris', now())"), {"i": ogr[0]})
    db.commit()

    r = istemci.delete(f"/admin/okullar/{oid}", headers=kisiler["super"])       # aktarım yeri sorulmaz
    assert r.status_code == 204, r.text
    assert _say(db, "SELECT count(*) FROM okullar WHERE id = :o", o=oid) == 0
    assert _say(db, "SELECT count(*) FROM ogrenciler WHERE id = ANY(:i)", i=ogr) == 0        # okul harici'ye DÜŞMEZ
    assert _say(db, "SELECT count(*) FROM ogrenci_cevaplar WHERE ogrenci_id = ANY(:i)", i=ogr) == 0
    assert _say(db, "SELECT count(*) FROM ogrenci_hesap_olaylari WHERE ogrenci_id = ANY(:i)", i=ogr) == 0
    assert _say(db, "SELECT count(*) FROM admin_kullanicilar WHERE id = ANY(:i)", i=yet) == 0
    assert _say(db, "SELECT count(*) FROM kvkk_onaylari WHERE kullanici_id = ANY(:i)", i=ogr + yet) == 0


def test_gercek_okulda_test_ogrencisi_aktarilmaz_silinir(db, kisiler, istemci):
    okul = kisiler["okul_a"]
    gercek = db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": okul}).scalar()
    test_ogr = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, test_hesabi, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Test Hesabı', :e, 'x', :o, TRUE, now(), now())"""),
               {"i": test_ogr, "e": f"t.{test_ogr.hex[:8]}@test.invalid", "o": okul})
    yetkili = db.execute(text("SELECT id FROM admin_kullanicilar WHERE okul_id = :o"), {"o": okul}).scalar()
    _kvkk_ekle(db, "yonetim", yetkili)
    db.commit()

    liste = {o["id"]: o for o in istemci.get("/admin/okullar", headers=kisiler["super"]).json()}
    assert liste[okul]["ogrenci_sayisi"] == 2 and liste[okul]["test_ogrenci_sayisi"] == 1 and liste[okul]["demo"] is False
    r = istemci.delete(f"/admin/okullar/{okul}", headers=kisiler["super"])
    assert r.status_code == 409 and "1 öğrenci" in r.json()["detail"]        # yalnızca gerçek öğrenci sayılır

    r = istemci.delete(f"/admin/okullar/{okul}?hedef_id=0", headers=kisiler["super"])
    assert r.status_code == 204, r.text
    assert db.execute(text("SELECT okul_id FROM ogrenciler WHERE id = :i"), {"i": gercek}).one()[0] is None   # gerçek öğrenci aktarıldı
    assert _say(db, "SELECT count(*) FROM ogrenciler WHERE id = :i", i=test_ogr) == 0                        # test öğrencisi silindi
    assert _say(db, "SELECT count(*) FROM admin_kullanicilar WHERE id = :i", i=yetkili) == 0
    assert _say(db, "SELECT count(*) FROM kvkk_onaylari WHERE kullanici_tipi = 'yonetim' AND kullanici_id = :i", i=yetkili) == 0
    assert "1 test öğrencisi" in db.execute(text("SELECT gerekce FROM audit_log WHERE islem = 'okul_sil' ORDER BY id DESC LIMIT 1")).scalar()


def test_test_hesaplari_demo_silme_yetkili_kayitlarini_birakmaz(db, kisiler, istemci):
    r = istemci.post("/yonetim/test-hesaplari/demo-okul", headers=kisiler["super"], json={"okul_adi": "Silme Demo 2", "ogrenci_sayisi": 1})
    oid = r.json()["okul_id"]
    yet = db.execute(text("SELECT id FROM admin_kullanicilar WHERE okul_id = :o"), {"o": oid}).scalar()
    assert _say(db, "SELECT count(*) FROM kvkk_onaylari WHERE kullanici_id = :i", i=yet) > 0
    assert istemci.delete(f"/yonetim/test-hesaplari/demo-okul/{oid}", headers=kisiler["super"]).status_code == 204
    assert _say(db, "SELECT count(*) FROM kvkk_onaylari WHERE kullanici_id = :i", i=yet) == 0
