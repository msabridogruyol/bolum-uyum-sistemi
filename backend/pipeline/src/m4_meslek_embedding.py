# -*- coding: utf-8 -*-
"""
Adım 0 — Embedding Önbellekleme (meslekler ve değişkenler)

[2026-11-01] Bölüm embedding'leri artık YALNIZCA b2_bolum_ders_metni.py'de hesaplanır (resmî ders planı metni).
Bu adım önceden bölümleri de kısa açıklamayla gömüyordu; meslek listesi yenilenip bu adım yeniden çalıştırılınca
b2'nin bölüm vektörleri ve bolum_isimleri.npy sessizce eski metinle değişiyordu. Bölüm kısmı kaldırıldı;
bölüm metni ve vektörlerinin tek sahibi b2'dir. Meslek ve değişken metinleri değişmedi (önbellek aynen kullanılır).

[DÜZELTME — Hukuk/Hakkak sorunu] Önceki sürüm, meslek ve bölümleri
embedding modeline yalnızca ÇIPLAK İSİM olarak veriyordu ("HUKUK",
"Hakkak"). Bağlam cümlesi olmadığında embedding modelleri bazen anlam
yerine kelime KÖKÜ benzerliğine tutunuyor (Hukuk/Hakim/Hakkak/Tahakkuk
hepsi "hak" kökünden) — bu, hem tekil yanlış eşleşmelere (Hukuk→Hakkak)
hem de genel olarak bölümlerin birbirinden yeterince ayrışmamasına yol
açtı (301 bölümün ortalama profil aralığı yalnızca ~5 puandı).

Bu sürüm artık:
  - Bölümler: "AD: kısa_açıklama" (örn. "HUKUK: Adalet sistemi, yasalar
    ve hukuki süreçlerin teori ve uygulamasını öğretir.")
  - Meslekler: "AD (alt_grup_adı)" (örn. "Hakkak (Zanaatkarlar ve İlgili
    İşlerde Çalışanlar)")
şeklinde, gerçek bağlam içeren metinler kullanıyor — değişkenlerde zaten
olan "ad: açıklama" mantığıyla tutarlı hale getirildi.

Meslekler ve değişkenler (31) için, 3 modelin
her biriyle embedding vektörlerini bir kez hesaplayıp diske kaydeder.
"""

import csv
import numpy as np
from pathlib import Path
from embedding_saglayici import embed_et, MODEL_TANIMLARI

VERI_DIZINI = Path(__file__).parent.parent / "veri"
ONBELLEK_DIZINI = Path(__file__).parent.parent / "onbellek"


def oku_satirlar(dosya_adi):
    with open(VERI_DIZINI / dosya_adi, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))



def meslek_metinlerini_olustur(satirlar: list[dict]) -> list[str]:
    """
    [ESCO GEÇİŞİ] Artık gerçek meslek açıklaması var (ESCO kaynaklı) —
    'AD (alt_grup_adı)' yerine 'AD: açıklama' formatına geçildi, tıpkı
    bölümler gibi. Bu, hem daha zengin bağlam sağlıyor hem de eski
    7.764'lük kaynakta olmayan güncel meslekleri (örn. Veri Analisti)
    kapsıyor.
    """
    metinler = []
    for r in satirlar:
        aciklama = (r.get("aciklama") or "").strip()
        if not aciklama:
            metinler.append(r["ad"])
        else:
            metinler.append(f"{r['ad']}: {aciklama}")
    return metinler


def ingilizce_metinleri_olustur():
    """
    Model C (İngilizce model) için metinler.
    [DÜZELTME — kök neden] Önceki sürüm occupations_en.csv'yi HİÇ FİLTRELEMEDEN
    okuyordu — ama m2_meslek_temizle.py yalnızca meslekler_esco.csv'yi (Türkçe)
    güncelliyor, occupations_en.csv'ye dokunmuyor. Sonuç: Türkçe modeller
    3.039 meslek, İngilizce model 3.043 meslek görüyordu — a4'te "3 model
    aynı boyutta olmalı" varsayımını bozup ValueError'a yol açıyordu.
    Artık İngilizce liste, meslekler_esco.csv'de HÂLÂ VAR OLAN esco_kodu'na
    göre filtreleniyor — iki dil her zaman birebir aynı meslek setini içerir.
    """
    ceviri_dosyalari_var = all(
        (VERI_DIZINI / f).exists()
        for f in ["occupations_en.csv", "degiskenler_en.csv"]
    )
    if not ceviri_dosyalari_var:
        raise FileNotFoundError(
            "Gerekli dosyalardan biri eksik (occupations_en.csv / degiskenler_en.csv)."
        )

    # Türkçe listede (temizlik sonrası) hâlâ var olan esco_kodu'ları topla
    with open(VERI_DIZINI / "meslekler_esco.csv", encoding="utf-8-sig") as f:
        gecerli_esco_kodlari = {r["esco_kodu"] for r in csv.DictReader(f)}

    with open(VERI_DIZINI / "occupations_en.csv", encoding="utf-8-sig") as f:
        tum_meslek_satirlari_en = list(csv.DictReader(f))
    gorulen = set()
    meslek_satirlari_en = []
    for r in tum_meslek_satirlari_en:
        if r["code"] in gecerli_esco_kodlari and r["code"] not in gorulen:
            gorulen.add(r["code"])
            meslek_satirlari_en.append(r)
    if len(meslek_satirlari_en) != len(gecerli_esco_kodlari):
        raise ValueError(f"Model C meslek sayısı ({len(meslek_satirlari_en)}) Türkçe listeyle "
                         f"({len(gecerli_esco_kodlari)}) uyuşmuyor — çalıştırma durduruldu.")

    silinen_sayisi = len(tum_meslek_satirlari_en) - len(meslek_satirlari_en)
    if silinen_sayisi:
        print(f"  (İngilizce liste filtrelendi: {silinen_sayisi} meslek Türkçe listede yok, atlandı)")

    meslekler_en = [f"{r['preferredLabel']}: {r['description']}" for r in meslek_satirlari_en]

    with open(VERI_DIZINI / "degiskenler_en.csv", encoding="utf-8-sig") as f:
        degisken_satirlari_en = list(csv.DictReader(f))
    degisken_metinleri_en = [f"{d['ad']}: {d['aciklama_en']}" for d in degisken_satirlari_en]

    return meslekler_en, degisken_metinleri_en



