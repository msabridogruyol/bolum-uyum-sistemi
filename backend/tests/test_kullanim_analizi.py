"""
[2026-11-11] Kullanım analizi: hangi menüde ne kadar süre (öğrenci, okul yetkilisi, süper admin ayrı; okul okul ve toplam).
"""
import uuid

from sqlalchemy import text

from tests.conftest import db_gerekli


def _gonder(istemci, yol, basliklar, oturum, kayitlar, cihaz="masaustu"):
    return istemci.post(yol, headers=basliklar, json={"oturum_id": str(oturum), "cihaz": cihaz, "kayitlar": kayitlar})


def _ogrenci_id(db, okul):
    return db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": okul}).scalar()


@db_gerekli
def test_yazim_toplama_ve_genel_analiz(db, kisiler, istemci):
    ot = uuid.uuid4()
    r = _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], ot, [
        {"menu_kod": "bolumler", "menu_ad": "Bölümler", "alt_kod": "tum", "alt_ad": "Tüm bölümler", "aktif_sn": 50, "acik_sn": 60, "ziyaret": 1},
        {"menu_kod": "koclugu", "menu_ad": "Koçluğum", "aktif_sn": 30, "acik_sn": 20, "ziyaret": 1},
    ])
    assert r.status_code == 200, r.text
    # aynı oturum, aynı menü, aynı saat dilimi: tek satırda toplanır
    assert _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], ot, [
        {"menu_kod": "bolumler", "menu_ad": "Bölümler", "alt_kod": "tum", "aktif_sn": 40, "acik_sn": 40}]).status_code == 200
    satir = db.execute(text("SELECT aktif_sn, acik_sn, ziyaret FROM kullanim_sureleri WHERE oturum_id = :o AND menu_kod = 'bolumler'"),
                       {"o": ot}).all()
    assert satir == [(90, 100, 1)]
    # açık süre aktif süreden az gönderilse de en az aktif kadar yazılır
    assert db.execute(text("SELECT acik_sn FROM kullanim_sureleri WHERE oturum_id = :o AND menu_kod = 'koclugu'"), {"o": ot}).scalar() == 30

    assert _gonder(istemci, "/yonetim/kullanim", kisiler["yetkili"], uuid.uuid4(), [
        {"menu_kod": "ogrenciler", "menu_ad": "Öğrenciler", "alt_kod": "ogrenci-detayi", "alt_ad": "Öğrenci detayı", "aktif_sn": 120, "acik_sn": 150, "ziyaret": 2},
    ], cihaz="mobil").status_code == 200

    r = istemci.get(f"/admin/kullanim-analizi?okul_id={kisiler['okul_a']}", headers=kisiler["super"])
    assert r.status_code == 200, r.text
    v = r.json()
    o = v["ozet"]["ogrenci"]
    assert (o["kayitli"], o["aktif_kullanici"], o["toplam_aktif_sn"], o["oturum"], o["katilim_orani"]) == (1, 1, 120, 1, 100.0)
    assert v["ozet"]["okul_yetkilisi"]["toplam_aktif_sn"] == 120 and v["ozet"]["okul_yetkilisi"]["kayitli"] == 1
    assert v["ozet"]["toplam"]["toplam_aktif_sn"] == 240
    # okul süzgecinde süper admin sayılmaz
    assert v["ozet"]["super_admin"]["kayitli"] == 0

    menuler = {m["menu_kod"]: m for m in v["menuler"]["ogrenci"]}
    assert menuler["bolumler"]["aktif_sn"] == 90 and menuler["bolumler"]["pay"] == 75.0 and menuler["bolumler"]["kullanici"] == 1
    assert menuler["bolumler"]["altlar"][0]["alt_ad"] == "Tüm bölümler"
    assert v["menuler"]["okul_yetkilisi"][0]["altlar"][0]["alt_ad"] == "Öğrenci detayı"

    okul = next(s for s in v["okullar"] if s["okul_id"] == kisiler["okul_a"])
    assert okul["ogrenci"]["toplam_sn"] == 120 and okul["ogrenci"]["en_cok_menu"] == "Bölümler"
    assert okul["okul_yetkilisi"]["aktif"] == 1 and okul["okul_yetkilisi"]["en_cok_menu"] == "Öğrenciler"
    assert sum(g["ogrenci_sn"] for g in v["gunluk"]) == 120 and len(v["gunluk"]) == 30
    assert sum(sum(s) for s in v["isi"]["okul_yetkilisi"]) == 120
    assert v["cihaz"]["okul_yetkilisi"][0]["cihaz"] == "mobil"
    assert v["en_cok"]["ogrenci"][0]["ad"] == "Test Öğrenci"


