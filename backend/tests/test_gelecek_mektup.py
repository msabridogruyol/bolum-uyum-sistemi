"""[2026-10-13] Gelecekteki sana mektup: tarih seçenekleri, şifreli saklama, mühür (teslimden önce metin dönmez), teslim, gizlilik."""
import uuid
from datetime import date, timedelta

from sqlalchemy import text

from app.core import gelecek_mektup as gm
from tests.conftest import db_gerekli


def test_tarih_secenekleri_sinifa_gore():
    s = {x["kod"]: x["tarih"] for x in gm.tarih_secenekleri("10. Sınıf", date(2026, 10, 13))}
    assert s["mezuniyet"] == "2029-06-30" and s["universite"] == "2029-10-01" and s["1yil"] == "2027-10-13"
    assert "mezuniyet" not in {x["kod"] for x in gm.tarih_secenekleri("Aday", date(2026, 10, 13))}
    # 12. sınıf, haziran ortası: mezuniyet 30 günden yakın → seçenek olarak çıkmaz
    assert "mezuniyet" not in {x["kod"] for x in gm.tarih_secenekleri("12. Sınıf", date(2027, 6, 15))}
    assert gm.tarih_gecerli_mi(date(2026, 12, 1), date(2026, 10, 13)) and not gm.tarih_gecerli_mi(date(2026, 10, 20), date(2026, 10, 13))


def test_sifreleme_ve_maskeleme():
    s = gm.sifrele("Merhaba gelecekteki ben")
    assert s != "Merhaba gelecekteki ben" and gm.coz(s) == "Merhaba gelecekteki ben" and gm.coz("bozuk") is None
    assert gm.maskele("ayse.yilmaz@gmail.com").startswith("ay") and "yilmaz" not in gm.maskele("ayse.yilmaz@gmail.com")


