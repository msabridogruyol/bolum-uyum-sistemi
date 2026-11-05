"""
[2026-11-05] Veli onay formu: 18 yaş altı öğrencide imzalı form okula ulaşana kadar kişisel veri işleyen işlemler kilitli;
okul yetkilisi / süper admin işaretler, geri alır ve tamamlanma durumunu görür.
"""
from datetime import timedelta

from sqlalchemy import text

from app.core import veli_onayi as vo
from tests.conftest import db_gerekli

pytestmark = db_gerekli


def _ogr(db, kisiler):
    return db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": kisiler["okul_a"]}).scalar()


def _veliyi_sifirla(db, oid):
    """conftest öğrenciyi reşit işaretler; bu testler veli onayı olmayan öğrenciyle başlar."""
    db.execute(text("DELETE FROM veli_onaylari WHERE ogrenci_id = :o"), {"o": oid})
    db.commit()


def test_onaysiz_ogrenci_kilitli_isaretlenince_acilir(db, kisiler, istemci):
    oid = _ogr(db, kisiler)
    _veliyi_sifirla(db, oid)
    r = istemci.post("/ogrenci/katmanlar/K1/basla", headers=kisiler["ogrenci"])
    assert r.status_code == 403 and "Veli onay formun" in r.json()["detail"]
    assert istemci.get("/ogrenci/veli-onayi", headers=kisiler["ogrenci"]).json()["tamam"] is False

    bugun = vo._bugun().isoformat()
    r = istemci.post(f"/yonetim/okul/{kisiler['okul_a']}/onaylar/veli", headers=kisiler["yetkili"],
                     json={"ogrenci_idler": [str(oid)], "islem": "alindi", "form_tarihi": bugun, "veli_ad_soyad": "Veli Kişi"})
    assert r.status_code == 200, r.text
    oz = r.json()["ozet"]
    assert oz["veli_alindi"] == 1 and oz["veli_bekleyen"] == 0 and oz["tamam"] == 1
    r = istemci.post("/ogrenci/katmanlar/K1/basla", headers=kisiler["ogrenci"])
    assert not (r.status_code == 403 and "Veli onay formun" in r.text)

    # Geri alınınca yeniden kilitlenir; geçmiş korunur
    r = istemci.post(f"/yonetim/ogrenci/{oid}/veli-onayi/geri-al", headers=kisiler["yetkili"], json={"aciklama": "Veli rızasını geri aldı"})
    assert r.status_code == 200 and r.json()["durum"]["tamam"] is False and len(r.json()["gecmis"]) == 2
    r = istemci.post("/ogrenci/katmanlar/K1/basla", headers=kisiler["ogrenci"])
    assert r.status_code == 403
    kayit = db.execute(text("SELECT count(*) FROM audit_log WHERE islem LIKE 'veli_onayi%'")).scalar()
    assert kayit == 2


def test_kurallar(db, kisiler, istemci):
    oid = _ogr(db, kisiler)
    _veliyi_sifirla(db, oid)
    url = f"/yonetim/okul/{kisiler['okul_a']}/onaylar/veli"
    ileri = (vo._bugun() + timedelta(days=1)).isoformat()
    assert istemci.post(url, headers=kisiler["yetkili"], json={"ogrenci_idler": [str(oid)], "islem": "alindi", "form_tarihi": ileri}).status_code == 400
    assert istemci.post(url, headers=kisiler["yetkili"], json={"ogrenci_idler": [str(oid)], "islem": "alindi"}).status_code == 400
    # Başka okulun yetkilisi gibi davranılamaz: B okulu adresi A yetkilisine kapalı
    r = istemci.post(f"/yonetim/okul/{kisiler['okul_b']}/onaylar/veli", headers=kisiler["yetkili"],
                     json={"ogrenci_idler": [str(oid)], "islem": "resit"})
    assert r.status_code == 403
    # Süper admin B okulu adresinden A öğrencisini işaretleyemez
    r = istemci.post(f"/yonetim/okul/{kisiler['okul_b']}/onaylar/veli", headers=kisiler["super"],
                     json={"ogrenci_idler": [str(oid)], "islem": "resit"})
    assert r.status_code == 400
    # Okullar özeti yalnızca süper admin
    assert istemci.get("/yonetim/onaylar/okullar", headers=kisiler["yetkili"]).status_code == 403
    r = istemci.get("/yonetim/onaylar/okullar", headers=kisiler["super"])
    assert r.status_code == 200 and any(o["okul_id"] == 0 for o in r.json()["okullar"])


def test_kamera_ve_test_hesabi(db, kisiler):
    oid = _ogr(db, kisiler)
    _veliyi_sifirla(db, oid)
    assert vo.kamera_izinli(db, oid) is False
    from app.models import AdminKullanici
    yon = db.query(AdminKullanici).filter(AdminKullanici.okul_id == kisiler["okul_a"]).first()
    vo.isaretle(db, yon, [oid], "alindi", vo._bugun(), None, kamera=False)
    assert vo.tamam_mi(db, oid) and vo.kamera_izinli(db, oid) is False
    vo.isaretle(db, yon, [oid], "alindi", vo._bugun(), None, kamera=True)
    assert vo.kamera_izinli(db, oid) is True
    vo.geri_al(db, yon, oid, None)
    db.execute(text("UPDATE ogrenciler SET test_hesabi = TRUE WHERE id = :o"), {"o": oid})
    assert vo.tamam_mi(db, oid), "test hesabı muaf"


def test_form_pdf(db, kisiler, istemci):
    r = istemci.get(f"/yonetim/okul/{kisiler['okul_a']}/onaylar/form", headers=kisiler["yetkili"])
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content[:4] == b"%PDF"
    r = istemci.get("/ogrenci/veli-onayi/form", headers=kisiler["ogrenci"])
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    r = istemci.get(f"/yonetim/okul/{kisiler['okul_a']}/onaylar", headers=kisiler["yetkili"])
    ogr = r.json()["ogrenciler"][0]
    assert ogr["kvkk"] is True and ogr["veli"]["islem"] == "resit"
