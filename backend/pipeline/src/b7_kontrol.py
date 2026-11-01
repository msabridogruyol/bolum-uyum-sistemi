# -*- coding: utf-8 -*-
r"""
B7 — Bölüm ↔ meslek eşleşmesinin otomatik kalite kontrolü (2026-11-01). Yalnızca ölçer; hiçbir dosyayı değiştirmez.

1) Ad eşi testi: adı bölüm adının ayırt edici sözcükleriyle başlayan meslekler (ör. Arkeoloji → Arkeolog,
   Matematik → Matematikçi) otomatik bulunur; bu mesleğin bölümün meslek sıralamasındaki yeri ölçülür.
   Liste elle yazılmaz; ad kuralı her çalıştırmada aynıdır.
2) Merkez meslek (hub) testi: bir meslek kaç bölümün ilk 40 mesleğinde var (çok sayıda bölüme giren meslek,
   bölümleri birbirine benzetir).
3) Model başına sonuç: hangi embedding modelinin zayıf kaldığı görülür.
Çıktı: ekrana özet + cikti/rapor/b7_kontrol.csv
Kullanım:  C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\b7_kontrol.py
"""
import collections
import csv
import re
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
ONB, VERI, RAPOR = KOK / "onbellek", KOK / "veri", KOK / "cikti" / "rapor"
MODELLER = ["model_a", "model_b", "model_c"]
GENEL = {"ve", "ile", "bilimleri", "bilimi", "mühendisliği", "öğretmenliği", "yönetimi", "işletmeciliği", "teknolojileri",
         "teknolojisi", "eğitimi", "tasarımı", "sistemleri", "uluslararası", "programcılığı", "uygulamaları", "sanatları"}


def kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def main():
    meslek = list(csv.DictReader(open(VERI / "meslekler_esco.csv", encoding="utf-8-sig")))
    ad = [kucuk(o["ad"]) for o in meslek]
    bad = list(np.load(ONB / "bolum_isimleri.npy", allow_pickle=True))
    isco23 = np.array([o["isco_grubu"].zfill(4).startswith("23") for o in meslek])
    nz = lambda X: X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    zr = lambda X: (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)
    S = {m: nz(np.load(ONB / f"bolumler_{m}.npy")) @ nz(np.load(ONB / f"meslekler_{m}.npy")).T for m in MODELLER}
    from bolum_meslek import Kurallar, benzerlik
    kural = Kurallar(meslek)
    S["birlesik"] = benzerlik(ONB, MODELLER)                          # b4 / b5 / b6 ile aynı birleştirme
    S["kurallarla"] = np.array([kural.uygula(b, S["birlesik"][i]) for i, b in enumerate(bad)])  # ISCO kuralları sonrası

    es = {}
    for b in bad:
        kok = [w[:5] for w in kucuk(b).split() if w not in GENEL and len(w) >= 4]
        if not kok:
            continue
        hit = [i for i, a in enumerate(ad) if all(any(t.startswith(k) for t in re.split(r"\W+", a)) for k in kok)
               and ("ÖĞRETMENLİĞİ" in b or not isco23[i])]          # öğretmenlik dışı bölümde öğretmen meslekleri sayılmaz
        if 0 < len(hit) < 60:
            es[b] = hit

    def siralar(X):
        out = {}
        for b, hit in es.items():
            s = X[bad.index(b)].copy()
            if "ÖĞRETMENLİĞİ" not in b:
                s[isco23] = -9
            r = np.empty(len(s), int); r[np.argsort(-s)] = np.arange(1, len(s) + 1)
            out[b] = int(r[hit].min())
        return out

    sonuc = {k: siralar(X) for k, X in S.items()}
    print(f"Ad eşi testi: {len(es)} bölüm (adı bölüm adıyla başlayan meslek bulunanlar)")
    for k, r in sonuc.items():
        v = np.array(list(r.values()))
        print(f"  {k:9s} medyan sıra {np.median(v):4.0f} · ilk 5'te %{100 * np.mean(v <= 5):3.0f} · ilk 40'ta %{100 * np.mean(v <= 40):3.0f}")
    X = S["kurallarla"].copy()
    say = collections.Counter()
    for i, b in enumerate(bad):
        s = X[i].copy()
        if "ÖĞRETMENLİĞİ" not in b:
            s[isco23] = -9
        say.update(np.argsort(-s)[:40].tolist())
    print("Merkez meslekler (kaç bölümün ilk 40'ında):", ", ".join(f"{meslek[i]['ad']} {n}" for i, n in say.most_common(6)))
    kotu = sorted(sonuc["kurallarla"].items(), key=lambda x: -x[1])[:10]
    print("Ad eşi en geride kalan bölümler:", ", ".join(f"{b} ({r})" for b, r in kotu))
    RAPOR.mkdir(parents=True, exist_ok=True)
    with open(RAPOR / "b7_kontrol.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["bolum", "ad_esi_meslekler"] + list(sonuc))
        for b, hit in es.items():
            w.writerow([b, " | ".join(meslek[i]["ad"] for i in hit[:5])] + [sonuc[k][b] for k in sonuc])


if __name__ == "__main__":
    main()
