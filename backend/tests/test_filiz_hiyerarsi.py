"""[2026-10-11] Filiz hiyerarşi koruması: öğrenci başka öğrencinin bilgisini alamaz; okul yetkilisi yalnızca kendi okulunu görür;
süper admin tüm sistemi görür; yapay zekâya giden yükte öğrenci adı / e-posta / TC yok. OpenAI çağrısı her yerde taklittir."""
import uuid

import pytest
from sqlalchemy import text

from app.core import filiz_gizlilik as G
from tests.conftest import db_gerekli


# ----------------------------------------------------------------------------- veritabansız
def _dizin():
    return G.AdDizini([G.OgrenciKaydi(id="1", ad_soyad="Ayşe Nur Kaya", email="ayse@x.k12.tr", ogrenci_no="77"),
                       G.OgrenciKaydi(id="2", ad_soyad="MEHMET YILMAZ")])


@pytest.mark.parametrize("soru", ["ayşe kaya'nın puanı", "AYŞE NUR KAYA nasıl", "Nur Kaya", "Mehmet Yılmazın neti", "mehmet yilmaz"])
def test_ad_dizini_turkce_duyarsiz_maskeler(soru):
    m = _dizin().maskele(soru)
    assert G.OGRENCI_ETIKETI in m and "kaya" not in m.lower() and "yılmaz" not in m.lower() and "yilmaz" not in m.lower()


def test_ad_dizini_tek_ad_ve_panel_kelimeleri_maskelenmez():
    d = _dizin()
    for t in ("Mehmet geldi", "Rapor Merkezi nerede", "İSTATİSTİKLER"):
        assert d.maskele(t) == t


def test_kendi_adi_maskelenmez():
    d = G.AdDizini([G.OgrenciKaydi(id="1", ad_soyad="Ayşe Kaya")])
    assert d.maskele("Ben Ayşe Kaya", haric=G.ad_normalize("Ayşe Kaya")) == "Ben Ayşe Kaya"


def test_temel_maskeleme():
    m = G.temel_maskele("veli@ornek.com 0532 123 45 67 12345678901 öğrenci no 123")
    assert "@" not in m and "0532" not in m and "12345678901" not in m and "123" not in m


def test_ad_benzeri_ciftler_veritabanindan_bagimsiz():
    m = G.ad_benzerlerini_maskele("Kerem Toprak'ın sonuçları, Rapor Merkezi ve Hacettepe Üniversitesi")
    assert "Kerem" not in m and "Toprak" not in m and "Rapor Merkezi" in m and "Hacettepe Üniversitesi" in m


@pytest.mark.parametrize("soru,beklenen", [
    ("Ayşe Kaya'nın puanı ne?", G.HIYERARSI_YANITI), ("arkadaşımın neti kaç", G.HIYERARSI_YANITI),
    ("sınıfımdakilerin sonuçları nasıl", G.HIYERARSI_YANITI), ("en yüksek net kimde", G.HIYERARSI_YANITI),
    ("Ayşe'nin hedefi ne", G.HIYERARSI_YANITI), ("okul ortalaması kaç", G.TOPLU_YANITI), ("sınıfta kaçıncıyım", G.TOPLU_YANITI),
    ("benim hedefim ne", None), ("Ben Can Er, sonuçlarım nasıl?", None), ("Hacettepe'nin taban puanı", None),
])
def test_ogrenci_hiyerarsi_kaliplari(soru, beklenen):
    assert G.ogrenci_hiyerarsi_yaniti(soru, _dizin(), "Can Er") == beklenen


