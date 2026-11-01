"""
[2026-10-18] Yeni K5 (iş türü kapıştırma) ve yeni soru tipleri.

Birim: soru planı (deterministik, dengeli, kapıştırma çiftleri), bölüm K5 puanı (güven), küme içi yeniden sıralama
(yuvalar), puanlama (tek seçim, uçlar). Veritabanı: uçtan uca akış (K1-K4 → küme → öğrenciye özel sorular → K5 puanı),
soru bankası listelerinin öğrenciye özel soruları dışlaması, katman tekrarında K5'in sıfırlanması, öğrenci API'si.
"""
import math
from collections import Counter
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


# --------------------------------------------------------------------------------------------- birim
def _ornek(n_bolum=12, n_eksen=14, tohum=3):
    import random
    r = random.Random(tohum)
    kume = [(100 + i, 100 - 2.5 * i) for i in range(n_bolum)]
    eksenler = list(range(1, n_eksen + 1))
    baglar = {b: {e: round(r.uniform(0.3, 1.0), 2) for e in r.sample(eksenler, r.choice((1, 2, 3)))} for b, _ in kume}
    cumleler = {e: [f"cumle {e}.{i}" for i in range(3)] for e in eksenler}
    kokler = {"encok": [f"en çok kök {i}" for i in range(8)], "tek": [f"tek kök {i}" for i in range(4)],
              "kutup": [f"uç kök {i}" for i in range(8)]}
    return kume, baglar, cumleler, kokler


def test_soru_plani_deterministik_ve_dengeli():
    from app.core import dal_servisi as ds
    kume, baglar, cumleler, kokler = _ornek()
    p1 = ds.soru_plani(kume, baglar, cumleler, kokler, tohum=77)
    p2 = ds.soru_plani(kume, baglar, cumleler, kokler, tohum=77)
    assert p1 == p2, "aynı tur (tohum) aynı soruları üretmeli"
    eksen_sayisi = len({e for b, _ in kume for e in baglar[b]})
    nq = min(ds.SORU_EN_FAZLA, max(ds.SORU_EN_AZ, math.ceil(eksen_sayisi * 3 / 4)))
    assert len(p1) == nq
    tipler = Counter(p["tip"] for p in p1)
    assert tipler["tek"] == round(nq * ds.PAY_TEK)
    assert tipler["kutup"] <= round(nq * ds.PAY_UCLAR)
    for p in p1:
        idler = [e for e, _ in p["secenekler"]]
        assert len(idler) == len(set(idler)), "bir soruda aynı iş türü iki kez olmamalı"
        assert len(idler) == (2 if p["tip"] == "kutup" else min(4, eksen_sayisi))
        assert all(m in cumleler[e] for e, m in p["secenekler"])
        assert p["kok"] in kokler[p["tip"]]
    # tarama soruları (en çok / tek) iş türlerini dengeli gösterir
    say = Counter(e for p in p1 if p["tip"] != "kutup" for e, _ in p["secenekler"])
    assert max(say.values()) - min(say.values()) <= 1 or len(say) < eksen_sayisi


def test_soru_plani_kapistirma_en_yakin_bolumlerin_ana_isleri():
    from app.core import dal_servisi as ds
    kume = [(1, 90.0), (2, 89.0), (3, 80.0), (4, 70.0)]
    baglar = {1: {11: 1.0, 12: 0.4}, 2: {21: 0.9}, 3: {31: 1.0}, 4: {41: 1.0, 11: 0.3}}
    cumleler = {e: [f"c{e}a", f"c{e}b", f"c{e}c"] for e in (11, 12, 21, 31, 41)}
    kokler = {"encok": ["k"], "tek": ["t"], "kutup": ["u"]}
    plan = ds.soru_plani(kume, baglar, cumleler, kokler, tohum=5)
    uclar = [frozenset(e for e, _ in p["secenekler"]) for p in plan if p["tip"] == "kutup"]
    assert uclar, "kapıştırma sorusu üretilmeli"
    assert uclar[0] == frozenset((11, 21)), "ilk kapıştırma K1-K4'te birbirine en yakın iki bölümün (90 / 89) ana işleri"
    assert len(uclar) == len(set(uclar)), "aynı çift iki kez sorulmaz"


