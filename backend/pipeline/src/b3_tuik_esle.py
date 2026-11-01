# -*- coding: utf-8 -*-
r"""
B3 — TÜİK Yükseköğretim İstihdam Göstergeleri → bölüm eşleşmesi (elle eş anlamlı listesi YOK)

Girdi : onet/Lisans mezunlarının bölümlere göre {kayıtlı istihdam oranı, ilk iş bulma süresi, aylık ortalama kazanç grupları}.xls
        veri/bolumler.csv
Çıktı : veri/tuik_lisans_bolum.csv  (bolum;istihdam_orani;ilk_is_suresi_ay;kazanc_grubu_1_5;tuik_adlari;eslesme)
        cikti/rapor/b3_tuik_eslesme.csv (her bölüm için eşleşme türü ve TÜİK ad(lar)ı — denetim için)
Kural (yalnızca ad metni; sırayla):
  1) tam     : küçük harf / noktalama normalleştirmesinden sonra ad aynı
  2) yakın   : karakter benzerliği ≥ 0,92 (difflib), tek aday
  3) kök     : tek sözcüklü adlarda biri ötekinin en az 6 harflik ön eki (ör. Veterinerlik ↔ Veteriner)
  4) kapsama : bölüm adının her sözcüğü (bağlaçlar hariç; ek farkı için ≥3 harflik ön ek) TÜİK adında geçiyor —
               TÜİK adı bölüm adını KAPSAMALI ve en fazla 1 ek sözcük taşımalı (ör. Tekstil Tasarımı → Tekstil ve moda
               tasarımı); sözcük eki farkı en fazla 2 harf. Ters yön
               kullanılmaz (Ağaç İşleri Endüstri Müh. → Endüstri Müh. gibi yanlış eşleşmeler olurdu). "öğretmenliği"
               iki adda birlikte olmalı. Birden çok TÜİK adı tutarsa ortalaması alınır (Dil ve Edebiyat → tüm
               "X dili ve edebiyatı" programları).
  5) anlam   : kalan bölümlerde adların embedding benzerliği (Türkçe modeller A ve B). Kabul koşulu: bölüm ↔ TÜİK adı
               KARŞILIKLI en yakın komşu VE benzerlik eşiği aşıyor. Eşik veriden: adı birebir eşleşen bölümlerin
               kendi adı dışındaki en benzer TÜİK adına benzerliği ("yanlış eşleşme" dağılımı), %95'lik değeri.. Ör. İslam Bilimleri ↔ İslami ilimler, Sigortacılık ve Risk
               Yönetimi ↔ Sigortacılık. Modeller yüklenemezse bu adım atlanır (raporda yazar).
  6) yok     : eşleşme yok → b4, D1/D2'yi diğer bölümlerden öğrenilen regresyonla tahmin eder.
Kullanım:  C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\b3_tuik_esle.py   (xlrd gerekir: pip install xlrd)
"""
import csv, difflib, re, sys
from pathlib import Path
import numpy as np

KOK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
ONET, VERI, RAPOR = KOK / "onet", KOK / "veri", KOK / "cikti" / "rapor"
BAGLAC = {"ve", "ile", "veya"}
GRUP = {"Çok düşük": 1, "Düşük": 2, "Orta": 3, "Yüksek": 4, "Çok yüksek": 5}


def oku(dosya):
    import xlrd
    sh = xlrd.open_workbook(ONET / dosya).sheet_by_index(0); out = {}
    for r in range(4, sh.nrows):
        ad = str(sh.cell_value(r, 0)).split("\n")[0].split("\r")[0].strip()
        if not ad or ad.startswith(("Toplam", "Kaynak", "Source", "*", "Not")):
            continue
        out[ad] = [sh.cell_value(r, c) for c in (1, 3, 5, 7)]
    return out


def nz(s):
    s = s.replace("İ", "i").replace("I", "ı").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-zçğıöşü0-9 ]", " ", s)).strip()


def sayi(l):
    x = [float(v) for v in l if isinstance(v, float)]
    return float(np.mean(x)) if x else np.nan


def grup(l):
    x = [GRUP[str(v).split("\n")[0].split("\r")[0].strip()] for v in l
         if str(v).split("\n")[0].split("\r")[0].strip() in GRUP]
    return float(np.mean(x)) if x else np.nan


def _ayni_sozcuk(a, b):
    """Ek farkı en fazla 2 harf (dil ~ dili, edebiyat ~ edebiyatı; finans ≁ finansman)."""
    kisa, uzun = sorted((a, b), key=len)
    return len(kisa) >= 3 and uzun.startswith(kisa) and len(uzun) - len(kisa) <= 2


def kapsar(bolum, tuik):
    """TÜİK adı bölüm adının tüm sözcüklerini içeriyor ve en fazla 1 ek sözcük taşıyor mu."""
    k = [w for w in bolum.split() if w not in BAGLAC]
    u = [w for w in tuik.split() if w not in BAGLAC]
    if len(k) < 2 or not len(k) <= len(u) <= len(k) + 1 or ("öğretmenliği" in k) != ("öğretmenliği" in u):
        return False
    return all(any(_ayni_sozcuk(a, b) for b in u) for a in k)


def kok(bolum, tuik):
    return " " not in bolum and " " not in tuik and min(len(bolum), len(tuik)) >= 6 and \
        (bolum.startswith(tuik) or tuik.startswith(bolum))


