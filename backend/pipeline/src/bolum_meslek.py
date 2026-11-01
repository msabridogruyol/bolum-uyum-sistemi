# -*- coding: utf-8 -*-
r"""
Bölüm → meslek bağı: b4 (bölüm profili), b5 (K5 bağları) ve b6 (örnek meslekler) AYNI fonksiyonu kullanır  [2026-11-01]
Böylece öğrencinin gördüğü örnek meslekler, bölüm profilinin dayandığı mesleklerdir.

1) Benzerlik: bölüm metni (b2) ↔ ESCO meslek metni, 3 embedding modeli. Her modelin benzerlikleri bölüm satırında
   standartlaştırılır (z) ve ortalanır — modeller eşit ağırlıklı.
2) ISCO-08 kuralları (elle meslek listesi yok; yalnızca uluslararası sınıflama ve mevzuat):
   a) Öğretmenlik dışı bölümde öğretmen meslekleri (ISCO 23) sayılmaz.
   b) ISCO 2310 (yükseköğretim öğretim elemanı) hiçbir bölümde sayılmaz: 2547 sayılı Kanun'a göre öğretim üyeliği
      doktora, öğretim görevliliği lisansüstü derece ister; lisans diplomasının doğrudan mesleği değildir.
      (1 Kasım denetimi: bu meslekler öğretmenlik bölümlerini "Statü ve prestij"te en üste taşıyordu.)
   c) Beceri düzeyi: lisans → ISCO ana grup 1–3 (ILO beceri düzeyi 3–4). Bölümün en benzer mesleği başka bir ana
      gruptaysa (ör. El Sanatları → zanaatkâr meslekleri, ana grup 7) o grup da sayılır; alanın kendisi orada tanımlıdır.
3) Ağırlık: en benzer 40 meslek, ağırlık = benzerlik − 40. mesleğin benzerliği (21 Ekim kuralı).
"""
import numpy as np

UST_MESLEK = 40


def benzerlik(onb, modeller):
    nz = lambda X: X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    zr = lambda X: (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)
    return np.mean([zr(nz(np.load(onb / f"bolumler_{m}.npy")) @ nz(np.load(onb / f"meslekler_{m}.npy")).T)
                    for m in modeller], 0)


class Kurallar:
    def __init__(self, meslek):
        isco = [str(o["isco_grubu"]).zfill(4) for o in meslek]
        self.ogretmen = np.array([c.startswith("23") for c in isco])
        self.yuksekogretim = np.array([c == "2310" for c in isco])
        self.ana = np.array([c[0] for c in isco])

    def uygula(self, bolum, s):
        """s: bölümün tüm mesleklere benzerliği (kopya). Kural dışı meslekler -9 olur."""
        s = s.copy()
        if "ÖĞRETMENLİĞİ" not in bolum:
            s[self.ogretmen] = -9.0
        s[self.yuksekogretim] = -9.0
        izin = {"0", "1", "2", "3", self.ana[int(np.argmax(s))]}
        s[~np.isin(self.ana, list(izin))] = -9.0
        return s

    def agirliklar(self, bolum, s, n=UST_MESLEK):
        s = self.uygula(bolum, s)
        sira = np.argsort(-s)[:n]
        taban = s[sira[-1]]
        return {int(i): float(s[i] - taban + 1e-3) for i in sira}
