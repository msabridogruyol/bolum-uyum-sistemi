"""[2026-11-24] TYT Fen'in isteğe bağlı branş kırılımı (Fizik/Kimya/Biyoloji) — rehberlik birimi raporu önerisi.

Geriye dönük uyum: toplu "tyt_fen" girişi aynen çalışır; branş girildiğinde hedef kıyasında TYT Fen'e toplanır;
ikisi bir arada girilemez."""
import pytest

from tests.conftest import db_gerekli


@db_gerekli
def test_brans_bazli_tyt_fen_girilebilir(istemci, db, kisiler):
    h = kisiler["ogrenci"]
    # /yapi branş seçeneğini sunar
    y = istemci.get("/ogrenci/net/yapi", headers=h).json()
    assert "tyt_fen" in y["brans_testleri"]
    kodlar = [t["kod"] for t in y["brans_testleri"]["tyt_fen"]]
    assert kodlar == ["tyt_fiz", "tyt_kim", "tyt_biy"]
    assert [t["soru"] for t in y["brans_testleri"]["tyt_fen"]] == [7, 7, 6]

    # branş bazlı deneme eklenebilir
    r = istemci.post("/ogrenci/net/denemeler", headers=h, json={
        "tarih": "2026-11-20", "oturum": "TYT", "ad": "Deneme 1",
        "dersler": {"tyt_mat": {"d": 30, "y": 4}, "tyt_fiz": {"d": 6, "y": 1}, "tyt_kim": {"d": 5, "y": 0}, "tyt_biy": {"d": 6, "y": 0}}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert set(d["dersler"]) == {"tyt_mat", "tyt_fiz", "tyt_kim", "tyt_biy"}
    assert d["dersler"]["tyt_fiz"]["net"] == 5.75
    # toplam = 29 + 5.75 + 5 + 6 = 45.75
    assert d["toplam_net"] == 45.75


@db_gerekli
def test_toplu_tyt_fen_hala_calisir(istemci, db, kisiler):
    r = istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT", "dersler": {"tyt_fen": {"d": 15, "y": 4}}})
    assert r.status_code == 200, r.text
    assert r.json()["dersler"]["tyt_fen"]["net"] == 14.0


@db_gerekli
def test_toplu_ve_brans_birlikte_reddedilir(istemci, db, kisiler):
    r = istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT", "dersler": {"tyt_fen": {"d": 10, "y": 0}, "tyt_fiz": {"d": 5, "y": 0}}})
    assert r.status_code == 400
    assert "ikisini birden değil" in r.json()["detail"]


@db_gerekli
def test_brans_soru_sayisi_asilamaz(istemci, db, kisiler):
    r = istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT", "dersler": {"tyt_biy": {"d": 7, "y": 0}}})  # biyoloji 6 soru
    assert r.status_code == 400
    assert "en fazla 6" in r.json()["detail"]


@db_gerekli
def test_brans_hedef_kiyasinda_tyt_fene_toplanir(istemci, db, kisiler, monkeypatch):
    # sahte YÖK Atlas hedefi: tytFenNet için bir hedef net
    from app.api import net_takibi
    monkeypatch.setattr(net_takibi, "_net_hedefi", lambda db, o: {
        "puan_turu": "SAY", "son": {"yil": 2025, "netler": {"tyt_fen": 15.0, "tyt_mat": 30.0}}, "gecmis": [], "ortalama": {}})
    istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT",
        "dersler": {"tyt_fiz": {"d": 6, "y": 1}, "tyt_kim": {"d": 5, "y": 0}, "tyt_biy": {"d": 6, "y": 0}}})
    k = istemci.get("/ogrenci/net/kiyas", headers=kisiler["ogrenci"]).json()
    fen = next(s for s in k["satirlar"] if s["kod"] == "tyt_fen")
    assert fen["ben"] == 16.75   # branşlar toplanıp TYT Fen olarak kıyaslandı
    assert fen["hedef"] == 15.0 and fen["fark"] == 1.75