def test_soru_plani_yetersiz_is_turu():
    from app.core import dal_servisi as ds
    assert ds.soru_plani([(1, 90.0)], {1: {5: 1.0}}, {5: ["a", "b", "c"]}, {"encok": ["k"], "tek": ["t"], "kutup": ["u"]}, 1) == []


def test_bolum_k5_puani_guven_ve_bag_agirligi():
    from app.core import dal_servisi as ds
    baglar = {1: {10: 1.0, 20: 0.5}, 2: {30: 1.0}, 3: {}}
    duz = ds.bolum_k5_puanlari([1, 2, 3], baglar, {10: 50.0, 20: 50.0, 30: 50.0})
    assert duz == {1: 50.0, 2: 50.0, 3: 50.0}
    p = {10: 100.0, 20: 40.0, 30: 0.0}   # std ≈ 41 ≥ 15 → güven 1
    k5 = ds.bolum_k5_puanlari([1, 2, 3], baglar, p)
    assert k5[1] == pytest.approx((100 * 1.0 + 40 * 0.5) / 1.5, abs=0.01)
    assert k5[2] == 0.0 and k5[3] == 50.0
    az = ds.bolum_k5_puanlari([2], baglar, {30: 44.0, 10: 56.0})   # std 6 → güven 0,4
    assert az[2] == pytest.approx(50 + 0.4 * (44 - 50), abs=0.01)


def test_k5_nihai_kume_ici_yuvalar():
    from app.core.skor_motoru import K5_SIRALAMA_ETKISI, k5_nihai
    toplam = {1: 95.0, 2: 90.0, 3: 88.0, 4: 60.0}
    k5 = {1: 20.0, 2: 50.0, 3: 100.0}
    n = k5_nihai(toplam, k5)
    assert n[4] == 60.0, "kümenin dışı değişmez"
    # ölçütler: 1 → 95 − 4,5 = 90,5; 2 → 90; 3 → 88 + 7,5 = 95,5
    assert sorted((b for b in k5), key=lambda b: -n[b]) == [3, 1, 2]
    assert sorted(n[b] for b in k5) == sorted(toplam[b] for b in k5), "küme kendi yuvalarını paylaşır"
    assert K5_SIRALAMA_ETKISI == 0.15
    assert k5_nihai(toplam, {1: 100.0}) == toplam, "tek bölümlük kümede sıralanacak bir şey yok"


def test_k5_nihai_esit_yuva_sirayi_korur():
    from app.core.skor_motoru import k5_nihai
    n = k5_nihai({1: 80.0, 2: 80.0}, {1: 40.0, 2: 90.0})
    assert n[2] > n[1] and n[2] == 80.0 and n[1] == pytest.approx(79.999)


def _puanla(soru, secenekler, agirlik, cevap):
    from app.core.katman_servisi import cevaplari_puanla
    onb = {"secenek": {s.id: s for s in secenekler}, "soru_secenekleri": {soru.id: secenekler},
           "agirlik": {s.id: [SimpleNamespace(degisken_id=d, agirlik=1)] for s, d in zip(secenekler, agirlik)}}
    return cevaplari_puanla(None, {soru.id: soru}, [cevap], onb)


def test_puanlama_tek_secim_ortalamasi_50():
    soru = SimpleNamespace(id=1, soru_tipi="sjt", cevap_bicimi="tek", degisken_id=None, b_ucu_degisken_id=None)
    sec = [SimpleNamespace(id=10 + i, soru_id=1, secenek_sirasi=i + 1) for i in range(4)]
    p = _puanla(soru, sec, [101, 102, 103, 104], SimpleNamespace(soru_id=1, secenek_id=12, en_az_secenek_id=None))
    assert p[103] == [100.0]
    assert all(p[d] == [pytest.approx(100 / 3)] for d in (101, 102, 104))
    assert sum(v[0] for v in p.values()) / 4 == pytest.approx(50.0)


