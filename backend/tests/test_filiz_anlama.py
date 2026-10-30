"""[2026-10-31] Filiz anlama katmanı: dağınık öğrenci dilini anlama, meslek → bölüm köprüsü, karşılaştırma, netleştirme.

Birim testleri yapay bir dizinle çalışır. Ölçüm testleri gerçek bölüm içeriği gerektirir (≥ 200 bölüm): CI'daki boş
şemada atlanır, gerçek içerikli veritabanında (ör. k5test2) çalışır:
  * tests/veri/filiz_dagnik_sorular.json      — kurallar ayarlanırken kullanılan 147 soru (hedef ≥ %95)
  * tests/veri/filiz_dagnik_sorular_ayri.json — ayarlamada KULLANILMAYAN 50 soru (hedef ≥ %90)
  Her iki sette yanlış içerik ≤ %3 (yanlış bölüm/mesleği anlatmak "anlamadım" demekten kötüdür)."""
import json
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core import filiz_bilgi as fb
from tests.conftest import db_gerekli

_VERI = Path(__file__).resolve().parent / "veri"


def test_konusma_dili_ve_kisaltmalar_duzelir():
    assert fb.duzelt("avukat olcam ne okumam lazim") == "avukat olacagim ne okumam lazim"
    assert fb.duzelt("doktorlar gece de mi calisiyo") == "doktorlar gece de mi calisiyor"
    assert fb.duzelt("bil müh kaç sene") == "bilgisayar muhendisligi kac yil"
    assert fb.duzelt("bilgisayar muh zor mu") == "bilgisayar muhendisligi zor mu"
    assert fb.duzelt("ne yapcam bilmiyom") == "ne yapacagim bilmiyorum"
    assert fb.duzelt("Süspansiyon ne demek") == "suspansiyon ne demek", "isim sonu konuşma eki sanılmamalı"


def test_ek_ve_yazim_toleransi():
    assert fb._ek_toleransli("hukukta", "hukuk") and fb._ek_toleransli("psikolojiden", "psikoloji")
    assert fb._ek_toleransli("hemsireligi", "hemsirelik") and fb._ek_toleransli("psikolji", "psikoloji")
    assert fb._ek_toleransli("tipta", "tip") and not fb._ek_toleransli("tipik", "tip")
    assert not fb._ek_toleransli("yazilir", "yazilim"), "son harf değişimi yalnızca k/p/t/ç yumuşamasında"


def _dizin():
    B = fb.Belge
    belgeler = [
        B("bolum", "Hukuk bölümü", "Öğrenim süresi: 4 yıl. Puan türü: EA. Hukuk, kuralları inceler.", "Bölümler › Hukuk › Genel bakış", None, "hukuk"),
        B("bolum_ders", "Hukuk: neler öğrenilir, hangi dersler var", "Anayasa ve ceza hukuku dersleri.", "Bölümler › Hukuk › Genel bakış", None, "hukuk"),
        B("bolum_is", "Hukuk mezunları nerelerde çalışır", "Adliyeler, bürolar. Mezunların sık yaptığı meslekler: Avukat, Hakim.", "Bölümler › Hukuk › Meslekler", None, "hukuk"),
        B("meslek", "Avukat (Hukuk)", "Müvekkilini temsil eder. Nasıl olunur: Hukuk lisansı ve staj.", "Bölümler › Hukuk › Meslekler › Avukat", None, "avukat"),
        B("bolum", "İşletme bölümü", "Öğrenim süresi: 4 yıl. Puan türü: EA. İşletme, örgütleri inceler.", "Bölümler › İşletme › Genel bakış", None, "isletme"),
        B("bolum", "Biyoloji Öğretmenliği bölümü", "Öğrenim süresi: 4 yıl. Biyoloji öğretmeni yetiştirir.", "Bölümler › Biyoloji Öğretmenliği", None, "biyoloji ogretmenligi"),
        B("bolum", "Fizik Öğretmenliği bölümü", "Öğrenim süresi: 4 yıl. Fizik öğretmeni yetiştirir.", "Bölümler › Fizik Öğretmenliği", None, "fizik ogretmenligi"),
        B("bolum", "Tıp bölümü", "Öğrenim süresi: 6 yıl. Puan türü: SAY. Tıp, hekim yetiştirir.", "Bölümler › Tıp › Genel bakış", None, "tip"),
        B("bolum_ders", "Tıp: neler öğrenilir, hangi dersler var", "Anatomi, fizyoloji dersleri.", "Bölümler › Tıp › Genel bakış", None, "tip"),
    ]
    return fb.Dizin(belgeler, {"doktor": ["TIP"], "avukat": ["HUKUK"]})


def test_varlik_cozumleme_takma_ad_ve_belirsizlik():
    d = _dizin()
    assert dict(d.varliklari_coz("hukukta neler okutuluyo"))["hukuk"] == {"hukuk"}
    assert "tip" in dict(d.varliklari_coz("doktor olmak istiyom"))["doktor"]
    assert dict(d.varliklari_coz("tıpta hangi dersler var"))["tip"] == {"tip"}
    assert len(dict(d.varliklari_coz("öğretmen olmak istiyorum"))["ogretmen"]) == 2, "genel ad birden çok bölüme gider"
    assert d.meslek_bolum["avukat"] == {"hukuk"}, "meslek → bölüm köprüsü bölüm sayfasındaki meslek listesinden"


