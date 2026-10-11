"""[2026-10-11] Hazır raporlar: yalnızca kendi okulu, test hesabı hariç, aktif gün sıralaması, kişilik puanı yok."""
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


@pytest.fixture
def ortam(db):
    from app.core.security import erisim_tokeni_uret
    ek = uuid.uuid4().hex[:6]
    a = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"HR A {ek}"}).scalar()
    b = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"HR B {ek}"}).scalar()
    idler = {}
    for ad, okul, giris, test in (("Çok Giren", a, 5, False), ("Az Giren", a, 1, False), ("Hiç Girmeyen", a, 0, False),
                                  ("Test Hesap", a, 9, True), ("Başka Okul", b, 7, False)):
        i = uuid.uuid4()
        db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sinif, sube, test_hesabi,
                           son_giris_zamani, olusturulma_zamani, guncelleme_zamani)
                           VALUES (:i, :ad, :e, 'x', :o, '10. Sınıf', 'A', :t, CASE WHEN :g > 0 THEN now() END, now(), now())"""),
                   {"i": i, "ad": ad, "e": f"{i.hex[:8]}@hr-test.com", "o": okul, "t": test, "g": giris})
        for g in range(giris):
            db.execute(text("INSERT INTO ogrenci_hesap_olaylari (ogrenci_id, olay) VALUES (:i, 'giris')"), {"i": i})
            db.execute(text("INSERT INTO ogrenci_aktif_gunler (ogrenci_id, gun) VALUES (:i, CURRENT_DATE - :g)"), {"i": i, "g": g})
        idler[ad] = str(i)
    y = uuid.uuid4()
    db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, olusturulma_zamani)
                       VALUES (:i, 'HR Yetkili', :e, 'x', 'okul_yetkilisi', :o, TRUE, now())"""), {"i": y, "e": f"{y.hex[:8]}@hr-test.com", "o": a})
    db.commit()
    return {"a": a, "b": b, "idler": idler, "h": {"Authorization": f"Bearer {erisim_tokeni_uret(y, 'okul_yetkilisi')}"}}


@db_gerekli
def test_kendi_okulu_giris_siralamasi_test_hesabi_haric(istemci, ortam):
    r = istemci.get(f"/yonetim/okul/{ortam['a']}/hazir-raporlar?gun=30", headers=ortam["h"])
    assert r.status_code == 200
    v = r.json()
    assert v["ogrenci_sayisi"] == 3 and v["hic_girmeyen"] == 1 and v["donemde_aktif"] == 2
    liste = {l["kod"]: l for l in v["listeler"]}
    cok = liste["en_aktif"]["satirlar"]
    assert [s["ad"] for s in cok] == ["Çok Giren", "Az Giren"] and cok[0]["deger"] == 5   # 5 farklı gün
    assert liste["en_az_aktif"]["satirlar"][0]["ad"] == "Hiç Girmeyen" and liste["en_az_aktif"]["satirlar"][0]["deger"] == 0
    metin = str(v)
    assert "Test Hesap" not in metin and "Başka Okul" not in metin


@db_gerekli
def test_yetkili_baska_okulun_raporunu_goremez(istemci, ortam):
    assert istemci.get(f"/yonetim/okul/{ortam['b']}/hazir-raporlar", headers=ortam["h"]).status_code == 403


@db_gerekli
def test_aktif_gun_gunde_bir_kez_islenir(db):
    from app.core.aktiflik import aktiflik_ozeti, gune_isle
    i = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Aktif Deneme', :e, 'x', now(), now())"""), {"i": i, "e": f"{i.hex[:8]}@hr-test.com"})
    gune_isle(db, i); gune_isle(db, i); db.commit()
    assert db.execute(text("SELECT count(*) FROM ogrenci_aktif_gunler WHERE ogrenci_id = :i"), {"i": i}).scalar() == 1
    oz = aktiflik_ozeti(db, i, 30)
    assert oz["aktif_gun"] == 1 and oz["seri"] == 1 and len(oz["takvim"]) == 30 and oz["takvim"][-1]["aktif"]