def test_puanlama_uclar():
    soru = SimpleNamespace(id=2, soru_tipi="kutup", cevap_bicimi="tek", degisken_id=7, b_ucu_degisken_id=8)
    sec = [SimpleNamespace(id=20 + i, soru_id=2, secenek_sirasi=i + 1) for i in range(4)]
    from app.core.katman_servisi import cevaplari_puanla
    onb = {"secenek": {s.id: s for s in sec}, "soru_secenekleri": {2: sec}, "agirlik": {}}
    p = cevaplari_puanla(None, {2: soru}, [SimpleNamespace(soru_id=2, secenek_id=21, en_az_secenek_id=None)], onb)
    assert p[7] == [pytest.approx(200 / 3)] and p[8] == [pytest.approx(100 / 3)]


def test_kutup_secenek_sirasi_puanlamayla_uyumlu():
    """Göç ve üretici aynı sabit sırayı kullanır: 1. şık A ucunu, 4. şık B ucunu tam destekler."""
    from app.core.dal_servisi import KUTUP_SECENEKLERI
    assert KUTUP_SECENEKLERI[0].endswith("A") and KUTUP_SECENEKLERI[-1].endswith("B") and len(KUTUP_SECENEKLERI) == 4


def test_soru_veri_dosyalari_tutarli():
    import json
    from pathlib import Path
    kok = Path(__file__).resolve().parents[1] / "app" / "data"
    s = json.loads((kok / "olcme_sorulari.json").read_text(encoding="utf-8"))["sorular"]
    assert len(s) == 60
    assert Counter((x["katman"], x["tip"]) for x in s) == Counter(
        {(k, t): n for k in ("K1", "K2", "K3", "K4") for t, n in (("encok", 8), ("tek", 3), ("kutup", 4))})
    for x in s:
        if x["tip"] == "kutup":
            assert x["a"] != x["b"] and x["uc_a"].strip() and x["uc_b"].strip()
        else:
            assert len(x["secenekler"]) == 4 and len({o["degisken"] for o in x["secenekler"]}) == 4
            assert all(o["degisken"][0] == {"K1": "D", "K2": "P", "K3": "I", "K4": "A"}[x["katman"]] for o in x["secenekler"])
    b = json.loads((kok / "k5_soru_bankasi.json").read_text(encoding="utf-8"))
    assert len(b["cumleler"]) == 129 and all(len(v) == 3 and len(set(v)) == 3 for v in b["cumleler"].values())
    tum = [c for v in b["cumleler"].values() for c in v]
    assert len(tum) == len(set(tum)), "aynı cümle iki iş türünde olmamalı"


# --------------------------------------------------------------------------------------------- veritabanı
def _ogrenci(db, kisiler):
    from app.models import Ogrenci
    oid = db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": kisiler["okul_a"]}).scalar()
    return db.get(Ogrenci, oid)


def _hedef_bolum(db):
    return db.execute(text("""SELECT b.bolum_id FROM bolum_k5_baglari b JOIN bolumler x ON x.id = b.bolum_id
                               WHERE x.durum = 'yayinda' GROUP BY b.bolum_id HAVING count(*) >= 2 ORDER BY b.bolum_id LIMIT 1""")).scalar()


def _k5_icerigi_var(db):
    """Uçtan uca K5 testleri gerçek içerik ister: K5N dalı, K1 soruları ve K5 bağı olan yayında bölüm."""
    return bool(db.execute(text("SELECT 1 FROM dallar WHERE kod = 'K5N'")).scalar()
                and db.execute(text("SELECT 1 FROM sorular s JOIN katmanlar k ON k.id = s.katman_id WHERE k.kod = 'K1' LIMIT 1")).scalar()
                and _hedef_bolum(db))


