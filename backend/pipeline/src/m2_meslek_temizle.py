# -*- coding: utf-8 -*-
"""
Bilinen Meslek Düzeltmeleri — Sözde Bilim Silme + Çeviri Hatası Düzeltme

m1_esco_ceviri.py her çalıştığında meslekler_esco.csv'yi SIFIRDAN üretir —
yani daha önce elle bulup temizlediğimiz sorunlar (Astrolog, Falcı, Orta,
Psişik, Yufkacı) geri gelir. Bu script, meslekler_esco.csv'ye HER ZAMAN
(çeviri yeniden yapılsa da yapılmasa da) uygulanması gereken bilinen
düzeltmeleri tekrar uygular. Birden fazla kez çalıştırmak güvenlidir
(idempotent) — zaten silinmiş/düzeltilmiş bir dosyada değişiklik yapmaz.

Yeni bir sorun bulundukça (m3_ceviri_kontrolu.py'nin işaretlediklerini
inceledikten sonra), buradaki SILINECEKLER / YENIDEN_ADLANDIR
sözlüklerine eklemeniz yeterli.
"""

import csv
from pathlib import Path

VERI_DIZINI = Path(__file__).parent.parent / "veri"

# esco_kodu bazlı silme — sözde bilim / üniversite ile ilgisi olmayan meslekler
SILINECEK_KODLAR = {
    "5161.1",  # Astrolog
    "5161.2",  # Falcı
    "5161.3",  # Orta (medium -> yanlış çevrilmiş)
    "5161.4",  # Psişik
}

# ad_en (orijinal İngilizce) eşleşmesiyle yeniden adlandırma — bilinen çeviri hataları
YENIDEN_ADLANDIR = {
    "upholsterer": "Döşemeci",  # önceden "Yufkacı" olarak yanlış çevrilmişti

    "hawker": "Seyyar Satıcı",
    "roughneck": "Sondaj İşçisi",
    "confectioner": "Şekerci",
    "pawnbroker": "Rehinci",
    "silversmith": "Gümüşçü",
    "basketmaker": "Sepetçi",
    "slaughterer": "Hayvan Kesicisi",
    "decksman": "Güverte Elemanı",
    "assayer": "Tahlilci",
    "stagehand": "Sahne Teknisyeni",
    "tile fitter": "Fayans Döşemecisi",
    "weaver": "Dokumacı",
    "verger": "Kilise Görevlisi",
    "companion": "Refakatçi",
    "violin maker": "Keman Yapımcısı",
    "shipwright": "Gemi Yapımcısı",
    "officer of the watch": "Nöbetçi Subay",
    "embalmer": "Tahnitçi",
    "dresser": "Giydirici",
    "woodcarver": "Ahşap Oymacı",
    "boatswain": "Lostromo",
    "brigadier": "Tuğgeneral",
    "wire harness assembler": "Kablo Demeti Montajcısı",
    "merchandiser": "Mağaza Düzenleyicisi",
    "knitter": "Örgücü",
    "marine fitter": "Deniz Tesisatçısı",
    "gunsmith": "Silah Ustası",
    "taxidermist": "Taksidermist",
    "hospital porter": "Hastane Hamalı",
    "tiling supervisor": "Fayans Döşeme Amiri",
    "bleacher operator": "Ağartma Makinesi Operatörü",
    "chaplain": "Papaz",
}


def calistir():
    yol = VERI_DIZINI / "meslekler_esco.csv"
    if not yol.exists():
        raise FileNotFoundError(f"{yol} yok — önce m1_esco_ceviri.py çalıştırılmalı.")

    with open(yol, encoding="utf-8-sig") as f:
        okuyucu = csv.DictReader(f)
        basliklar = okuyucu.fieldnames
        satirlar = list(okuyucu)

    once = len(satirlar)
    yeni_satirlar = []
    silinen = 0
    adlandirilan = 0
    tekrar = 0
    gorulen_kodlar = set()

    for r in satirlar:
        if r["esco_kodu"] in SILINECEK_KODLAR:
            silinen += 1
            continue
        if r["esco_kodu"] in gorulen_kodlar:  # birebir kopya satır — ilkini tut
            tekrar += 1
            continue
        gorulen_kodlar.add(r["esco_kodu"])
        ad_en_kucuk = r["ad_en"].strip().lower()
        if ad_en_kucuk in YENIDEN_ADLANDIR and r["ad"] != YENIDEN_ADLANDIR[ad_en_kucuk]:
            r["ad"] = YENIDEN_ADLANDIR[ad_en_kucuk]
            adlandirilan += 1
        yeni_satirlar.append(r)

    with open(yol, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=basliklar)
        yazici.writeheader()
        yazici.writerows(yeni_satirlar)

    print(f"m2_meslek_temizle.py: {once} -> {len(yeni_satirlar)} kayıt "
          f"({silinen} silindi, {tekrar} tekrar kaldırıldı, {adlandirilan} yeniden adlandırıldı).")


if __name__ == "__main__":
    calistir()