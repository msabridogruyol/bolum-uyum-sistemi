"""
[2026-10-14] Tek kaynak: öğrencinin sonuç ekranındaki bölüm uyumu (skor_motoru.siralama_getir — K5 etkili nihai uyum +
alan sırası) ile tercih ekranı, rehber öğrenci detayı ve okul listelerinin gösterdiği uyum / ilk öneri aynı olmalı.
Ham toplam_uyum 38 + K5 (dal_ici 90 → +0,15 × 40 = +6) = 44 olan bölüm, ham 43'lük bölümün önüne geçer; hedef olarak
ham 38 (< 40) ama öğrencinin gördüğü 44'tür. [2026-10-18] K5 katsayısı 0,50 → 0,15.
"""
import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli

pytestmark = db_gerekli


def _ayni_alanda_iki_bolum(db):
    r = db.execute(text("""
        SELECT e.dal_id, array_agg(b.id ORDER BY b.id) AS idler
          FROM bolum_dal_eslesme e JOIN dallar d ON d.id = e.dal_id JOIN bolumler b ON b.id = e.bolum_id
         WHERE d.kod LIKE 'U%' AND b.durum = 'yayinda'
         GROUP BY e.dal_id HAVING count(*) >= 2 ORDER BY e.dal_id LIMIT 1""")).first()
    if not r:
        pytest.skip("aynı üst alanda iki yayında bölüm yok")
    return r.idler[0], r.idler[1]


@pytest.fixture
def k5li_ogrenci(db, kisiler):
    """Testi tamamlamış, K5 verisi olan öğrenci; hedefi K5 ile yükselen bölüm."""
    oid = db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": kisiler["okul_a"]}).scalar()
    db.execute(text("UPDATE ogrenciler SET sinif = '12. Sınıf' WHERE id = :o"), {"o": oid})
    a, b = _ayni_alanda_iki_bolum(db)
    tur = db.execute(text("""INSERT INTO ogrenci_degerlendirme_turu (ogrenci_id, tur_no, baslama_zamani, tamamlanma_zamani, durum, sonuc_gecerli_mi)
                             VALUES (:o, 1, now(), now(), 'tamamlandi', TRUE) RETURNING id"""), {"o": oid}).scalar()
    for bid, u in ((a, 43), (b, 38)):
        db.execute(text("""INSERT INTO ogrenci_bolum_uyum_skorlari (ogrenci_id, tur_id, bolum_id, toplam_uyum, olusturulma_zamani)
                           VALUES (:o, :t, :b, :u, now())"""), {"o": oid, "t": tur, "b": bid, "u": u})
    dal = db.execute(text("SELECT id FROM dallar ORDER BY id LIMIT 1")).scalar()
    db.execute(text("""INSERT INTO ogrenci_dal_uyum_skorlari (ogrenci_id, tur_id, dal_id, bolum_id, dal_ici_uyum, olusturulma_zamani)
                       VALUES (:o, :t, :d, :b, 90, now())"""), {"o": oid, "t": tur, "d": dal, "b": b})
    db.execute(text("INSERT INTO ogrenci_hedef_bolum (ogrenci_id, bolum_id, secim_zamani, aktif_mi) VALUES (:o, :b, now(), TRUE)"),
               {"o": oid, "b": b})
    db.commit()
    return {"ogrenci_id": oid, "tur": tur, "ham_ilk": a, "k5_ilk": b}


def _ogrenci_ekrani(db, d):
    from app.core.skor_motoru import siralama_getir
    from app.models import Ogrenci, OgrenciDegerlendirmeTuru
    return siralama_getir(db, db.get(Ogrenci, d["ogrenci_id"]), db.get(OgrenciDegerlendirmeTuru, d["tur"]), ilk_n=10)


def test_ogrenci_ekrani_k5_etkili(db, k5li_ogrenci):
    sira = _ogrenci_ekrani(db, k5li_ogrenci)
    assert [(s.bolum_id, s.toplam_uyum) for s in sira] == [(k5li_ogrenci["k5_ilk"], 44.0), (k5li_ogrenci["ham_ilk"], 43.0)]


