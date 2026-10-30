"""[2026-10-30] Filiz her pakette (zorunlu, rehber modu); yapay zekâ her pakette, günlük sınır pakete göre
(Temel 5, Gelişim 15, Tam ve okulsuz 30), okulun aylık üst sınırı (öğrenci başı); sınır dolunca hizmet kesilmez,
Filiz rehber modunda cevap verir. Sınırlar yalnızca yapay zekâdan gelen cevapları sayar."""
import importlib.util
import uuid
from pathlib import Path

from sqlalchemy import text

from app.core.paketler import SECMELI, ZORUNLU, okul_modulleri
from tests.conftest import db_gerekli

_KOK = Path(__file__).resolve().parents[1]


def test_filiz_zorunlu_yapay_zeka_secmeli():
    assert "filiz" in ZORUNLU and "filiz" not in SECMELI
    assert "filiz_ai" in SECMELI, "okul yapay zekâyı isterse kapatabilsin"


def test_goc_tek_komutlar_ve_otomatik():
    yol = _KOK / "alembic" / "versions" / "0083_filiz_her_pakette.py"
    spec = importlib.util.spec_from_file_location("_m0083", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from app.core.sema_guncelleme import OTOMATIK, _komutlar
    assert "0083_filiz_her_pakette" in OTOMATIK and m.down_revision == "0082_bolum_kaldirma"
    komutlar = _komutlar(m.SQL)
    assert all(k.strip() for k in komutlar) and "DELETE" not in m.SQL.upper()


def _okul(db, paket, cikar="[]"):
    return db.execute(text("INSERT INTO okullar (ad, paket, modul_cikar) VALUES (:a, :p, CAST(:c AS jsonb)) RETURNING id"),
                      {"a": f"TST Filiz {uuid.uuid4().hex[:6]}", "p": paket, "c": cikar}).scalar()


def _ogrenci(db, okul_id):
    from app.models import Ogrenci
    oid = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Test Öğrenci', :e, 'x', :o, now(), now())"""),
               {"i": oid, "e": f"filiz.{oid.hex[:8]}@test.invalid", "o": okul_id})
    db.flush()
    return db.get(Ogrenci, oid)


def _yz_mesaj(db, ogrenci, adet, yapay_zeka=True):
    from app.models import OgrenciKoclukMesaji, OgrenciKoclukOturumu
    ot = OgrenciKoclukOturumu(ogrenci_id=ogrenci.id, durum="aktif")
    db.add(ot)
    db.flush()
    for _ in range(adet):
        db.add(OgrenciKoclukMesaji(oturum_id=ot.id, rol="ogrenci", icerik="soru"))
        db.add(OgrenciKoclukMesaji(oturum_id=ot.id, rol="asistan", icerik="cevap", yapay_zeka=yapay_zeka))
    db.flush()


def _goc(db):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for k in _komutlar(_sql_oku("0083_filiz_her_pakette")):
        db.execute(text(k))


@db_gerekli
def test_paketler_ve_okul_modulleri(db):
    _goc(db)
    for kod in ("temel", "gelisim", "tam"):
        oid = _okul(db, kod, '["filiz"]')            # okul Filiz'i çıkarmış olsa bile zorunlu
        etkin = okul_modulleri(db, oid)
        assert "filiz" in etkin and "filiz_ai" in etkin and "kocluk" in etkin, (kod, etkin)
    oid = _okul(db, "temel", '["filiz_ai"]')        # okul yapay zekâyı kapatabilir
    assert "filiz_ai" not in okul_modulleri(db, oid)
    db.rollback()


@db_gerekli
def test_sinirlar_pakete_gore_ve_rehber_moduna_gecis(db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)
    db.execute(text("UPDATE sistem_parametreleri SET deger = '0' WHERE anahtar = 'filiz_okul_aylik_ogrenci_basi'"))
    beklenen = {"temel": 5, "gelisim": 15, "tam": 30}
    for kod, sinir in beklenen.items():
        o = _ogrenci(db, _okul(db, kod))
        assert ai_koc._gunluk_limit(db, o) == sinir
        _yz_mesaj(db, o, sinir - 1)
        _yz_mesaj(db, o, 10, yapay_zeka=False)       # rehber modu / sabit cevaplar sayılmaz
        assert ai_koc._yz_durumu(db, o)[0] is True
        _yz_mesaj(db, o, 1)
        kullan, notu, *_ = ai_koc._yz_durumu(db, o)
        assert kullan is False and "rehber modunda" in notu
    assert ai_koc._gunluk_limit(db, _ogrenci(db, None)) == 30    # okula bağlı olmayan öğrenci
    db.rollback()


@db_gerekli
def test_okul_aylik_ust_siniri(db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)
    db.execute(text("UPDATE sistem_parametreleri SET deger = '2' WHERE anahtar = 'filiz_okul_aylik_ogrenci_basi'"))
    okul = _okul(db, "tam")
    a, b = _ogrenci(db, okul), _ogrenci(db, okul)     # 2 öğrenci × 2 = 4 mesaj/ay
    _yz_mesaj(db, a, 3)
    assert ai_koc._yz_durumu(db, b)[0] is True
    _yz_mesaj(db, a, 1)
    kullan, notu, *_ = ai_koc._yz_durumu(db, b)
    assert kullan is False and "Okulunun bu ayki" in notu
    assert ai_koc._yz_durumu(db, _ogrenci(db, _okul(db, "tam")))[0] is True   # başka okul etkilenmez
    db.rollback()


@db_gerekli
def test_sinir_dolunca_mesaj_kesilmez_rehber_cevap_gelir(istemci, kisiler, db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    db.execute(text("UPDATE okullar SET paket = 'temel' WHERE id = :o"), {"o": kisiler["okul_a"]})
    db.execute(text("UPDATE sistem_parametreleri SET deger = '1' WHERE anahtar = 'filiz_gunluk_mesaj_limiti_temel'"))
    db.commit()
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)
    monkeypatch.setattr(ai_koc, "openai_ile_konus", lambda s, m: "yapay zekâ cevabı")
    h = kisiler["ogrenci"]
    oturum = istemci.post("/koclugu/asistan/oturum/baslat", headers=h).json()["oturum_id"]
    r1 = istemci.post(f"/koclugu/asistan/oturum/{oturum}/mesaj", headers=h, json={"mesaj": "Hedefime nasıl yaklaşırım?"})
    assert r1.status_code == 200 and r1.json()["asistan_yaniti"] == "yapay zekâ cevabı" and not r1.json()["otomatik"]
    r2 = istemci.post(f"/koclugu/asistan/oturum/{oturum}/mesaj", headers=h, json={"mesaj": "Peki güçlü yönlerim neler?"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["otomatik"] is True and r2.json()["asistan_yaniti"].startswith("Bugünkü yapay zekâ mesaj hakkın doldu")
    d = istemci.get("/koclugu/asistan/durum", headers=h).json()
    assert d["mod"] == "otomatik" and d["gunluk_limit"] == 1
