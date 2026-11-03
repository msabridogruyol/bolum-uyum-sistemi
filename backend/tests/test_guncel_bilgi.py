"""[2026-11-03] Bilgi denetimi: ekranlara ve raporlara giden sistem bilgileri güncel işleyişle aynı olmalı.

* K5 katmanının adı "İş türü tercihleri" (eski "Dal Derinleşme Modülü" değil) — öğrenci ekranı ve Cevap Analizi bu adı gösterir.
* Hiçbir hesapta okunmayan eski parametreler Parametreler ekranında görünmez.
* K5 adımının kaydı (K5N) yönetim ekranında "kullanım dışı" görünmez.
* Kaynakça ve Sistem Hakkında metinlerinde kaldırılmış K5 / sıralama mekanizmaları güncelmiş gibi anlatılmaz.
* Filiz yeni değerlendirme turunun zamanını öğrencinin gerçek durumundan söyler (sabit "3 ay" değil)."""
import json
import re
from pathlib import Path

from sqlalchemy import text

from tests.conftest import db_gerekli

KOK = Path(__file__).resolve().parents[1]
ESKI_PARAMETRELER = ("k5_esik_puani", "k5_max_dal_sayisi", "yakinsama_esik_sigma", "yeniden_degerlendirme_min_gun")


def _gocu_uygula(db):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for k in _komutlar(_sql_oku("0092_guncel_adlar")):
        db.execute(text(k))


@db_gerekli
def test_k5_adi_ve_eski_parametreler(db):
    db.execute(text("UPDATE katmanlar SET ad = 'Dal Derinleşme Modülü' WHERE kod = 'K5'"))
    db.execute(text("""INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
                       SELECT 'k5_esik_puani', '80', 'eski', now()
                       WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'k5_esik_puani')"""))
    _gocu_uygula(db)
    assert db.execute(text("SELECT ad FROM katmanlar WHERE kod = 'K5'")).scalar() == "İş türü tercihleri"
    assert db.execute(text("SELECT count(*) FROM sistem_parametreleri WHERE anahtar = ANY(:a)"),
                      {"a": list(ESKI_PARAMETRELER)}).scalar() == 0
    # yönetici adı değiştirdiyse göç ezmez
    db.execute(text("UPDATE katmanlar SET ad = 'Okulumuzun K5 adı' WHERE kod = 'K5'"))
    _gocu_uygula(db)
    assert db.execute(text("SELECT ad FROM katmanlar WHERE kod = 'K5'")).scalar() == "Okulumuzun K5 adı"
    db.rollback()


def test_eski_parametreler_kodda_okunmuyor():
    for yol in (KOK / "app").rglob("*.py"):
        metin = yol.read_text(encoding="utf-8")
        for p in ESKI_PARAMETRELER:
            okuma = re.search(rf"parametre_oku\([^)]*['\"]{p}['\"]", metin)
            assert not okuma, f"{yol}: {p} yeniden okunuyorsa 0092 göçü onu silmemeli"


@db_gerekli
def test_k5_adimi_yonetimde_kullanimda(istemci, kisiler):
    liste = istemci.get("/admin/sorular-detay/dallar-detay", headers=kisiler["super"]).json()
    k5 = [d for d in liste if d["kod"] == "K5N"]
    assert k5 and k5[0]["kullanimda"] is True


def test_kaynakca_ve_sistem_hakkinda_guncel():
    B = json.loads((KOK / "app" / "data" / "kaynakca.json").read_text(encoding="utf-8"))["bilesenler"]
    gorunen = " ".join(str(b.get(a) or "") for b in B for a in ("ne", "ne_o", "not"))
    gorunen += " ".join(str(k.get(a) or "") for b in B for k in b.get("k", []) for a in ("destek", "destek_o"))
    for eski in ("1–2 alanın", "derinleşme katmanı", "alan soruları üzerinden", "birbirine yakın alanları birlikte gruplayan",
                 "266 bölüm", "1.204 soru", "≈3 dk/alan", "K5 derinleşmesi"):
        assert eski not in gorunen, eski
    sh = (KOK.parent / "frontend" / "src" / "pages" / "admin" / "SistemHakkindaSayfasi.jsx").read_text(encoding="utf-8")
    for eski in ("Pipeline betikleri bu kod deposunda değildir", "K1-K3 %20, K4 %40'tır", "19 seçilebilir modül",
                 "TAMAMEN KURAL TABANLI", "(pipeline a8) bekliyor", "en az 1 standart sapma"):
        assert eski not in sh, eski
    dallar = (KOK.parent / "frontend" / "src" / "pages" / "admin" / "DallarSayfasi.jsx").read_text(encoding="utf-8")
    assert "K4 sonucuna göre" not in dallar


@db_gerekli
def test_filiz_yeni_tur_zamani_gercek_durumdan(db, kisiler):
    from app.core.filiz_rehber import _yeni_tur_cumlesi

    class B:
        pass
    b = B()
    b.db = db
    from app.models import Ogrenci
    b.o = db.query(Ogrenci).filter(Ogrenci.okul_id == kisiler["okul_a"]).first()
    cumle = _yeni_tur_cumlesi(b)
    assert "3 ay" not in cumle and cumle
