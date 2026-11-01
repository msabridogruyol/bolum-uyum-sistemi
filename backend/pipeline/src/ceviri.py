# -*- coding: utf-8 -*-
"""
Çeviri Adımı — Model C için Türkçe metinleri İngilizceye çevirir.

[DÜZELTME] Önceki sürüm yalnızca "ad" (çıplak isim) çeviriyordu — bu,
embedding modellerinin "Hukuk" ile "Hakkak" gibi kelime KÖKÜ benzerliği
taşıyan ama anlamca alakasız kelimeleri birbirine karıştırmasına yol
açıyordu (bağlam/tanım cümlesi olmadığı için). Bu sürüm artık:
  - Bölümler için: "ad" + "kisa_aciklama" ikisini de çevirir
  - Meslekler için: "ad" + "alt_grup_adi" (ISCO kategori adı) ikisini de çevirir
m4_meslek_embedding.py bu ikisini birleştirip zengin bağlamlı bir metin
olarak embedding modeline verir.

Çeviri, YEREL bir makine çeviri modeliyle (Helsinki-NLP/opus-mt-tr-en)
yapılır — dış API'ye bağımlılık yok.

Çalıştırma: python ceviri.py
Çıktı: veri/meslekler_en.csv, veri/bolumler_en.csv, veri/degiskenler_en.csv
"""

import csv
from pathlib import Path
from transformers import MarianMTModel, MarianTokenizer

VERI_DIZINI = Path(__file__).parent.parent / "veri"
CEVIRI_MODEL_ADI = "Helsinki-NLP/opus-mt-tr-en"

_tokenizer = None
_model = None


def modeli_yukle():
    global _tokenizer, _model
    if _model is None:
        print(f"Çeviri modeli yükleniyor: {CEVIRI_MODEL_ADI} (ilk seferde iner)")
        _tokenizer = MarianTokenizer.from_pretrained(CEVIRI_MODEL_ADI)
        _model = MarianMTModel.from_pretrained(CEVIRI_MODEL_ADI)
    return _tokenizer, _model