# ----------------------------------------------------------------------------- düzenek (PostgreSQL)
def _ogrenci(db, okul_id, ad, eposta=None, no=None):
    i = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, ogrenci_no, sinif, sube, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, :a, :e, 'x', :o, :n, '11. Sınıf', 'B', now(), now())"""),
               {"i": i, "a": ad, "e": eposta or f"{uuid.uuid4().hex[:10]}@test.invalid", "o": okul_id, "n": no})
    db.commit()
    return str(i)


@pytest.fixture
def ortam(db, kisiler):
    ek = uuid.uuid4().hex[:6]
    k = dict(kisiler)
    k["zeynep_eposta"] = f"zeynep.{ek}@test.invalid"
    k["zeynep"] = _ogrenci(db, kisiler["okul_a"], "Zeynep Aksoy", k["zeynep_eposta"], "4321")
    k["kerem_eposta"] = f"kerem.{ek}@test.invalid"
    k["kerem"] = _ogrenci(db, kisiler["okul_b"], "Kerem Toprak", k["kerem_eposta"], "9876")
    return k


class SahteAI:
    def __init__(self, yanit="- Rehberlik sekmesinde görüşme kaydı açın.\nSAYFA: Rehberlik", hata=False):
        self.cagrilar, self.yanit, self.hata = [], yanit, hata

    def __call__(self, sistem, mesajlar):
        self.cagrilar.append((sistem, mesajlar))
        if self.hata:
            from app.core.ai_koc_servisi import AsistanKullanilamiyorHatasi
            raise AsistanKullanilamiyorHatasi("taklit hata")
        return self.yanit

    def yuk(self) -> str:
        return "\n".join(s + "\n" + "\n".join(m["content"] for m in ms) for s, ms in self.cagrilar)


@pytest.fixture
def ai(monkeypatch):
    """Anahtar tanımlı + OpenAI çağrısı taklit (öğrenci ve yönetim yolları)."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-taklit")
    s = SahteAI()
    monkeypatch.setattr("app.core.ai_koc_servisi.openai_ile_konus", s)
    monkeypatch.setattr("app.api.ai_koc.openai_ile_konus", s)
    return s