@db_gerekli
def test_yetki_ve_sinirlar(db, kisiler, istemci):
    assert istemci.get("/admin/kullanim-analizi", headers=kisiler["yetkili"]).status_code in (401, 403)
    assert istemci.get("/admin/kullanim-analizi", headers=kisiler["ogrenci"]).status_code in (401, 403)
    assert _gonder(istemci, "/yonetim/kullanim", kisiler["ogrenci"], uuid.uuid4(), []).status_code in (401, 403)
    # tek gönderimde bir saat diliminden uzun süre ya da geçersiz menü kodu kabul edilmez
    assert _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], uuid.uuid4(),
                   [{"menu_kod": "bolumler", "aktif_sn": 4000}]).status_code == 422
    assert _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], uuid.uuid4(),
                   [{"menu_kod": "Bölümler; DROP", "aktif_sn": 10}]).status_code == 422
    # birikimde de saat dilimi 3600 sn'yi aşmaz
    ot = uuid.uuid4()
    for _ in range(3):
        _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], ot, [{"menu_kod": "calisma", "aktif_sn": 1500, "acik_sn": 1500}])
    assert db.execute(text("SELECT aktif_sn FROM kullanim_sureleri WHERE oturum_id = :o"), {"o": ot}).scalar() == 3600
    # başka birinin oturum kimliğiyle gönderilen süre o kişinin satırına eklenmez
    _gonder(istemci, "/yonetim/kullanim", kisiler["yetkili"], ot, [{"menu_kod": "calisma", "aktif_sn": 100}])
    assert db.execute(text("SELECT count(*), sum(aktif_sn) FROM kullanim_sureleri WHERE oturum_id = :o"), {"o": ot}).one() == (1, 3600)


@db_gerekli
def test_kisi_listesi_ayrinti_csv_ve_test_hesabi(db, kisiler, istemci):
    oid = _ogrenci_id(db, kisiler["okul_a"])
    _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], uuid.uuid4(), [
        {"menu_kod": "netlerim", "menu_ad": "Net Takibi", "aktif_sn": 300, "acik_sn": 300, "ziyaret": 1}])
    # B okulunda hiç kullanmamış bir öğrenci
    yeni = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sinif, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Hiç Girmeyen', :e, 'x', :o, '10. Sınıf', now(), now())"""),
               {"i": yeni, "e": f"hic.{yeni.hex[:8]}@filizyol-test.com", "o": kisiler["okul_b"]})
    db.commit()
    r = istemci.get(f"/admin/kullanim-analizi/kullanicilar?tip=ogrenci&okul_id={kisiler['okul_b']}&yalniz=kullanmayan",
                    headers=kisiler["super"]).json()
    assert [k["ad"] for k in r["kullanicilar"]] == ["Hiç Girmeyen"] and r["kullanicilar"][0]["aktif_sn"] == 0
    r = istemci.get(f"/admin/kullanim-analizi/kullanicilar?tip=ogrenci&okul_id={kisiler['okul_a']}", headers=kisiler["super"]).json()
    assert r["kullanicilar"][0]["aktif_sn"] == 300 and r["kullanicilar"][0]["en_cok_menu"] == "Net Takibi"

    d = istemci.get(f"/admin/kullanim-analizi/kullanici?tip=ogrenci&kullanici_id={oid}", headers=kisiler["super"])
    assert d.status_code == 200, d.text
    d = d.json()
    assert d["ozet"]["toplam_aktif_sn"] == 300 and d["menuler"][0]["menu_ad"] == "Net Takibi" and len(d["oturumlar"]) == 1
    assert sum(d["saatler"]) == 300

    for tur in ("menuler", "okullar", "kullanicilar", "gunluk", "siniflar"):
        c = istemci.get(f"/admin/kullanim-analizi/csv?tur={tur}&okul_id={kisiler['okul_a']}", headers=kisiler["super"])
        assert c.status_code == 200 and c.headers["content-type"].startswith("text/csv"), (tur, c.text)
    assert "Net Takibi" in istemci.get(f"/admin/kullanim-analizi/csv?tur=menuler&okul_id={kisiler['okul_a']}", headers=kisiler["super"]).text

    # test hesabı varsayılan olarak sayılmaz
    db.execute(text("UPDATE ogrenciler SET test_hesabi = TRUE WHERE id = :i"), {"i": oid})
    db.commit()
    _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], uuid.uuid4(), [{"menu_kod": "netlerim", "aktif_sn": 10}])
    v = istemci.get(f"/admin/kullanim-analizi?okul_id={kisiler['okul_a']}", headers=kisiler["super"]).json()
    assert v["ozet"]["ogrenci"]["toplam_aktif_sn"] == 300 and v["ozet"]["ogrenci"]["kayitli"] == 0
    v = istemci.get(f"/admin/kullanim-analizi?okul_id={kisiler['okul_a']}&test_dahil=true", headers=kisiler["super"]).json()
    assert v["ozet"]["ogrenci"]["toplam_aktif_sn"] == 310


