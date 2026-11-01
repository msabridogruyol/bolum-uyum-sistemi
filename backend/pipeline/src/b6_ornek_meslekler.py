# -*- coding: utf-8 -*-
r"""
B6 — Bölüm sayfasındaki örnek meslekleri veriden üretir (elle liste YOK)                          [2026-10-22]

[2026-11-01] Bölüm → meslek sırası artık b4 / b5 ile AYNI fonksiyondan gelir (bolum_meslek.py: 3 model eşit ağırlıklı,
ISCO-08 kuralları). Ayrı "ad kanıtı" kaldırıldı: b2 bölüm adını metne kattığı için ad bilgisi zaten benzerlikte.
Önceki sürüm b4'ten farklı bir sıralama kullanıyordu (Tıp'ta hekim listede yoktu, b4'ün ilk 2 mesleğindeydi).
Gösterim: b4'ün kullandığı ilk 40 meslekten benzerlik sırasıyla (aynı kökten olanlar birleşir), en fazla 5.
Neden (2026-10-22): eski a2_ornek_meslek_sql.py, 74 bölümde listeyi elle yazılmış bir dosyadan alıyordu
(veri/bolum_meslek_elle.csv); o dosya artık yalnızca rapordaki "eski_elle_liste" karşılaştırma sütunu için okunur,
sonuca girmez.

Yöntem:
  1) Sıra: bolum_meslek.benzerlik (3 modelin satır z-skorlu ortalaması) + Kurallar.uygula (ISCO-08: öğretmenlik
     dışı bölümde ISCO 23, tüm bölümlerde 2310 yok; izinli ana gruplar) — b4 ve b5 ile birebir aynı.
  2) Aday: b4'ün profilde kullandığı ilk UST_MESLEK (40) meslek, benzerlik sırasıyla.
  3) Aynı ad / aynı meslek kökü birleşir; rol köklerinden (mühendis, teknisyen…) en fazla 2 (meslek_adlari.py).
  4) Bölüm başına en fazla 5 meslek. SQL'e ham kosinüs ortalaması ve z ≥ 1 olan model sayısı da yazılır (bilgi amaçlı).
Yükleme: admin paneli → Pipeline Sonuçları → "Örnek meslekler" adımı (önizleme, sonra canlıya al; önceki hâl yedeklenir).
Girdi : onbellek/bolumler_model_*.npy (b2), onbellek/meslekler_model_*.npy (m4), veri/bolumler.csv, veri/meslekler_esco.csv
Çıktı : cikti/ornek_meslekler_veri.sql      (admin → Pipeline Sonuçları ile yüklenir; bolum_ornek_meslekler tablosunu yeniler)
        cikti/rapor/b6_ornek_meslekler.csv   (bölüm başına yeni liste + eski elle liste — karşılaştırma)
Kullanım:  C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\b6_ornek_meslekler.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

KOK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
ONB, VERI, CIKTI = KOK / "onbellek", KOK / "veri", KOK / "cikti"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from meslek_adlari import ad_duzeltmeleri_oku, bas_harf_duzelt, benzerleri_birlestir, norm, q  # noqa: E402

MODELLER = ("model_a", "model_b", "model_c")
BOLUM_BASINA, Z_ESIGI = 5, 1.0


def oku(yol, ayirici=","):
    with open(yol, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=ayirici))


def main():
    meslek = oku(VERI / "meslekler_esco.csv")
    bolumler = [r["ad"] for r in oku(VERI / "bolumler.csv")]
    bad = list(np.load(ONB / "bolum_isimleri.npy", allow_pickle=True))
    bi = {b: i for i, b in enumerate(bad)}
    from bolum_meslek import UST_MESLEK, Kurallar, benzerlik
    kural = Kurallar(meslek)
    sira_S = benzerlik(ONB, MODELLER)               # b4 / b5 ile aynı sıralama
    S, Z = [], []
    for m in MODELLER:
        B = np.load(ONB / f"bolumler_{m}.npy"); M = np.load(ONB / f"meslekler_{m}.npy")
        s = (B / np.linalg.norm(B, axis=1, keepdims=True)) @ (M / np.linalg.norm(M, axis=1, keepdims=True)).T
        S.append(s); Z.append((s - s.mean()) / (s.std() + 1e-12))
    ham, guclu = np.mean(S, 0), np.sum(np.array(Z) >= Z_ESIGI, 0)   # SQL'e ham kosinüs ve model sayısı yazılır

    # Ad düzeltmeleri (yalnızca çeviri / yazım düzeltmesi, ör. "İct" → "BT"). Listeden ÇIKARMA kayıtları (yeni ad boş)
    # elle seçim olduğu için uygulanmaz.
    duz = {k: v for k, v in ad_duzeltmeleri_oku().items() if v}

    def ad_of(ad):
        ad = ad.replace("\u0307", "").strip()
        return duz.get(norm(ad)) or bas_harf_duzelt(ad)

    eski = {}
    if (VERI / "bolum_meslek_elle.csv").exists():
        for r in oku(VERI / "bolum_meslek_elle.csv", ";"):
            eski[r["bolum"].strip()] = r[list(r)[1]]
    degerler, rapor, dagilim = [], [], {}
    for b in bolumler:
        if b not in bi:
            continue
        i = bi[b]
        s = kural.uygula(b, sira_S[i])
        aday = [j for j in np.argsort(-s)[:UST_MESLEK] if s[j] > -9]      # b4'ün profilde kullandığı meslekler
        # Sıra: benzerlik (b4 ile aynı). Beceri düzeyine göre öne alma denendi (1 Kasım): pilot, şef, gemi makine
        # zabiti, antrenör ISCO'da 3. grupta olduğu için bu bölümlerin asıl meslekleri listeden düşüyordu; uygulanmadı.
        liste = [(int(guclu[i, j]), float(s[j]), meslek[j]["esco_kodu"], ad_of(meslek[j]["ad"]), float(ham[i, j])) for j in aday]
        liste = benzerleri_birlestir(liste)          # sıra korunur: b4 sırası
        sec = liste[:BOLUM_BASINA]
        dagilim[len(sec)] = dagilim.get(len(sec), 0) + 1
        for sira, (gk, _, kod, ad, benz) in enumerate(sec, 1):
            degerler.append(f"  ({q(b)}, {q(kod)}, {q(ad)}, {benz:.4f}, {gk}, {sira})")
        rapor.append([b, " | ".join(x[3] for x in sec), eski.get(b, "")])

    if not degerler:
        raise SystemExit("Hiç örnek meslek üretilmedi — SQL yazılmadı (girdi dosyalarını kontrol edin).")
    sql = f"""-- bolum_ornek_meslekler (b6, veri: bölüm metni ↔ ESCO meslek, 3 model; elle liste yok) — {len(degerler)} satır
