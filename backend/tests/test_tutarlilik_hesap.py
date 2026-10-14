"""[2026-10-14] Hesap tutarlılığı denetimi: gizli küçük grup yorumu, hedef seçen oranı, yuvarlama, güçlü yön eşiği,
mülakat simülasyonu yorumu, güven puanı geçerliliği. Veritabanı gerekmez: veriler sözlükle kurulur."""
import json

from app.api.is_hayati_mulakat_sim import _yanitsiz_notu, _yorum
from app.core.guvenlik_servisi import gecerli_mi
from app.core.rapor.veri import swot, yuvarla
from app.core.rapor.yorum import _say, ogrenci_yorumu, okul_yorumu


# ----------------------------------------------------------------------------- 1 · gizli küçük grup
def test_gizli_kapsamda_oran_cumlesi_yok():
    ov = {"ozet": {"toplam": 4, "kapsam_gizli": True, "tamamlayan": None, "hedef_secen": None, "hedef_secen_tamamlayan": None,
                   "durumlar": [{"kod": "giris_yok", "sayi": None}], "moduller": ["net_takibi"]},
          "kapsam": {"sinif": "11. Sınıf", "sube": "B"}, "net": {"giren": 1}, "gecersiz": None}
    y = okul_yorumu(ov)
    metin = json.dumps(y, ensure_ascii=False)
    assert "Bu grupta 5'ten az öğrenci olduğu için sayılar gizlilik gereği gösterilmiyor." in y["ozet"]
    assert "0 / 4" not in metin and "%0" not in metin and "yarının altında" not in metin
    assert "Tamamlama oranı" not in metin and "Net Takibi'ni" not in metin


def test_gizli_olmayan_kapsamda_oran_cumlesi_var():
    y = okul_yorumu({"ozet": {"toplam": 10, "tamamlayan": 4}})
    assert "Değerlendirmeyi tamamlayan öğrenci: 4 / 10 (%40)." in y["ozet"]
    assert any("yarının altında" in c for c in y["ozet"])


# ----------------------------------------------------------------------------- 2 · hedef seçen / tamamlayan
def test_hedef_orani_payi_tamamlayanlardan():
    # 9 öğrenci hedef seçmiş ama yalnızca 2'si testi tamamlamış: oran 2/6, %150 değil
    ov = {"ozet": {"toplam": 20, "tamamlayan": 6, "hedef_secen": 9, "hedef_secen_tamamlayan": 2}}
    ozet = " ".join(okul_yorumu(ov)["ozet"])
    assert "hedef bölüm seçen öğrenci sayısı 2 (tamamlayanların %33)" in ozet
    assert "%150" not in ozet


# ----------------------------------------------------------------------------- 5 · yuvarlama
def test_yuvarla_yarim_yukari():
    assert yuvarla(62.5) == 63 and yuvarla(61.5) == 62 and yuvarla(0.5) == 1
    assert round(62.5) == 62   # Python'un varsayılanı (çifte yuvarlama) — bu yüzden yuvarla() kullanılır
    assert yuvarla(2.675, 2) == 2.68 and yuvarla(1.005, 2) == 1.01
    assert yuvarla(None) is None and isinstance(yuvarla(49.72), int)
    assert _say(62.5) == "62,5" and _say(2.675) == "2,68"


def test_okul_yorumu_oran_yarim_yukari():
    # 5 / 8 = %62,5 → ekranda Math.round ile 63; yorum da 63 demeli
    y = okul_yorumu({"ozet": {"toplam": 8, "tamamlayan": 5}})
    assert "Değerlendirmeyi tamamlayan öğrenci: 5 / 8 (%63)." in y["ozet"]


# ----------------------------------------------------------------------------- 6 · 7 · güçlü yön eşiği ve SWOT
def _oz(kod, ad, ham):
    from app.core.seviye import seviye_etiketi
    return {"kod": kod, "ad": ad, "puan": yuvarla(ham, 1), "ham": ham, "seviye": seviye_etiketi(ham)}


def _v(ozellikler, gucluler=None):
    return {"durum": "tamamlandi", "tur": {"gecerli": True}, "katmanlar": [{"kod": "K", "ozellikler": ozellikler}],
            "gucluler": gucluler or [], "gelisim": [], "bolumler": [], "k5": [], "listem": [], "hedef": None, "aktivite": {}}


