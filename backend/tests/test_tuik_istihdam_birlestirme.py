"""[2026-11-01] TÜİK aynı yılın verisini ayrı tablolarda yayımlar (istihdam oranı / ilk iş bulma süresi / kazanç grubu, lisans ve
ön lisans ayrı). Sırayla yüklenince aynı programın tek satırında birleşmeli; önceki yükleme silinmemeli."""
import uuid

from sqlalchemy import text

from tests.conftest import db_gerekli


@db_gerekli
def test_ayri_tuik_tablolari_ayni_satirda_birlesir(istemci, kisiler, db):
    ad = f"DENEME BÖLÜMÜ {uuid.uuid4().hex[:5].upper()}"
    bid = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda') RETURNING id"), {"a": ad}).scalar()
    db.commit()
    yil = 2091
    h = kisiler["super"]

    def yukle(satir, kaynak):
        r = istemci.post("/admin/is-hayati/istihdam/kaydet", headers=h, json={
            "veri_yili": yil, "kaynak": kaynak, "satirlar": [{"program_adi_kaynak": ad, "duzey": "lisans", "bolum_id": bid, **satir}]})
        assert r.status_code == 200, r.text
        return r.json()

    assert yukle({"istihdam_orani": 81.5}, "TÜİK, 2091, istihdam oranı")["eklenen"] == 1
    assert yukle({"is_bulma_suresi_ay": 4.2}, "TÜİK, 2091, ilk iş bulma süresi")["guncellenen"] == 1
    assert yukle({"kazanc_grubu": "yuksek"}, "TÜİK, 2091, kazanç grupları")["guncellenen"] == 1
    rows = db.execute(text("SELECT istihdam_orani, is_bulma_suresi_ay, kazanc_grubu, kaynak FROM istihdam_gostergeleri "
                           "WHERE veri_yili = :y AND bolum_id = :b"), {"y": yil, "b": bid}).all()
    assert len(rows) == 1
    r = rows[0]
    assert float(r.istihdam_orani) == 81.5 and float(r.is_bulma_suresi_ay) == 4.2 and r.kazanc_grubu == "yuksek"
    assert "istihdam oranı" in r.kaynak and "kazanç grupları" in r.kaynak
    # Ön lisans aynı adla ayrı satırdır
    r2 = istemci.post("/admin/is-hayati/istihdam/kaydet", headers=h, json={
        "veri_yili": yil, "kaynak": "TÜİK ön lisans", "satirlar": [{"program_adi_kaynak": ad, "duzey": "onlisans", "istihdam_orani": 60}]}).json()
    assert r2["eklenen"] == 1
    # Açıkça istenirse yıl baştan yüklenir
    r3 = istemci.post("/admin/is-hayati/istihdam/kaydet", headers=h, json={
        "veri_yili": yil, "kaynak": "TÜİK yeniden", "ayni_yili_degistir": True,
        "satirlar": [{"program_adi_kaynak": ad, "duzey": "lisans", "istihdam_orani": 70}]}).json()
    assert r3["silinen"] == 2 and r3["eklenen"] == 1
    db.execute(text("DELETE FROM istihdam_gostergeleri WHERE veri_yili = :y"), {"y": yil})
    db.commit()


def test_tuik_hucreleri_iki_dilli_ve_eksik_isaret():
    from app.api.admin_is_hayati import _hucre
    assert _hucre(["Tıp\r\nMedicine"], 0) == "Tıp"
    assert _hucre(["Çok yüksek\r\nVery high"], 0) == "Çok yüksek"
    assert _hucre(["."], 0) is None and _hucre(["  "], 0) is None and _hucre([95.4], 0) == 95.4


def test_eslestirme_genel_sozcuk_ve_cati_bolumler():
    from app.core import is_hayati_servisi as ihs
    ad = [{"id": 1, "ad": "Mekatronik Mühendisliği", "anahtarlar": ["mekatronik muhendisligi"]},
          {"id": 2, "ad": "Elektrik ve Elektronik Mühendisliği", "anahtarlar": ["elektrik ve elektronik muhendisligi"]},
          {"id": 3, "ad": "Dil ve Edebiyat", "anahtarlar": ["dil ve edebiyat"]},
          {"id": 4, "ad": "Dil Öğretmenliği", "anahtarlar": ["dil ogretmenligi"]},
          {"id": 5, "ad": "Veterinerlik", "anahtarlar": ["veterinerlik"]}]
    assert ihs.program_eslestir("Elektrik mühendisliği", ad)["bolum_id"] == 2, "genel sözcük (mühendisliği) yetmez"
    assert ihs.program_eslestir("Uzay mühendisliği", ad)["bolum_id"] is None
    assert ihs.program_eslestir("Kore dili ve edebiyatı", ad)["bolum_id"] == 3
    assert ihs.program_eslestir("Almanca öğretmenliği", ad)["bolum_id"] == 4
    assert ihs.program_eslestir("Türkçe öğretmenliği", ad)["bolum_id"] is None, "Türkçe yabancı dil öğretmenliği değil"
    assert ihs.program_eslestir("Veteriner", ad)["bolum_id"] == 5


@db_gerekli
def test_cok_programli_bolum_tek_program_degeri_gostermez(db):
    from app.core import is_hayati_servisi as ihs
    ad = f"DENEME ÇATI {uuid.uuid4().hex[:5].upper()}"
    bid = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda') RETURNING id"), {"a": ad}).scalar()
    for p, o, k in (("A dili ve edebiyatı", 50, "dusuk"), ("B dili ve edebiyatı", 70, "orta")):
        db.execute(text("INSERT INTO istihdam_gostergeleri (bolum_id, program_adi_kaynak, duzey, istihdam_orani, kazanc_grubu, veri_yili, kaynak) "
                        "VALUES (:b, :p, 'lisans', :o, :k, 2092, 'TÜİK | ek')"), {"b": bid, "p": p, "o": o, "k": k})
    db.commit()
    v = ihs.istihdam_bolum(db, bid)
    assert v["istihdam_orani"] is None and v["aralik"]["istihdam_orani"] == [50.0, 70.0] and v["coklu_program"] == 2
    assert v["kazanc_grubu"] is None and v["kaynak"] == "TÜİK"
    db.execute(text("INSERT INTO istihdam_gostergeleri (bolum_id, program_adi_kaynak, duzey, istihdam_orani, veri_yili, kaynak) "
                    "VALUES (:b, :p, 'lisans', 61, 2092, 'TÜİK')"), {"b": bid, "p": ad.title()})
    db.commit()
    assert ihs.istihdam_bolum(db, bid)["istihdam_orani"] == 61.0, "adı bölümle aynı program varsa o gösterilir"
    db.execute(text("DELETE FROM istihdam_gostergeleri WHERE veri_yili = 2092"))
    db.commit()
