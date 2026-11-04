"""[2026-11-04] Veri Kaynakları › Otomatik çek: TÜİK veri tarayıcısı (JSON-stat) taklit edilerek; ağ kullanılmaz."""
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


def _jsonstat(boyutlar: list[tuple[str, list[str], dict | None]], degerler: dict[tuple, str]) -> dict:
    """boyutlar: [(ad, kodlar, etiketler)]; degerler: {(kod1, kod2, …): değer} → TÜİK biçimi (value: {"sıra": "metin"})."""
    ids = [b[0] for b in boyutlar]
    size = [len(b[1]) for b in boyutlar]
    value = {}
    for anahtar, v in degerler.items():
        n = 0
        for (ad, kodlar, _), k, s in zip(boyutlar, anahtar, size):
            n = n * s + kodlar.index(k)
        value[str(n)] = v
    return {"id": ids, "size": size, "value": value, "role": {},
            "dimension": {ad: {"category": {"index": kodlar, "label": et or {k: k for k in kodlar}}} for ad, kodlar, et in boyutlar}}


def _tufe(aylar: dict[str, float]) -> dict:
    b = [("REF_AREA", ["TR"], None), ("FREQ", ["M"], None), ("SINIFLAMA_DUZEYI", ["TUFE"], None),
         ("DEGISIM", ["1", "2", "3", "4", "5"], None), ("BASE_PER", ["2025"], None), ("COICOP_2018", ["0"], None),
         ("INDICATOR", ["F_TFE"], None), ("TIME_PERIOD", list(aylar), None)]
    d = {}
    for a, e in aylar.items():
        d[("TR", "M", "TUFE", "1", "2025", "0", "F_TFE", a)] = str(e)
        d[("TR", "M", "TUFE", "4", "2025", "0", "F_TFE", a)] = "30.5"
    return _jsonstat(b, d)


@db_gerekli
def test_tufe_eksik_aylari_ekler_degisenleri_yazmaz(db, monkeypatch):
    from app.core import otomatik_cekme as oc
    db.execute(text("DELETE FROM tufe_endeksi WHERE donem >= '2099-01'"))
    db.execute(text("INSERT INTO tufe_endeksi (donem, endeks, kaynak) VALUES ('2099-01', 500, 'test')"))
    db.commit()
    monkeypatch.setattr(oc, "_tuik_veri", lambda i: _tufe({"2099-01": 501.0, "2099-02": 510.25, "2099-03": 520.5}))
    try:
        r = oc.cek(db, "tufe")
        assert r["eklenen"] == 2 and r["son_donem"] == "2099-03" and r["farkli"] == ["2099-01"]
        assert float(db.execute(text("SELECT endeks FROM tufe_endeksi WHERE donem = '2099-01'")).scalar()) == 500.0
        assert float(db.execute(text("SELECT yillik_degisim FROM tufe_endeksi WHERE donem = '2099-03'")).scalar()) == 30.5
        assert oc.cek(db, "tufe")["eklenen"] == 0
    finally:
        db.execute(text("DELETE FROM tufe_endeksi WHERE donem >= '2099-01'"))
        db.commit()


def test_bicim_degisirse_anlasilir_hata(monkeypatch):
    from app.core import otomatik_cekme as oc
    j = _tufe({"2099-01": 1.0})
    j["id"] = [d for d in j["id"] if d != "DEGISIM"]
    monkeypatch.setattr(oc, "_tuik_veri", lambda i: j)
    with pytest.raises(oc.CekmeHatasi, match="biçimi değişmiş"):
        oc.tufe_cek(None)


def test_desteklenmeyen_kaynak_nedenini_soyler():
    from app.core import otomatik_cekme as oc
    with pytest.raises(oc.CekmeHatasi, match="TÜRK-İŞ"):
        oc.cek(None, "yasam_giderleri")


