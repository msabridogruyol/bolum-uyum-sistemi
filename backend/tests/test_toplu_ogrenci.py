"""[2026-10-12] Toplu öğrenci işlemleri: yeni eğitim yılında sınıf atlatma (+ geri alma) ve değerlendirmeyi sıfırlama."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


@pytest.fixture
def okul(db):
    from app.core.security import erisim_tokeni_uret
    ek = uuid.uuid4().hex[:6]
    a = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"TO A {ek}"}).scalar()
    b = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"TO B {ek}"}).scalar()
    ogr = {}
    for ad, sinif, sube, okul_id, test in [("Dokuz", "9. Sınıf", "A", a, False), ("On", "10. Sınıf", "B", a, False),
                                           ("Onbir", "11. Sınıf", "A", a, False), ("Oniki", "12. Sınıf", "C", a, False),
                                           ("Tekrar", "11. Sınıf", "B", a, False), ("Ham", "11-D", None, a, False),
                                           ("Aday", "Aday", None, a, False), ("Test", "9. Sınıf", "A", a, True),
                                           ("Baska", "9. Sınıf", "A", b, False)]:
        oid = uuid.uuid4()
        db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sinif, sube, test_hesabi,
                           olusturulma_zamani, guncelleme_zamani)
                           VALUES (:i, :ad, :e, 'x', :o, :s, :sb, :t, now(), now())"""),
                   {"i": oid, "ad": ad, "e": f"{oid.hex[:8]}@to-test.com", "o": okul_id, "s": sinif, "sb": sube, "t": test})
        ogr[ad] = oid
    y = uuid.uuid4()
    db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, sifre_degistirmeli, olusturulma_zamani)
                       VALUES (:i, 'TO Yetkili', :e, 'x', 'okul_yetkilisi', :o, TRUE, FALSE, now())"""), {"i": y, "e": f"{y.hex[:8]}@to-test.com", "o": a})
    db.commit()
    return {"a": a, "b": b, "ogr": ogr, "yet": {"Authorization": f"Bearer {erisim_tokeni_uret(y, 'okul_yetkilisi')}"}}


def _sinif(db, oid):
    return tuple(db.execute(text("SELECT sinif, sube FROM ogrenciler WHERE id = :i"), {"i": oid}).first())


@db_gerekli
def test_sinif_atlatma_onizleme_uygulama_ve_geri_alma(istemci, db, okul):
    o, h = okul["ogr"], okul["yet"]
    r = istemci.get(f"/yonetim/okul/{okul['a']}/sinif-atlat?haric={o['Tekrar']}", headers=h)
    assert r.status_code == 200
    g = {x["eski"]: x for x in r.json()["gecisler"]}
    assert g["9. Sınıf"]["sayi"] == 1                       # test hesabı sayılmaz
    assert g["11. Sınıf"]["sayi"] == 2 and g["11. Sınıf"]["kalan"] == 1   # "11-D" de 11. sınıf; Tekrar sınıfında kalır
    assert g["12. Sınıf"]["yeni"] == "Mezun"

    assert istemci.post(f"/yonetim/okul/{okul['a']}/sinif-atlat", headers=h, json={"onay": False}).status_code == 400
    r = istemci.post(f"/yonetim/okul/{okul['a']}/sinif-atlat", headers=h, json={"haric": [str(o["Tekrar"])], "onay": True})
    assert r.status_code == 200 and r.json()["sayi"] == 5
    db.expire_all()
    assert _sinif(db, o["Dokuz"]) == ("10. Sınıf", "A")
    assert _sinif(db, o["Onbir"]) == ("12. Sınıf", "A")
    assert _sinif(db, o["Oniki"]) == ("Mezun", "C")
    assert _sinif(db, o["Ham"]) == ("12. Sınıf", "D")          # şube harfi korunur
    assert _sinif(db, o["Tekrar"]) == ("11. Sınıf", "B")       # sınıf tekrarı
    assert _sinif(db, o["Aday"])[0] == "Aday" and _sinif(db, o["Test"])[0] == "9. Sınıf"
    assert _sinif(db, o["Baska"])[0] == "9. Sınıf"             # başka okul etkilenmez
    # Aynı yıl ikinci kez: uyarı
    assert "zaten sınıf atlatma" in (istemci.get(f"/yonetim/okul/{okul['a']}/sinif-atlat", headers=h).json()["uyari"] or "")

    # Bir öğrencinin sınıfı sonradan elle değiştirildiyse geri almada atlanır
    db.execute(text("UPDATE ogrenciler SET sinif = '12. Sınıf' WHERE id = :i"), {"i": o["On"]}); db.commit()
    r = istemci.post(f"/yonetim/toplu-islem/{r.json()['islem_id']}/geri-al", headers=h)
    assert r.status_code == 200 and r.json() == {"donen": 4, "atlanan": 1}
    db.expire_all()
    assert _sinif(db, o["Dokuz"]) == ("9. Sınıf", "A") and _sinif(db, o["Oniki"]) == ("12. Sınıf", "C")
    assert _sinif(db, o["Ham"]) == ("11-D", None)
    son = istemci.get(f"/yonetim/okul/{okul['a']}/sinif-atlat", headers=h).json()["son_islem"]
    assert son["geri_alindi"] is True and son["geri_alinabilir"] is False


@db_gerekli
def test_baska_okul_yetkisi_yok(istemci, okul):
    h = okul["yet"]
    assert istemci.get(f"/yonetim/okul/{okul['b']}/sinif-atlat", headers=h).status_code == 403
    assert istemci.post(f"/yonetim/okul/{okul['b']}/sinif-atlat", headers=h, json={"onay": True}).status_code == 403
    r = istemci.post("/yonetim/ogrenciler/degerlendirme-sifirla", headers=h, json={"idler": [str(okul["ogr"]["Baska"])]})
    assert r.status_code in (403, 404)


@db_gerekli
def test_degerlendirme_sifirlama_son_turu_siler_ve_beklemeden_baslatir(istemci, db, okul):
    from app.core.katman_servisi import aktif_veya_yeni_tur_getir
    from app.models import Ogrenci
    oid = okul["ogr"]["Onbir"]
    eski = datetime.now(timezone.utc) - timedelta(days=200)
    yakin = datetime.now(timezone.utc) - timedelta(days=5)
    db.execute(text("""INSERT INTO ogrenci_degerlendirme_turu (ogrenci_id, tur_no, durum, baslama_zamani, tamamlanma_zamani, sonuc_gecerli_mi)
                       VALUES (:o, 1, 'tamamlandi', :z, :z, TRUE), (:o, 2, 'tamamlandi', :y, :y, TRUE)"""), {"o": oid, "z": eski, "y": yakin})
    db.commit()
    # Sıfırlamadan önce: 2. tur 5 gün önce bitti → bekleme süresi
    from app.core.katman_servisi import IsKuraliHatasi
    with pytest.raises(IsKuraliHatasi):
        aktif_veya_yeni_tur_getir(db, db.get(Ogrenci, oid))
    db.rollback()

    r = istemci.post("/yonetim/ogrenciler/degerlendirme-sifirla", headers=okul["yet"],
                     json={"idler": [str(oid), str(okul["ogr"]["Dokuz"])]})
    assert r.status_code == 200 and r.json() == {"sifirlanan": 1, "degerlendirmesi_olmayan": 1}
    db.expire_all()
    turlar = [t for (t,) in db.execute(text("SELECT tur_no FROM ogrenci_degerlendirme_turu WHERE ogrenci_id = :o ORDER BY tur_no"), {"o": oid})]
    assert turlar == [1]                                   # yalnızca son tur silindi, önceki tur geçmişte kalır
    o = db.get(Ogrenci, oid)
    assert o.yeni_tur_izni is not None
    tur = aktif_veya_yeni_tur_getir(db, o)                 # bekleme olmadan yeni tur
    assert tur.tur_no == 2 and tur.durum == "devam_ediyor" and o.yeni_tur_izni is None
    db.rollback()