def ceviri_yap(metinler: list[str], batch_size: int = 32) -> list[str]:
    """
    [İYİLEŞTİRME] Önceki sürüm model.generate()'i varsayılan (greedy —
    her adımda yalnızca en olası kelimeyi seçen, hızlı ama düşük kaliteli)
    ayarlarla çağırıyordu. Bu sürüm num_beams=4 ile BEAM SEARCH kullanıyor
    — modelin birden fazla olası çeviriyi paralel değerlendirip en iyisini
    seçmesini sağlar, çeviri kalitesini belirgin şekilde artırır (biraz
    daha yavaş ama 301+7764 gibi bir defalık bir işlem için sorun değil).
    max_length de 64'ten 128'e çıkarıldı — uzun bölüm açıklamalarının
    kırpılmasını önlemek için.
    """
    tokenizer, model = modeli_yukle()
    sonuclar = []
    for i in range(0, len(metinler), batch_size):
        parca = metinler[i:i + batch_size]
        girdi = tokenizer(parca, return_tensors="pt", padding=True, truncation=True, max_length=128)
        cikti = model.generate(
            **girdi,
            max_length=128,
            num_beams=4,
            length_penalty=1.0,
            early_stopping=True,
        )
        cevrilmis = tokenizer.batch_decode(cikti, skip_special_tokens=True)
        sonuclar.extend(cevrilmis)
        if (i // batch_size) % 20 == 0:
            print(f"  {i + len(parca)}/{len(metinler)} çevrildi...")
    return sonuclar


def bolumleri_cevir():
    hedef_dosya = VERI_DIZINI / "bolumler_en.csv"
    if hedef_dosya.exists():
        print(f"{hedef_dosya.name} zaten var, atlanıyor. Yeniden çevirmek için dosyayı silin.")
        return

    with open(VERI_DIZINI / "bolumler.csv", encoding="utf-8-sig") as f:
        satirlar = list(csv.DictReader(f))

    kisa_aciklama_var = "kisa_aciklama" in satirlar[0] and satirlar[0].get("kisa_aciklama")
    if not kisa_aciklama_var:
        print("UYARI: bolumler.csv'de 'kisa_aciklama' sütunu yok/boş — yalnızca isim çevrilecek, "
              "bu embedding kalitesini düşürür. Önce açıklamalı bolumler.csv'yi yerleştirin.")

    adlar = [r["ad"] for r in satirlar]
    print(f"\nBölüm adları çevriliyor ({len(adlar)} kayıt)...")
    ad_en = ceviri_yap(adlar)

    if kisa_aciklama_var:
        aciklamalar = [r.get("kisa_aciklama", "") or r["ad"] for r in satirlar]
        print(f"Bölüm açıklamaları çevriliyor ({len(aciklamalar)} kayıt)...")
        aciklama_en = ceviri_yap(aciklamalar)
    else:
        aciklama_en = ad_en  # yedek — açıklama yoksa isimle aynı

    with open(hedef_dosya, "w", newline="", encoding="utf-8") as f:
        yazici = csv.writer(f)
        yazici.writerow(["ad", "ad_en", "kisa_aciklama_en"])
        for ad, a_en, k_en in zip(adlar, ad_en, aciklama_en):
            yazici.writerow([ad, a_en, k_en])

    print(f"Kaydedildi: {hedef_dosya.name}")


def meslekleri_cevir():
    hedef_dosya = VERI_DIZINI / "meslekler_en.csv"
    if hedef_dosya.exists():
        print(f"{hedef_dosya.name} zaten var, atlanıyor. Yeniden çevirmek için dosyayı silin.")
        return

    with open(VERI_DIZINI / "meslekler.csv", encoding="utf-8-sig") as f:
        satirlar = list(csv.DictReader(f))

    adlar = [r["ad"] for r in satirlar]
    alt_gruplar = [r.get("alt_grup_adi", "") or "" for r in satirlar]

    print(f"\nMeslek adları çevriliyor ({len(adlar)} kayıt)...")
    ad_en = ceviri_yap(adlar)

    # Aynı alt_grup_adi büyük olasılıkla yüzlerce kez tekrar ediyor — tekrar
    # çevirmemek için benzersizleri çevirip eşleştiriyoruz (çok daha hızlı).
    benzersiz_alt_gruplar = sorted(set(alt_gruplar))
    print(f"Meslek alt grupları çevriliyor ({len(benzersiz_alt_gruplar)} benzersiz kayıt, "
          f"{len(alt_gruplar)} toplam yerine)...")
    benzersiz_cevrilmis = ceviri_yap(benzersiz_alt_gruplar) if benzersiz_alt_gruplar else []
    alt_grup_sozluk = dict(zip(benzersiz_alt_gruplar, benzersiz_cevrilmis))
    alt_grup_en = [alt_grup_sozluk.get(a, "") for a in alt_gruplar]

    with open(hedef_dosya, "w", newline="", encoding="utf-8") as f:
        yazici = csv.writer(f)
        yazici.writerow(["ad", "ad_en", "isco_kodu", "alt_grup_adi_en"])
        for r, a_en, g_en in zip(satirlar, ad_en, alt_grup_en):
            yazici.writerow([r["ad"], a_en, r["isco_kodu"], g_en])

    print(f"Kaydedildi: {hedef_dosya.name}")


def degiskenleri_cevir():
    hedef_dosya = VERI_DIZINI / "degiskenler_en.csv"
    if hedef_dosya.exists():
        print(f"{hedef_dosya.name} zaten var, atlanıyor. Yeniden çevirmek için dosyayı silin.")
        return

    with open(VERI_DIZINI / "degiskenler.csv", encoding="utf-8-sig") as f:
        satirlar = list(csv.DictReader(f))

    aciklamalar = [r["aciklama"] for r in satirlar]
    print(f"\nDeğişken açıklamaları çevriliyor ({len(aciklamalar)} kayıt)...")
    aciklama_en = ceviri_yap(aciklamalar)

    with open(hedef_dosya, "w", newline="", encoding="utf-8") as f:
        yazici = csv.writer(f)
        yazici.writerow(["kod", "ad", "aciklama_en"])
        for r, en in zip(satirlar, aciklama_en):
            yazici.writerow([r["kod"], r["ad"], en])

    print(f"Kaydedildi: {hedef_dosya.name}")


if __name__ == "__main__":
    # [ESCO GEÇİŞİ] meslekleri_cevir() artık ÇAĞRILMIYOR — ESCO'nun orijinal
    # İngilizce açıklaması (occupations_en.csv) doğrudan kullanılıyor, çeviriye gerek yok.
    bolumleri_cevir()
    degiskenleri_cevir()
    print("\nÇeviri tamamlandı.")