def test_toplu_fonksiyonlar_ogrenci_ekraniyla_ayni(db, k5li_ogrenci):
    from app.core.skor_motoru import toplu_nihai_uyum, toplu_siralama
    sira = _ogrenci_ekrani(db, k5li_ogrenci)
    t = k5li_ogrenci["tur"]
    assert [(s.bolum_id, s.toplam_uyum, s.alan) for s in toplu_siralama(db, [t])[t]] == [(s.bolum_id, s.toplam_uyum, s.alan) for s in sira]
    assert toplu_nihai_uyum(db, [t], [k5li_ogrenci["k5_ilk"]]) == {t: {k5li_ogrenci["k5_ilk"]: 44.0}}


def test_tercih_ekrani_ayni_uyum_ve_sira(db, istemci, kisiler, k5li_ogrenci):
    r = istemci.get("/ogrenci/tercih", headers=kisiler["ogrenci"])
    assert r.status_code == 200, r.text
    bolumler = {b["id"]: b for b in r.json()["bolumler"]}
    assert (bolumler[k5li_ogrenci["k5_ilk"]]["uyum"], bolumler[k5li_ogrenci["k5_ilk"]]["sira"]) == (44, 1)
    assert (bolumler[k5li_ogrenci["ham_ilk"]]["uyum"], bolumler[k5li_ogrenci["ham_ilk"]]["sira"]) == (43, 2)


def test_rehber_ogrenci_detayi_ayni_uyum(db, istemci, kisiler, k5li_ogrenci):
    r = istemci.get(f"/yonetim/ogrenci/{k5li_ogrenci['ogrenci_id']}", headers=kisiler["yetkili"])
    assert r.status_code == 200, r.text
    v = r.json()
    assert v["hedef"]["uyum"] == 44.0
    assert [o["uyum"] for o in v["oneriler"]] == [s.toplam_uyum for s in _ogrenci_ekrani(db, k5li_ogrenci)]


def test_okul_listesi_ilk_bolum_ve_tek_bakista(db, kisiler, k5li_ogrenci):
    from app.api.okul_tek_bakista import tek_bakista_verisi
    from app.api.okul_yonetimi import _ilerleme
    il = _ilerleme(db, kisiler["okul_a"])[k5li_ogrenci["ogrenci_id"]]
    assert il["ilk_bolum"] == k5li_ogrenci["k5_ilk"]
    assert il["oneri_ilk10"] == [s.bolum_id for s in _ogrenci_ekrani(db, k5li_ogrenci)]
    v = tek_bakista_verisi(db, kisiler["okul_a"], None, None)
    # hedef uyumu ham 38 (< 40) ama nihai 44: 'hedef uyumu düşük' listesinde OLMAMALI
    assert v["hedef_uyum"]["hedefli"] >= 1
    assert all(x["ogrenci_id"] != str(k5li_ogrenci["ogrenci_id"]) for x in v["hedef_uyum"]["ogrenciler"])


def test_veritabanindaki_tum_turlar_icin_toplu_siralama_ayni(db):
    """Mevcut (gerçekçi) verideki her tamamlanmış tur: toplu_siralama == siralama_getir (skor, sıra, alan)."""
    from app.core.skor_motoru import siralama_getir, toplu_siralama
    from app.models import Ogrenci, OgrenciDegerlendirmeTuru
    turlar = db.execute(text("SELECT DISTINCT tur_id FROM ogrenci_bolum_uyum_skorlari ORDER BY tur_id LIMIT 60")).scalars().all()
    if not turlar:
        pytest.skip("uyum skoru olan tur yok")
    toplu = toplu_siralama(db, turlar)
    for t in turlar:
        tur = db.get(OgrenciDegerlendirmeTuru, t)
        tek = siralama_getir(db, db.get(Ogrenci, tur.ogrenci_id), tur, ilk_n=100000)
        assert [(s.bolum_id, s.toplam_uyum, s.alan) for s in toplu[t]] == [(s.bolum_id, s.toplam_uyum, s.alan) for s in tek], t
    ilk10 = toplu_siralama(db, turlar, ilk_n=10)
    assert all([s.bolum_id for s in ilk10[t]] == [s.bolum_id for s in toplu[t][:10]] for t in turlar)
