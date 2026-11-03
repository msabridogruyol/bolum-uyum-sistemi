"""[2026-11-02] 500 öğrencilik uygulama simülasyonunda (scripts/uygulama_simulasyonu.py) bulunan Filiz eksiklerinin
kalıcı testleri. Yapay dizinle çalışır (veritabanı gerekmez)."""
from app.core import filiz_anlama as fa
from app.core import filiz_bilgi as fb
from app.core import filiz_rehber as fr


def _dizin():
    B = fb.Belge
    return fb.Dizin([
        B("bolum", "Turizm Rehberliği bölümü", "Öğrenim süresi: 4 yıl. Puan türü: üniversiteye göre değişir. Rehber yetiştirir.",
          "Bölümler › Turizm Rehberliği › Genel bakış", None, "turizm rehberligi"),
        B("bolum", "Odyoloji bölümü", "Öğrenim süresi: 4 yıl. Puan türü: SAY. İşitmeyi inceler.", "Bölümler › Odyoloji › Genel bakış",
          None, "odyoloji"),
        B("bolum_is", "Odyoloji mezunları nerelerde çalışır", "Hastaneler. Mezunların sık yaptığı meslekler: Odyolog.",
          "Bölümler › Odyoloji › Meslekler", None, "odyoloji"),
        B("mulakat", "Odyoloji mülakat simülasyonu", "Pozisyon: Odyolog. Örnek sorular: İşitme testi.", "İş Hayatı › Mülakat Simülasyonu",
          "is_hayati", "odyoloji"),
        B("mulakat_pratik", "Mülakata hazırlanma ipuçları", "Cevabını önce yaz, sonra sesli oku. Mülakat için hazırlan.",
          "İş Hayatı › Mülakat Pratiği", "is_hayati", ""),
        B("sozluk", "Güçlü yön", "Profilinde öne çıkan özellik.", "Sözlük", None, "", ("guclu yon",)),
    ])


def test_bosluksuz_ve_tek_harf_hatali_bolum_adi(monkeypatch):
    d = _dizin()
    assert dict(d.varliklari_coz("turizmrehberligi hangi puan turuyle"))["turizm rehberligi"] == {"turizm rehberligi"}
    assert fb.duzelt("odyolji ne okutuyor").startswith("odyoloji"), "çapa sözcüğünde tek harf hatası"
    assert fb.duzelt("avukat olcam ne okumam lazim") == "avukat olacagim ne okumam lazim", "geçerli sözcük değişmez"


def test_degisken_puan_turu_anlasilir(monkeypatch):
    d = _dizin()
    c = fa.kunye_sorusu(d, "turizm rehberligi hangi puan turuyle ogrenci aliyor")
    assert c and "üniversiteye göre değişiyor" in c.yanit and "Değişken" not in c.yanit


def test_paketinde_is_hayati_yoksa_mulakat_sorusu_acikca_soylenir():
    d = _dizin()
    c = fa.kapali_modul_cevabi(d, "Odyoloji mülakatında ne sorulur?", {"kocluk", "filiz"})
    assert c and c.kaynak == "icerik_yok" and "İş Hayatı" in c.yanit and "Odyoloji" in c.yanit
    assert fa.kapali_modul_cevabi(d, "Odyoloji mülakatında ne sorulur?", {"is_hayati"}) is None
    assert fa.kapali_modul_cevabi(d, "Odyoloji mezunları nerede çalışır", {"filiz"}) is None


def test_tanim_sorusu_kisisel_konuya_gitmez(monkeypatch):
    d = _dizin()
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    monkeypatch.setattr(fb, "sozluk_bul", lambda db, s: d.belgeler[-1] if "guclu yon" in fb.duzelt(s) else None)
    c = fa.onceden_anla(None, "Güçlü yön ne demek?", set())
    assert c and c.kaynak == "icerik" and "Güçlü yön" in c.yanit


def test_yeni_konular_ve_sade_anahtarlar(monkeypatch):
    d = _dizin()
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    monkeypatch.setattr(fa, "onceden_anla", lambda db, m, mod: None)
    monkeypatch.setattr(fa, "sonradan_netlestir", lambda db, m, mod: None)
    for soru, konu in [("matematik ödevimi yapar mısın", fr.k_odev), ("sonuç e-postası gelmedi", fr.k_eposta),
                       ("YKS'ye kaç gün kaldı", fr.k_yks), ("şifremi unuttum", fr.k_sifre), ("raporumu nereden indiririm", fr.k_rapor),
                       ("sonuçlarım ne", fr.k_sonuc), ("taban puanları nerede", fr.k_universite), ("burs var mı", fr.k_burs_yurt),
                       ("ders çalışmak istemiyorum", fr.k_motivasyon)]:
        assert fr._rota(None, soru, set()) == ("konu", konu), soru
    assert fr._rota(None, "yurtdışında okumak", set())[1] is not fr.k_burs_yurt


def test_meslek_basligi_duzgun_yazilir():
    assert fb._meslek_goster("ağaç i̇şleri endüstri mühendisi") == "Ağaç işleri endüstri mühendisi"
    assert fb._meslek_goster("i̇statistikçi") == "İstatistikçi"


def test_bitisik_yazim_ve_meslek_adi_turkce():
    d = _dizin()
    fb.capa_ekle(["halk oyunlari", "teknolojisi"])
    assert fb.duzelt("halkoyunlari okumak istiyorum").startswith("halk oyunlari")
    assert fb.duzelt("Filiz senkimsin") == "filiz sen kimsin"
    assert fa._meslek_gorunen(d, "tasarimci", "tasarımcı olmak istiyorum") == "Tasarımcı"