def test_meslek_yolu_karsilastirma_netlestirme(monkeypatch):
    from app.core import filiz_anlama as fa
    d = _dizin()
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    c = fa.meslek_yolu(d, "doktor olmak icin ne okumaliyim")
    assert c and c.kaynak == "icerik" and "Tıp" in c.yanit and "6 yıl" in c.yanit
    c = fa.meslek_yolu(d, "avukat olcam ne okumam lazim")
    assert c and "Hukuk" in c.yanit and "Nasıl olunur" in c.yanit
    c = fa.karsilastirma(d, "hukuk mu işletme mi")
    assert c and "Hukuk" in c.yanit and "İşletme" in c.yanit and "Karşılaştır" in c.yanit
    c = fa.meslek_yolu(d, "ögretmen olmak istiyom hangi bölüm")
    assert c and c.kaynak == "icerik" and "Biyoloji Öğretmenliği" in c.yanit or (c and c.kaynak == "netlestirme")
    c = fa.sonradan_netlestir(None, "hukuk", None)
    assert c and c.kaynak == "netlestirme" and len(c.secenekler) == 3


def test_secenek_sorulari_ayni_icerige_doner(monkeypatch):
    from app.core import filiz_anlama as fa
    d = _dizin()
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    for b in d.belgeler:
        if b.tur in ("bolum", "bolum_ders", "bolum_is"):
            c = fa.onceden_anla(None, fa.soru_sablonu(b), set()) or fa.sonradan_netlestir(None, fa.soru_sablonu(b), set())
            assert c and c.kaynak == "icerik" and b.baslik in c.yanit, (b.baslik, c and c.yanit)


def test_esanlam_hedefleri_gercek_bolum_adlari():
    ad = set(json.loads((Path(__file__).resolve().parents[1] / "app" / "data" / "mulakat_simulasyonu.json").read_text("utf-8"))["bolumler"])
    es = json.loads((Path(__file__).resolve().parents[1] / "app" / "data" / "filiz_esanlamlar.json").read_text("utf-8"))["esanlam"]
    assert es and all(h in ad for v in es.values() for h in v), [k for k, v in es.items() if any(h not in ad for h in v)]


# ------------------------------------------------------------------------------------- ölçüm (gerçek içerik)
def _olc(db, dosya, moduller):
    from app.core.filiz_rehber import katman_tahmini
    S = json.loads((_VERI / dosya).read_text("utf-8"))["sorular"]
    dogru = yanlis = 0
    for q, bek, ip in S:
        k, c = katman_tahmini(db, q, moduller)
        metin = fb.duzelt((c.yanit + " " + " ".join(c.secenekler)) if hasattr(c, "yanit") else "")
        ipucu = (not ip) or any(fb.sade(x).strip() in metin for x in ip.split("|"))
        if k in bek.split("|") and (k not in ("icerik", "netlestirme") or ipucu):
            dogru += 1
        elif k == "icerik":
            yanlis += 1
    return dogru / len(S), yanlis / len(S)


@db_gerekli
def test_dagnik_sorular_olcumu(db):
    if db.execute(text("SELECT count(*) FROM bolumler WHERE detay IS NOT NULL")).scalar() < 200:
        pytest.skip("gerçek bölüm içeriği yok (boş test şeması)")
    fb.dizini_sifirla()
    oran, yanlis = _olc(db, "filiz_dagnik_sorular.json", {"is_hayati"})
    assert oran >= 0.95 and yanlis <= 0.03, (oran, yanlis)
    oran, yanlis = _olc(db, "filiz_dagnik_sorular_ayri.json", {"is_hayati"})
    assert oran >= 0.90 and yanlis <= 0.03, (oran, yanlis)
    fb.dizini_sifirla()


# ------------------------------------------------------------------------------------- uçtan uca
def _goc(db):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for g in ("0083_filiz_her_pakette", "0084_filiz_olcum"):
        for k in _komutlar(_sql_oku(g)):
            db.execute(text(k))
    db.commit()


@db_gerekli
def test_netlestirme_secenekleri_ve_anlasilamayan_listesi(istemci, kisiler, db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    db.execute(text("""INSERT INTO bolumler (ad, kisa_aciklama, detay, durum) VALUES ('ZEYTİNCİLİK', 'Kısa',
                       CAST(:d AS jsonb), 'yayinda')"""), {"d": json.dumps({"ozet": "Zeytin yetiştiriciliği.", "ornek_dersler": ["Bağcılık"]})})
    db.commit()
    fb.dizini_sifirla()
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: False)
    h = kisiler["ogrenci"]
    ot = istemci.post("/koclugu/asistan/oturum/baslat", headers=h).json()["oturum_id"]
    r = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": "zeytincilik"}).json()
    assert r["kaynak"] in ("icerik", "netlestirme") and r["secenekler"], r   # yalnız bölüm adı: genel bilgi + seçenekler
    ders = next(o for o in r["secenekler"] if "dersler" in o)
    r2 = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": ders}).json()
    assert r2["kaynak"] == "icerik" and "Bağcılık" in r2["asistan_yaniti"], "seçenek düğmesi içeriğe götürmeli"
    istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": "qwzx ahmet@ornek.com 05551234567"})
    # Liste varsayılan kapalı
    assert istemci.get("/admin/filiz/anlasilamayan", headers=kisiler["super"]).status_code == 403
    db.execute(text("UPDATE sistem_parametreleri SET deger = '1' WHERE anahtar = 'filiz_anlasilamayan_listesi_acik'"))
    db.commit()
    v = istemci.get("/admin/filiz/anlasilamayan", headers=kisiler["super"]).json()
    metin = json.dumps(v, ensure_ascii=False)
    assert "ahmet@ornek.com" not in metin and "05551234567" not in metin and "qwzx [e-posta] [telefon]" in metin
    assert istemci.get("/admin/filiz/anlasilamayan", headers=kisiler["yetkili"]).status_code in (401, 403)
    fb.dizini_sifirla()
