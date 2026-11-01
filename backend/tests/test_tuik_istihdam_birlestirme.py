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
