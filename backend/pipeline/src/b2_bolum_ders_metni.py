# -*- coding: utf-8 -*-
r"""
B2 — Bölüm metnini resmî ders planlarından kurar ve bölüm embedding'lerini yeniden hesaplar (2026-10-21; güncelleme 2026-11-01)

Neden: bölüm–meslek eşleştirmesine giren bölüm metni (kisa_aciklama) yapay zekâ ile yazılmıştı. Bu adım, bölüm metnini
üniversitelerin resmî lisans ders planlarındaki DERS ADLARINDAN kurar (veri/bolum_dersleri.csv; her satırda kaynak
üniversite ve bağlantı). Resmî ders planı bulunamayan bölümlerde mevcut kısa açıklama kullanılır ve raporda işaretlenir.

Girdi : veri/bolum_dersleri.csv  (bolum;durum;dersler (| ile);kaynaklar)
        veri/bolumler.csv        (ad, kisa_aciklama — yedek metin)
Çıktı : onbellek/bolumler_model_{a,b,c}.npy  (eski dosyalar önce yedekler/ klasörüne kopyalanır)
        veri/bolum_metni.csv     (bolum;kaynak;metin — embedding'e giren metin, denetim için)
Meslek ve değişken embedding'lerine DOKUNMAZ.
[2026-11-01] 1 Kasım çalıştırmasının denetiminde bulunan üç kök neden düzeltildi:
  1) YÖK ortak zorunlu dersleri (Türk Dili, Atatürk İlkeleri ve İnkılap Tarihi, Yabancı Dil) ve her programda olan
     dersler (Kariyer Planlama, Staj, Topluma Hizmet, İş Sağlığı ve Güvenliği, Bitirme/Diploma, adsız Seçmeli) metinden
     çıkarılır: 232 bölümün 142'sinde vardı ve bölümü "dil" mesleklerine çekiyordu (ör. Deri Müh. → Dilbilimci).
     Dersin konusu bölümün kendi adındaysa (ör. İş Sağlığı ve Güvenliği bölümü) ders çıkarılmaz.
  2) Uzun ders listesi model sınırında kırpılıyordu (kısa sınırlı modelde yalnız ilk yıl dersleri okunuyordu).
     Liste 8'er derslik parçalara bölünür; her parça ayrı kodlanır, bölüm vektörü parçaların ortalamasıdır.
  3) Her parça bölümün resmî adıyla başlar ("Tıp bölümü dersleri: …"); ad, YÖK program adıdır (elle bilgi yok).
  60'tan fazla ders varsa ilk 60 yerine programa eşit aralıklı 60 ders alınır (son sınıf dersleri de girer).
Kullanım:  C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\b2_bolum_ders_metni.py
Sonra: b4_bolum_profili.py, ardından b5_k5_baglari.py
"""
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
VERI, ONB, YEDEK = KOK / "veri", KOK / "onbellek", KOK / "yedekler"
sys.path.insert(0, str(Path(__file__).resolve().parent))
EN_FAZLA_DERS = 60
PARCA = 8             # bir parçadaki ders sayısı (en kısa sınırlı modelin sınırına sığar)
# YÖK ortak zorunlu dersleri ve her programda bulunan dersler (ders adının BAŞI eşleşir; büyük/küçük harf duyarsız)
R = r"[\s\-.ıivx0-9]*$"   # ders adının sonunda yalnızca sıra eki (I, II, 1, -2 …) olabilir
ORTAK_DERS = re.compile(
    r"^(türk dili" + R + r"|turkish language" + R + r"|atatürk ilke|ataturk ilke|ataturk.s principles|principles of atat|"
    r"history of turkish (revolution|republic)|inkılap tarihi|(temel )?yabancı dil" + R + r"|ingilizce" + R +
    r"|english" + R + r"|kariyer planla|career planning|staj" + R + r"|yaz stajı|internship" + R +
    r"|summer (practice|training|internship)|topluma hizmet|community service|iş sağlığı ve güvenliği" + R +
    r"|occupational health and safety" + R + r"|bitirme|diploma (tezi|projesi|çalışması)|mezuniyet (projesi|tezi)|"
    r"graduation (project|thesis)|((bölüm|alan dışı|üniversite|serbest|mesleki) )?seçmeli( ders)?" + R + r"|elective" + R + ")", re.I)


def oku(yol, ayirici=","):
    with open(yol, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=ayirici))


def ingilizce_mi(s):
    return not any(c in s for c in "çğıöşüÇĞİÖŞÜ") and sum(w.lower() in {"and", "of", "to", "the", "introduction", "engineering",
                                                                       "theory", "analysis", "design", "systems"}
                                                          for w in s.split()) > 0


