"""[2026-10-30] Filiz her pakette (zorunlu, rehber modu); yapay zekâ her pakette, günlük sınır pakete göre
(Temel 5, Gelişim 20, Tam ve okulsuz 40), okulun aylık üst sınırı (öğrenci başı Temel 30 / Gelişim 60 / Tam 120); sınır dolunca hizmet kesilmez,
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
    db.execute(text("UPDATE sistem_parametreleri SET deger = '0' WHERE anahtar LIKE 'filiz_okul_aylik_ogrenci_basi%'"))
    beklenen = {"temel": 5, "gelisim": 20, "tam": 40}
    for kod, sinir in beklenen.items():
        o = _ogrenci(db, _okul(db, kod))
        assert ai_koc._gunluk_limit(db, o) == sinir
        _yz_mesaj(db, o, sinir - 1)
        _yz_mesaj(db, o, 10, yapay_zeka=False)       # rehber modu / sabit cevaplar sayılmaz
        assert ai_koc._yz_durumu(db, o)[0] is True
        _yz_mesaj(db, o, 1)
        kullan, notu, *_ = ai_koc._yz_durumu(db, o)
        assert kullan is False and "rehber modunda" in notu
    assert ai_koc._gunluk_limit(db, _ogrenci(db, None)) == 40    # okula bağlı olmayan öğrenci
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


@db_gerekli
def test_aylik_havuz_pakete_gore(db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)
    for kod, kisi_basi in {"temel": 30, "gelisim": 60, "tam": 120}.items():
        o = _ogrenci(db, _okul(db, kod))
        db.execute(text("UPDATE sistem_parametreleri SET deger = '1000' WHERE anahtar LIKE 'filiz_gunluk_mesaj_limiti%'"))
        _yz_mesaj(db, o, kisi_basi - 1)
        assert ai_koc._yz_durumu(db, o)[0] is True, kod
        _yz_mesaj(db, o, 1)
        assert ai_koc._yz_durumu(db, o)[0] is False, kod
    db.rollback()


# ---------------------------------------------------------------- [2026-10-31] yük önlemleri (tek kapı: yz_sohbet)
class _SahteIstemci:
    def __init__(self, davranis):
        self.davranis, self.cagrilar = davranis, []
        self.chat = self
        self.completions = self

    def with_options(self, **_):
        return self

    def create(self, model, **_):
        self.cagrilar.append(model)
        sonuc = self.davranis(model)
        if isinstance(sonuc, Exception):
            raise sonuc
        from types import SimpleNamespace as N
        return N(choices=[N(message=N(content=sonuc))])


def _kur_istemci(monkeypatch, davranis):
    from app.core import ai_koc_servisi as s
    ist = _SahteIstemci(davranis)
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(s, "_yz_istemcisi", lambda sure: ist)
    return s, ist


def test_ana_model_hata_verirse_yedek_model(monkeypatch):
    s, ist = _kur_istemci(monkeypatch, lambda m: TimeoutError() if m == s.MODEL_ADI else "yedek cevap")
    assert s.yz_sohbet([{"role": "user", "content": "x"}], temperature=0.5, max_tokens=10) == "yedek cevap"
    assert ist.cagrilar == [s.MODEL_ADI, s.YEDEK_MODEL_ADI]


def test_iki_model_de_hata_verirse_anlasilir_hata(monkeypatch):
    s, ist = _kur_istemci(monkeypatch, lambda m: RuntimeError("kota"))
    import pytest
    with pytest.raises(s.AsistanKullanilamiyorHatasi):
        s.yz_sohbet([{"role": "user", "content": "x"}], temperature=0.5, max_tokens=10)
    assert s._YZ_KAPI.acquire(blocking=False)      # kapı serbest bırakılmış olmalı
    s._YZ_KAPI.release()


def test_kapi_doluysa_beklemeden_mesgul(monkeypatch):
    import threading
    import pytest
    s, ist = _kur_istemci(monkeypatch, lambda m: "cevap")
    monkeypatch.setattr(s, "_YZ_KAPI", threading.BoundedSemaphore(1))
    s._YZ_KAPI.acquire()
    try:
        with pytest.raises(s.AsistanMesgulHatasi):
            s.yz_sohbet([{"role": "user", "content": "x"}], temperature=0.5, max_tokens=10)
        assert ist.cagrilar == [], "kapı doluyken model çağrılmamalı"
    finally:
        s._YZ_KAPI.release()


@db_gerekli
def test_yapay_zeka_hata_verince_sohbet_kesilmez(istemci, kisiler, db, monkeypatch):
    from app.api import ai_koc
    from app.core.ai_koc_servisi import AsistanMesgulHatasi
    _goc(db)
    db.commit()
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)

    def mesgul(*_a, **_k):
        raise AsistanMesgulHatasi("yoğun")
    monkeypatch.setattr(ai_koc, "openai_ile_konus", mesgul)
    h = kisiler["ogrenci"]
    oturum = istemci.post("/koclugu/asistan/oturum/baslat", headers=h).json()["oturum_id"]
    r = istemci.post(f"/koclugu/asistan/oturum/{oturum}/mesaj", headers=h, json={"mesaj": "Güçlü yönlerim neler?"})
    assert r.status_code == 200, r.text
    assert r.json()["otomatik"] is True and r.json()["asistan_yaniti"].startswith("Yapay zekâ şu an yoğun")
    sayi = db.execute(text("""SELECT count(*) FROM ogrenci_koclugu_mesajlari m JOIN ogrenci_koclugu_oturumlari o ON o.id = m.oturum_id
                              WHERE o.id = :o AND m.yapay_zeka"""), {"o": oturum}).scalar()
    assert sayi == 0, "rehber cevabı yapay zekâ hakkından düşmemeli"


# ---------------------------------------------------------------------------------- [2026-10-31] bağımsız inceleme
@db_gerekli
def test_mulakat_yapay_zeka_durumu_calisir(db, monkeypatch):
    from app.api import ai_koc, is_hayati_mulakat as m
    _goc(db)
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)
    o = _ogrenci(db, _okul(db, "gelisim"))
    d = m._ai_durum(db, o)
    assert d["acik"] is True and d["limit"] == 20, d
    db.rollback()


@db_gerekli
def test_sinir_sifir_yapay_zeka_kapali_kilit_ve_not_yok(db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)
    db.execute(text("UPDATE sistem_parametreleri SET deger = '0' WHERE anahtar = 'filiz_gunluk_mesaj_limiti_temel'"))
    o = _ogrenci(db, _okul(db, "temel"))
    kullan, notu, *_ = ai_koc._yz_durumu(db, o)
    assert kullan is False and notu is None
    db.rollback()


@db_gerekli
def test_goc_yonetici_cikardigi_filiz_ai_yi_geri_eklemez(db):
    _goc(db)
    db.execute(text("""UPDATE paketler SET moduller = moduller - 'filiz_ai' WHERE kod = 'temel'"""))
    _goc(db)      # açılışta yeniden çalışır
    assert not db.execute(text("SELECT moduller ? 'filiz_ai' FROM paketler WHERE kod = 'temel'")).scalar()
    assert db.execute(text("SELECT moduller ? 'filiz' FROM paketler WHERE kod = 'temel'")).scalar(), "zorunlu filiz geri gelir"
    db.rollback()
