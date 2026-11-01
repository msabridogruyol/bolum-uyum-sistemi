# -*- coding: utf-8 -*-
"""
Meslek adı yardımcıları (b6_ornek_meslekler.py kullanır)                                        [2026-11-01]

Önceden a2_ornek_meslek_sql.py içindeydi; a2'nin kendi işi (elle yazılmış listeden örnek meslek SQL'i) b6 (örnek meslekler) ile
değiştirildiği için yalnızca ortak işlevler buraya taşındı, içerikleri DEĞİŞMEDİ:
  q                    — SQL metni için tırnaklama
  norm                 — Türkçe-güvenli karşılaştırma biçimi
  bas_harf_duzelt      — 'ilaç mühendisi' → 'İlaç mühendisi'
  benzerleri_birlestir — aynı kökten meslekler birleşir (rol köklerinden en fazla 2)
  ad_duzeltmeleri_oku  — veri/meslek_ad_duzeltme.csv (yalnızca çeviri/yazım düzeltmesi)
"""
import re
import unicodedata
from pathlib import Path

VERI_DIZINI = Path(__file__).parent.parent / "veri"
AYNI_KOK_EN_FAZLA = 2   # aynı meslek kökünden (ör. '... mühendisi') bir bölümde en fazla 2 örnek


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def norm(metin) -> str:
    """Karşılaştırma için: Unicode NFC, tek boşluk, Türkçe-güvenli küçük harf."""
    t = unicodedata.normalize("NFC", str(metin)).replace("\u00a0", " ").replace("\u0307", "")
    t = re.sub(r"\s+", " ", t).strip()
    # eşleştirmede ı/i ayrımı yapılmaz ('Ict' = 'İct'), yazım hatalarına dayanıklı olsun
    return t.replace("İ", "i").replace("I", "ı").lower().replace("ı", "i")


# Türkçe'de gerçekten 'I' ile başlayan kelimeler (bunlar 'İ'ye çevrilmez)
I_ILE_BASLAYAN = ("ısı", "ışık", "ışı", "ıslak", "ıslah", "ızgara", "ırmak", "ılık", "ıhlamur", "ıssız")


def bas_harf_duzelt(ad: str) -> str:
    """'ilaç mühendisi' → 'İlaç mühendisi', 'Inşaat mühendisi' → 'İnşaat mühendisi' (Python'un İngilizce büyük harf hatası)."""
    if not ad:
        return ad
    if ad[0] == "i":
        return "İ" + ad[1:]
    if ad[0].islower():
        return ad[0].upper() + ad[1:]
    if ad[0] == "I" and not ad.replace("I", "ı", 1).lower().startswith(I_ILE_BASLAYAN):
        return "İ" + ad[1:]
    return ad


def kok_eslesir(a: str, b: str) -> bool:
    """'avukat' ~ 'avukatı', 'savcı' ~ 'savcısı' (iyelik eki farkı en fazla 3 harf)."""
    kisa, uzun = sorted((a, b), key=len)
    return len(kisa) >= 4 and uzun.startswith(kisa) and len(uzun) - len(kisa) <= 3


# Son kelimesi "rol" bildiren meslekler: asıl anlam baştaki kelimede ("Yazılım mühendisi",
# "Veri mühendisi" farklı işler). Bunlardan aynı rolde en fazla 2 tane gösterilir.
ROL_KELIMELERI = ("mühendis", "teknisyen", "tekniker", "uzman", "yönetici", "müdür", "öğretmen",
                  "görevli", "operatör", "tasarımcı", "danışman", "analist", "geliştirici", "asistan",
                  "işçi", "eğitmen", "sorumlu", "memur", "temsilci", "koordinatör", "araştırmacı",
                  "sanatçı", "bilimci", "amir", "süpervizör", "öğretim", "editör", "planlamacı")
ROL_KELIMELERI_N = tuple(norm(k) for k in ROL_KELIMELERI)


def benzerleri_birlestir(liste: list) -> list:
    """
    [2026-10-03 v4] Sıralı listede son kelimesi aynı kökten olan meslekler birleşir:
      - Meslek kökü (avukat, hakim, mimar...): yalnızca EN GÜÇLÜ olan kalır
        ('Avukat' varken 'Şirket avukatı' gösterilmez).
      - Rol kökü (mühendis, teknisyen, uzman...): en fazla 2 tane kalır.
    Hiçbir meslek BAŞKA bir adla gösterilmez (eski sürüm 'Yazılım mimarı'nı 'Mimar' yapıyordu).
    """
    sonuc, kokler = [], []          # kokler: [(son_kelime, adet)]
    gorulen = set()
    for x in liste:
        ad_n = norm(x[3])
        if ad_n in gorulen:
            continue
        son = ad_n.split()[-1]
        rol = son.startswith(ROL_KELIMELERI_N)
        sinir = AYNI_KOK_EN_FAZLA if rol else 1
        eslesen = next((i for i, (k, _) in enumerate(kokler) if kok_eslesir(son, k)), None)
        if eslesen is not None:
            if kokler[eslesen][1] >= sinir:
                continue
            kokler[eslesen] = (kokler[eslesen][0], kokler[eslesen][1] + 1)
        else:
            kokler.append((son, 1))
        gorulen.add(ad_n)
        sonuc.append(x)
    return sonuc


def ad_duzeltmeleri_oku() -> dict:
    """eski_ad (küçük harf) -> yeni_ad ('' = çıkar). Dosya yoksa boş döner."""
    yol = VERI_DIZINI / "meslek_ad_duzeltme.csv"
    if not yol.exists():
        return {}
    sozluk = {}
    for satir in yol.read_text(encoding="utf-8-sig").splitlines()[1:]:
        if not satir.strip():
            continue
        eski, _, yeni = satir.partition(";")
        sozluk[norm(eski)] = yeni.strip()
    print(f"Ad düzeltme listesi: {len(sozluk)} kayıt")
    return sozluk
