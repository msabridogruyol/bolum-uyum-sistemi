# -*- coding: utf-8 -*-
"""
Çeviri Tutarlılık Kontrolü

Fikir: Eğer bir meslek adı yanlış çevrildiyse (örn. "upholsterer" -> "Yufkacı"),
o ismin embedding'i, KENDİ açıklamasının embedding'inden anlamsal olarak
UZAK çıkar — çünkü açıklama doğru İngilizce içerikten geliyor ama isim
yanlış. Doğru çevrilmiş bir mesleğin adı ve açıklaması ise (isim açıklamanın
içinde geçmese bile) genelde birbirine yakın çıkar, çünkü ikisi de aynı
kavramı anlatıyor.

Bu script, TÜM 3.039 mesleğin adı ile açıklamasını AYRI AYRI embed edip
aralarındaki benzerliği hesaplar, en düşük benzerliğe sahip N mesleği
(muhtemel çeviri hataları) bir rapora yazar — otomatik düzeltmez, yalnızca
İNCELEMENİZ için işaretler.

Çalıştırma: python m3_ceviri_kontrolu.py
Çıktı: cikti/ceviri_supheli_liste.csv
"""

import csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font
from embedding_saglayici import embed_et

VERI_DIZINI = Path(__file__).parent.parent / "veri"
CIKTI_DIZINI = Path(__file__).parent.parent / "cikti"
MODEL_ADI = "model_a"  # Türkçe, hızlı bir model yeterli — bu bir tanılama, üretim skoru değil
SUPHELI_ESIK = 0.35     # bu benzerliğin altındakiler rapora yazılır (deneysel bir başlangıç değeri)


def calistir():
    with open(VERI_DIZINI / "meslekler_esco.csv", encoding="utf-8-sig") as f:
        satirlar = list(csv.DictReader(f))

    adlar = [r["ad"] for r in satirlar]
    aciklamalar = [r["aciklama"] for r in satirlar]

    print(f"{len(adlar)} meslek adı encode ediliyor...")
    ad_vek = embed_et(adlar, MODEL_ADI, onek="query")

    print(f"{len(aciklamalar)} açıklama encode ediliyor...")
    aciklama_vek = embed_et(aciklamalar, MODEL_ADI, onek="passage")

    # Her meslek için yalnızca KENDİ adı ile KENDİ açıklaması arasındaki benzerlik
    benzerlikler = (ad_vek * aciklama_vek).sum(axis=1)  # satır satır nokta çarpımı

    supheliler = []
    for r, benzerlik in zip(satirlar, benzerlikler):
        if benzerlik < SUPHELI_ESIK:
            supheliler.append((r["ad"], r["ad_en"], round(float(benzerlik), 3), r["aciklama"][:150]))

    supheliler.sort(key=lambda x: x[2])  # en düşükten başla

    CIKTI_DIZINI.mkdir(exist_ok=True)
    cikti_yolu = CIKTI_DIZINI / "ceviri_supheli_liste.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Supheli Liste"
    ws.append(["ad_tr", "ad_en", "benzerlik", "aciklama_baslangici"])
    for satir in supheliler:
        ws.append(satir)
    for hucre in ws[1]:
        hucre.font = Font(bold=True)  # [2026-10-04] eski .copy() yazımı uyarı veriyordu
    wb.save(cikti_yolu)

    print(f"\n{len(supheliler)}/{len(satirlar)} meslek şüpheli olarak işaretlendi (eşik: {SUPHELI_ESIK}).")
    print(f"Çıktı: {cikti_yolu}")
    print("Bu dosyayı gözden geçirin — her satır 'muhtemel çeviri hatası' demek, kesin hata değil.")


if __name__ == "__main__":
    calistir()
