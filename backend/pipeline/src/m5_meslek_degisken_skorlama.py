# -*- coding: utf-8 -*-
"""
M5 — Meslek ↔ Değişken Skorlaması

[2026-10-07] YÖNTEM: ANLAMSAL İZDÜŞÜM (semantic projection)
  Kaynak yöntem: Grand, Blank, Pereira & Fedorenko (2022), "Semantic projection recovers rich human
  knowledge of multiple object features from word embeddings", Nature Human Behaviour 6, 975-987.

  Eski yöntem (benzerlik): meslek metni ile değişken açıklaması arasındaki kosinüs benzerliği. Bu,
  "iki metin aynı konudan mı bahsediyor?" sorusunu ölçer, "bu meslek bu özelliği ne kadar gerektirir?"
  sorusunu değil. Bazı açıklamalar (ör. "statü / prestij") hemen her meslek metnine benzediği için
  her bölümde yüksek çıkıyordu; Tarih'te sayısal eğilim sözelden yüksek, Tıp'ta "topluma katkı" en düşük
  değer gibi sonuçlar üretiyordu.

  Yeni yöntem: her değişken için iki KUTUP tanımlanır (veri/degisken_kutuplari.csv):
     yüksek kutup — bu özelliği yoğun gerektiren işi anlatan 3 cümle
     düşük kutup  — tersini anlatan 3 cümle
  Meslek puanı = ortalama benzerlik(meslek, yüksek kutup) − ortalama benzerlik(meslek, düşük kutup).
  İki kutba ortak olan "genel benzerlik" bu farkta birbirini götürür; geriye mesleğin bu eksendeki
  konumu kalır. Sonra her değişken tüm meslekler arasında standartlaştırılır (50 + 15·z, 0-100).

  Kutuplar DEĞİŞKENİN TANIMIDIR — her meslek ve bölüm için aynı şekilde, otomatik uygulanır;
  hiçbir mesleğe ya da bölüme elle puan verilmez. 3 modelin (A, B, C) her biri ayrı hesaplar,
  b4 bunların ortalamasını alır. C modeli İngilizce olduğu için kutupların İngilizce karşılığı kullanılır.

  OTOMATİK KALİTE KONTROLÜ: veri/m5_kontrol_meslekleri.csv'deki bilinen meslekler (ör. "Doğa /
  laboratuvar" özelliğinde Biyolog üst %25'te, Muhasebeci alt %25'te olmalı) her çalıştırmada test
  edilir. Bu liste puanlamaya GİRMEZ, yalnızca sonucu sınar. Sonuç: cikti/m5_kalite_kontrol.csv

  [2026-10-07 — KELİME SIZINTISI DÜZELTMELERİ]
  1) Karşıt-çift cümleler: D/P/I/A7/A8 kutupları aynı bağlamda yalnızca özelliği tersine çeviren
     cümle çiftleridir. Kutuplarda başka bir alanın adı (bilgisayar, makine, finans, gelir, sözleşme...)
     geçmez; böylece o alanın meslekleri özellikten bağımsız olarak bir uca çekilmez.
  2) "@KATMAN" düşük kutbu: ilgi alanları (A1-A6, A9) için düşük kutup, aynı gruptaki DİĞER ilgi
     alanlarının yüksek kutuplarının ortalamasıdır. "Sayısal" artık "sanatın tersi" gibi keyfî bir
     karşıtla değil, "diğer ilgi alanlarına göre ne kadar sayısal" sorusuyla ölçülür.
  3) Meslek genel kayması arındırma (SATIR_ARINDIR): bazı meslek metinleri (ör. kısa ya da bozuk
     çeviriler) hemen her özellikte en altta / en üstte çıkıyordu. Her meslek için, aynı katmandaki
     değişkenlerin ortalaması çıkarılır (katman içi satır merkezleme), sonra her değişken yeniden
     standartlaştırılır. Bu, eşleşmede zaten kullanılan katman içi ölçekleme mantığının meslek
     düzeyindeki karşılığıdır.

  Kutbu tanımlı olmayan değişken varsa o değişken için eski benzerlik yöntemi kullanılır (uyarı verilir).
  Karşılaştırma için eski yöntem:  python m5_meslek_degisken_skorlama.py benzerlik
"""

import csv
import re
import sys
import unicodedata
import numpy as np
from pathlib import Path

from embedding_saglayici import embed_et, MODEL_TANIMLARI

ONBELLEK_DIZINI = Path(__file__).parent.parent / "onbellek"
VERI_DIZINI = Path(__file__).parent.parent / "veri"
CIKTI_DIZINI = Path(__file__).parent.parent / "cikti"