BEGIN;
DELETE FROM bolum_ornek_meslekler;
INSERT INTO bolum_ornek_meslekler (bolum_id, meslek_isco_kodu, meslek_adi, benzerlik_skoru, model_sayisi, sira)
SELECT b.id, v.isco, v.ad, v.benzerlik, v.model_sayisi, v.sira
FROM (VALUES
{",{}".format(chr(10)).join(degerler)}
) AS v(bolum_adi, isco, ad, benzerlik, model_sayisi, sira)
JOIN bolumler b ON b.ad = v.bolum_adi;
COMMIT;
SELECT COUNT(*) AS satir, COUNT(DISTINCT bolum_id) AS bolum FROM bolum_ornek_meslekler;
"""
    (CIKTI / "ornek_meslekler_veri.sql").write_text(sql, encoding="utf-8")
    (CIKTI / "rapor").mkdir(parents=True, exist_ok=True)
    with open(CIKTI / "rapor" / "b6_ornek_meslekler.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["bolum", "yeni_liste (veri)", "eski_elle_liste"]); w.writerows(rapor)
    print(f"Tamam: {len(degerler)} satır, {len(rapor)} bölüm → cikti/ornek_meslekler_veri.sql | "
          + ", ".join(f"{k} meslek: {v} bölüm" for k, v in sorted(dagilim.items(), reverse=True)))


if __name__ == "__main__":
    main()
