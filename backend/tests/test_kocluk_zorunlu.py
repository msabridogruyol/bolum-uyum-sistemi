"""[2026-10-19] Bölüm yönlendirme + koçluk sistemin omurgası: koçluk her pakette ve her okulda açık, çıkarılamaz."""
from sqlalchemy import text

from app.core.paketler import MODULLER, SECMELI, ZORUNLU, okul_modulleri, paket_listesi
from tests.conftest import db_gerekli


def test_kocluk_zorunlu_ve_secmeli_listede_yok():
    assert ZORUNLU == ["kocluk"] and "kocluk" in MODULLER and "kocluk" not in SECMELI


@db_gerekli
def test_paketten_ya_da_okuldan_cikarilan_kocluk_yine_acik(db):
    db.execute(text("""INSERT INTO paketler (kod, ad, moduller, sira) VALUES ('tst_kocluksuz', 'TST koçluksuz', '["takvim"]'::jsonb, 99)
                       ON CONFLICT (kod) DO UPDATE SET moduller = EXCLUDED.moduller"""))
    oid = db.execute(text("""INSERT INTO okullar (ad, paket, modul_cikar) VALUES ('TST Koçluk Okulu', 'tst_kocluksuz', '["kocluk"]'::jsonb)
                             RETURNING id""")).scalar()
    etkin = okul_modulleri(db, oid)
    assert "kocluk" in etkin and "takvim" in etkin and "net_takibi" not in etkin
    assert "kocluk" in next(p for p in paket_listesi(db) if p["kod"] == "tst_kocluksuz")["moduller"]
    db.rollback()