@pytest.fixture
def k5_tamam(db, kisiler):
    from app.core.test_hesabi_servisi import senaryo_uygula
    if not _k5_icerigi_var(db):
        pytest.skip("K5 içeriği yok (0076 uygulanmamış ya da boş test şeması: soru, bölüm, K5 bağı yok)")
    o = _ogrenci(db, kisiler)
    hedef = _hedef_bolum(db)
    senaryo_uygula(db, o, {"asama": "tamamlandi", "egilim": "bolum", "egilim_bolum_id": hedef, "tohum": 11})
    db.flush()
    tur = db.execute(text("SELECT id FROM ogrenci_degerlendirme_turu WHERE ogrenci_id = :o ORDER BY tur_no DESC LIMIT 1"),
                     {"o": o.id}).scalar()
    return o, tur, hedef


@db_gerekli
def test_uctan_uca_k5(db, k5_tamam):
    from app.core import dal_servisi as ds
    from app.core.skor_motoru import nihai_uyum_haritasi
    from app.models import OgrenciDegerlendirmeTuru
    o, tur_id, _ = k5_tamam
    tur = db.get(OgrenciDegerlendirmeTuru, tur_id)
    durum = db.execute(text("""SELECT d.durum FROM ogrenci_dal_oturumlari d JOIN dallar l ON l.id = d.dal_id
                                WHERE d.tur_id = :t AND l.kod = 'K5N'"""), {"t": tur_id}).scalar()
    assert durum == "tamamlandi"
    kume = ds.kume_sec(db, o, tur)
    assert ds.KUME_EN_AZ <= len(kume) <= ds.KUME_EN_FAZLA
    assert all(u >= ds.KUME_ESIK for _, u in kume) or len(kume) == ds.KUME_EN_AZ
    sorular = db.execute(text("SELECT id, soru_tipi, cevap_bicimi, uc_a_metni FROM sorular WHERE tur_id = :t AND ogrenci_id = :o"),
                         {"t": tur_id, "o": o.id}).all()
    assert ds.SORU_EN_AZ <= len(sorular) <= ds.SORU_EN_FAZLA
    assert {s.soru_tipi for s in sorular} <= {"sjt", "kutup"} and all(s.uc_a_metni for s in sorular if s.soru_tipi == "kutup")
    k5 = dict(db.execute(text("""SELECT u.bolum_id, u.dal_ici_uyum FROM ogrenci_dal_uyum_skorlari u JOIN dallar l ON l.id = u.dal_id
                                 WHERE u.tur_id = :t AND l.kod = 'K5N'"""), {"t": tur_id}).all())
    assert set(k5) == {b for b, _ in kume}
    toplam = dict(db.execute(text("SELECT bolum_id, toplam_uyum FROM ogrenci_bolum_uyum_skorlari WHERE tur_id = :t"), {"t": tur_id}).all())
    nihai = nihai_uyum_haritasi(db, o, tur)
    disarida = [b for b in toplam if b not in k5]
    assert all(nihai[b] == float(toplam[b]) for b in disarida), "K5 kümenin dışını değiştirmez"
    assert sorted(round(nihai[b], 1) for b in k5) == sorted(round(float(toplam[b]), 1) for b in k5)
    # idempotent: tetikleme yeni oturum / soru üretmez
    ds.k5_tetikle(db, o, tur)
    assert db.execute(text("SELECT count(*) FROM sorular WHERE tur_id = :t"), {"t": tur_id}).scalar() == len(sorular)


@db_gerekli
def test_ogrenciye_ozel_sorular_bankada_gorunmez(db, istemci, kisiler, k5_tamam):
    _, tur_id, _ = k5_tamam
    ozel = {r[0] for r in db.execute(text("SELECT id FROM sorular WHERE tur_id = :t"), {"t": tur_id}).all()}
    db.commit()
    r = istemci.get("/admin/sorular", headers=kisiler["super"], params={"katman_kod": "K5"})
    assert r.status_code == 200, r.text
    assert not ozel & {s["id"] for s in r.json()}
    r = istemci.get("/admin/sorular-detay/k5-bankasi", headers=kisiler["super"])
    assert r.status_code == 200 and len(r.json()["is_turleri"]) == 129


