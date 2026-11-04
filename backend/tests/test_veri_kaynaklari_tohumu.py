"""[2026-11-04] 0097: yaşam maliyeti referansı (TÜRK-İŞ), kamu maaşları (AA), YKS 2027 tarihleri — kaynaklı ilk veri."""
from datetime import date

from sqlalchemy import text

from tests.conftest import db_gerekli


@db_gerekli
def test_tohumlar_kaynakli_ve_bir_kez(db):
    r = {x.kod: x for x in db.execute(text("SELECT kod, aylik_tutar, donem, kaynak FROM yasam_maliyeti_referans WHERE donem = '2026-10'")).all()}
    assert float(r["bekar_yasam"].aylik_tutar) == 49124.30 and float(r["aclik_siniri"].aylik_tutar) == 38024.03
    assert all("TÜRK-İŞ" in x.kaynak for x in r.values())
    k = db.execute(text("SELECT kadro_adi, net_min, net_max, kaynak FROM kamu_maaslari WHERE donem = '2026-2'")).all()
    assert len(k) == 10 and all(x.net_min == x.net_max and "aa.com.tr" in x.kaynak for x in k)
    y = db.execute(text("SELECT baslangic FROM takvim_etkinlikleri WHERE okul_id IS NULL AND ogrenci_id IS NULL AND tur = 'sinav' "
                        "AND baslik ILIKE '%YKS 2027%' ORDER BY baslangic")).scalars().all()
    assert y == [date(2027, 6, 19), date(2027, 6, 20)]
    for isaret in ("0097_yasam_maliyeti_turkis_2026_10", "0097_kamu_maaslari_2026_2", "0097_yks_2027"):
        assert db.execute(text("SELECT 1 FROM tek_seferlik_gocler WHERE ad = :a"), {"a": isaret}).first()


@db_gerekli
def test_yks_geri_sayimi_resmi_tarihi_kullanir(db):
    from app.api.motivasyon import _yks_tarihi
    assert _yks_tarihi(db, 2027) == (date(2027, 6, 19), True)


@db_gerekli
def test_kamu_eslesmesi_tam_ad_ve_parca(db):
    from app.core import is_hayati_servisi as ihs
    ad = lambda b, m=(): {x["kadro_adi"].split(" (")[0] for x in ihs.kamu_eslesen(db, b, list(m))}
    assert "Uzman doktor" in ad("TIP") and "Uzman doktor" not in ad("TIP MÜHENDİSLİĞİ"), "'=tip' yalnızca tam adla eşleşir"
    assert "Mühendis" in ad("TIP MÜHENDİSLİĞİ")
    assert {"Öğretmen", "Uzman öğretmen"} <= ad("SINIF ÖĞRETMENLİĞİ")
    assert "Avukat" in ad("HUKUK") and "Vaiz" in ad("İLAHİYAT")
    assert ad("SOSYOLOJİ") == set() and ad("DİŞ HEKİMLİĞİ") == set()


@db_gerekli
def test_giderler_referans_doner(istemci, kisiler):
    r = istemci.get("/ogrenci/is-hayati/giderler", headers=kisiler["ogrenci"])
    assert r.status_code == 200, r.text
    ref = r.json()["referans"]
    assert ref[0]["kod"] == "bekar_yasam" and ref[0]["aylik_tutar"] == 49124.3 and ref[0]["donem"] == "2026-10"


@db_gerekli
def test_veri_kaynaklari_artik_eksik_gostermez(db):
    from app.core import veri_kaynaklari as vk
    durum = {k["kod"]: k["durum"] for k in vk.liste(db)["kaynaklar"]}
    for kod in ("kamu_maaslari", "yasam_giderleri", "yks_tarihi"):
        assert durum[kod] != "yok", kod
