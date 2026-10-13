"""[2026-10-13] İş Hayatı → Düşünme Atölyesi: içerik bütünlüğü (veritabansız) ve uçlar (PostgreSQL)."""
import json
import re
from pathlib import Path

from sqlalchemy import text

from tests.conftest import db_gerekli
from tests.test_mulakat_simulasyonu import _ogrenci_ve_bolum

VERI = Path(__file__).resolve().parents[1] / "app/data"
ATOLYE = json.loads((VERI / "dusunme_atolyesi.json").read_text("utf-8"))["araclar"]
KODLAR = ["kok_neden", "korelasyon", "algoritma", "ikiye_bolme", "tercih_verisi", "ogrenmeyi_ogren"]


def _tek_dogru(secenekler, n=3):
    assert len(secenekler) == n and sum(bool(x["dogru"]) for x in secenekler) == 1
    assert all(x["metin"].strip() and x["aciklama"].strip() for x in secenekler)


def test_icerik_dort_arac_ve_tutarli_alistirmalar():
    assert [a["kod"] for a in ATOLYE] == KODLAR
    meslekler = set()
    for a in ATOLYE:
        for alan in ("ad", "ikon", "ozet", "dene"):
            assert a[alan].strip(), (a["kod"], alan)
        assert a["giris"]["durum"].strip() and a["arac"]["metin"].strip() and 3 <= len(a["arac"]["adimlar"]) <= 5
        _tek_dogru(a["okulda"]["secenekler"])
        _tek_dogru(a["iste"]["secenekler"])
        meslekler.add(a["iste"]["meslek"])
        al = a["alistirma"]
        if al["tur"] == "zincir":
            assert len(al["adimlar"]) == 4 and al["kok"].strip()
            for s in al["adimlar"]:
                _tek_dogru(s["secenekler"])
            assert sorted(c["tur"] for c in al["cozumler"]) == ["belirti", "kok"]
        elif al["tur"] == "iliski":
            assert len(al["vakalar"]) == 3
            dogrular = set()
            for v in al["vakalar"]:
                _tek_dogru(v["secenekler"], 4)
                assert len(v["noktalar"]) >= 6 and all(len(p) == 2 for p in v["noktalar"])
                dogrular.add(next(i for i, x in enumerate(v["secenekler"]) if x["dogru"]))
            assert len(dogrular) > 1, "üç vakanın doğru cevabı aynı türde olmamalı"
        elif al["tur"] == "siralama":
            assert len(al["adimlar"]) == 6 and len(set(al["adimlar"])) == 6
            _tek_dogru(al["eksik"]["secenekler"])
        elif al["tur"] == "veri_oku":
            assert len(al["sorular"]) == 5 and len(al["program"]["yillar"]) == 3
            for q in al["sorular"]:
                _tek_dogru(q["secenekler"])
            assert "kurgusal" in al["program"]["ad"]
        elif al["tur"] == "deney":
            kelimeler = [x["kelime"] for x in al["liste_1"] + al["liste_2"]]
            anlamlar = [x["anlam"] for x in al["liste_1"] + al["liste_2"]]
            assert len(al["liste_1"]) == len(al["liste_2"]) == 6 and len(set(kelimeler)) == 12 and len(set(anlamlar)) == 12
            assert all(eval(g["soru"].replace("×", "*").replace("÷", "/").replace("−", "-")) == g["cevap"] for g in al["ara_gorev"])  # noqa: S307
        else:
            assert al["tur"] == "sayi_bul" and al["alt"] < al["ust"]
        metin = json.dumps(a, ensure_ascii=False)
        assert not re.search(r"yapay zek|filizyol", metin, re.I)
    assert len(meslekler) >= 4


def test_mulakat_etiketleri_gecerli_arac():
    m = json.loads((VERI / "mulakat_simulasyonu.json").read_text("utf-8"))["bolumler"]
    etiketler = [q["arac"] for b in m.values() for q in b["sorular"] if q.get("arac")]
    assert etiketler and set(etiketler) <= set(KODLAR)


@db_gerekli
def test_uclar_icerik_ilerleme_ve_mulakat_baglantisi(istemci, db):
    b, oid, baslik = _ogrenci_ve_bolum(db)
    r = istemci.get(f"/ogrenci/is-hayati/dusunme?bolum_id={b}", headers=baslik)
    assert r.status_code == 200, r.text
    v = r.json()
    assert [a["kod"] for a in v["araclar"]] == KODLAR and v["ilerleme"] == {}
    assert sum(len(a["mulakat"]) for a in v["araclar"]) >= 1   # bilgisayar mühendisliğinde etiketli soru var
    for _ in range(2):
        r = istemci.post("/ogrenci/is-hayati/dusunme/kok_neden", headers=baslik, json={"ilk_dogru": 3, "ilk_toplam": 5, "okulda": True, "iste": False})
        assert r.status_code == 200, r.text
    assert r.json()["deneme"] == 2
    assert db.execute(text("SELECT count(*) FROM is_hayati_dusunme WHERE ogrenci_id = :o"), {"o": oid}).scalar() == 1
    il = istemci.get("/ogrenci/is-hayati/dusunme", headers=baslik).json()["ilerleme"]
    assert il["kok_neden"]["ilk"] == {"dogru": 3, "toplam": 5} and il["kok_neden"]["son"]["iste"] is False
    assert istemci.post("/ogrenci/is-hayati/dusunme/yok", headers=baslik, json={}).status_code == 404
    assert istemci.post("/ogrenci/is-hayati/dusunme/algoritma", headers=baslik, json={"ilk_dogru": 3, "ilk_toplam": 2}).status_code == 400
    # mülakat sorusunda araç etiketi döner
    q = istemci.get(f"/ogrenci/is-hayati/mulakat-sim/{b}", headers=baslik).json()["sorular"]
    assert any(x["arac"] and x["arac"]["kod"] in KODLAR for x in q)


@db_gerekli
def test_ogrenme_deneyi_ikinci_olcum_12_saat_sonra(istemci, db):
    _b, oid, baslik = _ogrenci_ve_bolum(db)
    url = "/ogrenci/is-hayati/dusunme-deney"
    r = istemci.post(url, headers=baslik, json={"asama": 1, "okuma": 3, "sinama": 5, "toplam": 6, "sinama_listesi": 2})
    assert r.status_code == 200, r.text
    assert r.json()["ikinci_hazir"] is False and r.json()["kalan_saat"] >= 11
    assert istemci.post(url, headers=baslik, json={"asama": 2, "okuma": 2, "sinama": 4, "toplam": 6}).status_code == 400
    db.execute(text("UPDATE is_hayati_ogrenme_deneyi SET olcum1_zamani = now() - interval '13 hours' WHERE ogrenci_id = :o"), {"o": oid})
    db.commit()
    assert istemci.get("/ogrenci/is-hayati/dusunme", headers=baslik).json()["deney"]["ikinci_hazir"] is True
    r = istemci.post(url, headers=baslik, json={"asama": 2, "okuma": 2, "sinama": 4, "toplam": 6})
    assert r.status_code == 200 and r.json()["olcum2"] == {"okuma": 2, "sinama": 4, "toplam": 6} and r.json()["sinama_listesi"] == 2
    assert istemci.post(url, headers=baslik, json={"asama": 1, "okuma": 7, "sinama": 1, "toplam": 6}).status_code == 400
    # deney yeniden yapılınca 2. ölçüm sıfırlanır
    r = istemci.post(url, headers=baslik, json={"asama": 1, "okuma": 4, "sinama": 4, "toplam": 6})
    assert r.json()["olcum2"] is None