def _ogrenci(db, test=False):
    from app.core.security import erisim_tokeni_uret
    okul = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"GM {uuid.uuid4().hex[:6]}"}).scalar()
    oid = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sinif, test_hesabi, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'GM Öğrenci', :e, 'x', :o, '11. Sınıf', :t, now(), now())"""),
               {"i": oid, "e": f"{oid.hex[:8]}@gm-test.invalid", "o": okul, "t": test})
    db.commit()
    return oid, {"Authorization": f"Bearer {erisim_tokeni_uret(oid, 'ogrenci')}"}


METIN = "Sevgili gelecekteki ben, bugün hangi bölümü seçeceğimi düşünüyorum ve biraz kaygılıyım."


@db_gerekli
def test_yaz_muhurle_tarih_degistir_sil(istemci, db):
    oid, b = _ogrenci(db)
    v = istemci.get("/ogrenci/gelecek-mektup", headers=b).json()
    assert v["mektuplar"] == [] and any(s["kod"] == "mezuniyet" for s in v["secenekler"])
    t = (gm.turkiye_bugun() + timedelta(days=60)).isoformat()
    assert istemci.post("/ogrenci/gelecek-mektup", headers=b, json={"metin": "kısa", "teslim_tarihi": t}).status_code == 400
    yakin = (gm.turkiye_bugun() + timedelta(days=5)).isoformat()
    assert istemci.post("/ogrenci/gelecek-mektup", headers=b, json={"metin": METIN, "teslim_tarihi": yakin}).status_code == 400
    assert istemci.post("/ogrenci/gelecek-mektup", headers=b, json={"metin": METIN, "teslim_tarihi": t, "kisisel_eposta": "bozuk"}).status_code == 400
    r = istemci.post("/ogrenci/gelecek-mektup", headers=b, json={"metin": METIN, "teslim_tarihi": t, "kisisel_eposta": "kisisel@ornek.com"})
    assert r.status_code == 200, r.text
    m = r.json()["mektuplar"][0]
    assert m["metin"] is None and m["acik"] is False and m["kisisel_eposta"].endswith("@ornek.com")   # mühürlü: metin dönmez
    ham = db.execute(text("SELECT metin_sifreli, kisisel_eposta_sifreli FROM gelecek_mektuplari WHERE ogrenci_id = :o"), {"o": oid}).first()
    assert "gelecekteki" not in ham.metin_sifreli and "ornek.com" not in ham.kisisel_eposta_sifreli   # şifreli
    t2 = (gm.turkiye_bugun() + timedelta(days=400)).isoformat()
    assert istemci.put(f"/ogrenci/gelecek-mektup/{m['id']}", headers=b, json={"teslim_tarihi": t2}).json()["mektuplar"][0]["teslim_tarihi"] == t2
    for _ in range(2):
        istemci.post("/ogrenci/gelecek-mektup", headers=b, json={"metin": METIN, "teslim_tarihi": t})
    assert istemci.post("/ogrenci/gelecek-mektup", headers=b, json={"metin": METIN, "teslim_tarihi": t}).status_code == 400   # en çok 3
    # başka öğrenci silemez
    _o2, b2 = _ogrenci(db)
    assert istemci.delete(f"/ogrenci/gelecek-mektup/{m['id']}", headers=b2).status_code == 404
    assert len(istemci.delete(f"/ogrenci/gelecek-mektup/{m['id']}", headers=b).json()["mektuplar"]) == 2


@db_gerekli
def test_teslim_gunu_gonderilir_ve_hesapta_acilir(istemci, db, monkeypatch):
    from app.core import eposta_servisi as ep
    gidenler = []
    monkeypatch.setattr(ep, "eposta_yapilandirildi_mi", lambda: True)
    monkeypatch.setattr(ep, "eposta_gonder", lambda alici, konu, html, metin, ekler=None: gidenler.append((alici, konu, metin)) or True)
    db.execute(text("DELETE FROM gelecek_mektuplari"))   # test işlemi içinde; sonunda geri alınır (yerel kayıtlar sayımı bozmasın)
    oid, b = _ogrenci(db)
    t = (gm.turkiye_bugun() + timedelta(days=40)).isoformat()
    istemci.post("/ogrenci/gelecek-mektup", headers=b, json={"metin": METIN, "teslim_tarihi": t, "kisisel_eposta": "kisisel@ornek.com"})
    test_oid, test_b = _ogrenci(db, test=True)
    istemci.post("/ogrenci/gelecek-mektup", headers=test_b, json={"metin": METIN, "teslim_tarihi": t})
    assert gm.teslim_et(db, gm.turkiye_bugun())["gonderildi"] == 0    # henüz günü gelmedi
    s = gm.teslim_et(db, gm.turkiye_bugun() + timedelta(days=40))
    assert s["gonderildi"] >= 1 and s["eposta_yok"] >= 1               # test hesabına gitmez
    benim = [g for g in gidenler if g[0] in ("kisisel@ornek.com",) or g[0].startswith(oid.hex[:8])]
    assert len(benim) == 2 and METIN in benim[0][2]                   # kişisel + okul e-postası
    db.execute(text("UPDATE gelecek_mektuplari SET teslim_tarihi = :t WHERE ogrenci_id = :o"), {"t": gm.turkiye_bugun(), "o": oid})
    db.commit()
    m = istemci.get("/ogrenci/gelecek-mektup", headers=b).json()["mektuplar"][0]
    assert m["acik"] and m["metin"] == METIN and m["durum"] == "gonderildi"
    assert gm.teslim_et(db, gm.turkiye_bugun() + timedelta(days=40))["gonderildi"] == 0   # bir kez gider


@db_gerekli
def test_yonetim_mektuba_erisemez(istemci, kisiler):
    # Yönetim tokeni öğrenci ucunu kullanamaz; okul/yönetim ucu yoktur
    assert istemci.get("/ogrenci/gelecek-mektup", headers=kisiler["yetkili"]).status_code in (401, 403)
    from app.main import app
    assert not [r.path for r in app.routes if "mektup" in getattr(r, "path", "") and not r.path.startswith("/ogrenci/")]
