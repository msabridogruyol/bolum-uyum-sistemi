"""[2026-10-11] Filiz yönetim asistanı: kural tabanlı eşleştirme (veritabansız) + uç nokta kapsamı (PostgreSQL)."""
import inspect
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app.core import filiz_yonetim_rehber as R
from tests.conftest import db_gerekli

OKUL = SimpleNamespace(rol="okul_yetkilisi", okul_id=7)
SUPER = SimpleNamespace(rol="super_admin", okul_id=None)


# ----------------------------------------------------------------------------- veritabansız
def test_normalize_turkce():
    assert R.normalize("  Öğrenci ŞİFRESİ nasıl sıfırlanır?! ") == "ogrenci sifresi nasil sifirlanir"
    assert R.normalize("İSTATİSTİK") == "istatistik"


@pytest.mark.parametrize("soru,kod", [
    ("Raporu nereden alırım?", "rapor"), ("Veli raporu nasıl alınır?", "veli_rapor"), ("Öğrenci şifresi nasıl sıfırlanır?", "sifre"),
    ("Öğrenci nasıl eklenir?", "ogrenci_ekle"), ("Kritik öğrenciler nerede?", "kritik"), ("İSTATİSTİKLER", "istatistik"),
    ("Anket nasıl oluşturulur?", "anket"), ("Deneme sonucu nasıl yüklenir?", "deneme"), ("kaynakça", "kaynakca"), ("Paketimizde ne var", "paket"),
])
def test_okul_niyetleri(soru, kod):
    assert R.niyet_bul(soru, "okul_yetkilisi")[0]["k"] == kod


@pytest.mark.parametrize("soru,kod", [("Hata kayıtları nerede?", "hata"), ("TÜİK verisi nasıl güncellenir?", "tuik"),
                                      ("Pipeline taslağı", "pipeline"), ("audit log", "audit")])
def test_super_niyetleri(soru, kod):
    assert R.niyet_bul(soru, "super_admin")[0]["k"] == kod


def test_super_niyetleri_okul_yetkilisine_cikmaz():
    # [2026-11-02] Okul yetkilisine süper admin cevabı/bağlantısı çıkmaz; sistem yöneticisinin işiyse yalnızca bu söylenir
    n = R.niyet_bul("hata kayıtları", "okul_yetkilisi")
    assert [x["k"] for x in n] == ["sistem_yoneticisi"] and all(not s.startswith("/") for x in n for _, s in x["bag"])
    assert R.niyet_bul("TÜİK verisi", "okul_yetkilisi") == []


def test_ozel_kalip_once():
    assert [n["k"] for n in R.niyet_bul("veli raporu", "okul_yetkilisi")][0] == "veli_rapor"


@pytest.mark.parametrize("soru,beklenen", [
    ("sınıf öğretmenini nereye yazarım", "Sınıf öğretmenini nereye yazarım?"),
    ("güven puanı düşük", "Güven puanı nedir, düşükse ne yapmalıyım?"),
    ("aday öğrenci", "Aday öğrenci nedir?"),
    ("logo değiştirmek", "Okulumuzun rengi ve logosu nasıl değişir?"),
])
def test_sss_eslesme(soru, beklenen):
    c = R.sss_eslestir(soru, "okul_yetkilisi", 7)
    assert c and c[0]["soru"] == beklenen and len(c) <= 3


def test_sss_baglantisi_kendi_okuluna():
    c = R.sss_eslestir("öğrenci şifresini unuttu", "okul_yetkilisi", 7)[0]
    assert c["baglanti"]["yol"] == "/admin/okul/7?sekme=ogrenciler"


def test_super_admin_sistem_hakkinda_basliklari():
    c = R.sss_eslestir("uyum hesaplama nasıl yapılıyor", "super_admin")
    assert c[0]["baglanti"]["yol"] == "/admin/sistem-hakkinda#sh-4"
    assert all("#sh-" not in (x["baglanti"] or {}).get("yol", "") for x in R.sss_eslestir("uyum hesaplama", "okul_yetkilisi", 7))


def test_anlamsiz_soru_oneri_doner():
    y = R.yanitla(None, OKUL, "asdf qwer zxcv")
    assert y["tur"] == "anlamadim" and y["oneriler"] == R.ONERILER["okul_yetkilisi"] and not y["cevaplar"]


def test_yanit_baglantilari_rol_bazli():
    y = R.yanitla(None, OKUL, "veli raporu nasıl alınır")
    assert y["tur"] == "yanit" and y["baglantilar"][0]["yol"] == "/admin/okul/7?sekme=siniflar"
    y = R.yanitla(None, SUPER, "hata kayıtları nerede")
    assert y["baglantilar"][0]["yol"] == "/admin/hata-kayitlari"


def test_filiz_sss_maddesi_var():
    assert any(s == "Filiz panelde ne yapar?" for _, s, _, _ in R.YONETIM_SSS)
    assert "Rehber modu" in R.yanitla(None, OKUL, "Filiz sen kimsin?")["metin"]


