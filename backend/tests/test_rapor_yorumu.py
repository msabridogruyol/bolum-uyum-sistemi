"""[2026-10-12] Rapor yorumları (app/core/rapor/yorum.py): kitleye uygun dil, gizlilik ve çerçeve kuralları.
Veritabanı gerekmez: rapor verisi sözlükle kurulur."""
import json
import pathlib
import re

from app.core.rapor.yorum import KITLELER, ogrenci_yorumu, okul_yorumu

ICERIK = json.loads((pathlib.Path(__file__).resolve().parents[1] / "app/data/rapor_yorumlari.json").read_text("utf-8"))["degiskenler"]


def _oz(kod, ad, puan):
    return {"kod": kod, "ad": ad, "puan": puan}


def _veri(**ek):
    v = {
        "durum": "tamamlandi", "tur": {"no": 1, "gecerli": True, "guven": 85},
        "katmanlar": [
            {"kod": "K1", "ozellikler": [_oz("D3", "Statü ve prestij", 93), _oz("D2", "Yüksek gelir", 20)]},
            {"kod": "K2", "ozellikler": [_oz("P4", "Duygusal hassasiyet", 95), _oz("P1", "İnsanlarla çalışma (dışadönüklük)", 80),
                                         _oz("P3", "Sorumluluk ve disiplin", 25)]},
            {"kod": "K3", "ozellikler": [_oz("I3", "Baskı altında karar verme", 91), _oz("I2", "Ekip ve çatışma yönetimi", 30)]},
            {"kod": "K4", "ozellikler": [_oz("A3", "İnsan odaklı eğilim", 88), _oz("A9", "Girişimcilik ve ikna eğilimi", 22)]},
        ],
        "bolumler": [{"ad": "Psikoloji", "alan": "Psikoloji & Sosyal Hizmet", "uyum": 90},
                     {"ad": "Sosyal Hizmet", "alan": "Psikoloji & Sosyal Hizmet", "uyum": 88},
                     {"ad": "Rehberlik", "alan": "Eğitim", "uyum": 85}],
        "hedef": {"ad": "Maden Mühendisliği", "uyum": 3.0, "siradaki": "Gerçek maaşları öğren"},
        "netler": {"oturumlar": [{"oturum": "TYT", "sayi": 3, "ilk": 60.25, "son": 77.25, "degisim": 17.0}],
                   "dersler": [], "kiyas": {"satirlar": [{"ad": "Matematik", "fark": -12.25}, {"ad": "Türkçe", "fark": 1.5}]}},
        "aktivite": {"gorev_toplam": 6, "son4_hafta": 1},
    }
    v.update(ek)
    return v


def test_icerik_tam_ve_dil_kurallari():
    assert len(ICERIK) == 31
    for kod, v in ICERIK.items():
        for alan in ("anlam", "ogrenci", "veli", "ogretmen"):
            assert v["yuksek"][alan].strip()
        for alan in ("anlam", "yap", "kacin", "veli", "ogretmen"):
            assert v["dusuk"][alan].strip()
        # klinik / etiketleyici dil yok
        tum = " ".join(x for y in v.values() for x in y.values()).lower()
        assert not re.search(r"nevrotik|bozukluk|hastalık|tembel|başarısız", tum), kod


def test_hassasiyet_guclu_yon_sayilmaz_destek_onerilir():
    y = ogrenci_yorumu(_veri(), "ogrenci")
    assert all(g["ad"] != "Duygusal hassasiyet" for g in y["guclu"])
    assert "Duygusal hassasiyet" not in " ".join(y["ozet"])
    assert any(d["ad"] == "Stresle baş etme" for d in y["destek"])


def test_sinif_ogretmeni_kisilik_ve_hassasiyet_gormez():
    y = ogrenci_yorumu(_veri(), "ogretmen")
    metin = json.dumps(y, ensure_ascii=False)
    assert "Stresle baş etme" not in metin
    for ad in ("İnsanlarla çalışma", "Sorumluluk ve disiplin", "Duygusal hassasiyet"):
        assert ad not in metin
    assert y["gorusme"] == []
    assert any("paylaşmayın" in k for k in y["kacin"])


def test_hedef_farki_yapici_ve_veriye_dayali():
    y = ogrenci_yorumu(_veri(), "ogrenci")
    oz = " ".join(y["ozet"])
    assert "Maden Mühendisliği" in oz and "yanlış olduğu anlamına gelmez" in oz
    assert any("Matematik" in m and "12,25" in m for m in y["yap"])        # rapordaki fark, yeni sayı üretilmez
    assert any("60,25" in c and "77,25" in c for c in y["ozet"])
    assert any("uyum yüzdesine" in k for k in y["kacin"])