@db_gerekli
def test_katman_tekrari_k5i_sifirlar(db, k5_tamam):
    from app.core.katman_servisi import katmani_tekrara_ac
    from app.models import Katman, OgrenciDegerlendirmeTuru
    o, tur_id, _ = k5_tamam
    katmani_tekrara_ac(db, o, db.get(OgrenciDegerlendirmeTuru, tur_id), db.query(Katman).filter(Katman.kod == "K2").one())
    db.flush()
    assert db.execute(text("SELECT count(*) FROM sorular WHERE tur_id = :t"), {"t": tur_id}).scalar() == 0
    assert db.execute(text("""SELECT count(*) FROM ogrenci_dal_oturumlari d JOIN dallar l ON l.id = d.dal_id
                               WHERE d.tur_id = :t AND l.kod = 'K5N'"""), {"t": tur_id}).scalar() == 0
    assert db.execute(text("""SELECT count(*) FROM ogrenci_degisken_skorlari s JOIN degiskenler v ON v.id = s.degisken_id
                               WHERE s.tur_id = :t AND v.dal_id IS NOT NULL"""), {"t": tur_id}).scalar() == 0


@db_gerekli
def test_tur_silinince_ozel_sorular_da_silinir(db, k5_tamam):
    _, tur_id, _ = k5_tamam
    db.execute(text("DELETE FROM ogrenci_degerlendirme_turu WHERE id = :t"), {"t": tur_id})
    db.flush()
    assert db.execute(text("SELECT count(*) FROM sorular WHERE tur_id = :t"), {"t": tur_id}).scalar() == 0


@db_gerekli
def test_ogrenci_api_uclar_ve_k5_akisi(db, istemci, kisiler):
    """Öğrenci API'si: uçlar sorusunda iki uç metni gelir; K1-K4 bitince tek K5 adımı açılır ve soruları öğrenciye özeldir."""
    if not _k5_icerigi_var(db):
        pytest.skip("K5 içeriği yok (0076 uygulanmamış ya da boş test şeması: soru, bölüm, K5 bağı yok)")
    h = kisiler["ogrenci"]
    for kod in ("K1", "K2", "K3", "K4"):
        r = istemci.post(f"/ogrenci/katmanlar/{kod}/basla", headers=h)
        assert r.status_code == 200, r.text
        sorular = r.json()["sorular"]
        beklenen = db.execute(text("SELECT count(*) FROM sorular s JOIN katmanlar k ON k.id = s.katman_id WHERE k.kod = :k "
                                   "AND s.aktif_mi AND s.ogrenci_id IS NULL"), {"k": kod}).scalar()
        assert len(sorular) == beklenen >= 15      # 0076: 15; 0081 sonrası 20-23 (dikkat soruları dahil)
        for s in sorular:
            if s["soru_tipi"] == "kutup":
                assert s["uc_a_metni"] and s["uc_b_metni"] and [x["secenek_metni"] for x in s["secenekler"]][0] == "Kesinlikle A"
            sec = s["secenekler"]
            istek = {"soru_id": s["id"], "secenek_id": sec[(s["id"] * 7) % len(sec)]["id"]}
            if s["cevap_bicimi"] == "encok_enaz":
                istek["en_az_secenek_id"] = sec[(s["id"] * 7 + 1) % len(sec)]["id"]
            assert istemci.post(f"/ogrenci/katmanlar/{kod}/cevap", headers=h, json=istek).status_code == 204
        r = istemci.post(f"/ogrenci/katmanlar/{kod}/tamamla", headers=h)
        assert r.status_code == 200, r.text
    d = istemci.get("/ogrenci/k5/durum", headers=h).json()
    assert [a["dal_kodu"] for a in d["acilan"]] == ["K5N"] and d["acilan"][0]["durum"] == "baslamadi"
    r = istemci.post("/ogrenci/dallar/K5N/basla", headers=h)
    assert r.status_code == 200, r.text
    k5 = r.json()["sorular"]
    assert 6 <= len(k5) <= 15
    for s in k5:
        sec = s["secenekler"]
        istek = {"soru_id": s["id"], "secenek_id": sec[0]["id"]}
        if s["cevap_bicimi"] == "encok_enaz":
            istek["en_az_secenek_id"] = sec[1]["id"]
        assert istemci.post("/ogrenci/dallar/K5N/cevap", headers=h, json=istek).status_code == 204
    r = istemci.post("/ogrenci/dallar/K5N/tamamla", headers=h)
    assert r.status_code == 200, r.text
    kat = {k["kod"]: k["durum"] for k in istemci.get("/ogrenci/katmanlar", headers=h).json()}
    assert kat["K5"] == "tamamlandi"
    r = istemci.get("/ogrenci/katmanlar/K5/sonuc", headers=h).json()
    assert r["tamamlandi_mi"] and r["sonuclar"]


