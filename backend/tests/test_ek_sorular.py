"""[2026-10-19] Ek ölçme soruları + dikkat (kontrol) soruları (göç 0081) ve soru sırası."""
import importlib.util
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace as N

from sqlalchemy import text

from tests.conftest import db_gerekli

_KOK = Path(__file__).resolve().parents[1]
_ON = {"K1": "D", "K2": "P", "K3": "I", "K4": "A"}


def _veri(ad):
    return json.loads((_KOK / "app" / "data" / ad).read_text(encoding="utf-8"))


def test_ek_soru_dosyasi_tutarli():
    ek = _veri("olcme_sorulari_ek.json")["sorular"]
    ana = _veri("olcme_sorulari.json")["sorular"]
    assert not {s["metin"] for s in ek} & {s["metin"] for s in ana}, "aynı metin iki dosyada olmamalı"
    kontrol = [s for s in ek if s["tip"] == "kontrol"]
    assert Counter(s["katman"] for s in kontrol) == Counter({k: 2 for k in _ON})
    for s in kontrol:
        assert len(s["secenekler"]) == 4 and len(set(s["secenekler"])) == 4 and 1 <= s["beklenen"] <= 4
    assert len({s["beklenen"] for s in kontrol}) >= 3, "beklenen şık hep aynı yerde olmamalı"
    for s in ek:
        if s["tip"] != "kontrol":
            assert s["tip"] == "encok" and len(s["secenekler"]) == 4
            assert len({o["degisken"] for o in s["secenekler"]}) == 4
            assert all(o["degisken"][0] == _ON[s["katman"]] for o in s["secenekler"])


def test_her_ozellik_en_az_8_kez_olculur():
    say = Counter()
    for s in _veri("olcme_sorulari.json")["sorular"] + _veri("olcme_sorulari_ek.json")["sorular"]:
        if s["tip"] == "kutup":
            say[s["a"]] += 1
            say[s["b"]] += 1
        elif s["tip"] != "kontrol":
            for o in s["secenekler"]:
                say[o["degisken"]] += 1
    assert len(say) == 31 and min(say.values()) >= 8 and max(say.values()) <= 10, say


def test_gocu_sql_tek_komut_ve_guvenli():
    yol = _KOK / "alembic" / "versions" / "0081_ek_olcme_sorulari.py"
    spec = importlib.util.spec_from_file_location("_m0081", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from app.core.sema_guncelleme import OTOMATIK, _komutlar
    assert "0081_ek_olcme_sorulari" in OTOMATIK
    komutlar = _komutlar(m.SQL)
    assert len(komutlar) == 2 and komutlar[1].startswith("DO $$")
    assert "DELETE" not in m.SQL.upper(), "0081 yalnızca ekleme yapar"


def test_soru_sirasi_tura_gore_ve_dikkat_arada():
    from app.core.katman_servisi import soru_sirasi
    sorular = [N(id=i, soru_tipi="sjt") for i in range(1, 20)] + [N(id=90, soru_tipi="kontrol"), N(id=91, soru_tipi="kontrol")]
    a = soru_sirasi(sorular, 7)
    assert [s.id for s in a] == [s.id for s in soru_sirasi(list(reversed(sorular)), 7)]     # aynı turda aynı sıra
    assert len({tuple(s.id for s in soru_sirasi(sorular, t)) for t in range(1, 20)}) > 10
    yer = [i for i, s in enumerate(a) if s.soru_tipi == "kontrol"]
    assert yer == [7, 14] and sorted(s.id for s in a) == sorted(s.id for s in sorular)


@db_gerekli
def test_goc_idempotent_ve_dikkat_sorulari_puanlanmaz(db):
    """İşaret silinse bile (ör. elle) göç aynı soruları ikinci kez eklemez. Test işlemi sonunda geri alınır.
    Yalnızca DO bloğu çalıştırılır: sema_guncelleme'nin DDL komutları açık test işlemi yüzünden kilitte beklerdi."""
    if not db.execute(text("SELECT 1 FROM tek_seferlik_gocler WHERE ad LIKE '0081_ek_sorular_%'")).first():
        import pytest
        pytest.skip("0081 uygulanmamış (boş test şeması)")
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    do_blogu = _komutlar(_sql_oku("0081_ek_olcme_sorulari"))[1]
    once = db.execute(text("SELECT count(*) FROM sorular WHERE ogrenci_id IS NULL")).scalar()
    db.execute(text("DELETE FROM tek_seferlik_gocler WHERE ad LIKE '0081_ek_sorular_%'"))
    db.execute(text(do_blogu))
    assert db.execute(text("SELECT count(*) FROM sorular WHERE ogrenci_id IS NULL")).scalar() == once
    assert db.execute(text("SELECT 1 FROM tek_seferlik_gocler WHERE ad LIKE '0081_ek_sorular_%'")).first()
    k = db.execute(text("""SELECT count(*), count(beklenen_secenek_sira), count(degisken_id) FROM sorular
                           WHERE soru_tipi = 'kontrol' AND ogrenci_id IS NULL AND aktif_mi""")).one()
    assert k[0] == 8 and k[1] == 8 and k[2] == 0
    assert db.execute(text("""SELECT count(*) FROM sjt_secenek_degisken_agirlik a JOIN soru_secenekleri o ON o.id = a.secenek_id
                              JOIN sorular s ON s.id = o.soru_id WHERE s.soru_tipi = 'kontrol'""")).scalar() == 0