def test_rehber_modulu_yapay_zeka_servisi_kullanmaz():
    """Kural tabanlı rehber yapay zekâ servisine veri göndermez (yapay zekâ modu ayrı modülde: filiz_yonetim_ai)."""
    kaynak = inspect.getsource(R)
    assert "ai_koc_servisi" not in kaynak and "openai" not in kaynak.lower()


# ----------------------------------------------------------------------------- uç noktalar (PostgreSQL)
def _kulup_talebi(db, okul_id):
    ek = uuid.uuid4().hex[:8]
    k = db.execute(text("INSERT INTO okul_kulupleri (okul_id, ad) VALUES (:o, :a) RETURNING id"), {"o": okul_id, "a": f"K {ek}"}).scalar()
    o = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Gizli Ad Soyadı', :e, 'x', :o, now(), now())"""), {"i": o, "e": f"k.{ek}@test.invalid", "o": okul_id})
    db.execute(text("INSERT INTO kulup_uyelikleri (kulup_id, ogrenci_id, durum) VALUES (:k, :o, 'bekliyor')"), {"k": k, "o": o})
    db.commit()


@db_gerekli
def test_ozet_yetkisiz_401_ogrenci_reddedilir(istemci, kisiler):
    assert istemci.get("/yonetim/filiz/ozet").status_code == 401
    assert istemci.get("/yonetim/filiz/ozet", headers=kisiler["ogrenci"]).status_code in (401, 403)
    assert istemci.post("/yonetim/filiz/sor", json={"metin": "x"}, headers=kisiler["ogrenci"]).status_code in (401, 403)


@db_gerekli
def test_ozet_yalniz_kendi_okulu_ve_isimsiz(istemci, kisiler, db):
    _kulup_talebi(db, kisiler["okul_b"])          # başka okulun talebi sayılmaz
    r = istemci.get("/yonetim/filiz/ozet", headers=kisiler["yetkili"])
    assert r.status_code == 200
    assert not any(b["k"] == "kulup" for b in r.json()["bulgular"])
    _kulup_talebi(db, kisiler["okul_a"])
    v = istemci.get("/yonetim/filiz/ozet", headers=kisiler["yetkili"]).json()
    kulup = next(b for b in v["bulgular"] if b["k"] == "kulup")
    assert kulup["metin"].startswith("1 kulüp") and kulup["baglanti"]["yol"] == f"/admin/okul/{kisiler['okul_a']}?sekme=kulupler"
    assert "Gizli" not in r.text + str(v) and "Test Öğrenci" not in str(v)
    assert v["oneriler"] == R.ONERILER["okul_yetkilisi"]


@db_gerekli
def test_filiz_zorunlu_okuldan_cikarilamaz(istemci, kisiler, db):
    """[2026-10-30] Filiz her pakette zorunlu (önceden modül kapalıysa 403 dönüyordu): okulun çıkarma listesinde olsa da açık."""
    db.execute(text("""UPDATE okullar SET modul_cikar = '["filiz"]'::jsonb WHERE id = :o"""), {"o": kisiler["okul_a"]})
    db.commit()
    assert istemci.get("/yonetim/filiz/ozet", headers=kisiler["yetkili"]).status_code == 200
    assert istemci.post("/yonetim/filiz/sor", json={"metin": "rapor"}, headers=kisiler["yetkili"]).status_code == 200
    assert istemci.get("/yonetim/filiz/sss", headers=kisiler["yetkili"]).status_code == 200   # SSS sayfası Filiz'e bağlı değil


@db_gerekli
def test_super_admin_ozet_ve_sor(istemci, kisiler):
    r = istemci.get("/yonetim/filiz/ozet", headers=kisiler["super"])
    assert r.status_code == 200 and r.json()["rol"] == "super_admin"
    for b in r.json()["bulgular"]:
        assert b["baglanti"]["yol"].startswith("/admin")
    y = istemci.post("/yonetim/filiz/sor", json={"metin": "bugün ne var?"}, headers=kisiler["super"]).json()
    assert y["tur"] == "durum"
    y = istemci.post("/yonetim/filiz/sor", json={"metin": "TÜİK verisi"}, headers=kisiler["super"]).json()
    assert y["baglantilar"][0]["yol"] == "/admin/is-hayati-verileri"


@db_gerekli
def test_sor_uzun_metin_422(istemci, kisiler):
    assert istemci.post("/yonetim/filiz/sor", json={"metin": "a" * 501}, headers=kisiler["yetkili"]).status_code == 422


@db_gerekli
def test_sss_tek_kaynak(istemci, kisiler):
    v = istemci.get("/yonetim/filiz/sss", headers=kisiler["yetkili"]).json()["sss"]
    assert len(v) == len(R.YONETIM_SSS) and any(s["soru"] == "Filiz panelde ne yapar?" for s in v)
