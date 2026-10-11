"""[2026-10-11] Sistem sözlüğü ek terimleri: öğrenci girişi gerekir, kişisel veri yok, bölüm/meslek/özellik döner."""
import uuid

from sqlalchemy import text

from tests.conftest import db_gerekli


@db_gerekli
def test_sozluk_ek_giris_ister_ve_icerik_doner(istemci, db):
    from app.core.security import erisim_tokeni_uret
    assert istemci.get("/ogrenci/sozluk/ek").status_code == 401
    i = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Sözlük Deneme', :e, 'x', now(), now())"""), {"i": i, "e": f"{i.hex[:8]}@sz-test.com"})
    db.commit()
    r = istemci.get("/ogrenci/sozluk/ek", headers={"Authorization": f"Bearer {erisim_tokeni_uret(i, 'ogrenci')}"})
    assert r.status_code == 200
    v = r.json()
    assert set(v) == {"bolumler", "meslekler", "ozellikler"}
    for b in v["bolumler"]:
        assert set(b) == {"id", "ad", "t"} and b["t"]
    for m in v["meslekler"]:
        assert m["t"] and all(set(x) == {"id", "ad"} for x in m["bolumler"])
    assert "Sözlük Deneme" not in r.text   # kişisel veri yok
