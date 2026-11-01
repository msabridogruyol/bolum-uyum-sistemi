"""[2026-10-13] İş Hayatı → Mülakat Simülasyonu: içerik bütünlüğü (veritabansız) ve uçlar (PostgreSQL)."""
import json
import re
from pathlib import Path

from sqlalchemy import text

from tests.conftest import db_gerekli

VERI = json.loads((Path(__file__).resolve().parents[1] / "app/data/mulakat_simulasyonu.json").read_text("utf-8"))["bolumler"]
AD = "BİLGİSAYAR MÜHENDİSLİĞİ"


def test_icerik_her_bolumde_dort_soru_ve_iki_aday():
    assert len(VERI) >= 255   # [2026-10-18] 301 → 278 (birleştirme); [2026-10-29] 278 → 266 (0082); [2026-11-01] → 262 (0086)
    ilk = ikinci = 0
    for ad, b in VERI.items():
        assert b["mulakatci"].strip() and b["pozisyon"].strip(), ad
        assert len(b["sorular"]) == 4, ad
        assert sum(q["tur"] == "ikisi_de" for q in b["sorular"]) <= 1, ad
        for q in b["sorular"]:
            assert q["soru"].strip() and q["ders"].strip() and len(q["adaylar"]) == 2, ad
            iyi = [a["iyi"] for a in q["adaylar"]]
            if q["tur"] == "dogru":
                assert sum(iyi) == 1, (ad, q["konu"])
                ilk += iyi[0]
                ikinci += iyi[1]
            else:
                assert all(iyi) and all(a.get("sonuc") for a in q["adaylar"]), (ad, q["konu"])
            metin = json.dumps(q, ensure_ascii=False)
            assert not re.search(r"yapay zek|filizyol", metin, re.I), (ad, q["konu"])
    # iyi aday her zaman aynı tarafta olmasın (öğrenci konuma bakarak tahmin edemesin)
    assert 0.4 <= ilk / (ilk + ikinci) <= 0.6


def _ogrenci_ve_bolum(db):
    import uuid
    from app.core.security import erisim_tokeni_uret
    b = db.execute(text("SELECT id FROM bolumler WHERE ad = :a"), {"a": AD}).scalar()
    if b is None:
        b = db.execute(text("""INSERT INTO bolumler (ad, durum, detay, olusturulma_zamani)
                               VALUES (:a, 'yayinda', '{}'::jsonb, now()) RETURNING id"""), {"a": AD}).scalar()
    else:
        db.execute(text("UPDATE bolumler SET durum = 'yayinda' WHERE id = :b"), {"b": b})
    okul = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"MS {uuid.uuid4().hex[:6]}"}).scalar()
    oid = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'MS Öğrenci', :e, 'x', :o, now(), now())"""), {"i": oid, "e": f"{oid.hex[:8]}@ms-test.invalid", "o": okul})
    db.commit()
    return b, oid, {"Authorization": f"Bearer {erisim_tokeni_uret(oid, 'ogrenci')}"}


@db_gerekli
def test_uclar_soru_getirir_secimleri_kaydeder_ve_ozet_doner(istemci, db):
    b, oid, baslik = _ogrenci_ve_bolum(db)
    r = istemci.get(f"/ogrenci/is-hayati/mulakat-sim/{b}", headers=baslik)
    assert r.status_code == 200, r.text
    v = r.json()
    assert v["bolum"]["ad"] == AD and len(v["sorular"]) == 4 and v["mulakatci"]
    # her soruda iyi adayı seç → dogru = toplam
    secim = {str(q["no"]): next(i for i, a in enumerate(q["adaylar"]) if a["iyi"]) for q in v["sorular"]}
    r = istemci.post("/ogrenci/is-hayati/mulakat-sim", headers=baslik, json={"bolum_id": b, "secimler": secim})
    assert r.status_code == 200, r.text
    o = r.json()
    assert o["dogru"] == o["toplam"] and o["toplam"] + o["ikisi_de"] == 4 and o["yorum"]
    assert db.execute(text("SELECT count(*) FROM is_hayati_mulakat_sim WHERE ogrenci_id = :o"), {"o": oid}).scalar() == 1
    assert istemci.get(f"/ogrenci/is-hayati/mulakat-sim/{b}", headers=baslik).json()["son"][0]["dogru"] == o["dogru"]
    # boş seçim reddedilir
    assert istemci.post("/ogrenci/is-hayati/mulakat-sim", headers=baslik, json={"bolum_id": b, "secimler": {}}).status_code == 400