def vektorler(metinler):
    """Türkçe embedding modelleri (A, B) — L2-normalize, modellerin kosinüs benzerliği ortalanır."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from embedding_saglayici import embed_et
    return [embed_et(metinler, m, onek="query") for m in ("model_a", "model_b")]


def anlam_adimi(bolumler, T, rapor, vektor_fn=None):
    vektor_fn = vektor_fn or vektorler
    try:
        tk = sorted(T)
        Vb, Vt = vektor_fn([nz(b) for b in bolumler]), vektor_fn(tk)
    except Exception as e:                                      # model yoksa adım atlanır
        print(f"Anlam adımı atlandı (embedding modeli yüklenemedi: {e})")
        return
    S = np.mean([a @ c.T for a, c in zip(Vb, Vt)], 0)
    ti = {T[k]: j for j, k in enumerate(tk)}
    # Eşik veriden: adı birebir eşleşen bölümlerin, KENDİ TÜİK adı dışındaki en benzer TÜİK adına benzerliği
    # "yanlış eşleşme" dağılımıdır; eşik bu dağılımın %95'lik değeri (yanlış kabul oranı ≈ %5, karşılıklı en yakın
    # komşu koşuluyla birlikte daha da düşük).
    yanlis = []
    for i, r in enumerate(rapor):
        if r[1] == "tam" and r[2] in ti:
            x = S[i].copy(); x[ti[r[2]]] = -9; yanlis.append(x.max())
    if not yanlis:
        print("Anlam adımı atlandı (birebir eşleşen bölüm yok, eşik hesaplanamadı)")
        return
    esik = float(np.percentile(yanlis, 95))
    kullanilan = {a for r in rapor for a in r[2].split(" | ") if a}
    yeni = 0
    for i, r in enumerate(rapor):
        if r[1] != "yok":
            continue
        j = int(np.argmax(S[i]))
        if S[i, j] >= esik and int(np.argmax(S[:, j])) == i and tk[j] and T[tk[j]] not in kullanilan:
            r[1], r[2] = "anlam", T[tk[j]]; yeni += 1
            r.append(round(float(S[i, j]), 3))
    print(f"Anlam adımı: eşik {esik:.3f} (yanlış eşleşme dağılımının %95'i), yeni eşleşme {yeni}")


def main():
    # TÜİK dosyalarında aynı program farklı büyük/küçük harfle yazılabiliyor ("Geleneksel Türk/türk sanatları"):
    # değerler normalleştirilmiş adla tutulur.
    nzs = lambda d: {nz(k): v for k, v in d.items()}
    ist0 = oku("Lisans mezunlarının bölümlere göre kayıtlı istihdam oranı.xls")
    sure0 = oku("Lisans mezunlarının bölümlere göre ilk iş bulma süresi.xls")
    kaz0 = oku("Lisans mezunlarının bölümlere göre aylık ortalama kazanç grupları.xls")
    ist, sure, kaz = (lambda d: (lambda a: d.get(nz(a), [])))(nzs(ist0)), (lambda d: (lambda a: d.get(nz(a), [])))(nzs(sure0)), \
        (lambda d: (lambda a: d.get(nz(a), [])))(nzs(kaz0))
    T = {nz(k): k for k in sorted(set(ist0) | set(sure0) | set(kaz0))}   # sıralı: her çalıştırmada aynı sıra
    bolumler = [r["ad"] for r in csv.DictReader(open(VERI / "bolumler.csv", encoding="utf-8-sig"))]
    satir, rapor = [], []
    for b in bolumler:
        k = nz(b)
        if k in T:
            adlar, tur = [T[k]], "tam"
        else:
            c = difflib.get_close_matches(k, list(T), n=2, cutoff=0.92)
            if len(c) == 1:
                adlar, tur = [T[c[0]]], "yakın"
            else:
                c = [t for t in T if kok(k, t)]
                if len(c) == 1:
                    adlar, tur = [T[c[0]]], "kök"
                else:
                    c = [t for t in T if kapsar(k, t)]
                    adlar, tur = ([T[t] for t in c], "kapsama") if c else ([], "yok")
        rapor.append([b, tur, " | ".join(adlar)])
    anlam_adimi(bolumler, T, rapor)
    for b, tur, ad_metni, *_ in rapor:
        adlar = [a for a in ad_metni.split(" | ") if a]
        if adlar:
            ort = lambda x: float(np.mean([y for y in x if not np.isnan(y)])) if any(not np.isnan(y) for y in x) else np.nan
            v = [ort([sayi(ist(a)) for a in adlar]), ort([sayi(sure(a)) for a in adlar]), ort([grup(kaz(a)) for a in adlar])]
            if not np.isnan(v).all():
                satir.append([b] + [("" if np.isnan(x) else round(float(x), 4)) for x in v] + [" | ".join(adlar), tur])
    with open(VERI / "tuik_lisans_bolum.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["bolum", "istihdam_orani", "ilk_is_suresi_ay", "kazanc_grubu_1_5", "tuik_adlari", "eslesme"])
        w.writerows(satir)
    RAPOR.mkdir(parents=True, exist_ok=True)
    with open(RAPOR / "b3_tuik_eslesme.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["bolum", "eslesme", "tuik_adlari", "anlam_benzerligi"]); w.writerows(rapor)
    from collections import Counter
    print("TÜİK eşleşmesi:", dict(Counter(r[1] for r in rapor)), f"→ {len(satir)} bölümde TÜİK verisi")


if __name__ == "__main__":
    main()