def calistir():
    ONBELLEK_DIZINI.mkdir(exist_ok=True)

    meslek_satirlari = oku_satirlar("meslekler_esco.csv")  # [ESCO GEÇİŞİ]
    degisken_satirlari = oku_satirlar("degiskenler.csv")

    meslekler = meslek_metinlerini_olustur(meslek_satirlari)
    degisken_metinleri = [f"{d['ad']}: {d['aciklama']}" for d in degisken_satirlari]

    # İsim listeleri (yalnızca ad, .npy satır sırası için) — çıktı CSV'lerinde
    # kullanılacak "meslek_adi"/"bolum_adi" hâlâ ÇIPLAK isim olmalı, embed
    # edilen zengin metinle karıştırılmamalı.
    meslek_adlari_duz = [r["ad"] for r in meslek_satirlari]

    hesaplanmis_hf_adlari = {}

    for model_adi, hf_adi in MODEL_TANIMLARI.items():
        onbellek_anahtari = hf_adi.replace("/", "__")

        zaten_var = all(
            (ONBELLEK_DIZINI / f"{isim}_{model_adi}.npy").exists()
            for isim in ["meslekler", "degiskenler"]
        )
        if zaten_var:
            print(f"[{model_adi}] Zaten hesaplanmış (.npy dosyaları mevcut), atlanıyor. "
                  f"Yeniden hesaplamak istiyorsanız onbellek/*_{model_adi}.npy dosyalarını silin.")
            continue

        if onbellek_anahtari in hesaplanmis_hf_adlari:
            kaynak = hesaplanmis_hf_adlari[onbellek_anahtari]
            print(f"[{model_adi}] {hf_adi} zaten hesaplandı ({kaynak}), kopyalanıyor")
            for isim in ["meslekler", "degiskenler"]:
                veri = np.load(ONBELLEK_DIZINI / f"{isim}_{kaynak}.npy")
                np.save(ONBELLEK_DIZINI / f"{isim}_{model_adi}.npy", veri)
            continue

        print(f"\n=== {model_adi} ({hf_adi}) ===")

        if "-en" in hf_adi.lower() and "bge" in hf_adi.lower():
            m_meslekler, m_degisken_metinleri = ingilizce_metinleri_olustur()
            print("  (İngilizce çevrilmiş + zenginleştirilmiş metinler kullanılıyor)")
        else:
            m_meslekler, m_degisken_metinleri = meslekler, degisken_metinleri

        print(f"Meslekler encode ediliyor ({len(m_meslekler)} kayıt)...")
        meslek_vek = embed_et(m_meslekler, model_adi, onek="query")
        np.save(ONBELLEK_DIZINI / f"meslekler_{model_adi}.npy", meslek_vek)

        print(f"Değişkenler encode ediliyor ({len(m_degisken_metinleri)} kayıt)...")
        degisken_vek = embed_et(m_degisken_metinleri, model_adi, onek="passage")
        np.save(ONBELLEK_DIZINI / f"degiskenler_{model_adi}.npy", degisken_vek)

        hesaplanmis_hf_adlari[onbellek_anahtari] = model_adi

    np.save(ONBELLEK_DIZINI / "meslek_isimleri.npy", np.array(meslek_adlari_duz, dtype=object))
    np.save(ONBELLEK_DIZINI / "degisken_kodlari.npy",
            np.array([d["kod"] for d in degisken_satirlari], dtype=object))

    print(f"\nTamamlandı. Embedding'ler '{ONBELLEK_DIZINI}' klasörüne kaydedildi.")

    print("\n=== Sağlık Kontrolü ===")
    for model_adi in MODEL_TANIMLARI:
        meslek_vek = np.load(ONBELLEK_DIZINI / f"meslekler_{model_adi}.npy")
        degisken_vek = np.load(ONBELLEK_DIZINI / f"degiskenler_{model_adi}.npy")
        benzerlik = meslek_vek @ degisken_vek.T
        ortalama = float(benzerlik.mean())
        std = float(benzerlik.std())
        print(f"[{model_adi}] tüm meslek×değişken benzerlik dağılımı: "
              f"ortalama={ortalama:.3f}, std={std:.3f}")
        if std < 0.05:
            print(f"  ⚠️  UYARI: standart sapma çok düşük — embedding'ler ayırt edici "
                  f"olmayabilir. m5'e geçmeden önce bunu bildirin.")
    print("Sıradaki: m5_meslek_degisken_skorlama.py; ardından bölüm adımları (b1 → b7).")


if __name__ == "__main__":
    calistir()