@db_gerekli
def test_basla_oturumu_kilitler(db, kisiler):
    """Eşzamanlı iki 'başla' isteği soruları iki kez üretmesin: K5 oturumu satır kilidiyle (FOR UPDATE) okunur.
    (Gerçek eşzamanlı istek denemesi yerel sunucuda ayrıca yapıldı: 2 paralel istek → 1 soru seti.)"""
    from sqlalchemy import event
    from app.core import dal_servisi as ds
    from app.core.test_hesabi_servisi import senaryo_uygula
    from app.models import OgrenciDegerlendirmeTuru
    if not _k5_icerigi_var(db):
        pytest.skip("K5 içeriği yok (0076 uygulanmamış ya da boş test şeması: soru, bölüm, K5 bağı yok)")
    o = _ogrenci(db, kisiler)
    senaryo_uygula(db, o, {"asama": "k5_bekliyor", "egilim": "bolum", "egilim_bolum_id": _hedef_bolum(db), "tohum": 3})
    db.flush()
    tur = db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id).one()
    sql = []
    baglanti = db.connection()
    event.listen(baglanti, "before_cursor_execute", lambda *a: sql.append(a[2]))
    _, sorular = ds.dal_oturumu_baslat(db, o, ds.k5_dali(db), tur)
    _, tekrar = ds.dal_oturumu_baslat(db, o, ds.k5_dali(db), tur)
    assert any("FOR UPDATE" in q for q in sql)
    assert [s.id for s in sorular] == [s.id for s in tekrar], "ikinci çağrı yeni soru üretmez"


def test_goc_sql_uretimi_ve_veri_dosyalari():
    """0076-0078 göçlerinin SQL'i üretilebilmeli; sema_guncelleme ';\\n' ile böldüğünde DO blokları bölünmemeli."""
    import importlib.util
    import json
    from pathlib import Path
    kok = Path(__file__).resolve().parents[1]
    for ad in ("0076_yeni_k5_sorular", "0077_bolum_kisa_aciklama", "0078_bolum_icerik_duzeltme"):
        spec = importlib.util.spec_from_file_location(ad, kok / "alembic" / "versions" / f"{ad}.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        for komut in [k for k in m.SQL.split(";\n") if k.strip()]:
            assert komut.count("$$") % 2 == 0 and komut.count("$j$") % 2 == 0, (ad, komut[:80])
    d = json.loads((kok / "app" / "data" / "bolum_detay_duzeltme.json").read_text(encoding="utf-8"))["duzeltmeler"]
    assert d and all(x["eski"] != x["yeni"] and x["yol"] and x["bolum"] for x in d)
    a = json.loads((kok / "app" / "data" / "bolum_kisa_aciklama.json").read_text(encoding="utf-8"))["bolumler"]
    assert len(a) >= 255 and all(v.strip() for v in a.values())   # [2026-10-29] 278 → 266 (0082); [2026-11-01] 266 → 262 (0086)
