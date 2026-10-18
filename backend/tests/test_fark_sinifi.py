"""
[2026-10-17] Sen ve bölüm karşılaştırması yakınlık dilinde:
  uyumlu (|fark| < 5, yeşil) · fazla / az (turuncu) · belirgin fazla / az (15+, kırmızı); fazlalık güçlü yön değil;
  değerler (D) güçlü yön sayılmaz; P4 (kaygı) yalnızca fazlası fark sayılır.
"""
from types import SimpleNamespace as NS

from app.core import koclugu_servisi as ks


def test_fark_sinifi_ve_renk():
    assert ks.fark_sinifi(0) == "uyumlu" and ks.fark_sinifi(4.9) == "uyumlu" and ks.fark_sinifi(-4.9) == "uyumlu"
    assert ks.fark_sinifi(5) == "fazla" and ks.fark_sinifi(15) == "belirgin_fazla"
    assert ks.fark_sinifi(-5) == "eksik" and ks.fark_sinifi(-15) == "belirgin_eksik"
    assert ks.fark_sinifi(-30, ters_yonlu=True) == "uyumlu"          # bölümden sakin olmak sorun değil
    assert ks.fark_sinifi(20, ters_yonlu=True) == "belirgin_fazla"
    assert [ks.fark_rengi(x) for x in ("uyumlu", "fazla", "eksik", "belirgin_fazla", "belirgin_eksik")] == \
        ["yesil", "turuncu", "turuncu", "kirmizi", "kirmizi"]


def _satir(kod, gap, goreli, ters=False):
    s = ks.GapSatiri(NS(kod=kod, ters_yonlu=ters), 50.0, 50.0, 50.0, None, goreli_fark=gap)
    s.ogrenci_goreli = goreli
    return s


def test_guclu_yon_ve_aciklama():
    fazla = _satir("P1", 12.0, 75.0)
    assert fazla.fark_sinifi == "fazla" and not ks.guclu_yon_mu(fazla)
    assert "beklenenden fazla" in ks.fark_aciklamasi(fazla, "Hukuk") and "avantaj" not in ks.fark_aciklamasi(fazla, "Hukuk")
    guclu = _satir("P1", 2.0, 70.0)
    assert ks.guclu_yon_mu(guclu) and "Hukuk için beklenen düzeyle uyumlu" in ks.fark_aciklamasi(guclu, "Hukuk")
    assert not ks.guclu_yon_mu(_satir("P1", 2.0, 52.0))              # uyumlu ama kendi profilinde yüksek değil
    deger = _satir("D2", 18.0, 80.0)
    assert deger.fark_sinifi == "belirgin_fazla" and not ks.guclu_yon_mu(deger)
    assert "çalışanların çoğundan daha önemli" in ks.fark_aciklamasi(deger, "Sosyal Hizmet")
    assert not ks.guclu_yon_mu(_satir("D2", 1.0, 80.0))               # değer uyumlu olsa da güçlü yön değildir
    sakin = _satir("P4", -25.0, 30.0, ters=True)
    assert sakin.fark_sinifi == "uyumlu" and not ks.guclu_yon_mu(sakin)
