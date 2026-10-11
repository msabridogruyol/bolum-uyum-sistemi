"""[2026-10-10] app/core/psikometri.py birim testi — `python3 test_psikometri.py` ya da `pytest test_psikometri.py`."""
import random
import sys

sys.path.insert(0, ".")

from app.core.psikometri import cronbach_alfa, f_ppf, feldt_ga, sablon_analizi


def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj)
    assert kosul, mesaj


def test_alfa_elle_hesap():
    # 4 kişi × 3 madde. Elle: madde varyansları 5/3, 19/12, 5/3 (Σ = 59/12); toplam puanlar 5, 8, 10, 14 → varyans 57/4
    # α = 3/2 · (1 − (59/12)/(57/4)) = 3/2 · 112/171 = 168/171 = 0.982456…
    veri = [[1, 2, 2], [2, 3, 3], [3, 3, 4], [4, 5, 5]]
    a = cronbach_alfa(veri)
    basarili(abs(a - 168 / 171) < 1e-12, f"Cronbach alfa elle hesapla aynı ({a:.6f} = 168/171)")


def test_f_yuzdelik():
    # Bilinen tablo değerleri: F(0.95; 5, 10) = 3.3258, F(0.975; 10, 20) = 2.7737
    basarili(abs(f_ppf(0.95, 5, 10) - 3.3258) < 1e-3, f"F(0.95;5,10) = {f_ppf(0.95, 5, 10):.4f}")
    basarili(abs(f_ppf(0.975, 10, 20) - 2.7737) < 1e-3, f"F(0.975;10,20) = {f_ppf(0.975, 10, 20):.4f}")
    try:
        from scipy.stats import f as F
        for d1, d2 in [(29, 261), (99, 891), (999, 9990)]:
            for p in (0.025, 0.975):
                basarili(abs(f_ppf(p, d1, d2) - F.ppf(p, d1, d2)) < 1e-6, f"F({p};{d1},{d2}) scipy ile aynı")
    except ImportError:
        pass


def test_feldt_ga():
    alt, ust = feldt_ga(0.80, 100, 10)
    basarili(alt < 0.80 < ust and 0.72 < alt < 0.76 and 0.84 < ust < 0.87, f"Feldt GA α=.80 n=100 k=10 → [{alt:.3f}, {ust:.3f}]")


def test_sablon_analizi_ters_ve_esikler():
    rnd = random.Random(7)
    sorular = [{"id": f"s{i}", "tur": "likert", "ters": i == 4} for i in range(1, 7)] + [{"id": "s7", "tur": "acik"}]

    def yanit(n):
        out = []
        for _ in range(n):
            t = rnd.gauss(0, 1)
            c = {}
            for i in range(1, 7):
                v = max(1, min(5, round(3 + t + rnd.gauss(0, 0.8))))
                c[f"s{i}"] = 6 - v if i == 4 else v      # ters madde ters yönde yanıtlanır
            c["s7"] = "metin"
            out.append(c)
        return out

    az = sablon_analizi(sorular, yanit(20))
    basarili(az["durum"] == "veri_bekleniyor" and "alfa" not in az, "n < 30 → istatistik yok, veri bekleniyor")
    orta = sablon_analizi(sorular, yanit(60))
    basarili(orta["durum"] == "yetersiz_orneklem" and orta["alfa_ga"] is not None, "30 ≤ n < 100 → yetersiz örneklem uyarısı + GA")
    cok = sablon_analizi(sorular, yanit(400) + [{"s1": 3}])   # eksik satır listwise dışarıda
    basarili(cok["n"] == 400 and cok["madde_sayisi"] == 6, "eksik yanıt dışlandı, açık uçlu madde sayılmadı")
    basarili(cok["alfa"] > 0.8, f"ters madde çevrilince alfa yüksek ({cok['alfa']})")
    m4 = next(m for m in cok["maddeler"] if m["id"] == "s4")
    basarili(m4["r_it"] > 0.5 and m4["ters"], f"ters madde r_it pozitif ({m4['r_it']})")
    # ters bayrağı unutulursa madde zayıf görünür
    yanlis = sablon_analizi([{**s, "ters": False} for s in sorular], yanit(400))
    m4y = next(m for m in yanlis["maddeler"] if m["id"] == "s4")
    basarili(m4y["r_it"] < 0.3 and "r_it < 0.30" in m4y["uyarilar"], "çevrilmeyen ters madde r_it < 0.30 bayrağı alır")
    alt = sablon_analizi(sorular, yanit(200), {"A": ["s1", "s2", "s3"], "B": ["s4", "s5", "s6"]})
    basarili(len(alt["alt_boyutlar"]) == 2 and all(a["alfa"] is not None for a in alt["alt_boyutlar"]), "alt boyut alfaları")


if __name__ == "__main__":
    for ad, f in list(globals().items()):
        if ad.startswith("test_") and callable(f):
            f()
    print("Tüm psikometri testleri geçti.")
