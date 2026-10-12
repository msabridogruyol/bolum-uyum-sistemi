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


# ----------------------------------------------------------------------------- [2026-10-12] Yeniden değerlendirme kuralları
def _katmanlar(db):
    for i, kod in enumerate(["K1", "K2", "K3", "K4"], 1):
        if not db.execute(text("SELECT 1 FROM katmanlar WHERE kod = :k"), {"k": kod}).first():
            db.execute(text("INSERT INTO katmanlar (kod, ad, sira, kosullu_mu) VALUES (:k, :k, :s, FALSE)"), {"k": kod, "s": i})
    return {k: i for k, i in db.execute(text("SELECT kod, id FROM katmanlar WHERE kod IN ('K1','K2','K3','K4')"))}


def _tamamlanmis_tur(db, oid, gun_once, gecerli, olaylar=()):
    kat = _katmanlar(db)
    z = datetime.now(timezone.utc) - timedelta(days=gun_once)
    tid = db.execute(text("""INSERT INTO ogrenci_degerlendirme_turu (ogrenci_id, tur_no, durum, baslama_zamani, tamamlanma_zamani,
                             sonuc_gecerli_mi, guven_skoru) VALUES (:o, 1, 'tamamlandi', :z, :z, :g, :gs) RETURNING id"""),
                     {"o": oid, "z": z, "g": gecerli, "gs": 90 if gecerli else 30}).scalar()
    for kod, kid in kat.items():
        db.execute(text("""INSERT INTO ogrenci_katman_oturumlari (ogrenci_id, tur_id, katman_id, durum, baslama_zamani, tamamlanma_zamani)
                           VALUES (:o, :t, :k, 'tamamlandi', :z, :z)"""), {"o": oid, "t": tid, "k": kid, "z": z})
    for kod, tip, n in olaylar:
        for _ in range(n):
            db.execute(text("""INSERT INTO guvenlik_olaylari (ogrenci_id, tur_id, olay_tipi, katman_kod, olay_zamani)
                               VALUES (:o, :t, :tip, :k, :z)"""), {"o": oid, "t": tid, "tip": tip, "k": kod, "z": z})
    db.commit()
    return tid


@db_gerekli
def test_gecerli_turdan_sonra_3_ay_bekleme_ve_yonetim_izni(istemci, db, okul):
    from app.core.katman_servisi import IsKuraliHatasi, aktif_veya_yeni_tur_getir, degerlendirme_durumu
    from app.core.security import erisim_tokeni_uret
    from app.models import Ogrenci
    oid = okul["ogr"]["On"]
    _tamamlanmis_tur(db, oid, 10, True)
    o = db.get(Ogrenci, oid)
    d = degerlendirme_durumu(db, o)
    assert d["durum"] == "bekleme" and 79 <= d["kalan_gun"] <= 81 and d["bekleme_gun"] == 90
    with pytest.raises(IsKuraliHatasi) as e:
        aktif_veya_yeni_tur_getir(db, o)
    assert "tarihinde açılır" in str(e.value)
    db.rollback()
    ogr = {"Authorization": f"Bearer {erisim_tokeni_uret(oid, 'ogrenci')}"}
    assert istemci.get("/ogrenci/degerlendirme-durumu", headers=ogr).json()["durum"] == "bekleme"
    # Okul yetkilisi yeniden değerlendirme açar: önceki tur kalır, yeni tur beklemeden açılır
    r = istemci.post("/yonetim/ogrenciler/yeniden-degerlendirme", headers=okul["yet"], json={"idler": [str(oid), str(okul["ogr"]["Dokuz"])]})
    assert r.json() == {"acilan": 1, "devam_eden": 0, "degerlendirmesi_olmayan": 1}
    db.expire_all()
    o = db.get(Ogrenci, oid)
    assert degerlendirme_durumu(db, o)["durum"] == "acik"
    tur = aktif_veya_yeni_tur_getir(db, o)
    assert tur.tur_no == 2 and o.yeni_tur_izni is None
    db.rollback()


