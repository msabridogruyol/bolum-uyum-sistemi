"""[2026-10-19] Maarif Modeli ilişkilendirmesi: veri tutarlı, iş değerleri eşleşmez, metin yorumsal."""
import json
from pathlib import Path

from app.core.maarif import NOT, TUR_ADI, karsiliklar, kisa_metin

GECERLI = {f"D{i}" for i in range(1, 8)} | {f"P{i}" for i in range(1, 9)} | {f"I{i}" for i in range(1, 8)} | {f"A{i}" for i in range(1, 10)}


def test_eslesme_dosyasi_tutarli():
    d = json.loads((Path(__file__).resolve().parents[1] / "app" / "data" / "maarif_eslesme.json").read_text(encoding="utf-8"))
    for kod, liste in d["ozellikler"].items():
        assert kod in GECERLI, kod
        assert liste and all(x[0] in TUR_ADI and x[1] for x in liste), kod
        assert all(len(x) == 3 for x in liste if x[0] != "deger"), kod      # eğilim/beceri resmî kodla


def test_is_degerleri_eslesmez_ve_metin():
    assert all(karsiliklar(k) == [] for k in ("D1", "D2", "D3", "D4", None, "YOK"))
    assert kisa_metin("P5") == "Merak · Açık fikirlilik"
    assert "puanlamayı etkilemez" in NOT and "MEB onayı anlamına gelmez" in NOT


def test_rehber_ve_ogretmen_yorumunda_maarif_karsiligi():
    """[2026-11-03] Rehber / sınıf öğretmeni yorumunda güçlü yönün Maarif karşılığı; öğrenci ve veli yorumunda yok (ayrı kartta)."""
    from app.core.maarif import kisa_metin
    from app.core.rapor.yorum import _maarif_alani
    assert _maarif_alani("P5", "rehber") == {"maarif": kisa_metin("P5")} and kisa_metin("P5")
    assert _maarif_alani("P5", "ogretmen")["maarif"]
    assert _maarif_alani("P5", "ogrenci") == {} and _maarif_alani("P5", "veli") == {}
    assert _maarif_alani("D1", "rehber") == {}, "iş değerleri Maarif'le eşleştirilmedi"


def test_veli_sunumunda_maarif_slayti():
    from app.core.rapor import veli_sunumu as vs
    assert hasattr(vs, "_maarif")
    kaynak = open(vs.__file__, encoding="utf-8").read()
    assert "_maarif(d)" in kaynak and "MEB onayı" in open(__import__("app.core.maarif", fromlist=["x"]).__file__, encoding="utf-8").read()
