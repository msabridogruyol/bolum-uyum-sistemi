"""[2026-10-12] Çoklu dil: kişisel dil tercihi, içerik çevirisi (yalnızca içerik havuzu + önbellek), Filiz'in cevap dili."""
import json
import pathlib
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


@pytest.fixture
def ortam(db):
    from app.core.security import erisim_tokeni_uret, sifre_hashle
    ek = uuid.uuid4().hex[:6]
    okul = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"CD {ek}"}).scalar()
    oid, yid = uuid.uuid4(), uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sinif, sube, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Dil Öğrenci', :e, :h, :o, '10. Sınıf', 'A', now(), now())"""),
               {"i": oid, "e": f"{oid.hex[:8]}@cd-test.com", "h": sifre_hashle("Sifre12345!"), "o": okul})
    db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, sifre_degistirmeli, olusturulma_zamani)
                       VALUES (:i, 'Dil Yetkili', :e, 'x', 'okul_yetkilisi', :o, TRUE, FALSE, now())"""),
               {"i": yid, "e": f"{yid.hex[:8]}@cd-test.com", "o": okul})
    db.commit()
    return {"ogr": {"Authorization": f"Bearer {erisim_tokeni_uret(oid, 'ogrenci')}"},
            "yet": {"Authorization": f"Bearer {erisim_tokeni_uret(yid, 'okul_yetkilisi')}"}}


@db_gerekli
def test_ogrenci_ve_yetkili_kendi_dilini_secer(istemci, ortam):
    assert istemci.get("/ogrenci/profil", headers=ortam["ogr"]).json()["dil"] is None        # hiç seçmedi
    assert istemci.put("/ogrenci/profil/dil", headers=ortam["ogr"], json={"dil": "de"}).json() == {"dil": "de"}
    assert istemci.get("/ogrenci/profil", headers=ortam["ogr"]).json()["dil"] == "de"
    assert istemci.put("/ogrenci/profil/dil", headers=ortam["ogr"], json={"dil": "xx"}).status_code == 400
    assert istemci.put("/yonetim/ben/dil", headers=ortam["yet"], json={"dil": "ru"}).json() == {"dil": "ru"}
    assert istemci.get("/yonetim/ben", headers=ortam["yet"]).json()["dil"] == "ru"
    assert istemci.put("/ogrenci/profil/dil", json={"dil": "en"}).status_code == 401           # giriş gerekir


@db_gerekli
def test_icerik_cevirisi_yalnizca_havuzdaki_metinler_ve_onbellek(istemci, db, monkeypatch):
    from app.core import ceviri_servisi as cs
    havuz_metni = "Bu metin bölüm açıklamalarından gelen bir içerik cümlesidir."
    kisisel = "Ayşe Yılmaz bugün rehber öğretmenle görüştü ve notu kaydedildi."
    monkeypatch.setattr(cs, "_HAVUZ", {havuz_metni})
    monkeypatch.setattr(cs, "_HAVUZ_ZAMAN", 10 ** 12)          # havuz yeniden kurulmasın
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    gonderilen = []

    def sahte(metinler, dil):
        gonderilen.extend(metinler)
        return [f"[{dil}] {m}" for m in metinler]
    monkeypatch.setattr(cs, "_parti_cevir", sahte)
    db.execute(text("DELETE FROM ceviri_onbellek WHERE kaynak = :k"), {"k": havuz_metni}); db.commit()

    r = istemci.post("/ceviri/icerik", json={"dil": "en", "metinler": [havuz_metni, kisisel, "  " + havuz_metni + "\n"]})
    assert r.status_code == 200
    c = r.json()["ceviriler"]
    assert c[0] == f"[en] {havuz_metni}" and c[2] == c[0]       # boşluklar normalize edilir
    assert c[1] is None                                          # havuzda olmayan metin çevrilmez
    assert gonderilen == [havuz_metni]                           # kişisel metin yapay zekâya HİÇ gönderilmez

    gonderilen.clear()
    r = istemci.post("/ceviri/icerik", json={"dil": "en", "metinler": [havuz_metni]})
    assert r.json()["ceviriler"] == [f"[en] {havuz_metni}"] and gonderilen == []   # ikinci kez önbellekten
    assert istemci.post("/ceviri/icerik", json={"dil": "tr", "metinler": [havuz_metni]}).json()["ceviriler"] == [None]
    assert istemci.post("/ceviri/icerik", json={"dil": "zz", "metinler": [havuz_metni]}).status_code == 400
    db.execute(text("DELETE FROM ceviri_onbellek WHERE kaynak = :k"), {"k": havuz_metni}); db.commit()


@db_gerekli
def test_anahtar_yoksa_turkce_kalir(istemci, monkeypatch):
    from app.core import ceviri_servisi as cs
    monkeypatch.setattr(cs, "_HAVUZ", {"Anahtar yokken bu içerik metni Türkçe kalmalıdır."})
    monkeypatch.setattr(cs, "_HAVUZ_ZAMAN", 10 ** 12)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = istemci.post("/ceviri/icerik", json={"dil": "fr", "metinler": ["Anahtar yokken bu içerik metni Türkçe kalmalıdır."]})
    assert r.status_code == 200 and r.json()["ceviriler"] == [None]


def test_icerik_havuzu_veri_dosyalarindan_kurulur():
    from app.core.ceviri_servisi import _yapraklar
    h = set()
    _yapraklar({"a": ["Kısa", "Bu cümle havuza girecek kadar uzundur."], "b": {"c": "Birinci satır yeterince uzun\nİkinci satır da yeterince uzun"}}, h)
    assert "Bu cümle havuza girecek kadar uzundur." in h and "Kısa" not in h
    assert "Birinci satır yeterince uzun" in h and "İkinci satır da yeterince uzun" in h


def test_filiz_secili_dilde_cevap_verir():
    from app.core.ceviri_servisi import _istek_dili, dil_coz, yapay_zeka_dil_talimati
    assert dil_coz("de-DE") == "de" and dil_coz("xx") == "tr" and dil_coz(None) == "tr"
    j = _istek_dili.set("tr")
    assert yapay_zeka_dil_talimati() == ""
    _istek_dili.reset(j)
    j = _istek_dili.set("ko")
    assert "Korean" in yapay_zeka_dil_talimati()
    _istek_dili.reset(j)


def test_x_dil_basligi_istek_diline_yazilir(istemci, monkeypatch):
    """Ara katman X-Dil başlığını okur; Filiz'e giden sistem istemine dil talimatı eklenir."""
    from app.core import ai_koc_servisi as aks
    yakalanan = {}

    class SahteIstemci:
        def __init__(self, *a, **k):
            self.chat = self
            self.completions = self

        def create(self, **k):
            yakalanan["sistem"] = k["messages"][0]["content"]

            class C:
                message = type("M", (), {"content": "ok"})()
            return type("Y", (), {"choices": [C()]})()
    import sys, types
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=SahteIstemci))
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    from app.core.ceviri_servisi import _istek_dili
    j = _istek_dili.set("ru")
    try:
        assert aks.openai_ile_konus("SISTEM", [{"role": "user", "content": "selam"}]) == "ok"
    finally:
        _istek_dili.reset(j)
    assert yakalanan["sistem"].startswith("SISTEM") and "Russian" in yakalanan["sistem"]