def test_kitle_dili():
    o, v, r = (ogrenci_yorumu(_veri(), k) for k in ("ogrenci", "veli", "rehber"))
    assert all("çocuğunuz" not in m.lower() for m in o["yap"] + o["kacin"])
    assert any("çocuğunuz" in m.lower() for m in v["ozet"] + v["yap"] + v["kacin"])
    assert r["gorusme"] and all(k in KITLELER for k in ("ogrenci", "veli", "ogretmen", "rehber"))


def test_eksik_veriyle_calisir():
    for durum in ("devam", "k5_bekliyor"):
        y = ogrenci_yorumu({"durum": durum}, "ogrenci")
        assert y["ozet"] and y["yap"]
    y = ogrenci_yorumu(_veri(bolumler=[], hedef=None, netler={}, aktivite={}), "veli")
    assert y["ozet"] and y["kacin"]
    y = ogrenci_yorumu(_veri(tur={"gecerli": False}), "rehber")
    assert any("güven" in m.lower() for m in y["yap"]) and any("güven" in m.lower() for m in y["kacin"])


def test_okul_oncelikli_isler():
    ov = {"ozet": {"toplam": 50, "tamamlayan": 20, "hedef_secen": 3, "moduller": ["net_takibi"],
                   "durumlar": [{"kod": "giris_yok", "sayi": 8}],
                   "siniflar": [{"sinif": "12. Sınıf", "ogrenci": 10, "tamamlayan": 2}],
                   "subeler": [{"etiket": "9-A", "sube": "A", "sinif": "9. Sınıf", "ogrenci": 12, "tamamlayan": 3}]},
          "net": {"giren": 4}, "gecersiz": 2, "alanlar": [{"alan": "Diğer", "sayi": 9}, {"alan": "Mühendislik", "sayi": 8}],
          "ortak_guclu": [{"ad": "Sayısal ve veri eğilimi", "kod": "A1"}], "ortak_gelisim": [{"ad": "Sözel ve dil eğilimi", "kod": "A2"}]}
    y = okul_yorumu(ov)
    assert y["isler"][0]["oncelik"] == 1 and all({"metin", "kim", "ne_zaman"} <= set(i) for i in y["isler"])
    metin = " ".join(i["metin"] for i in y["isler"])
    assert "12. sınıf" in metin and "8 öğrenci" in metin and "9-A" in metin and "Mühendislik" in metin
    assert "Diğer alanında" not in metin
    assert y["guclu"] and y["destek"] and len(y["kacin"]) == 4
    assert okul_yorumu({"ozet": {"toplam": 0}})["ozet"] == ["Bu kapsamda henüz öğrenci yok."]


def test_degerler_ayri_ve_notr_dusuk_adlar():
    y = ogrenci_yorumu(_veri(), "ogrenci")
    ozet = " ".join(y["ozet"])
    assert "önem verdiğin değerler: Statü ve prestij" in ozet
    assert "öne çıkan yönlerin:" in ozet and "Statü ve prestij ·" not in ozet.split("önem verdiğin")[0]
    assert "Bölüm uyumunda en öne çıkan alanlar: Psikoloji & Sosyal Hizmet · Eğitim." in ozet
    # düşük kutupta etiketleyici ad yerine nötr ad
    assert any(d["ad"] == "Planlı çalışma alışkanlığı" for d in y["destek"])
    assert "Sorumluluk ve disiplin" not in json.dumps(y["destek"], ensure_ascii=False)


def test_etik_karar_veli_ve_ogretmende_gelisim_alani_olmaz():
    v = _veri(katmanlar=[{"kod": "K3", "ozellikler": [_oz("I4", "Etik karar verme", 15), _oz("I3", "Baskı altında karar verme", 91)]}])
    for kitle in ("veli", "ogretmen"):
        assert "Etik karar verme" not in json.dumps(ogrenci_yorumu(v, kitle), ensure_ascii=False)
    assert any(d["ad"] == "Etik karar verme" for d in ogrenci_yorumu(v, "rehber")["destek"])


def test_okul_yorumu_kisilik_kullanmaz():
    ov = {"ozet": {"toplam": 30, "tamamlayan": 28}, "ortak_guclu": [{"ad": "Duygusal hassasiyet", "kod": "P4"}, {"ad": "Sayısal", "kod": "A1"}],
          "ortak_gelisim": [{"ad": "Sorumluluk ve disiplin", "kod": "P3"}]}
    m = json.dumps(okul_yorumu(ov), ensure_ascii=False)
    assert "Duygusal hassasiyet" not in m and "Sorumluluk" not in m and "Sayısal" in m


def test_deneme_yoksa_veli_gorusmesi_ve_dusus_ifadesi():
    y = ogrenci_yorumu(_veri(netler={}, hedef=None), "veli")
    assert not any("deneme" in g.lower() for g in y["gorusme"])
    d = ogrenci_yorumu(_veri(netler={"oturumlar": [{"oturum": "TYT", "sayi": 3, "ilk": 70, "son": 60, "degisim": -10}]}), "ogrenci")
    assert any("düşüş" in c for c in d["ozet"]) and any("kendini yargılama" in k for k in d["kacin"])
