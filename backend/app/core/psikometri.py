# -*- coding: utf-8 -*-
"""
[2026-10-10] Anket / tarama formları için psikometrik istatistikler (saf Python; ek bağımlılık yok).

- Cronbach alfa (ters maddeler önceden 6 − x ile çevrilmiş olmalı; bkz. maddeleri_hazirla)
- Alfa için %95 güven aralığı — Feldt (1965) F dağılımı yaklaşımı:
      df1 = n − 1, df2 = (n − 1)(k − 1)
      alt = 1 − (1 − α) · F(0.975; df1, df2),  üst = 1 − (1 − α) · F(0.025; df1, df2)
- Madde istatistikleri: ortalama, ss (n − 1), düzeltilmiş madde-toplam korelasyonu (madde ↔ diğer maddelerin toplamı),
  madde silinirse alfa, taban (%1) / tavan (%5) yüzdesi.

McDonald omega bilinçli olarak hesaplanmaz: doğru tahmin bir faktör analizi (ML/ULS yükleri) ister; temel bileşen
yaklaşımı omega'yı sistematik olarak şişirir. Yapı geçerliği için dış araçta faktör analizi önerilir.
"""
import math

EN_AZ_ISTATISTIK = 30     # bunun altında istatistik verilmez ("veri bekleniyor")
EN_AZ_YORUM = 100         # bunun altında "yorum için yetersiz örneklem" uyarısı
ESIK_RIT = 0.30
ESIK_ALFA = 0.70


# ----------------------------------------------------------------------------- temel
def _ort(x):
    return sum(x) / len(x)


def _var(x):
    n = len(x)
    if n < 2:
        return 0.0
    m = _ort(x)
    return sum((v - m) ** 2 for v in x) / (n - 1)


def _kor(x, y):
    mx, my = _ort(x), _ort(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def cronbach_alfa(satirlar: list[list[float]]) -> float | None:
    """satirlar: her yanıtlayıcı için k madde puanı (eksiksiz). α = k/(k−1) · (1 − Σσ²ᵢ / σ²ₜ)."""
    if not satirlar or len(satirlar) < 2:
        return None
    k = len(satirlar[0])
    if k < 2:
        return None
    sutunlar = list(zip(*satirlar))
    toplam_var = _var([sum(s) for s in satirlar])
    if toplam_var <= 0:
        return None
    return k / (k - 1) * (1 - sum(_var(list(c)) for c in sutunlar) / toplam_var)


# ----------------------------------------------------------------------------- F dağılımı (Feldt GA için)
def _betacf(a, b, x, maks=20000, eps=3e-14):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, maks + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1) < eps:
            break
    return h