def test_sozluk_kopyasi_frontend_ile_ayni():
    """İçerik havuzu sözlüğü backend kopyasından okur; frontend dosyası değişince kopya da güncellenmeli."""
    kok = pathlib.Path(__file__).resolve().parents[2]
    fe = kok / "frontend" / "src" / "yardimci" / "sozlukGenis.json"
    be = kok / "backend" / "app" / "data" / "sozluk_genis.json"
    if not fe.exists():
        pytest.skip("frontend klasörü yok")
    assert json.loads(fe.read_text("utf-8")) == json.loads(be.read_text("utf-8"))


def test_ana_sozluk_kopyasi_sozluk_js_ile_ayni():
    """[2026-10-31] Filiz, Sözlük sayfasındaki ana terimleri backend kopyasından okur (scripts/sozluk_temel_kopyala.mjs).
    sozluk.js değişip betik çalıştırılmazsa Filiz ile Sözlük sayfası farklı tanım verir."""
    import shutil
    import subprocess
    kok = pathlib.Path(__file__).resolve().parents[2]
    js = kok / "frontend" / "src" / "yardimci" / "sozluk.js"
    be = kok / "backend" / "app" / "data" / "sozluk_temel.json"
    if not js.exists() or not shutil.which("node"):
        pytest.skip("frontend klasörü ya da node yok")
    kod = ("import('" + js.as_uri() + "').then(m => console.log(JSON.stringify(m.SOZLUK.map(({k, ad, g, t, o, es}) => "
           "({k, ad, g, t, ...(o ? {o} : {}), es: es || []})))))")
    cikti = subprocess.run(["node", "--input-type=module", "-e", kod], capture_output=True, text=True, timeout=60)
    assert cikti.returncode == 0, cikti.stderr
    assert json.loads(cikti.stdout) == json.loads(be.read_text("utf-8"))["terimler"], \
        "sozluk.js değişmiş: node scripts/sozluk_temel_kopyala.mjs çalıştırın"