@db_gerekli
def test_guven_sorununda_yalnizca_sorunlu_katman_tekrar_cozulur(istemci, db, okul):
    from app.core.katman_servisi import IsKuraliHatasi, aktif_veya_yeni_tur_getir
    from app.core.security import erisim_tokeni_uret
    from app.models import Ogrenci
    oid = okul["ogr"]["Onbir"]
    tid = _tamamlanmis_tur(db, oid, 2, False, olaylar=[("K2", "sekme_degisti", 8), ("K1", "sekme_degisti", 1)])
    ogr = {"Authorization": f"Bearer {erisim_tokeni_uret(oid, 'ogrenci')}"}
    d = istemci.get("/ogrenci/degerlendirme-durumu", headers=ogr).json()
    assert d["durum"] == "guven_sorunu" and [k["kod"] for k in d["sorunlu_katmanlar"]] == ["K2"]
    # Yeni tam tur açılmaz
    with pytest.raises(IsKuraliHatasi) as e:
        aktif_veya_yeni_tur_getir(db, db.get(Ogrenci, oid))
    assert "K2" in str(e.value)
    db.rollback()
    assert istemci.post("/ogrenci/katmanlar/K1/tekrar", headers=ogr).status_code == 400   # sorunsuz katman
    assert istemci.post("/ogrenci/katmanlar/K2/tekrar", headers=ogr).status_code == 200
    db.expire_all()
    tur = db.execute(text("SELECT durum, tur_no FROM ogrenci_degerlendirme_turu WHERE id = :t"), {"t": tid}).first()
    assert tur.durum == "devam_ediyor" and tur.tur_no == 1                     # aynı tur, yeni tur açılmadı
    oturumlar = {k for (k,) in db.execute(text("""SELECT k.kod FROM ogrenci_katman_oturumlari o JOIN katmanlar k ON k.id = o.katman_id
                                                    WHERE o.tur_id = :t"""), {"t": tid})}
    assert "K2" not in oturumlar and {"K1", "K3", "K4"} <= oturumlar
    olay = dict(db.execute(text("SELECT katman_kod, count(*) FROM guvenlik_olaylari WHERE tur_id = :t GROUP BY 1"), {"t": tid}).all())
    assert olay == {"K1": 1}                                                    # eski K2 ihlalleri yeni denemeyi düşürmez
    assert aktif_veya_yeni_tur_getir(db, db.get(Ogrenci, oid)).id == tid        # öğrenci aynı turda K2'yi çözer
    db.rollback()


@db_gerekli
def test_yetkili_tek_katmani_tekrarlatir(istemci, db, okul):
    oid = okul["ogr"]["Oniki"]
    tid = _tamamlanmis_tur(db, oid, 5, True)
    r = istemci.get(f"/yonetim/ogrenci/{oid}/degerlendirme-durumu", headers=okul["yet"])
    assert r.status_code == 200 and r.json()["durum"] == "bekleme" and len(r.json()["katmanlar"]) == 4
    assert istemci.post(f"/yonetim/ogrenci/{oid}/katman-tekrar", headers=okul["yet"], json={"kod": "K3"}).status_code == 200
    db.expire_all()
    assert db.execute(text("SELECT durum FROM ogrenci_degerlendirme_turu WHERE id = :t"), {"t": tid}).scalar() == "devam_ediyor"
    assert istemci.post(f"/yonetim/ogrenci/{okul['ogr']['Baska']}/katman-tekrar", headers=okul["yet"], json={"kod": "K3"}).status_code in (403, 404)


