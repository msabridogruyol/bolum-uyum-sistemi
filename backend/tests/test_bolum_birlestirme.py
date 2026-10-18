"""[2026-10-18] Bölüm birleştirme (0075): içerik dosyalarında silinen ad kalmadı; SQL ortalama alır, bağlı satırları
izleyerek siler (NULL olabilen bağlantıyı NULL yapar), ikinci çalıştırmada hiçbir şey değiştirmez."""
import importlib.util
import json
from pathlib import Path

from sqlalchemy import text

from tests.conftest import db_gerekli

KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("g0075", KOK / "alembic/versions/0075_bolum_birlestirme.py")
GOC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GOC)


def test_gruplar_tutarli():
    anlar = [g.split("|")[0] for g in GOC.GRUPLAR]
    assert len(GOC.GRUPLAR) == 21 and len(GOC.SILINEN_ADLAR) == 23
    assert len(set(GOC.SILINEN_ADLAR)) == 23 and not set(anlar) & set(GOC.SILINEN_ADLAR)
    assert "KAMU YÖNETİMİ" not in GOC.SILINEN_ADLAR          # kullanıcı kararı: ayrı kalır
    assert "MATEMATİK" not in GOC.SILINEN_ADLAR and "EKONOMETRİ" not in GOC.SILINEN_ADLAR


def test_icerik_dosyalarinda_silinen_ad_yok_ana_ad_var():
    dosyalar = {"app/data/mulakat_simulasyonu.json": "bolumler", "app/data/meslege_yol.json": "bolumler",
                "app/core/meslek_jargonu.json": None}
    for yol, anahtar in dosyalar.items():
        d = json.loads((KOK / yol).read_text("utf-8"))
        d = d[anahtar] if anahtar else d
        assert not set(GOC.SILINEN_ADLAR) & set(d), yol
        assert all(g.split("|")[0] in d for g in GOC.GRUPLAR), yol
    for yol in (KOK.parent / "frontend/src/dil").glob("*.json"):
        assert not set(GOC.SILINEN_ADLAR) & set(json.loads(yol.read_text("utf-8"))), yol.name


def test_sema_guncelleme_listesinde_ve_bolunebilir():
    from app.core import sema_guncelleme as sg
    assert "0075_bolum_birlestirme" in sg.OTOMATIK
    assert len(sg._komutlar(GOC.SQL)) == 2      # fonksiyon + blok; gövdeler bölünmüyor


def _bolum(db, ad):
    return db.execute(text("""INSERT INTO bolumler (ad, durum, detay, olusturulma_zamani)
                              VALUES (:a, 'yayinda', '{}'::jsonb, now()) RETURNING id"""), {"a": ad}).scalar()


@db_gerekli
def test_ortalama_alir_bagli_satirlari_siler_tekrar_calistirmada_degismez(db):
    ana, u1, u2 = (_bolum(db, f"TST BİRLEŞTİR {x}") for x in ("ANA", "U1", "U2"))
    d1, d2 = [r[0] for r in db.execute(text("SELECT id FROM degiskenler ORDER BY id LIMIT 2"))]
    for b, (a1, a2) in ((ana, (40, 70)), (u1, (50, 60)), (u2, (60, 80))):
        for d, a in ((d1, a1), (d2, a2)):
            db.execute(text("""INSERT INTO bolum_agirliklari (bolum_id, degisken_id, agirlik_degeri, yakinsama_skoru,
                               agirlikli_varyans, etkin_meslek_sayisi, versiyon, olusturulma_zamani)
                               VALUES (:b, :d, :a, 1, 10, :e, 1, now())"""), {"b": b, "d": d, "a": a, "e": 5 + b % 3})
    # bağlı tablolar (test işlemiyle birlikte geri alınır): zorunlu bağlantı (+ ona bağlı torun) ve NULL olabilen bağlantı
    db.execute(text("CREATE TABLE tst_cocuk (id serial PRIMARY KEY, bolum_id int NOT NULL REFERENCES bolumler(id))"))
    db.execute(text("CREATE TABLE tst_torun (id serial PRIMARY KEY, cocuk_id int NOT NULL REFERENCES tst_cocuk(id))"))
    db.execute(text("CREATE TABLE tst_bos (id serial PRIMARY KEY, bolum_id int REFERENCES bolumler(id))"))
    for b in (ana, u1, u2):
        c = db.execute(text("INSERT INTO tst_cocuk (bolum_id) VALUES (:b) RETURNING id"), {"b": b}).scalar()
        db.execute(text("INSERT INTO tst_torun (cocuk_id) VALUES (:c)"), {"c": c})
        db.execute(text("INSERT INTO tst_bos (bolum_id) VALUES (:b)"), {"b": b})

    def calistir():
        for k in GOC.sql_uret(["TST BİRLEŞTİR ANA|TST BİRLEŞTİR U1|TST BİRLEŞTİR U2"]).split(";\n"):
            if k.strip():
                db.execute(text(k))

    calistir()
    q = lambda s, **k: db.execute(text(s), k).all()
    assert q("SELECT id FROM bolumler WHERE id IN (:a, :b)", a=u1, b=u2) == []
    deger = dict(q("SELECT degisken_id, agirlik_degeri FROM bolum_agirliklari WHERE bolum_id = :a", a=ana))
    assert float(deger[d1]) == 50.0 and float(deger[d2]) == 70.0
    assert q("SELECT bolum_id FROM tst_cocuk") == [(ana,)]
    assert len(q("SELECT id FROM tst_torun")) == 1
    assert sorted(r[0] is None for r in q("SELECT bolum_id FROM tst_bos")) == [False, True, True]
    calistir()   # ikinci kez: üye yok → ortalama tekrar alınmaz
    assert dict(q("SELECT degisken_id, agirlik_degeri FROM bolum_agirliklari WHERE bolum_id = :a", a=ana)) == deger