@db_gerekli
def test_istihdam_onceki_eslesmeyi_korur_oneriyi_baglamaz(db, istemci, kisiler, monkeypatch):
    from app.core import otomatik_cekme as oc
    ek = uuid.uuid4().hex[:5].upper()
    a, b = f"OTO BÖLÜM {ek}", f"ELLE BÖLÜM {ek}"
    bid_a = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda') RETURNING id"), {"a": a}).scalar()
    bid_b = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda') RETURNING id"), {"a": b}).scalar()
    # Geçen yıl yönetici "Farklı adlı program"ı elle B bölümüne bağlamış
    db.execute(text("INSERT INTO istihdam_gostergeleri (bolum_id, program_adi_kaynak, duzey, istihdam_orani, veri_yili, kaynak) "
                    "VALUES (:b, :p, 'lisans', 50, 2096, 'test')"), {"b": bid_b, "p": f"Farklı adlı program {ek}"})
    db.commit()
    prog = [f"Oto bölüm {ek}", f"Farklı adlı program {ek}", f"Hiç benzemeyen xq{ek}"]
    kod = ["_T", "L1", "L2", "L3"]
    et = {"_T": "Toplam", "L1": prog[0], "L2": prog[1], "L3": prog[2]}

    def tablo(i):
        b_ = [("REF_AREA", ["TR"], None), ("FREQ", ["A"], None), ("INDICATOR", ["X"], None), ("BOLUM", kod, et),
              ("TIME_PERIOD", ["2096", "2097"], None)]
        deg = {"DF_LM_KIO_BOLUM": "81.25", "DF_LM_B_IIB_SURE": "9.5", "DF_LSNS_MEZ_BOL_AOK": "4"}[i]
        return _jsonstat(b_, {("TR", "A", "X", k, "2097"): deg for k in kod})
    monkeypatch.setattr(oc, "_tuik_veri", tablo)
    try:
        r = istemci.post("/admin/veri-kaynaklari/tuik_istihdam/otomatik-cek", headers=kisiler["super"])
        assert r.status_code == 200, r.text
        rows = {x.program_adi_kaynak: x for x in db.execute(text(
            "SELECT program_adi_kaynak, bolum_id, istihdam_orani, is_bulma_suresi_ay, kazanc_grubu FROM istihdam_gostergeleri "
            "WHERE veri_yili = 2097")).all()}
        assert rows[prog[0]].bolum_id == bid_a, "kesin eşleşme bağlanır"
        assert rows[prog[1]].bolum_id == bid_b, "önceki yılın elle bağlantısı korunur"
        assert rows[prog[2]].bolum_id is None
        assert float(rows[prog[0]].istihdam_orani) == 81.25 and rows[prog[0]].kazanc_grubu == "yuksek"
        assert "Toplam" not in rows
        k = db.execute(text("SELECT sonuc, notlar FROM veri_kaynagi_kontrolleri WHERE kaynak_kodu = 'tuik_istihdam' ORDER BY id DESC LIMIT 1")).first()
        assert k.sonuc == "guncellendi" and k.notlar.startswith("Otomatik çekildi")
    finally:
        db.execute(text("DELETE FROM istihdam_gostergeleri WHERE veri_yili IN (2096, 2097)"))
        db.commit()


@db_gerekli
def test_hata_422_ve_veri_yazilmaz(istemci, kisiler, monkeypatch):
    from app.core import otomatik_cekme as oc

    def bozuk(i):
        raise oc.CekmeHatasi("TÜİK sunucusuna bağlanılamadı (deneme).")
    monkeypatch.setattr(oc, "_tuik_veri", bozuk)
    r = istemci.post("/admin/veri-kaynaklari/tufe/otomatik-cek", headers=kisiler["super"])
    assert r.status_code == 422 and "bağlanılamadı" in r.json()["detail"]
    r = istemci.post("/admin/veri-kaynaklari/kamu_maaslari/otomatik-cek", headers=kisiler["super"])
    assert r.status_code == 422 and "Otomatik çekme yok" in r.json()["detail"]
    assert istemci.get("/admin/veri-kaynaklari", headers=kisiler["super"]).json()["kaynaklar"][0].get("otomatik_cekme") is not None
