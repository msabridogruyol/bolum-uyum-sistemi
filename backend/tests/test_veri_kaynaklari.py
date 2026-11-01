"""[2026-11-01] Veri Kaynakları (süper admin): varlık, dönem, son güncelleme, kontrol kaydı, durum kuralları."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from app.core import veri_kaynaklari as vk
from tests.conftest import db_gerekli


def _goc(db):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for k in _komutlar(_sql_oku("0085_veri_kaynagi_kontrol")):
        db.execute(text(k))
    db.commit()


def test_durum_kurallari():
    simdi = datetime(2026, 11, 1, tzinfo=timezone.utc)
    eski = (simdi - timedelta(days=400)).isoformat()
    yeni = (simdi - timedelta(days=10)).isoformat()
    assert vk.durum_hesapla(None, None, 365, simdi)[0] == "yok"
    assert vk.durum_hesapla({"kayit": 0}, None, 365, simdi)[0] == "yok"
    assert vk.durum_hesapla({"kayit": 5, "son_guncelleme": yeni}, None, 365, simdi)[0] == "guncel"
    assert vk.durum_hesapla({"kayit": 5, "son_guncelleme": eski}, None, 365, simdi)[0] == "kontrol_zamani"
    # Elle "kontrol ettim, güncel" kaydı eski veriyi yeniden güncel sayar
    assert vk.durum_hesapla({"kayit": 5, "son_guncelleme": eski}, {"sonuc": "guncel", "zaman": yeni}, 365, simdi)[0] == "guncel"
    # Yeni dönem beklenen veri, kontrol kaydı olsa da "bekleniyor" kalır
    assert vk.durum_hesapla({"kayit": 5, "son_guncelleme": yeni, "bekleniyor": "2026 verisi"},
                            {"sonuc": "guncel", "zaman": yeni}, 365, simdi)[0] == "bekleniyor"
    # "Sorun var" kaydı, sonrasında veri güncellenene kadar görünür
    assert vk.durum_hesapla({"kayit": 5, "son_guncelleme": eski}, {"sonuc": "sorun", "zaman": yeni, "notlar": "x"}, 365, simdi)[0] == "sorun"
    assert vk.durum_hesapla({"kayit": 5, "son_guncelleme": simdi.isoformat()}, {"sonuc": "sorun", "zaman": yeni}, 365, simdi)[0] == "guncel"


@db_gerekli
def test_liste_ve_kontrol_kaydi(istemci, kisiler, db):
    _goc(db)
    db.execute(text("DELETE FROM asgari_ucret"))
    db.execute(text("INSERT INTO asgari_ucret (donem, brut, net, kaynak, yururluk_tarihi) VALUES ('2020', 1, 1, 'deneme', '2020-01-01')"))
    db.commit()
    r = istemci.get("/admin/veri-kaynaklari", headers=kisiler["super"])
    assert r.status_code == 200
    v = r.json()
    kod = {k["kod"]: k for k in v["kaynaklar"]}
    assert set(kod) == {k[0] for k in vk.KAYNAKLAR} and sum(v["ozet"].values()) == len(vk.KAYNAKLAR)
    a = kod["asgari_ucret"]
    assert a["kayit"] == 1 and a["durum"] == "bekleniyor" and str(date.today().year) in a["aciklama"]
    assert kod["tuik_istihdam"]["durum"] in ("yok", "bekleniyor", "guncel", "kontrol_zamani")
    # Kontrol kaydı + audit log
    assert istemci.post("/admin/veri-kaynaklari/kaynakca/kontrol", headers=kisiler["super"],
                        json={"sonuc": "sorun"}).status_code == 422, "sorun notsuz kaydedilmez"
    assert istemci.post("/admin/veri-kaynaklari/yok-boyle/kontrol", headers=kisiler["super"], json={"sonuc": "guncel"}).status_code == 404
    r = istemci.post("/admin/veri-kaynaklari/kaynakca/kontrol", headers=kisiler["super"], json={"sonuc": "guncel", "notlar": "bağlantılar açılıyor"})
    assert r.status_code == 200
    k = next(x for x in istemci.get("/admin/veri-kaynaklari", headers=kisiler["super"]).json()["kaynaklar"] if x["kod"] == "kaynakca")
    assert k["durum"] == "guncel" and k["son_kontrol"]["notlar"] == "bağlantılar açılıyor"
    assert istemci.get("/admin/veri-kaynaklari/kaynakca/gecmis", headers=kisiler["super"]).json()["kontroller"]
    assert db.execute(text("SELECT COUNT(*) FROM audit_log WHERE islem = 'veri_kaynagi_kontrol'")).scalar() >= 1
    # Yalnızca süper admin
    assert istemci.get("/admin/veri-kaynaklari", headers=kisiler["yetkili"]).status_code in (401, 403)


@db_gerekli
def test_hatirlatma_ayda_bir(db):
    _goc(db)
    bugun = date(2031, 3, 5)
    db.execute(text("DELETE FROM tek_seferlik_gocler WHERE ad = 'veri_kaynagi_hatirlatma_2031_03'"))
    db.commit()
    ilk = vk.hatirlat(db, bugun)
    assert ilk > 0 and vk.hatirlat(db, bugun) == 0