@db_gerekli
def test_hesap_silinince_sureleri_de_silinir(db, kisiler, istemci):
    oid = _ogrenci_id(db, kisiler["okul_a"])
    _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], uuid.uuid4(), [{"menu_kod": "takvim", "aktif_sn": 20}])
    assert db.execute(text("SELECT count(*) FROM kullanim_sureleri WHERE ogrenci_id = :i"), {"i": oid}).scalar() == 1
    from app.core.hesap_yonetimi import ogrenciyi_sil
    from app.models import Ogrenci
    ogrenciyi_sil(db, db.get(Ogrenci, oid))
    db.commit()
    assert db.execute(text("SELECT count(*) FROM kullanim_sureleri WHERE ogrenci_id = :i"), {"i": oid}).scalar() == 0


@db_gerekli
def test_ucuncu_duzey_icerik(db, kisiler, istemci):
    """Menü › alt sekme › içerik: ör. İş Hayatı › Okulda Öğretilmeyenler › tek tek dersler."""
    oid = _ogrenci_id(db, kisiler["okul_a"])
    ot = uuid.uuid4()
    k = lambda detay, ad, sn, z=1: {"menu_kod": "is-hayati", "menu_ad": "İş Hayatı", "alt_kod": "dersler",
                                   "alt_ad": "Okulda Öğretilmeyenler", "detay_kod": detay, "detay_ad": ad,
                                   "aktif_sn": sn, "acik_sn": sn, "ziyaret": z}
    assert _gonder(istemci, "/ogrenci/kullanim", kisiler["ogrenci"], ot, [
        k("", None, 20), k("bordro", "Brüt, net ve bordro okuma", 300), k("vergi", "Vergi", 100),
        # alt sekme yokken içerik yazılmaz (menü düzeyine düşer)
        {"menu_kod": "takvim", "detay_kod": "x", "detay_ad": "X", "aktif_sn": 10},
    ]).status_code == 200
    assert db.execute(text("SELECT detay_kod FROM kullanim_sureleri WHERE oturum_id = :o AND menu_kod = 'takvim'"), {"o": ot}).scalar() == ""

    v = istemci.get(f"/admin/kullanim-analizi?okul_id={kisiler['okul_a']}", headers=kisiler["super"]).json()
    m = next(x for x in v["menuler"]["ogrenci"] if x["menu_kod"] == "is-hayati")
    assert m["aktif_sn"] == 420 and m["altlar"][0]["alt_ad"] == "Okulda Öğretilmeyenler" and m["altlar"][0]["aktif_sn"] == 420
    detay = m["altlar"][0]["detaylar"]
    assert [(d["detay_ad"], d["aktif_sn"], d["kullanici"]) for d in detay] == [("Brüt, net ve bordro okuma", 300, 1), ("Vergi", 100, 1)]
    assert detay[0]["pay_altta"] == round(100 * 300 / 420, 1)

    d = istemci.get(f"/admin/kullanim-analizi/kullanici?tip=ogrenci&kullanici_id={oid}", headers=kisiler["super"]).json()
    m = next(x for x in d["menuler"] if x["menu_kod"] == "is-hayati")
    assert m["altlar"][0]["detaylar"][0]["detay_kod"] == "bordro"
    c = istemci.get(f"/admin/kullanim-analizi/csv?tur=menuler&okul_id={kisiler['okul_a']}", headers=kisiler["super"]).text
    assert "Brüt, net ve bordro okuma" in c
