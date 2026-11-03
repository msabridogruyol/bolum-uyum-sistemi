"""[2026-11-03] Kriz algılamanın iki katmanı ve okul bildirimi.

* Kural katmanı (ai_koc_servisi.kriz_mesaji_mi) → "kesin": sabit kriz cevabı; okul ayarı açıksa okul yetkilisine bildirim.
* Sınıflandırıcı (kriz_modeli) → "olası": nazik destek cevabı; bildirim yok.
* filiz_kriz_okul_bildirimi varsayılan kapalı; açıkken bildirimde mesaj içeriği yok; aynı öğrenci için 24 saatte bir."""
import json
from pathlib import Path

from sqlalchemy import text

from app.core import kriz_modeli as km
from app.core.ai_koc_servisi import DESTEK_YANITI, KRIZ_YANITI, kriz_duzeyi
from tests.conftest import db_gerekli

ORNEK = [json.loads(s) for s in (Path(__file__).parent / "veri" / "kriz_ornekleri.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
NORMAL = [s for s in (Path(__file__).resolve().parents[1] / "scripts" / "veri" / "kriz_normal_ornekler.txt")
          .read_text(encoding="utf-8").splitlines() if s.strip()]


def test_model_dosyasi_ve_ngram_kurali():
    m = km._yukle()
    assert m and 0.5 <= m["esik"] < 1 and m["en_az"] == 3 and m["en_cok"] == 5 and len(m["idf"]) > 1000
    assert km.ngramlar("Ölsem") == [" ol", "ols", "lse", "sem", "em ", " ols", "olse", "lsem", "sem ", " olse", "olsem", "lsem "], \
        "Türkçe karakter sadeleşir, sözcük boşlukla çevrilir"
    assert set(km.ngramlar("ab")) == {" ab", "ab ", " ab "}, "kısa sözcük: n-gram sözcükten uzun olamaz"


def test_iki_katman_birlikte_kriz_orneklerini_yakalar():
    kriz = [o["metin"] for o in ORNEK if o["kriz"]]
    kacan = [k for k in kriz if kriz_duzeyi(k) is None]
    assert len(kacan) <= 2, kacan


def test_normal_sorularda_alarm_cok_az():
    alarm = [s for s in NORMAL if kriz_duzeyi(s)]
    assert len(alarm) / len(NORMAL) <= 0.004, alarm[:10]
    assert not [s for s in NORMAL if kriz_duzeyi(s) == "kesin"], "normal soruda kesin kriz (sert mesaj) olmamalı"


def test_olasi_duzey_yalnizca_siniflandiricidan():
    for o in ORNEK:
        d = kriz_duzeyi(o["metin"])
        if d == "olasi":
            assert km.olasi_kriz_mi(o["metin"])


@db_gerekli
def test_kesin_krizde_okula_bildirim_icerik_paylasilmaz(istemci, kisiler, db):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for k in _komutlar(_sql_oku("0091_kriz_okul_bildirimi")):
        db.execute(text(k))
    h = kisiler["ogrenci"]
    mesaj = "Artık yaşamak istemiyorum, kimse fark etmez"

    # 1) varsayılan kapalı: kriz cevabı var, bildirim yok
    db.execute(text("UPDATE sistem_parametreleri SET deger = '' WHERE anahtar = 'filiz_kriz_okul_bildirimi'"))
    db.commit()
    ot = istemci.post("/koclugu/asistan/oturum/baslat", headers=h).json()["oturum_id"]
    r = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": mesaj}).json()
    assert r["kaynak"] == "kriz" and r["asistan_yaniti"] == KRIZ_YANITI
    say = lambda: db.execute(text("SELECT count(*) FROM bildirimler WHERE tur = 'kriz_uyarisi' AND okul_id = :o"),  # noqa: E731
                             {"o": kisiler["okul_a"]}).scalar()
    assert say() == 0

    # 2) bu okul için açık: okul yetkilisine bildirim, içerik yok; öğrenciye söylenir
    db.execute(text("UPDATE sistem_parametreleri SET deger = :d WHERE anahtar = 'filiz_kriz_okul_bildirimi'"),
               {"d": f"999999,{kisiler['okul_a']}"})
    db.commit()
    r = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": mesaj}).json()
    assert r["kaynak"] == "kriz" and r["asistan_yaniti"].startswith(KRIZ_YANITI) and "paylaşılmadı" in r["asistan_yaniti"]
    assert say() == 1
    satir = db.execute(text("SELECT baslik, metin, alici_tipi FROM bildirimler WHERE tur = 'kriz_uyarisi' AND okul_id = :o"),
                       {"o": kisiler["okul_a"]}).first()
    assert "yaşamak" not in (satir.metin + satir.baslik) and satir.alici_tipi == "yonetim"

    # 3) 24 saat içinde tekrar: yeni bildirim yok
    istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": "kendimi kestim yine"})
    assert say() == 1

    # 4) olası düzey: destek cevabı, bildirim yok
    olasi = next((o["metin"] for o in ORNEK if o["kriz"] and kriz_duzeyi(o["metin"]) == "olasi"), None)
    if olasi:
        r = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": olasi}).json()
        assert r["kaynak"] == "destek" and r["asistan_yaniti"] == DESTEK_YANITI
        assert say() == 1


@db_gerekli
def test_okulsuz_ogrencide_bildirim_yok(db):
    from app.core.kriz_bildirimi import acik_mi
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for k in _komutlar(_sql_oku("0091_kriz_okul_bildirimi")):
        db.execute(text(k))
    db.execute(text("UPDATE sistem_parametreleri SET deger = '*' WHERE anahtar = 'filiz_kriz_okul_bildirimi'"))
    assert acik_mi(db, None) is False and acik_mi(db, 12345) is True
    db.execute(text("UPDATE sistem_parametreleri SET deger = '' WHERE anahtar = 'filiz_kriz_okul_bildirimi'"))
    assert acik_mi(db, 12345) is False