# ----------------------------------------------------------------------------- [2026-10-12] Sonuç e-postası (+ PDF)
@db_gerekli
def test_sonuc_epostasi_bir_kez_gider_pdf_paketle_eklenir(istemci, db, okul, monkeypatch):
    from app.core import eposta_servisi as ep
    from app.core import sonuc_epostasi as se
    monkeypatch.setenv("TEST_EPOSTA_KAYDI", "1")
    ep.GONDERILENLER.clear()
    oid = okul["ogr"]["On"]
    tid = _tamamlanmis_tur(db, oid, 0, True)
    r = se.gonder(db, oid, tid)
    assert r["durum"] == "gonderildi"
    assert len(ep.GONDERILENLER) == 1 and ep.GONDERILENLER[0]["alici"].endswith("@to-test.com")
    beklenen_ek = se.rapor_ekli_mi(db, okul["a"])
    ekler = ep.GONDERILENLER[0]["ekler"]
    assert bool(ekler) == beklenen_ek and r["ekli"] == beklenen_ek
    if ekler:
        assert ekler[0][0].endswith(".pdf") and ekler[0][2] == "application/pdf" and ekler[0][1] > 1000
    # aynı tamamlanma için ikinci kez gitmez
    assert se.gonder(db, oid, tid)["durum"] == "zaten_gonderildi" and len(ep.GONDERILENLER) == 1
    # okul yetkilisi yeniden gönderebilir; durum detayda görünür
    assert istemci.post(f"/yonetim/ogrenci/{oid}/sonuc-epostasi", headers=okul["yet"]).status_code == 200
    assert len(ep.GONDERILENLER) == 2
    d = istemci.get(f"/yonetim/ogrenci/{oid}/degerlendirme-durumu", headers=okul["yet"]).json()["sonuc_epostasi"]
    assert d["durum"] == "gonderildi" and d["gonderilebilir"] is True
    # başka okulun öğrencisine gönderemez
    assert istemci.post(f"/yonetim/ogrenci/{okul['ogr']['Baska']}/sonuc-epostasi", headers=okul["yet"]).status_code in (403, 404)


@db_gerekli
def test_sonuc_epostasi_guven_sorununda_ve_test_hesabinda_gitmez(istemci, db, okul, monkeypatch):
    from app.core import eposta_servisi as ep
    from app.core import sonuc_epostasi as se
    from app.models import Ogrenci
    monkeypatch.setenv("TEST_EPOSTA_KAYDI", "1")
    ep.GONDERILENLER.clear()
    oid = okul["ogr"]["Onbir"]
    tid = _tamamlanmis_tur(db, oid, 0, False, olaylar=[("K2", "sekme_degisti", 8)])
    assert se.gonder(db, oid, tid)["durum"] == "uygun_degil"
    assert not se.otomatik_gidecek_mi(db, db.get(Ogrenci, oid), db.get(__import__("app.models", fromlist=["x"]).OgrenciDegerlendirmeTuru, tid))
    assert istemci.post(f"/yonetim/ogrenci/{oid}/sonuc-epostasi", headers=okul["yet"]).status_code == 400
    test_id = okul["ogr"]["Test"]
    assert se.gonder(db, test_id, _tamamlanmis_tur(db, test_id, 0, True))["durum"] == "uygun_degil"
    assert ep.GONDERILENLER == []


@db_gerekli
def test_katman_tekrari_bitince_sonuc_epostasi_yeniden_gider(db, okul, monkeypatch):
    """Güven sorunu → sorunlu katman yeniden çözülüp tur tekrar tamamlanınca (yeni tamamlanma zamanı) e-posta yine gider."""
    from app.core import eposta_servisi as ep
    from app.core import sonuc_epostasi as se
    monkeypatch.setenv("TEST_EPOSTA_KAYDI", "1")
    ep.GONDERILENLER.clear()
    oid = okul["ogr"]["Oniki"]
    tid = _tamamlanmis_tur(db, oid, 1, True)
    assert se.gonder(db, oid, tid)["durum"] == "gonderildi"
    db.execute(text("UPDATE ogrenci_degerlendirme_turu SET tamamlanma_zamani = clock_timestamp() + interval '1 second' WHERE id = :t"), {"t": tid})
    db.commit()
    assert se.gonder(db, oid, tid)["durum"] == "gonderildi" and len(ep.GONDERILENLER) == 2