def kucuk(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def ortak_mi(ders, bolum):
    d = kucuk(ders).strip()
    if not ORTAK_DERS.match(d):
        return False
    # konu bölümün kendi adındaysa çıkarma (ör. "İş Sağlığı ve Güvenliği" bölümünde İSG dersleri)
    kok = [w[:5] for w in re.findall(r"\w+", d)[:3] if len(w) >= 4]
    return not (kok and all(k in kucuk(bolum) for k in kok))


def secim(dl, n):
    if len(dl) <= n:
        return dl
    return [dl[round(i * (len(dl) - 1) / (n - 1))] for i in range(n)]


def baslik(ad):
    return " ".join(w[:1] + kucuk(w[1:]) if w not in ("VE", "İLE") else kucuk(w) for w in ad.split())


def parcali_embed(embed_et, parcalar, model):
    """parcalar: her bölüm için metin listesi → bölüm başına parça vektörlerinin ortalaması (L2 normalize)."""
    duz = [p for ps in parcalar for p in ps]
    V = embed_et(duz, model, onek="passage")
    V = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-12)
    cikti, i = [], 0
    for ps in parcalar:
        v = V[i:i + len(ps)].mean(0); i += len(ps)
        cikti.append(v / (np.linalg.norm(v) + 1e-12))
    return np.array(cikti, dtype=np.float32)


def main():
    from embedding_saglayici import embed_et
    bolumler = oku(VERI / "bolumler.csv")
    ders = {r["bolum"].strip(): r for r in oku(VERI / "bolum_dersleri.csv", ";")}
    adlar = [r["ad"] for r in bolumler]
    metin_tr, metin_en_kaynak, kaynak, cikan = [], [], [], 0
    for r in bolumler:
        d = ders.get(r["ad"])
        tum = [x.strip() for x in (d["dersler"].split("|") if d else []) if x.strip()]
        dl = [x for x in tum if not ortak_mi(x, r["ad"])]
        cikan += len(tum) - len(dl)
        dl = secim(list(dict.fromkeys(dl)), EN_FAZLA_DERS)
        if d and d["durum"] in ("tamam", "kismi", "esdeger") and len(dl) >= 5:
            metin_tr.append("Dersler: " + ", ".join(dl)); metin_en_kaynak.append(dl); kaynak.append("ders_plani")
        else:
            a = (r.get("kisa_aciklama") or r["ad"]).strip()
            metin_tr.append(a); metin_en_kaynak.append(None); kaynak.append("kisa_aciklama")
    print(f"Bölüm: {len(adlar)} · ders planından: {kaynak.count('ders_plani')} · kısa açıklamadan: {kaynak.count('kisa_aciklama')}"
          f" · çıkarılan ortak ders: {cikan}")

    # Model C (İngilizce) için: Türkçe ders adları yerel çeviri modeliyle çevrilir; İngilizce olanlar aynen kalır.
    from ceviri import ceviri_yap
    tr_dersler = sorted({x for dl in metin_en_kaynak if dl for x in dl if not ingilizce_mi(x)} | {baslik(a) for a in adlar})
    print(f"Çeviri: {len(tr_dersler)} farklı Türkçe ders adı (yerel model)")
    cev = dict(zip(tr_dersler, ceviri_yap(tr_dersler))) if tr_dersler else {}
    en_bolum = {r["ad"]: r.get("kisa_aciklama_en") or "" for r in oku(VERI / "bolumler_en.csv")}
    metin_en = []
    for ad, dl, mt in zip(adlar, metin_en_kaynak, metin_tr):
        metin_en.append("Courses: " + ", ".join(cev.get(x, x) for x in dl) if dl else (en_bolum.get(ad) or mt))
    # Parçalar: her parça bölümün resmî adıyla başlar; kısa açıklamalı bölümde tek parça
    p_tr, p_en = [], []
    for ad, dl, mt in zip(adlar, metin_en_kaynak, metin_tr):
        a_tr, a_en = baslik(ad), cev.get(baslik(ad), baslik(ad))
        if dl:
            gr = [dl[i:i + PARCA] for i in range(0, len(dl), PARCA)]
            p_tr.append([f"{a_tr} bölümü dersleri: " + ", ".join(g) for g in gr])
            p_en.append([f"{a_en} degree courses: " + ", ".join(cev.get(x, x) for x in g) for g in gr])
        else:
            p_tr.append([f"{a_tr} bölümü: {mt}"]); p_en.append([f"{a_en} degree: {en_bolum.get(ad) or mt}"])

    YEDEK.mkdir(exist_ok=True)
    damga = datetime.now().strftime("%Y%m%d_%H%M")
    for m in ("model_a", "model_b", "model_c"):
        eski = ONB / f"bolumler_{m}.npy"
        if eski.exists():
            shutil.copy(eski, YEDEK / f"bolumler_{m}_{damga}.npy")
        print(f"[{m}] bölüm metinleri encode ediliyor…")
        v = parcali_embed(embed_et, p_en if m == "model_c" else p_tr, m)
        np.save(eski, v)
    np.save(ONB / "bolum_isimleri.npy", np.array(adlar, dtype=object))
    with open(VERI / "bolum_metni.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["bolum", "kaynak", "metin", "metin_en"])
        w.writerows(zip(adlar, kaynak, metin_tr, metin_en))
    print(f"Tamam. Eski bölüm embedding'leri: {YEDEK} (…_{damga}.npy). Sıradaki: b4_bolum_profili.py, sonra b5_k5_baglari.py")


if __name__ == "__main__":
    main()