def test_esik_ham_puanla_karsilastirilir():
    o = _oz("I3", "Baskı altında karar verme", 61.96)   # 1 ondalıkta 62,0 ama "Ortanın üstü"
    assert o["puan"] == 62.0 and o["seviye"] == "Ortanın üstü"
    y = ogrenci_yorumu(_v([o]), "ogrenci")
    assert "Baskı altında karar verme" not in " ".join(y["ozet"])   # güçlü yön olarak listelenmez


def test_swot_esigi_gecen_yoksa_guclu_denmez():
    v = _v([_oz("A1", "Sayısal ve veri eğilimi", 48), _oz("A2", "Sözel ve dil eğilimi", 45), _oz("I1", "Problem çözme", 47)])
    s = swot(v, "rehber")
    assert len(s["S"]) == 1
    assert s["S"][0].startswith("Henüz belirgin biçimde öne çıkan bir özellik yok; görece en yüksek puanlar:")
    assert "Orta (48)" not in s["S"][0] and "Sayısal ve veri eğilimi (48)" in s["S"][0]
    assert swot(v, "ogrenci")["S"][0].startswith("Henüz belirgin biçimde öne çıkan bir özelliğin yok")


def test_swot_degerleri_guclu_yon_saymaz():
    d = _oz("D3", "Statü ve prestij", 93)
    i = _oz("I3", "Baskı altında karar verme", 80)
    s = swot(_v([d, i], gucluler=[i]), "ogrenci")
    assert not any("Statü" in x for x in s["S"]) and any("Baskı altında karar verme" in x for x in s["S"])
    assert "Bir işte en çok önem verdiğin değerler: Statü ve prestij" in s["O"]


def test_swot_puan_yarim_yukari():
    i = _oz("I3", "Baskı altında karar verme", 62.5)
    assert swot(_v([i], gucluler=[i]))["S"] == ["Baskı altında karar verme: güçlü (63)"]


# ----------------------------------------------------------------------------- 9 · güven puanı
def test_guven_gecerliligi_gosterilen_puanla():
    assert gecerli_mi(49.72, 50.0)        # ekranda 50 / eşik 50 → geçerli
    assert gecerli_mi(49.5, 50.0)
    assert not gecerli_mi(49.49, 50.0)


# ----------------------------------------------------------------------------- 10 · mülakat simülasyonu yorumu
def test_mulakat_yarisi_cogunluk_sayilmaz():
    assert _yorum(2, 4).startswith("Soruların yarısında")
    assert _yorum(3, 4).startswith("Soruların çoğunda")
    assert _yorum(1, 4).startswith("Bu alanın düşünme biçimi")
    assert _yorum(4, 4).startswith("Her soruda")


def test_mulakat_yanitsiz_sorular_belirtilir():
    assert _yorum(1, 1, yanitsiz=3).startswith("Yanıtladığın her soruda")
    assert _yanitsiz_notu(3).startswith("3 soruyu boş bıraktın") and _yanitsiz_notu(0) is None
    assert _yorum(2, 3, yanitsiz=1).startswith("Yanıtladığın soruların çoğunda")
    assert "boş bıraktın" not in _yorum(2, 2)


# ----------------------------------------------------------------------------- kendi adı maskeleme (yapay zekâya giden metin)
def test_kendi_adi_maskeleme_siradan_kelimeleri_bozmaz():
    from app.core.filiz_gizlilik import kendi_adini_maskele as k
    assert k("Doğa bilimleri ve doğayı seviyorum", "Doğa Yılmaz") == "Doğa bilimleri ve doğayı seviyorum"
    assert k("Deniz biyolojisi ilgimi çekiyor", "Deniz Kaya") == "Deniz biyolojisi ilgimi çekiyor"
    assert k("ben ayşe kaya, kaya tırmanışını severim", "Ayşe Nur Kaya") == "ben [ad], kaya tırmanışını severim"
    assert k("Merhaba ben Ayşe Nur Kaya, Kaya ailesinin kızıyım.", "Ayşe Nur Kaya") == "Merhaba ben [ad], [ad] ailesinin kızıyım."
    assert k("Ayşe Kaya'nın hedefi tıp", "Ayşe Nur Kaya") == "[ad]'nın hedefi tıp"


def test_sunum_pdf_yarim_yukari():
    from app.core.rapor.sunum_pdf import _tam
    assert _tam(62.5) == 63 and _tam(72.4) == 72
