"""[2026-10-29] Bölüm kaldırma (0082): içerik dosyalarında kaldırılan ad kalmadı; SQL bölümü ve bağlı satırları siler
(NULL olabilen bağlantıyı NULL yapar), diğer bölümlere dokunmaz, ikinci çalıştırmada hiçbir şey değiştirmez."""
import importlib.util
import json
from pathlib import Path

from sqlalchemy import text

from tests.conftest import db_gerekli

KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("g0082", KOK / "alembic/versions/0082_bolum_kaldirma.py")
GOC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GOC)


def test_liste_tutarli_ve_birlestirme_ana_bolumleriyle_cakismiyor():
    assert len(GOC.KALDIRILAN) == len(set(GOC.KALDIRILAN)) == 12
    _s = importlib.util.spec_from_file_location("g0075", KOK / "alembic/versions/0075_bolum_birlestirme.py")
    g75 = importlib.util.module_from_spec(_s)
    _s.loader.exec_module(g75)
    assert not set(GOC.KALDIRILAN) & {g.split("|")[0] for g in g75.GRUPLAR}


def test_icerik_dosyalarinda_kaldirilan_ad_yok():
    dosyalar = {"app/data/mulakat_simulasyonu.json": "bolumler", "app/data/meslege_yol.json": "bolumler",
                "app/data/bolum_kisa_aciklama.json": "bolumler", "app/core/meslek_jargonu.json": None}
    for yol, anahtar in dosyalar.items():
        d = json.loads((KOK / yol).read_text("utf-8"))
        assert not set(GOC.KALDIRILAN) & set(d[anahtar] if anahtar else d), yol
    duz = json.loads((KOK / "app/data/bolum_detay_duzeltme.json").read_text("utf-8"))["duzeltmeler"]
    assert not {x["bolum"] for x in duz} & set(GOC.KALDIRILAN)
    for yol in (KOK.parent / "frontend/src/dil").glob("*.json"):
        assert not set(GOC.KALDIRILAN) & set(json.loads(yol.read_text("utf-8"))), yol.name


def test_sema_guncelleme_listesinde_ve_bolunebilir():
    from app.core import sema_guncelleme as sg
    assert "0082_bolum_kaldirma" in sg.OTOMATIK
    assert sg.OTOMATIK.index("0082_bolum_kaldirma") > sg.OTOMATIK.index("0075_bolum_birlestirme")
    assert len(sg._komutlar(GOC.SQL)) == 2      # fonksiyon + blok; gövdeler bölünmüyor


@db_gerekli
def test_bolumu_ve_bagli_satirlari_siler_digerine_dokunmaz_tekrar_calistirmada_degismez(db):
    def bolum(ad):
        return db.execute(text("""INSERT INTO bolumler (ad, durum, detay, olusturulma_zamani)
                                  VALUES (:a, 'yayinda', '{}'::jsonb, now()) RETURNING id"""), {"a": ad}).scalar()
    sil, kal = bolum("TST KALDIR SIL"), bolum("TST KALDIR KAL")
    db.execute(text("CREATE TABLE tst_k_cocuk (id serial PRIMARY KEY, bolum_id int NOT NULL REFERENCES bolumler(id))"))
    db.execute(text("CREATE TABLE tst_k_torun (id serial PRIMARY KEY, cocuk_id int NOT NULL REFERENCES tst_k_cocuk(id))"))
    db.execute(text("CREATE TABLE tst_k_bos (id serial PRIMARY KEY, bolum_id int REFERENCES bolumler(id))"))
    for b in (sil, kal):
        c = db.execute(text("INSERT INTO tst_k_cocuk (bolum_id) VALUES (:b) RETURNING id"), {"b": b}).scalar()
        db.execute(text("INSERT INTO tst_k_torun (cocuk_id) VALUES (:c)"), {"c": c})
        db.execute(text("INSERT INTO tst_k_bos (bolum_id) VALUES (:b)"), {"b": b})

    def calistir():
        for k in GOC.sql_uret(["TST KALDIR SIL", "TST KALDIR YOK"]).split(";\n"):
            if k.strip():
                db.execute(text(k))

    def durum():
        return (db.execute(text("SELECT ad FROM bolumler WHERE ad LIKE 'TST KALDIR %' ORDER BY ad")).scalars().all(),
                db.execute(text("SELECT count(*) FROM tst_k_cocuk")).scalar(),
                db.execute(text("SELECT count(*) FROM tst_k_torun")).scalar(),
                db.execute(text("SELECT count(bolum_id), count(*) FROM tst_k_bos")).one())

    calistir()
    ilk = durum()
    assert ilk[0] == ["TST KALDIR KAL"] and ilk[1] == 1 and ilk[2] == 1 and tuple(ilk[3]) == (1, 2)
    calistir()
    assert durum() == ilk


# ---------------------------------------------------------------- [2026-11-01] 0086: yalnızca ön lisans olan 4 bölüm
_s86 = importlib.util.spec_from_file_location("g0086", KOK / "alembic/versions/0086_onlisans_bolum_kaldirma.py")
GOC86 = importlib.util.module_from_spec(_s86)
_s86.loader.exec_module(GOC86)


def test_onlisans_kaldirma_listesi_icerik_ve_sira():
    from app.core import sema_guncelleme as sg
    assert len(GOC86.KALDIRILAN) == 4 and not set(GOC86.KALDIRILAN) & set(GOC.KALDIRILAN)
    assert sg.OTOMATIK.index("0086_onlisans_bolum_kaldirma") > sg.OTOMATIK.index("0082_bolum_kaldirma")
    assert len(sg._komutlar(GOC86.SQL)) == 2
    for yol, anahtar in {"app/data/mulakat_simulasyonu.json": "bolumler", "app/data/meslege_yol.json": "bolumler",
                         "app/data/bolum_kisa_aciklama.json": "bolumler", "app/core/meslek_jargonu.json": None}.items():
        d = json.loads((KOK / yol).read_text("utf-8"))
        assert not set(GOC86.KALDIRILAN) & set(d[anahtar] if anahtar else d), yol
    for yol in (KOK.parent / "frontend/src/dil").glob("*.json"):
        assert not set(GOC86.KALDIRILAN) & set(json.loads(yol.read_text("utf-8"))), yol.name