@pytest.fixture
def anahtarsiz(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = SahteAI()
    monkeypatch.setattr("app.core.ai_koc_servisi.openai_ile_konus", s)
    monkeypatch.setattr("app.api.ai_koc.openai_ile_konus", s)
    return s


def _ogrenci_sor(istemci, kisiler, mesaj):
    o = istemci.post("/koclugu/asistan/oturum/baslat", headers=kisiler["ogrenci"])
    assert o.status_code == 200, o.text
    r = istemci.post(f"/koclugu/asistan/oturum/{o.json()['oturum_id']}/mesaj", json={"mesaj": mesaj}, headers=kisiler["ogrenci"])
    assert r.status_code == 200, r.text
    return o.json()["oturum_id"], r.json()


def _sor(istemci, basliklar, metin, gecmis=None):
    r = istemci.post("/yonetim/filiz/sor", json={"metin": metin, "gecmis": gecmis or []}, headers=basliklar)
    assert r.status_code == 200, r.text
    return r.json()


# ----------------------------------------------------------------------------- öğrenci tarafı
@db_gerekli
@pytest.mark.parametrize("soru", ["Zeynep Aksoy'un puanı kaç?", "zeynep aksoy hangi bölümü hedefliyor", "Arkadaşımın neti kaç?",
                                  "En yüksek net kimde?"])
def test_ogrenci_baska_ogrenciyi_sorarsa_ai_cagrilmaz(istemci, ortam, ai, soru):
    _, c = _ogrenci_sor(istemci, ortam, soru)
    assert c["asistan_yaniti"] == G.HIYERARSI_YANITI and not ai.cagrilar


@db_gerekli
def test_ogrenci_kural_tabanlida_da_ret(istemci, ortam, anahtarsiz, db):
    _, c = _ogrenci_sor(istemci, ortam, "Zeynep Aksoy'un sonucu ne?")
    assert c["asistan_yaniti"] == G.HIYERARSI_YANITI and c["otomatik"] is True and not anahtarsiz.cagrilar
    from app.core.filiz_rehber import otomatik_yanit
    from app.models import Ogrenci
    ben = db.query(Ogrenci).filter(Ogrenci.okul_id == ortam["okul_a"], Ogrenci.ad_soyad == "Test Öğrenci").first()
    assert otomatik_yanit(db, ben, "arkadaşımın puanı kaç") == G.HIYERARSI_YANITI
    assert otomatik_yanit(db, ben, "okul ortalaması kaç") == G.TOPLU_YANITI


@db_gerekli
def test_ogrenci_ai_baglaminda_baska_ogrenci_adi_yok(istemci, ortam, ai, db):
    oturum, _ = _ogrenci_sor(istemci, ortam, "Merhaba")
    # Geçmişte (eski bir sürümden kalmış) başka bir öğrencinin adı geçen mesaj + e-posta: modele maskelenmiş gider
    db.execute(text("INSERT INTO ogrenci_koclugu_mesajlari (oturum_id, rol, icerik, olusturulma_zamani) VALUES (:o, 'ogrenci', :m, now())"),
               {"o": oturum, "m": f"Zeynep Aksoy ile çalışıyorum, e-postası {ortam['zeynep_eposta']}"})
    db.commit()
    ai.yanit = "Zeynep Aksoy gibi düzenli çalışabilirsin."
    r = istemci.post(f"/koclugu/asistan/oturum/{oturum}/mesaj", json={"mesaj": "Ben Test Öğrenci, bu hafta neye odaklanayım?"},
                     headers=ortam["ogrenci"]).json()
    yuk = ai.yuk()
    assert ai.cagrilar and "Zeynep" not in yuk and "Aksoy" not in yuk and "Kerem" not in yuk and ortam["zeynep_eposta"] not in yuk
    assert G.OGRENCI_ETIKETI in yuk and "Test Öğrenci" in yuk                 # kendi adı korunur
    assert "Zeynep" not in r["asistan_yaniti"] and G.OGRENCI_ETIKETI in r["asistan_yaniti"]   # yanıt son filtresi
    assert "Başka öğrenciler hakkında bilgi verme" in ai.cagrilar[-1][0]


@db_gerekli
def test_ogrenci_sistem_istemi_yalniz_kendi_verisi(ortam, db):
    from app.core.ai_koc_servisi import sistem_promptu_olustur
    from app.models import Ogrenci
    ben = db.query(Ogrenci).filter(Ogrenci.okul_id == ortam["okul_a"], Ogrenci.ad_soyad == "Test Öğrenci").first()
    p = sistem_promptu_olustur(db, ben, None, "/koclugu")
    assert "Test Öğrenci" in p and "Zeynep" not in p and "Aksoy" not in p and "Kerem" not in p


# ----------------------------------------------------------------------------- yönetim tarafı
@db_gerekli
@pytest.mark.parametrize("soru", ["Zeynep Aksoy nasıl gidiyor?", "ZEYNEP AKSOY'un sonuçları", "öğrenci no 4321", "{eposta} kimin?"])
def test_okul_yetkilisi_kendi_ogrencisini_bulur_ai_cagrilmaz(istemci, ortam, ai, soru):
    c = _sor(istemci, ortam["yetkili"], soru.format(eposta=ortam["zeynep_eposta"]))
    assert c["tur"] == "ogrenci" and c["mod"] == "ai" and not ai.cagrilar
    assert [o["ad_soyad"] for o in c["ogrenciler"]] == ["Zeynep Aksoy"]
    assert c["ogrenciler"][0]["baglanti"]["yol"] == f"/admin/okul/{ortam['okul_a']}?sekme=ogrenciler&ogrenci={ortam['zeynep']}"


@db_gerekli
def test_okul_yetkilisi_baska_okulun_ogrencisini_bulamaz_varligi_belli_olmaz(istemci, ortam, ai):
    var = _sor(istemci, ortam["yetkili"], "Kerem Toprak'ın sonuçları nasıl?")
    yok = _sor(istemci, ortam["yetkili"], "Hayali Kişioğlu'nun sonuçları nasıl?")
    eposta = _sor(istemci, ortam["yetkili"], f"{ortam['kerem_eposta']} öğrencisi")
    no = _sor(istemci, ortam["yetkili"], "öğrenci no 9876")
    for c in (var, yok, eposta, no):
        assert c["tur"] == "ogrenci" and c["ogrenciler"] == [] and c["metin"].startswith("Bu isimde okulunuzda bir öğrenci bulunamadı")
    assert var == yok == eposta == no                                   # cevap birebir aynı: başka okulda olup olmadığı belli değil
    assert "Kerem" not in str(var) and str(ortam["okul_b"]) not in str(var) and not ai.cagrilar


@db_gerekli
def test_super_admin_her_okuldaki_ogrenciyi_bulur(istemci, ortam, ai):
    c = _sor(istemci, ortam["super"], "kerem toprak")
    assert [o["ad_soyad"] for o in c["ogrenciler"]] == ["Kerem Toprak"] and not ai.cagrilar
    assert c["ogrenciler"][0]["baglanti"]["yol"] == f"/admin/okul/{ortam['okul_b']}?sekme=ogrenciler&ogrenci={ortam['kerem']}"
    c = _sor(istemci, ortam["super"], "Zeynep Aksoy")
    assert c["ogrenciler"][0]["id"] == ortam["zeynep"]


@db_gerekli
def test_kisi_listesi_ve_kriz_yerel(istemci, ortam, ai):
    c = _sor(istemci, ortam["yetkili"], "Kritik öğrencilerim kimler?")
    assert c["tur"] == "yanit" and any("sekme=rehberlik" in b["yol"] for b in c["baglantilar"]) and not c["ogrenciler"]
    c = _sor(istemci, ortam["yetkili"], "En düşük netler kimin?")
    assert any("sekme=raporlar" in b["yol"] for b in c["baglantilar"])
    c = _sor(istemci, ortam["yetkili"], "Bir öğrencim intihar etmek istediğini söyledi")
    assert c["tur"] == "kriz" and "112" in c["metin"] and "kriz" in c["metin"]
    assert not ai.cagrilar


@db_gerekli
def test_yonetici_genel_soru_ai_ya_gider_yukte_kisisel_veri_yok(istemci, ortam, ai):
    gecmis = [{"rol": "kullanici", "metin": f"Zeynep Aksoy ({ortam['zeynep_eposta']}, TC 12345678901) için ne yapmalıyım?"},
              {"rol": "filiz", "metin": "Zeynep Aksoy ile görüşün."}]
    c = _sor(istemci, ortam["yetkili"], "Rehberlik görüşmesi notlarını nasıl tutmalıyım? Veli 0532 111 22 33 aradı.", gecmis)
    assert c["mod"] == "ai" and c["tur"] == "ai" and len(ai.cagrilar) == 1
    yuk = ai.yuk()
    for yasak in ("Zeynep", "Aksoy", "Kerem", "Toprak", "Test Öğrenci", ortam["zeynep_eposta"], "12345678901", "0532 111"):
        assert yasak not in yuk, yasak
    assert "SSS:" in ai.cagrilar[0][0] and "SAYFA LİSTESİ" in ai.cagrilar[0][0]
    assert c["baglantilar"] == [{"etiket": "Rehberlik", "yol": f"/admin/okul/{ortam['okul_a']}?sekme=rehberlik"}]
    assert "SAYFA:" not in c["metin"]


@db_gerekli
def test_ai_yanitinda_ogrenci_adi_maskelenir(istemci, ortam, ai):
    ai.yanit = "Zeynep Aksoy gibi öğrencilerle görüşme planlayın."
    c = _sor(istemci, ortam["yetkili"], "Görüşme planlamasını nasıl yaparım?")
    assert "Zeynep" not in c["metin"] and G.OGRENCI_ETIKETI in c["metin"]


@db_gerekli
def test_ai_hata_verirse_rehber_cevabi(istemci, ortam, ai):
    ai.hata = True
    c = _sor(istemci, ortam["yetkili"], "Veli raporu nasıl alınır?")
    assert c["mod"] == "rehber" and c["tur"] == "yanit" and ai.cagrilar
    assert c["baglantilar"][0]["yol"] == f"/admin/okul/{ortam['okul_a']}?sekme=siniflar"


@db_gerekli
def test_anahtar_yoksa_rehber_modu(istemci, ortam, anahtarsiz):
    assert istemci.get("/yonetim/filiz/ozet", headers=ortam["yetkili"]).json()["mod"] == "rehber"
    assert istemci.get("/yonetim/filiz/ozet", headers=ortam["super"]).json()["mod"] == "rehber"
    c = _sor(istemci, ortam["super"], "Hata kayıtları nerede?")
    assert c["mod"] == "rehber" and c["baglantilar"][0]["yol"] == "/admin/hata-kayitlari" and not anahtarsiz.cagrilar


@db_gerekli
def test_okulda_filiz_ai_yoksa_rehber_super_admin_ai(istemci, ortam, ai, db):
    db.execute(text("""UPDATE okullar SET modul_cikar = '["filiz_ai"]'::jsonb WHERE id = :o"""), {"o": ortam["okul_a"]})
    db.commit()
    o = istemci.get("/yonetim/filiz/ozet", headers=ortam["yetkili"]).json()
    assert o["mod"] == "rehber" and "dış servise gönderilmez" in o["aydinlatma"]
    c = _sor(istemci, ortam["yetkili"], "Veli raporu nasıl alınır?")
    assert c["mod"] == "rehber" and not ai.cagrilar
    o = istemci.get("/yonetim/filiz/ozet", headers=ortam["super"]).json()
    assert o["mod"] == "ai" and "OpenAI" in o["aydinlatma"]


@db_gerekli
def test_gunluk_sinir_dolunca_rehber(istemci, ortam, ai, db):
    db.execute(text("""INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
                       VALUES ('filiz_yonetim_gunluk_limit', '1', 'test', now())
                       ON CONFLICT (anahtar) DO UPDATE SET deger = '1'"""))
    db.commit()
    assert _sor(istemci, ortam["yetkili"], "Görüşme notu nasıl yazılır?")["mod"] == "ai"
    c = _sor(istemci, ortam["yetkili"], "Veli raporu nasıl alınır?")
    assert c["mod"] == "rehber" and c.get("not") and len(ai.cagrilar) == 1


def test_yonetim_sor_agir_kademede():
    from app.core.hiz_siniri import kademe_bul
    assert kademe_bul("POST", "/yonetim/filiz/sor") == "agir"
