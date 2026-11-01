# -*- coding: utf-8 -*-
"""
ESCO Meslek Çevirisi — İngilizce'den Türkçe'ye (KESİNTİYE DAYANIKLI SÜRÜM)

[DÜZELTME] Önceki sürüm hiçbir ara kayıt yapmıyordu — Ctrl+C ile durdurulduğunda
(ya da bilgisayar kapanırsa/donarsa) TÜM ilerleme kayboluyordu. Bu sürüm her
500 kayıtta bir diske yazıyor ve yeniden çalıştırıldığında KALDIĞI YERDEN
devam ediyor — kesinti olursa yalnızca son 500 kaydı kaybedersiniz, hepsini değil.

Çalıştırma: python m1_esco_ceviri.py
Durdurmak isterseniz Ctrl+C güvenlidir — ilerleme diskte duruyor.
Tekrar 'python m1_esco_ceviri.py' derseniz kaldığı yerden devam eder.
"""

import csv
import json
import os
from pathlib import Path
import torch
from transformers import MarianMTModel, MarianTokenizer

torch.set_num_threads(os.cpu_count())

VERI_DIZINI = Path(__file__).parent.parent / "veri"
CEVIRI_MODEL_ADI = "Helsinki-NLP/opus-mt-tc-big-en-tr"

AD_CHECKPOINT = VERI_DIZINI / "_esco_ad_tr_checkpoint.json"
ACIKLAMA_CHECKPOINT = VERI_DIZINI / "_esco_aciklama_tr_checkpoint.json"
KAYIT_ARALIGI = 500  # her 500 kayıtta bir diske yaz

_tokenizer = None
_model = None


def modeli_yukle():
    global _tokenizer, _model
    if _model is None:
        print(f"Çeviri modeli yükleniyor: {CEVIRI_MODEL_ADI} (ilk seferde iner)")
        _tokenizer = MarianTokenizer.from_pretrained(CEVIRI_MODEL_ADI)
        _model = MarianMTModel.from_pretrained(CEVIRI_MODEL_ADI)
    return _tokenizer, _model


def checkpoint_oku(yol: Path) -> list[str]:
    if yol.exists():
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    return []


def checkpoint_yaz(yol: Path, sonuclar: list[str]):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(sonuclar, f, ensure_ascii=False)


def ceviri_yap(metinler: list[str], checkpoint_yolu: Path, etiket: str, batch_size: int = 20) -> list[str]:
    """Kaldığı yerden devam eder — checkpoint_yolu'nda kayıtlı sonuç varsa onu kullanır.
    [DÜZELTME] batch_size 32 -> 20: her 20 kayıtta bir ilerleme satırı basılsın diye."""
    sonuclar = checkpoint_oku(checkpoint_yolu)
    baslangic = len(sonuclar)
    if baslangic > 0:
        print(f"  [{etiket}] Kayıttan devam ediliyor: {baslangic}/{len(metinler)} zaten çevrilmiş.")
    if baslangic >= len(metinler):
        return sonuclar

    tokenizer, model = modeli_yukle()

    for i in range(baslangic, len(metinler), batch_size):
        parca = metinler[i:i + batch_size]
        girdi = tokenizer(parca, return_tensors="pt", padding=True, truncation=True, max_length=180)
        cikti = model.generate(
            **girdi,
            max_length=180,
            num_beams=2,
            length_penalty=1.0,
            early_stopping=True,
        )
        cevrilmis = tokenizer.batch_decode(cikti, skip_special_tokens=True)
        sonuclar.extend(cevrilmis)
        print(f"  [{etiket}] {min(i + len(parca), len(metinler))}/{len(metinler)} çevrildi...", flush=True)

        if len(sonuclar) % KAYIT_ARALIGI < batch_size or i + batch_size >= len(metinler):
            checkpoint_yaz(checkpoint_yolu, sonuclar)

    checkpoint_yaz(checkpoint_yolu, sonuclar)
    return sonuclar


def calistir():
    girdi_yolu = VERI_DIZINI / "occupations_en.csv"
    if not girdi_yolu.exists():
        raise FileNotFoundError(f"{girdi_yolu} bulunamadı.")

    with open(girdi_yolu, encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    print(f"{len(satirlar)} meslek okundu.")

    adlar = [r["preferredLabel"] for r in satirlar]
    aciklamalar = [r["description"] for r in satirlar]

    print("\nMeslek adları çevriliyor...")
    ad_tr = ceviri_yap(adlar, AD_CHECKPOINT, "AD")

    print("\nMeslek açıklamaları çevriliyor (biraz sürebilir, 3.043 kayıt)...")
    aciklama_tr = ceviri_yap(aciklamalar, ACIKLAMA_CHECKPOINT, "AÇIKLAMA")

    cikti_yolu = VERI_DIZINI / "meslekler_esco.csv"
    with open(cikti_yolu, "w", newline="", encoding="utf-8") as f:
        yazici = csv.writer(f)
        yazici.writerow(["esco_uri", "isco_grubu", "esco_kodu", "ad", "aciklama", "ad_en"])
        for r, ad, aciklama in zip(satirlar, ad_tr, aciklama_tr):
            yazici.writerow([r["conceptUri"], r["iscoGroup"], r["code"], ad.capitalize(), aciklama, r["preferredLabel"]])

    print(f"\nTamamlandı. Çıktı: {cikti_yolu}")
    print("İsterseniz artık _esco_ad_tr_checkpoint.json ve _esco_aciklama_tr_checkpoint.json dosyalarını silebilirsiniz.")


if __name__ == "__main__":
    calistir()