def _betai(a, b, x):
    """Düzenlenmiş eksik beta fonksiyonu I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    ln = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    bt = math.exp(ln)
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def f_cdf(x, d1, d2):
    if x <= 0:
        return 0.0
    return _betai(d1 / 2, d2 / 2, d1 * x / (d1 * x + d2))


def f_ppf(p, d1, d2):
    """F dağılımının p-yüzdeliği (ikiye bölme)."""
    alt, ust = 0.0, 1.0
    while f_cdf(ust, d1, d2) < p:
        ust *= 2
        if ust > 1e8:
            break
    for _ in range(200):
        orta = (alt + ust) / 2
        if f_cdf(orta, d1, d2) < p:
            alt = orta
        else:
            ust = orta
        if ust - alt < 1e-12 * max(1.0, ust):
            break
    return (alt + ust) / 2


def feldt_ga(alfa: float, n: int, k: int, guven: float = 0.95) -> tuple[float, float] | None:
    if alfa is None or n < 2 or k < 2:
        return None
    d1, d2 = n - 1, (n - 1) * (k - 1)
    q = (1 - guven) / 2
    return 1 - (1 - alfa) * f_ppf(1 - q, d1, d2), 1 - (1 - alfa) * f_ppf(q, d1, d2)


# ----------------------------------------------------------------------------- yanıtları hazırla
def maddeleri_hazirla(sorular: list[dict], cevaplar: list[dict]) -> tuple[list[dict], list[list[float]]]:
    """Likert maddeleri seçer; yalnızca TÜM likert maddeleri 1–5 aralığında yanıtlanmış satırları alır (listwise);
    ters maddeleri 6 − x ile çevirir. Dönüş: (maddeler, satırlar)."""
    maddeler = [s for s in sorular if s.get("tur") == "likert"]
    satirlar = []
    for c in cevaplar:
        satir = []
        for s in maddeler:
            v = c.get(s["id"])
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not 1 <= v <= 5:
                break
            satir.append(float(6 - v if s.get("ters") else v))
        else:
            satirlar.append(satir)
    return maddeler, satirlar


# ----------------------------------------------------------------------------- analiz
def _yuv(x, b=3):
    return None if x is None else round(x, b)


def olcek_analizi(maddeler: list[dict], satirlar: list[list[float]], ham_satirlar: list[list[float]] | None = None) -> dict:
    """Tek bir (alt) ölçek için alfa, GA ve madde istatistikleri. Taban/tavan ham (çevrilmemiş) cevaba göre verilir."""
    n, k = len(satirlar), len(maddeler)
    sonuc = {"n": n, "madde_sayisi": k, "uyarilar": []}
    if n < EN_AZ_ISTATISTIK:
        sonuc["durum"] = "veri_bekleniyor"
        return sonuc
    alfa = cronbach_alfa(satirlar)
    ga = feldt_ga(alfa, n, k) if alfa is not None else None
    sonuc.update(alfa=_yuv(alfa), alfa_ga=[_yuv(ga[0]), _yuv(ga[1])] if ga else None)
    sutunlar = [list(c) for c in zip(*satirlar)]
    ham = [list(c) for c in zip(*(ham_satirlar or satirlar))]
    toplamlar = [sum(s) for s in satirlar]
    mad = []
    for j, m in enumerate(maddeler):
        x = sutunlar[j]
        digerleri = [t - v for t, v in zip(toplamlar, x)]
        rit = _kor(x, digerleri)
        silinirse = cronbach_alfa([[v for i, v in enumerate(s) if i != j] for s in satirlar]) if k > 2 else None
        h = ham[j]
        uy = []
        if rit is None or rit < ESIK_RIT:
            uy.append("r_it < 0.30")
        if silinirse is not None and alfa is not None and silinirse > alfa + 0.005:
            uy.append("silinirse alfa artıyor")
        mad.append({
            "id": m["id"], "metin": m.get("metin"), "ters": bool(m.get("ters")),
            "ortalama": _yuv(_ort(x), 2), "ss": _yuv(math.sqrt(_var(x)), 2),
            "r_it": _yuv(rit), "silinirse_alfa": _yuv(silinirse),
            "taban_yuzde": round(100 * sum(1 for v in h if v == 1) / n, 1),
            "tavan_yuzde": round(100 * sum(1 for v in h if v == 5) / n, 1),
            "uyarilar": uy,
        })
    sonuc["maddeler"] = mad
    if alfa is None or alfa < ESIK_ALFA:
        sonuc["uyarilar"].append("alfa < 0.70")
    if any(m["r_it"] is None or m["r_it"] < ESIK_RIT for m in mad):
        sonuc["uyarilar"].append(f"{sum(1 for m in mad if m['r_it'] is None or m['r_it'] < ESIK_RIT)} maddede r_it < 0.30")
    if n < EN_AZ_YORUM:
        sonuc["uyarilar"].append("yorum için yetersiz örneklem (n < 100)")
    sonuc["durum"] = "yetersiz_orneklem" if n < EN_AZ_YORUM else ("dikkat" if sonuc["uyarilar"] else "iyi")
    return sonuc


def sablon_analizi(sorular: list[dict], cevaplar: list[dict], alt_boyutlar: dict | None = None) -> dict:
    """sorular: şablon soruları; cevaplar: {soru_id: değer} sözlükleri; alt_boyutlar: {"ad": [soru_id, ...]} (isteğe bağlı)."""
    maddeler, satirlar = maddeleri_hazirla(sorular, cevaplar)
    ters = [bool(m.get("ters")) for m in maddeler]
    ham = [[6 - v if t else v for v, t in zip(s, ters)] for s in satirlar]
    sonuc = olcek_analizi(maddeler, satirlar, ham)
    if alt_boyutlar:
        alt = []
        for ad, idler in alt_boyutlar.items():
            sec = [i for i, m in enumerate(maddeler) if m["id"] in idler]
            if len(sec) < 2:
                continue
            a = olcek_analizi([maddeler[i] for i in sec], [[s[i] for i in sec] for s in satirlar], [[s[i] for i in sec] for s in ham])
            alt.append({"ad": ad, **{k: a.get(k) for k in ("n", "madde_sayisi", "alfa", "alfa_ga", "durum", "uyarilar")}})
        sonuc["alt_boyutlar"] = alt
    return sonuc