MODEL_ADLARI = ["model_a", "model_b", "model_c"]
OLCEK_STD = 15.0          # standartlaştırma: 50 + 15·z
KONTROL_YUKSEK = 75.0     # kontrol: "yüksek olmalı" meslek bu yüzdeliğin üstünde
KONTROL_DUSUK = 25.0      # kontrol: "düşük olmalı" meslek bu yüzdeliğin altında
SATIR_ARINDIR = False     # denendi: birleşik cümle setinde kapalı daha iyi sonuç verdi (sistem_dogrulama)
KATMAN_ISARETI = "@KATMAN"  # düşük kutup = aynı katmandaki diğer ilgi alanlarının yüksek kutupları
# [2026-10-08] "@KATMAN_TUMU": düşük kutup = aynı katmandaki TÜM diğer değişkenlerin (P4 hariç) yüksek kutup
# merkezlerinin ortalaması. Uzman profiliyle doğrulamada Risk alma, İnisiyatif, Titizlik ve Güvence'de
# en iyi sonucu bu verdi (ör. Risk alma r: -0,18 → 0,36).
KATMAN_TUMU_ISARETI = "@KATMAN_TUMU"
KATMAN_TUMU_HARIC = {"P4"}


def norm(metin) -> str:
    t = unicodedata.normalize("NFC", str(metin)).replace(" ", " ").replace("̇", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t.replace("İ", "i").replace("I", "ı").lower().replace("ı", "i")


def meslek_isco_kodlari():
    with open(VERI_DIZINI / "meslekler_esco.csv", encoding="utf-8-sig") as f:
        return [r["esco_kodu"] for r in csv.DictReader(f)]


def kutuplari_oku() -> dict:
    """kod -> {'yuksek': [...], 'dusuk': [...], 'yuksek_en': [...], 'dusuk_en': [...]}"""
    yol = VERI_DIZINI / "degisken_kutuplari.csv"
    if not yol.exists():
        return {}
    sonuc = {}
    with open(yol, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            sonuc[r["kod"].strip()] = {k: [x.strip() for x in (r.get(k) or "").split("|") if x.strip()]
                                       for k in ("yuksek", "dusuk", "yuksek_en", "dusuk_en")}
    return sonuc


def standartlastir(x: np.ndarray) -> np.ndarray:
    """Her sütun (değişken) tüm meslekler arasında 50 + 15·z, 0-100'e kırpılır."""
    ort = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    return np.clip(50.0 + OLCEK_STD * (x - ort) / np.where(std < 1e-12, 1.0, std), 0, 100)


def izdusum_matrisi(model_adi: str, meslek_vek: np.ndarray, degisken_kodlari, kutuplar: dict) -> tuple[np.ndarray, list]:
    ingilizce = "-en" in MODEL_TANIMLARI[model_adi].lower()
    eski_vek = np.load(ONBELLEK_DIZINI / f"degiskenler_{model_adi}.npy")   # yedek: eski yöntem
    ham = np.zeros((meslek_vek.shape[0], len(degisken_kodlari)))
    eski_yontemle = []
    # tüm kutup cümlelerini tek seferde embed et
    cumleler, indeks, katman_tumu = [], {}, set()
    for kod in degisken_kodlari:
        k = kutuplar.get(str(kod))
        if not k:
            continue
        y, d = (k["yuksek_en"], k["dusuk_en"]) if ingilizce else (k["yuksek"], k["dusuk"])
        if ingilizce and (not y or not d):            # İngilizce yoksa Türkçeye düş
            y, d = k["yuksek"], k["dusuk"]
        if not y or not d:
            continue
        tumu = d == [KATMAN_TUMU_ISARETI]
        if d == [KATMAN_ISARETI] or tumu:
            d = []                                    # düşük kutup aşağıda katmandan kurulur
        indeks[str(kod)] = (len(cumleler), len(y), len(d))
        if tumu:
            katman_tumu.add(str(kod))
        cumleler += y + d
    vek = embed_et(cumleler, model_adi, onek="passage") if cumleler else np.zeros((0, meslek_vek.shape[1]))
    yuksek_merkez = {kod: vek[b:b + ny].mean(axis=0) for kod, (b, ny, nd) in indeks.items()}
    katman_grubu = {}
    for kod, (b, ny, nd) in indeks.items():
        if nd == 0 and kod not in katman_tumu:
            katman_grubu.setdefault(kod[0], []).append(kod)
    for j, kod in enumerate(degisken_kodlari):
        kod = str(kod)
        if kod in indeks:
            bas, ny, nd = indeks[kod]
            yuksek = yuksek_merkez[kod]
            if nd == 0 and kod in katman_tumu:
                digerleri = [yuksek_merkez[x] for x in indeks if x[0] == kod[0] and x != kod and x not in KATMAN_TUMU_HARIC]
                if not digerleri:
                    raise ValueError(f"{kod}: {KATMAN_TUMU_ISARETI} için aynı katmanda başka değişken yok")
                dusuk = np.mean(digerleri, axis=0)
            elif nd == 0:
                digerleri = [yuksek_merkez[x] for x in katman_grubu[kod[0]] if x != kod]
                if not digerleri:
                    raise ValueError(f"{kod}: {KATMAN_ISARETI} için aynı katmanda en az 2 değişken gerekir")
                dusuk = np.mean(digerleri, axis=0)
            else:
                dusuk = vek[bas + ny:bas + ny + nd].mean(axis=0)
            ham[:, j] = meslek_vek @ yuksek - meslek_vek @ dusuk
        else:
            ham[:, j] = meslek_vek @ eski_vek[j]
            eski_yontemle.append(kod)
    return ham, eski_yontemle


def satir_arindir(skor: np.ndarray, degisken_kodlari) -> np.ndarray:
    """Katman içi satır merkezleme: her meslekte, aynı katmandaki değişkenlerin ortalaması çıkarılır,
    sonra her değişken meslekler arasında yeniden 50 + 15·z yapılır."""
    z = (skor - skor.mean(axis=0, keepdims=True)) / (skor.std(axis=0, keepdims=True) + 1e-12)
    for h in sorted({str(k)[0] for k in degisken_kodlari}):
        sut = [j for j, k in enumerate(degisken_kodlari) if str(k)[0] == h]
        if len(sut) > 1:
            z[:, sut] = z[:, sut] - z[:, sut].mean(axis=1, keepdims=True)
    return standartlastir(z)


def genel_kayma_raporu(skor: np.ndarray, meslek_isimleri, baslik: str) -> None:
    """Kaç değişkende en alttaki 10 meslek arasında? (aynı meslek çok değişkende en altta ise genel kayma)"""
    say = np.zeros(skor.shape[0], dtype=int)
    for j in range(skor.shape[1]):
        say[np.argsort(skor[:, j])[:10]] += 1
    s = np.argsort(-say)[:5]
    print(f"  {baslik}: " + ", ".join(f"{meslek_isimleri[i]} ({say[i]})" for i in s))


def kalite_kontrol(skor_ort: np.ndarray, meslek_isimleri, degisken_kodlari) -> None:
    yol = VERI_DIZINI / "m5_kontrol_meslekleri.csv"
    if not yol.exists():
        print("  (veri/m5_kontrol_meslekleri.csv yok — kalite kontrolü atlandı)")
        return
    ad_indeks = {}
    for i, ad in enumerate(meslek_isimleri):
        ad_indeks.setdefault(norm(ad), []).append(i)
    kod_indeks = {str(k): j for j, k in enumerate(degisken_kodlari)}
    yuzdelik = skor_ort.argsort(axis=0).argsort(axis=0) / (skor_ort.shape[0] - 1) * 100
    satirlar, gecen, toplam, bulunamayan = [], 0, 0, []
    with open(yol, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            kod = r["kod"].strip()
            if kod not in kod_indeks:
                continue
            j = kod_indeks[kod]
            for yon, sutun in (("yüksek", "yuksek_olmali"), ("düşük", "dusuk_olmali")):
                for ad in [x.strip() for x in (r.get(sutun) or "").split("|") if x.strip()]:
                    idx = ad_indeks.get(norm(ad))
                    if not idx:
                        bulunamayan.append(ad); continue
                    p = float(np.mean([yuzdelik[i, j] for i in idx]))
                    ok = p >= KONTROL_YUKSEK if yon == "yüksek" else p <= KONTROL_DUSUK
                    toplam += 1; gecen += ok
                    satirlar.append([kod, ad, yon, round(p, 1), "GEÇTİ" if ok else "KALDI"])
    with open(CIKTI_DIZINI / "m5_kalite_kontrol.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["degisken", "meslek", "olmasi_gereken", "yuzdelik", "sonuc"])
        w.writerows(satirlar)
    print(f"\n=== Kalite kontrolü (bilinen meslekler) ===")
    print(f"Geçen: {gecen}/{toplam} (%{gecen / max(toplam, 1) * 100:.0f})  → ayrıntı: cikti/m5_kalite_kontrol.csv")
    kalanlar = [s for s in satirlar if s[4] == "KALDI"]
    for s in kalanlar[:15]:
        print(f"  KALDI  {s[0]}  {s[1]}: {s[2]} olmalıydı, yüzdelik {s[3]}")
    if bulunamayan:
        print(f"  (listede bulunamayan meslek adı: {', '.join(sorted(set(bulunamayan))[:10])})")


def calistir(yontem: str = "izdusum"):
    meslek_isimleri = np.load(ONBELLEK_DIZINI / "meslek_isimleri.npy", allow_pickle=True)
    degisken_kodlari = np.load(ONBELLEK_DIZINI / "degisken_kodlari.npy", allow_pickle=True)
    isco_kodlari = meslek_isco_kodlari()
    kutuplar = kutuplari_oku() if yontem == "izdusum" else {}
    print(f"YÖNTEM: {'anlamsal izdüşüm' if yontem == 'izdusum' else 'eski benzerlik'} | "
          f"kutbu tanımlı değişken: {sum(1 for k in degisken_kodlari if str(k) in kutuplar)}/{len(degisken_kodlari)}")

    CIKTI_DIZINI.mkdir(exist_ok=True)
    matrisler = {}
    for model_adi in MODEL_ADLARI:
        print(f"--- {model_adi} ---")
        meslek_vek = np.load(ONBELLEK_DIZINI / f"meslekler_{model_adi}.npy")
        if yontem == "izdusum":
            ham, eski = izdusum_matrisi(model_adi, meslek_vek, degisken_kodlari, kutuplar)
            if eski:
                print(f"  UYARI — kutbu olmayan {len(eski)} değişken eski yöntemle: {', '.join(eski)}")
        else:
            ham = meslek_vek @ np.load(ONBELLEK_DIZINI / f"degiskenler_{model_adi}.npy").T
        skor = standartlastir(ham)
        if SATIR_ARINDIR:
            skor = satir_arindir(skor, degisken_kodlari)
        matrisler[model_adi] = skor
        np.save(ONBELLEK_DIZINI / f"m5_skor_matrisi_{model_adi}.npy", skor)

    ort = np.mean([matrisler[m] for m in MODEL_ADLARI], axis=0)
    print("\nGenel kayma kontrolü — en çok değişkende en alttaki 10'a giren meslekler "
          f"(87 değişkende; arındırma {'AÇIK' if SATIR_ARINDIR else 'KAPALI'}):")
    genel_kayma_raporu(ort, meslek_isimleri, "sonuç")
    # modeller arası uyum: her değişkende 3 modelin meslek sıralamaları ne kadar benzer?
    from itertools import combinations
    uyum = []
    for j in range(len(degisken_kodlari)):
        r = [np.corrcoef(matrisler[a][:, j], matrisler[b][:, j])[0, 1] for a, b in combinations(MODEL_ADLARI, 2)]
        uyum.append(np.nanmean(r))
    print(f"\nModeller arası uyum (ortalama korelasyon): {np.nanmean(uyum):.2f}  "
          f"(en düşük 3: {', '.join(f'{degisken_kodlari[j]} {uyum[j]:.2f}' for j in np.argsort(uyum)[:3])})")

    # her değişkende en yüksek / en düşük 5 meslek (inceleme için)
    with open(CIKTI_DIZINI / "m5_degisken_uclari.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["degisken", "en_yuksek_10", "en_dusuk_10", "model_uyumu"])
        for j, kod in enumerate(degisken_kodlari):
            s = np.argsort(-ort[:, j])
            w.writerow([kod, " | ".join(map(str, meslek_isimleri[s[:10]])), " | ".join(map(str, meslek_isimleri[s[-10:]])), round(float(uyum[j]), 2)])

    kalite_kontrol(ort, meslek_isimleri, degisken_kodlari)

    cikti_yolu = CIKTI_DIZINI / "m5_meslek_degisken_skorlari.csv"
    with open(cikti_yolu, "w", newline="", encoding="utf-8-sig") as f:
        yazici = csv.writer(f, delimiter=";")
        yazici.writerow(["meslek_isco_kodu", "meslek_adi", "degisken_kod", "model", "skor"])
        for model_adi in MODEL_ADLARI:
            m = matrisler[model_adi]
            for i in range(len(meslek_isimleri)):
                for k in range(len(degisken_kodlari)):
                    yazici.writerow([isco_kodlari[i], meslek_isimleri[i], degisken_kodlari[k],
                                     model_adi, round(float(m[i, k]), 2)])

    print(f"\nM5 tamamlandı. Çıktılar: {cikti_yolu.name}, m5_degisken_uclari.csv, m5_kalite_kontrol.csv + onbellek/m5_skor_matrisi_*.npy")


if __name__ == "__main__":
    calistir(sys.argv[1] if len(sys.argv) > 1 else "izdusum")
