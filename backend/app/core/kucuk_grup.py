# -*- coding: utf-8 -*-
"""
[2026-10-10] Küçük grup gizleme (KVKK aydınlatma metni: "Okul ve kurum raporlarında yalnızca toplu sayılar kullanılır").

Toplulaştırılmış istatistiklerde (oran, dağılım, ortalama, grup kırılımı) bir hücreyi oluşturan öğrenci sayısı
EN_AZ_GRUP'tan azsa değer gösterilmez (None → arayüzde "5'ten az öğrenci"); küçük gruplar mümkünse "Diğer" altında
birleştirilir. Öğrenci bazlı (isimli) raporlar ve listeler bu kuralın dışındadır; okulun genel toplam sayıları
(kaç öğrenci kayıtlı) gizlenmez.

Anonim anketler de aynı eşiği kullanır (app/api/anketler.py: EN_AZ = EN_AZ_GRUP).
"""
from collections import Counter

EN_AZ_GRUP = 5
GIZLI_METIN = f"{EN_AZ_GRUP}'ten az öğrenci"
DIPNOT = (f"Gizlilik: {EN_AZ_GRUP}'ten az öğrenciye dayanan toplu değerler gösterilmez (“{GIZLI_METIN}”); "
          "küçük gruplar “Diğer” altında birleştirilir.")


def yeterli(n) -> bool:
    return (n or 0) >= EN_AZ_GRUP


def gizle(deger, n):
    """n öğrenciye dayanan toplu değer; n < EN_AZ_GRUP ise None."""
    return deger if yeterli(n) else None


def kirilim_gizle(satirlar: list[dict], alanlar: list[str], n_anahtari: str = "ogrenci", ikincil: bool = True,
                  bos=None) -> list[dict]:
    """Grup kırılımı satırlarında (şube / sınıf düzeyi / cinsiyet ...) öğrenci sayısı EN_AZ_GRUP'tan az olanların
    `alanlar` değerlerini `bos` yapar (bos: değer, çağrılabilir ya da {alan: değer/çağrılabilir}) ve satıra gizli=True ekler (yerinde; listeyi de döndürür). Grup büyüklüğü
    (n_anahtari) gösterilmeye devam eder.

    ikincil=True: üst toplam (okul / sınıf düzeyi) görünürken gizlenen satırların toplamı yine EN_AZ_GRUP'tan azsa,
    gizli değer çıkarma yoluyla bulunabilir (ör. tek küçük şube) — bu durumda en küçük görünür satırlar da gizlenir."""
    n = lambda s: s.get(n_anahtari) or 0  # noqa: E731
    gizli = [s for s in satirlar if not yeterli(n(s))]
    if ikincil and gizli:
        gizli_id = {id(s) for s in gizli}
        gorunur = sorted((s for s in satirlar if id(s) not in gizli_id), key=n)
        while gorunur and 0 < sum(n(s) for s in gizli) < EN_AZ_GRUP:
            gizli.append(gorunur.pop(0))
    for s in gizli:
        for a in alanlar:
            if a in s:
                b = bos.get(a) if isinstance(bos, dict) else bos
                s[a] = b() if callable(b) else b
        s["gizli"] = True
    return satirlar


def grup_birlestir(sayim, ad_anahtari: str = "ad", sayi_anahtari: str = "sayi", diger_etiketi: str = "Diğer",
                   ilk_n: int | None = None) -> list[dict]:
    """Dağılım (ad → öğrenci sayısı; Counter / dict ya da [{ad, sayi}] listesi): sayısı EN_AZ_GRUP'tan az olan
    kalemler tek bir `diger_etiketi` satırında birleşir (birlesik = kaç kalem). Birleşik satır da EN_AZ_GRUP'tan
    azsa sayısı None, gizli=True olur. Büyük kalemler azalan sırada, en fazla ilk_n tane; "Diğer" en sonda."""
    if not isinstance(sayim, (Counter, dict)):
        c = Counter()
        for x in sayim:
            c[x[ad_anahtari]] += x[sayi_anahtari] or 0
        sayim = c
    buyuk, diger_n, diger_k = [], 0, 0
    for ad, s in sorted(sayim.items(), key=lambda kv: -kv[1]):
        if ad == diger_etiketi or not yeterli(s):
            diger_n += s
            diger_k += 1
        else:
            buyuk.append({ad_anahtari: ad, sayi_anahtari: s})
    if ilk_n is not None:
        buyuk = buyuk[:ilk_n]
    if diger_n:
        buyuk.append({ad_anahtari: diger_etiketi, sayi_anahtari: diger_n if yeterli(diger_n) else None,
                      "diger": True, "birlesik": diger_k, "gizli": not yeterli(diger_n)})
    return buyuk


def siniflari_birlestir(siniflar: list, diger_etiketi: str = "Diğer sınıflar") -> dict:
    """Her öğe bir yanıtın grubu (ör. sınıf): EN_AZ_GRUP'tan az yanıtlı gruplar `diger_etiketi` olur;
    birleşik grup da azsa None (grup bilgisi gösterilmez). {grup: gösterilecek_etiket | None}"""
    say = Counter(siniflar)
    kucuk = {k for k, n in say.items() if n < EN_AZ_GRUP}
    diger = sum(say[k] for k in kucuk)
    return {k: (k if k not in kucuk else (diger_etiketi if diger >= EN_AZ_GRUP else None)) for k in say}
