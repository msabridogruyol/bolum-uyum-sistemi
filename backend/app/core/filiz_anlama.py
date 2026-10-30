# -*- coding: utf-8 -*-
"""
[2026-10-31] Filiz anlama katmanı: öğrencinin dağınık sorusunu anlamak ve emin değilken sormak.

Öğrenciler soruyu tam ve doğru kurmaz ("avukat olcam ne okumam lazim", "hukukta neler var dersler falan",
"hukuk mu işletme mi"). filiz_bilgi sorguyu düzeltir ve bölüm / meslek / gündelik meslek adlarını (ekli ya da hafif
hatalı yazılsa da) tanır; bu modül niyeti yorumlar:
  * meslek yolu   — "X olmak için ne okumalıyım / hangi bölüm": X'e giden bölüm(ler), süre, puan türü, nasıl olunur
  * karşılaştırma — iki-üç bölüm adı + "mi / yoksa / fark / hangisi": kısa yan yana özet + Karşılaştır ekranı
  * bilgi sorusu  — filiz_bilgi.bilgi_sorusu_mu (bölüm/meslek adı + bilgi niyeti)
  * netleştirme   — emin değilken tahmin yürütmek yerine "Şunu mu demek istedin?" + tıklanabilir seçenekler
Her cevap yalnızca sistemdeki içerikten kurulur ve kaynak gösterir; hiçbir şey uydurulmaz.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core import filiz_bilgi as fb


@dataclass
class Cevap:
    yanit: str
    kaynak: str                       # icerik | netlestirme | icerik_yok (konu kapalı modülde) | rehber | sabit | bilinmiyor
    secenekler: list[str] = field(default_factory=list)


_MESLEK_YOLU = ("olmak ic", "olmak isti", "olacagim", "olabilirim", "olurum", "olmak lazim", "olmam lazim", "olmak icin",
                "ne okuma", "neyi okuma", "hangi bolum", "okumam lazim", "okumaliyim", "okumam gerek", "nasil olun",
                "nasil olabil", "icin ne oku", "olmanin yolu", "olmak istersem", "olmak icin hangi")
_KARSILASTIR = (" mi ", " mu ", " yoksa ", " fark", "karsilastir", " vs ", " hangisi", " arasinda", " ile ")


def _gorunen(d: fb.Dizin, v: str) -> str:
    return d.bolumler.get(v) or v


def _bolum_ozet(d: fb.Dizin, v: str) -> dict:
    """Bölümün genel belgesinden süre, puan türü ve ilk cümle (yalnızca var olan veri)."""
    g = next((b for b in d.belgeler if b.tur == "bolum" and b.varlik == v), None)
    metin = g.metin if g else ""
    sure = re.search(r"Öğrenim süresi: ([^.]+)\.", metin)
    puan = re.search(r"Puan türü: ([^.]+)\.", metin)
    govde = re.sub(r"^(Öğrenim süresi: [^.]+\. )?(Puan türü: [^.]+\. )?", "", metin)
    ilk = re.split(r"(?<=[.!?])\s", govde, maxsplit=1)[0] if govde else ""
    is_ = next((b for b in d.belgeler if b.tur == "bolum_is" and b.varlik == v), None)
    meslek = re.search(r"Mezunların sık yaptığı meslekler: ([^.]+)\.", is_.metin if is_ else "")
    return {"ad": _gorunen(d, v), "sure": sure.group(1) if sure else None, "puan": puan.group(1) if puan else None,
            "ilk": ilk, "meslek": ", ".join(meslek.group(1).split(", ")[:3]) if meslek else None,
            "nerede": g.nerede if g else f"Bölümler › {_gorunen(d, v)}"}


def _kunye(o: dict) -> str:
    parca = [x for x in (f"{o['sure']}" if o["sure"] else "", f"{o['puan']} puan türü" if o["puan"] else "") if x]
    return f" ({', '.join(parca)})" if parca else ""


def soru_sablonu(b: fb.Belge) -> str:
    """Bir belgeye götüren, öğrencinin tıklayabileceği soru (netleştirme seçeneği). Bu sorular yine aynı belgeye yönlenir."""
    ad = b.baslik
    if ad.rstrip().endswith("?"):
        return ad.strip()
    if b.tur == "bolum":
        return f"{ad.removesuffix(' bölümü')} bölümü hakkında bilgi verir misin?"
    if b.tur == "bolum_ders":
        return f"{ad.split(':')[0]} bölümünde hangi dersler var?"
    if b.tur == "bolum_is":
        return f"{ad.removesuffix(' mezunları nerelerde çalışır')} mezunları nerelerde çalışır?"
    if b.tur == "bolum_bilmen":
        return f"{ad.removesuffix(' hakkında bilmen gerekenler')} bölümü hakkında bilmem gerekenler neler?"
    if b.tur == "meslek":
        return f"{ad.rsplit(' (', 1)[0]} bir iş gününde ne yapar?"
    if b.tur == "gun":
        return f"{ad.removeprefix('Bir gününü yaşa: ').capitalize()} olarak bir gün nasıl geçer?"
    if b.tur == "zorgun":
        return f"{ad.removesuffix(': zor günler').removesuffix(' alanında zor günler').capitalize()} için zor günler nasıl geçer?"
    if b.tur == "mulakat":
        return f"{ad.removesuffix(' mülakat simülasyonu')} mülakatında ne sorulur?"
    if b.tur == "sozluk":
        return f"{ad} ne demek?"
    return f"{ad} nedir?"


def _bolum_secenekleri(d: fb.Dizin, v: str) -> list[str]:
    ad = _gorunen(d, v)
    return [f"{ad} bölümü hakkında bilgi verir misin?", f"{ad} bölümünde hangi dersler var?", f"{ad} mezunları nerelerde çalışır?"]


# ---------------------------------------------------------------------------------------------------- niyetler
def meslek_yolu(d: fb.Dizin, soru: str) -> Cevap | None:
    t = f" {fb.duzelt(soru)} "
    if not any(k in t for k in _MESLEK_YOLU):
        return None
    for anahtar, hedef in d.varliklari_coz(soru):
        bolumler = sorted(h for h in hedef if h in d.bolumler)
        if not bolumler or anahtar in d.bolumler:      # soruda doğrudan bölüm adı varsa bu niyet değil
            continue
        meslek_adi = anahtar.capitalize()
        if len(bolumler) > 6:
            ornek = bolumler[:6]
            return Cevap(f"“{meslek_adi}” birçok bölümle yapılabiliyor ({len(bolumler)} bölüm). Hangi alanda olmak istersin? "
                         f"Birkaç örnek aşağıda; Bölümler › Tüm bölümler sayfasında da arayabilirsin.",
                         "netlestirme", [f"{_gorunen(d, v)} bölümü hakkında bilgi verir misin?" for v in ornek[:4]])
        satirlar = []
        for v in bolumler:
            o = _bolum_ozet(d, v)
            satirlar.append(f"• {o['ad']}{_kunye(o)}")
        nasil = next((b for b in d.belgeler if b.tur == "meslek" and b.varlik == anahtar), None)
        nasil_metin = re.search(r"Nasıl olunur: (.+)$", nasil.metin) if nasil else None
        yanit = f"📖 {meslek_adi} olmak için okunabilecek bölüm{'ler' if len(bolumler) > 1 else ''}:\n" + "\n".join(satirlar)
        if nasil_metin:
            yanit += f"\n\nNasıl olunur: {fb._kirp(nasil_metin.group(1), 300)}"
        yanit += f"\n\nKaynak: {_bolum_ozet(d, bolumler[0])['nerede']}" + (" ve ilgili bölüm sayfaları" if len(bolumler) > 1 else "")
        secenek = ([f"{_gorunen(d, bolumler[0])} bölümünde hangi dersler var?", f"{_gorunen(d, bolumler[0])} mezunları nerelerde çalışır?"]
                   if len(bolumler) == 1 else [f"{_gorunen(d, v)} bölümü hakkında bilgi verir misin?" for v in bolumler[:3]])
        return Cevap(yanit, "icerik", secenek + ["Bana hangi bölümler uygun?"])
    return None


def karsilastirma(d: fb.Dizin, soru: str) -> Cevap | None:
    t = f" {fb.duzelt(soru)} "
    if not any(k in t for k in _KARSILASTIR):
        return None
    bolumler: list[str] = []
    for anahtar, hedef in d.varliklari_coz(soru):
        bh = [h for h in hedef if h in d.bolumler]
        if len(bh) == 1 and bh[0] not in bolumler:
            bolumler.append(bh[0])
    if len(bolumler) < 2:
        return None
    bolumler = bolumler[:3]
    satir = []
    for v in bolumler:
        o = _bolum_ozet(d, v)
        s = f"• {o['ad']}{_kunye(o)}: {o['ilk']}"
        if o["meslek"]:
            s += f" Mezunlar örneğin: {o['meslek']}."
        satir.append(s)
    yanit = ("📖 Kısaca karşılaştıralım:\n" + "\n".join(satir) +
             "\n\nUyum puanını, nedenlerini, meslekleri ve iş hayatını yan yana görmek için Bölümler › Karşılaştır sayfasını kullanabilirsin."
             "\nKaynak: " + " · ".join(_bolum_ozet(d, v)["nerede"] for v in bolumler))
    secenek = [f"{_gorunen(d, v)} bölümünde hangi dersler var?" for v in bolumler[:2]] + ["Bölüm seçiminde kararsızım, ne yapmalıyım?"]
    return Cevap(yanit, "icerik", secenek)


def onceden_anla(db: Session, soru: str, moduller: set[str] | None) -> Cevap | None:
    """Kişisel konulardan ÖNCE denenir: karşılaştırma, meslek yolu, güçlü bilgi sorusu."""
    d = fb.dizin(db)
    if fb.kisisel_mi(soru) and not any(k in f" {fb.duzelt(soru)} " for k in _MESLEK_YOLU):
        return None
    for f in (karsilastirma, meslek_yolu):
        c = f(d, soru)
        if c:
            return c
    # Tanım sorusu ve terim sözlükte aynen var: sözlük (soruda geçen bölüm adından daha uzun/özgülse)
    sb = fb.sozluk_bul(db, soru)
    if sb is not None:
        en_uzun_ad = max((len(a) for a, _ in d.varliklari_coz(soru)), default=0)
        if max(len(a) for a in sb.adlar) >= en_uzun_ad:
            return Cevap(f"📖 {sb.baslik}\n{fb._kirp(sb.metin)}\n\nKaynak: {sb.nerede}", "icerik")
    if fb.bilgi_sorusu_mu(db, soru) or fb.sozluk_sorusu_mu(db, soru):
        bulunan = fb.bilgi_ara(db, soru, moduller)
        if bulunan:
            ilk = bulunan[0].belge
            diger = [soru_sablonu(s.belge) for s in bulunan[1:3] if s.belge.baslik != ilk.baslik]
            return Cevap(fb.bilgi_cevabi(bulunan[:1]), "icerik", list(dict.fromkeys(diger)))
    return None


def sonradan_netlestir(db: Session, soru: str, moduller: set[str] | None) -> Cevap | None:
    """Kişisel konular da eşleşmediyse: güçlü içerik → cevap; varlık var ama niyet belirsiz → o varlık için seçenekler;
    zayıf adaylar → "Şunu mu demek istedin?". Kişisel ve ders çalışma soruları burada içerikle cevaplanmaz."""
    d = fb.dizin(db)
    kisisel = fb.kisisel_mi(soru) or fb.ders_baglami_mi(soru, db)
    coz = d.varliklari_coz(soru)
    hedefler = set().union(*(h for _, h in coz)) if coz else set()
    if not kisisel:
        bulunan = fb.bilgi_ara(db, soru, moduller)
        # Soruda bir ad tanındıysa yalnızca o ada ait belgeyle cevap verilir (başka bölümün/mesleğin içeriği gösterilmez)
        if bulunan and hedefler and bulunan[0].belge.varlik not in hedefler:
            bulunan = []
        if bulunan and (bulunan[0].puan >= fb.BAGLAM_ESIK or d.soru_varliklari(soru)):
            ilk = bulunan[0].belge
            diger = [soru_sablonu(s.belge) for s in bulunan[1:3] if s.belge.baslik != ilk.baslik]
            return Cevap(fb.bilgi_cevabi(bulunan[:1]), "icerik", list(dict.fromkeys(diger)))
    bolum_hedef: list[str] = []
    for anahtar, hedef in coz:
        for h in sorted(hedef):
            if h in d.bolumler and h not in bolum_hedef:
                bolum_hedef.append(h)
    if len(bolum_hedef) == 1:
        v = bolum_hedef[0]
        # Bilgi niyeti varsa (ör. seçenek düğmesinden gelen soru) o bölümün en iyi belgesiyle cevap: döngüye girilmez
        if not kisisel and any(k in f" {fb.duzelt(soru)} " for k in fb._BILGI_NIYET):
            kendi = [x for x in d.ara(soru, moduller, adet=12) if x.belge.varlik == v
                     or d.meslek_bolum.get(x.belge.varlik, set()) == {v}]
            if kendi:
                ilk = kendi[0].belge
                return Cevap(fb.bilgi_cevabi(kendi[:1]), "icerik",
                             [o for o in _bolum_secenekleri(d, v) if o != soru_sablonu(ilk)][:2])
        return Cevap(f"{_gorunen(d, v)} hakkında neyi merak ediyorsun? 🌱", "netlestirme", _bolum_secenekleri(d, v))
    if 1 < len(bolum_hedef) <= 6:
        return Cevap("Hangisini kastettin? 🌱", "netlestirme",
                     [f"{_gorunen(d, v)} bölümü hakkında bilgi verir misin?" for v in bolum_hedef[:4]])
    if kisisel or fb.ders_baglami_mi(soru, db):
        return None
    # Konu İş Hayatı'ndaysa ama okulda bu modül kapalıysa: açıkça söyle (alakasız seçenek gösterme)
    if moduller is not None and "is_hayati" not in moduller:
        tum = fb.bilgi_ara(db, soru, (moduller | {"is_hayati"}))
        if tum and tum[0].belge.modul == "is_hayati" and tum[0].puan >= fb.BAGLAM_ESIK:
            return Cevap("Bu konu İş Hayatı bölümünde anlatılıyor; okulunun paketinde bu bölüm yer almıyor. "
                         "Rehber öğretmenine sorabilirsin. 🌱", "icerik_yok", ["Rehber öğretmenime nasıl ulaşırım?"])
    # Zayıf adaylardan seçenek: soruda ad yoksa yalnızca genel türler (bir mesleğin günü / zor günleri rastgele önerilmez)
    adaylar = [s for s in d.ara(soru, moduller, adet=8)
               if s.puan >= 8.0 and not s.belge.varlik]
    secenek = list(dict.fromkeys(soru_sablonu(s.belge) for s in adaylar))[:3]
    if secenek:
        return Cevap("Tam anlayamadım; şunlardan birini mi soruyorsun? 🌱", "netlestirme", secenek)
    return None
