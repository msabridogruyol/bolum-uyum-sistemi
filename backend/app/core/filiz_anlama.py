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

from sqlalchemy import text
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
_ACIK_KARSI = (" fark", "karsilastir", " vs ", " hangisi", " arasinda", " yoksa ", " ayni sey", " ayni mi", " benzer")


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


def _puan_metni(p: str | None) -> str | None:
    """[2026-11-02] "Değişken" puan türü öğrenciye açık değil: üniversiteye / programa göre değiştiği söylenir."""
    if p and (p.strip().lower().startswith("değişken") or p.strip().lower().startswith("üniversiteye göre")):
        return "üniversiteye göre değişen"
    return p


def _kunye(o: dict) -> str:
    p = _puan_metni(o["puan"])
    parca = [x for x in (f"{o['sure']}" if o["sure"] else "", f"{p} puan türü" if p else "") if x]
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
        return f"{ad.removeprefix('Bir gününü yaşa: ')} olarak bir gün nasıl geçer?"
    if b.tur == "zorgun":
        return f"{ad.removesuffix(': zor günler').removesuffix(' alanında zor günler')} için zor günler nasıl geçer?"
    if b.tur == "mulakat":
        return f"{ad.removesuffix(' mülakat simülasyonu')} mülakatında ne sorulur?"
    if b.tur == "sozluk":
        return f"{ad} ne demek?"
    return f"{ad} nedir?"


def _bolum_secenekleri(d: fb.Dizin, v: str) -> list[str]:
    ad = _gorunen(d, v)
    return [f"{ad} bölümü hakkında bilgi verir misin?", f"{ad} bölümünde hangi dersler var?", f"{ad} mezunları nerelerde çalışır?"]


def _meslek_gorunen(d: fb.Dizin, anahtar: str, soru: str) -> str:
    """[2026-11-02 simülasyon] Meslek adı ekranda Türkçe harflerle: önce sistemdeki meslek sayfasının adı, yoksa öğrencinin
    yazdığı sözcük(ler) (önceden sadeleştirilmiş anahtar "Tasarimci" diye gösteriliyordu)."""
    m = next((b.baslik.rsplit(" (", 1)[0] for b in d.belgeler if b.tur == "meslek" and b.varlik == anahtar), None)
    if m:
        return m
    kel = anahtar.split()
    soz = re.findall(r"[\wçğıöşüÇĞİÖŞÜâîû]+", soru or "")
    for i in range(len(soz) - len(kel) + 1):
        parca = soz[i:i + len(kel)]
        if all(fb.sade(p).strip().startswith(k[: max(3, len(k) - 2)]) for p, k in zip(parca, kel)):
            ad = " ".join(parca)
            return ad[:1].replace("i", "İ").upper() + ad[1:]
    return anahtar.capitalize()


# ---------------------------------------------------------------------------------------------------- niyetler
def meslek_yolu(d: fb.Dizin, soru: str) -> Cevap | None:
    t = f" {fb.duzelt(soru)} "
    if not any(k in t for k in _MESLEK_YOLU):
        return None
    for anahtar, hedef in d.varliklari_coz(soru):
        bolumler = sorted(h for h in hedef if h in d.bolumler)
        if not bolumler or anahtar in d.bolumler:      # soruda doğrudan bölüm adı varsa bu niyet değil
            continue
        meslek_adi = _meslek_gorunen(d, anahtar, soru)
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


# Yalnızca "X mi Y mi" kalıbında tek başına yazılan kısa adlar ("tip mi dis mi"): genel metinde "dis" dış/diş belirsiz
_KISA_KARSI = {"dis": "dis hekimligi", "disci": "dis hekimligi", "eczane": "eczacilik"}


def karsilastirma(d: fb.Dizin, soru: str) -> Cevap | None:
    t = f" {fb.duzelt(soru)} "
    if not any(k in t for k in _KARSILASTIR):
        return None
    bolumler: list[str] = []
    parca = [p.strip() for p in re.split(r" (?:mi|mu|yoksa|veya|ya da|ile) ", t) if p.strip()]
    ek = [_KISA_KARSI[p.split()[-1]] for p in parca if p.split() and p.split()[-1] in _KISA_KARSI
          and _KISA_KARSI[p.split()[-1]] in d.bolumler]
    for anahtar, hedef in d.varliklari_coz(soru) + [(e, {e}) for e in ek]:
        bh = sorted((h for h in hedef if h in d.bolumler), key=lambda h: (not h.startswith(anahtar.split()[0]), len(h)))
        # Ad birden çok bölüme çıkıyorsa ("bilgisayar", "siyaset bilimi") adla başlayan en kısa bölüm; seçenekler diğerlerini gösterir
        if bh and (len(bh) == 1 or bh[0].startswith(anahtar.split()[0])) and bh[0] not in bolumler:
            bolumler.append(bh[0])
    if len(bolumler) < 2:
        return None
    # "X mi Y mi" kalıbı ya da açık karşılaştırma sözcüğü gerekir: "işletmede matematik var mı" karşılaştırma değil
    ayri = sum(1 for p in parca if any(h in d.bolumler for _, hs in d.varliklari_coz(p) for h in hs)
               or (p.split() and p.split()[-1] in _KISA_KARSI))
    if ayri < 2 and not any(k in t for k in _ACIK_KARSI):
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


# "kazanmak" üniversite için de kullanılır ("psikolojiyi kazanırsam"): yalnızca para anlamındaki kalıplar
_MAAS = ("maas", "kazanilir", "ne kadar kazan", "ne kadar para", "para kazan", "cok kazandir", "ucreti", "aylik gelir",
         "ne kazanir", "kazanci", "kac para", "iyi para", "para var mi")


def _bolum_id(db: Session, v: str) -> int | None:
    for bid, ad in db.execute(text("SELECT id, ad FROM bolumler WHERE durum = 'yayinda'")).all():
        if " ".join(fb.sade(ad).split()) == v:
            return bid
    return None


def maas_sorusu(d: fb.Dizin, soru: str, moduller: set[str] | None, db: Session | None = None) -> Cevap | None:
    """Maaş sorusu. Sistemdeki kazanç verisi (TÜİK meslek grubu ortalamasından tahmin, kamu kadro maaşları) İş Hayatı'ndadır:
    modül açık ve o bölüm için veri varsa oraya yönlendirir; yoksa uydurmadan söyler."""
    t = f" {fb.duzelt(soru)} "
    if not any(k in t for k in _MAAS):
        return None
    hedef = [h for _, hs in d.varliklari_coz(soru) for h in sorted(hs) if h in d.bolumler]
    if not hedef:
        return None
    ad = _gorunen(d, hedef[0])
    secenek = [f"{ad} mezunları nerelerde çalışır?", f"{ad} bölümü hakkında bilgi verir misin?"]
    if moduller is not None and "is_hayati" not in moduller:
        return Cevap("Kazanç bilgileri İş Hayatı bölümünde yer alıyor; okulunun paketinde bu bölüm yok. "
                     f"{ad} mezunlarının hangi alanlarda çalıştığını anlatabilirim. 🌱", "icerik_yok", secenek)
    eksik = None
    if db is not None:
        try:
            from app.core import is_hayati_servisi as ihs
            bid = _bolum_id(db, hedef[0])
            v = ihs.bolum_verisi(db, bid) if bid else None
            eksik = set(v["eksik"]) if v else None
        except Exception:
            db.rollback()
    if eksik is not None and not {"kazanc", "kamu"} <= eksik:
        return Cevap(f"📖 {ad} için kazanç bilgisi İş Hayatı sayfasında, “İlk Maaşla Bir Ay” sekmesinde. Rakamlar TÜİK meslek grubu "
                     "ortalamalarından hesaplanan bir tahmindir (varsa kamu kadro maaşları da orada); ilk iş maaşı genellikle "
                     "ortalamanın altındadır. Maaşlar kuruma, şehre ve deneyime göre de değişir.\n\nKaynak: İş Hayatı › İlk Maaşla Bir Ay",
                     "icerik", secenek + ["Brüt ve net maaş farkı ne demek?"])
    return Cevap(f"Sistemde {ad} için kazanç verisi henüz yok; maaşlar kuruma, şehre, sektöre ve deneyime göre çok değişir. "
                 f"{ad} mezunlarının hangi alanlarda çalıştığını ve bölümü anlatabilirim. 🌱", "icerik", secenek)


_KUNYE = ("kac yil", "kac yilda", "suresi", "kac donem", "kac yillik", "puan turu", "hangi puan", "puan turuyle", "hangi alan",
          " yil mi", " yillik mi", "kac senede", "kac yilda biter", "yil surer", "yil okunur")


def kunye_sorusu(d: fb.Dizin, soru: str) -> Cevap | None:
    """Süre / puan türü sorusu ve tek bölüm: bölüm sayfasındaki künye bilgisiyle doğrudan cevap."""
    t = f" {fb.duzelt(soru)} "
    if not any(k in t for k in _KUNYE):
        return None
    hedef = {h for _, hs in d.varliklari_coz(soru) for h in hs if h in d.bolumler}
    if len(hedef) != 1:
        return None
    o = _bolum_ozet(d, next(iter(hedef)))
    if not (o["sure"] or o["puan"]):
        return None
    p = _puan_metni(o["puan"])
    parca = ([f"öğrenim süresi {o['sure']}"] if o["sure"] else []) + (
        [("puan türü üniversiteye göre değişiyor" if p != o["puan"] else f"puan türü {p}")] if p else [])
    return Cevap(f"📖 {o['ad']}: {', '.join(parca)}.\n{o['ilk']}\n\nKaynak: {o['nerede']}", "icerik", _bolum_secenekleri(d, next(iter(hedef)))[1:])


# [2026-11-02 simülasyon] İş Hayatı'na özgü içerik türleri: soru açıkça bunlardan birini istiyorsa ve okulun paketinde
# İş Hayatı yoksa, başka bir sayfayla (ör. bölümün "mezunlar nerede çalışır" sayfası) cevap verilmez; durum söylenir.
_IS_HAYATI_NIYET = {
    "mulakat": (("mulakat", "is gorusmesi", "is gorusmesinde", "gorusmede ne sor"), "Mülakat simülasyonu ve mülakat pratiği"),
    "cv": ((" cv ", " cv'", "ozgecmis", "on yazi"), "CV ve ön yazı atölyesi"),
    "ders": (("brut", "net maas", "bordro", "sgk prim", "kidem tazminat", "ihbar sure"), "Maaş, bordro ve çalışma hakları dersleri"),
}


def kapali_modul_cevabi(d: fb.Dizin, soru: str, moduller: set[str] | None) -> Cevap | None:
    if moduller is None or "is_hayati" in moduller:
        return None
    t = f" {fb.duzelt(soru)} "
    for anahtarlar, ad in _IS_HAYATI_NIYET.values():
        if any(k in t for k in anahtarlar):
            bolum = [h for _, hs in d.varliklari_coz(soru) for h in sorted(hs) if h in d.bolumler]
            secenek = _bolum_secenekleri(d, bolum[0]) if bolum else ["Rehber öğretmenime nasıl ulaşırım?"]
            ek = f" {_gorunen(d, bolum[0])} bölümünü ve mezunlarının nerelerde çalıştığını anlatabilirim." if bolum else \
                " Bu konuda rehber öğretmenin de yardımcı olabilir."
            return Cevap(f"{ad} İş Hayatı bölümünde yer alıyor; okulunun paketinde bu bölüm yok.{ek} 🌱", "icerik_yok", secenek)
    return None


def onceden_anla(db: Session, soru: str, moduller: set[str] | None) -> Cevap | None:
    """Kişisel konulardan ÖNCE denenir: karşılaştırma, meslek yolu, güçlü bilgi sorusu."""
    d = fb.dizin(db)
    t = f" {fb.duzelt(soru)} "
    # [2026-11-02 simülasyon] "Güçlü yön ne demek?", "hedef bölüm ne anlama geliyor": kişisel sözcük geçse de bu bir
    # tanım sorusudur; terim sözlükte aynen varsa sözlükten cevaplanır (öğrencinin kendi sonucuna gidilmez).
    if any(k in t for k in fb._TANIM) and not any(k in t for k in (" benim ", " bana ", " hedefim", " sonucum", " puanim")):
        sb = fb.sozluk_bul(db, soru)
        if sb is not None and not d.varliklari_coz(soru):
            return Cevap(f"📖 {sb.baslik}\n{fb._kirp(sb.metin)}\n\nKaynak: {sb.nerede}", "icerik")
    if fb.kisisel_mi(soru) and not any(k in t for k in _MESLEK_YOLU):
        return None
    c = kapali_modul_cevabi(d, soru, moduller)
    if c:
        return c
    for f in (karsilastirma, meslek_yolu):
        c = f(d, soru)
        if c:
            return c
    for f in (lambda d_, s_, m_: maas_sorusu(d_, s_, m_, db), lambda d_, s_, m_: kunye_sorusu(d_, s_)):
        c = f(d, soru, moduller)
        if c:
            return c
    # Tanım sorusu ve terim sözlükte aynen var: sözlük (soruda geçen bölüm adından daha uzun/özgülse)
    sb = fb.sozluk_bul(db, soru)
    if sb is not None:
        coz = d.varliklari_coz(soru)
        en_uzun_ad = max((len(a) for a, _ in coz), default=0)
        tanim = any(k in f" {fb.duzelt(soru)} " for k in fb._TANIM)
        # Tanım kalıbı yoksa ("hazırlık sınıfı zorunlu mu") sözlük yalnızca soruda bölüm/meslek adı geçmiyorsa
        if (tanim or not coz) and max(len(a) for a in sb.adlar) >= en_uzun_ad:
            return Cevap(f"📖 {sb.baslik}\n{fb._kirp(sb.metin)}\n\nKaynak: {sb.nerede}", "icerik")
    if fb.bilgi_sorusu_mu(db, soru) or fb.sozluk_sorusu_mu(db, soru):
        bulunan = fb.bilgi_ara(db, soru, moduller)
        if bulunan:
            ilk = bulunan[0].belge
            diger = [soru_sablonu(s.belge) for s in bulunan[1:3] if s.belge.baslik != ilk.baslik]
            return Cevap(fb.bilgi_cevabi(bulunan[:1]), "icerik", list(dict.fromkeys(diger)))
    return None


_GENEL_KOK = {w[:5] for w in "verir misin musun nasil neler nedir hangi olur olan icin gibi kadar zaman yapar yapmak".split()}


def alan_bolumleri(d: fb.Dizin, soru: str, bolum_hedef: list[str]) -> list[str]:
    """Soru bir alanı soruyorsa ("muhendislik", "ogretmenlik", "saglik alaninda neler var"): adında o sözcük geçen bölümler."""
    if bolum_hedef and len(bolum_hedef) <= 6:
        return []
    if len(bolum_hedef) > 6:
        return bolum_hedef
    kel = [w for w in fb.duzelt(soru).split() if len(w) >= 5 and w not in fb._DURAK and w[:5] not in _GENEL_KOK]
    for w in kel:
        uyan = [v for v in d.bolumler if any(len(x) >= 5 and fb._ek_toleransli(w, x) for x in v.split())]
        if len(uyan) >= 2:
            return uyan
    # Kısa alan sorusu ("saglik", "saglik alaninda neler var"): bölüm tanıtımlarında bu sözcük öne çıkan bölümler
    alan_sozu = any(w.startswith("alan") for w in fb.duzelt(soru).split())
    if kel and (len(kel) == 1 or (alan_sozu and len(kel) <= 2)) and len(fb.sorgu_kokleri(soru)) <= 3 \
            and not any(k in f" {fb.duzelt(soru)} " for k in fb._TANIM):
        bol: list[str] = []
        for s in d.ara(" ".join(kel), set(), adet=40):
            if s.puan < 5.0 or s.belge.tur not in ("bolum", "bolum_ders", "bolum_is"):
                continue                                   # bölümün kendi tanıtımı (meslek / bilmen gerekenler değil)
            v = s.belge.varlik
            for h in ([v] if v in d.bolumler else []):
                if h not in bol:
                    bol.append(h)
        if len(bol) >= 2:
            return bol[:8]
    return []


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
        # Soruda ad yokken tek bir bölümün/mesleğin sayfası cevap olmaz ("mülakatta ne sorarlar" → rastgele bölümün mülakatı)
        if bulunan and not hedefler and bulunan[0].belge.varlik:
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
        if not kisisel:
            niyet = any(k in f" {fb.duzelt(soru)} " for k in fb._BILGI_NIYET)
            kendi = [x for x in d.ara(soru, moduller, adet=12) if x.belge.varlik == v
                     or x.belge.sahip == v]
            # Bilgi niyeti varsa ya da bölümün kendi belgesi soruyla güçlü eşleşiyorsa ("grafik tasarım için yetenek sınavı var mı")
            if kendi and (niyet or kendi[0].puan >= fb.BAGLAM_ESIK or fb._niyet_katsayisi(soru, kendi[0].belge.tur) > 1):
                ilk = kendi[0].belge
                return Cevap(fb.bilgi_cevabi(kendi[:1]), "icerik",
                             [o for o in _bolum_secenekleri(d, v) if o != soru_sablonu(ilk)][:2])
        return Cevap(f"{_gorunen(d, v)} hakkında neyi merak ediyorsun? 🌱", "netlestirme", _bolum_secenekleri(d, v))
    if 1 < len(bolum_hedef) <= 6:
        return Cevap("Hangisini kastettin? 🌱", "netlestirme",
                     [f"{_gorunen(d, v)} bölümü hakkında bilgi verir misin?" for v in bolum_hedef[:4]])
    alan = [] if kisisel else alan_bolumleri(d, soru, bolum_hedef)
    if len(alan) >= 2:
        ornek = sorted(alan, key=len)[:4]
        return Cevap("Bu alanla ilgili sistemde birden çok bölüm var. Hangisini merak ediyorsun? 🌱 Tamamını Bölümler sayfasında görebilirsin.",
                     "netlestirme", [f"{_gorunen(d, v)} bölümü hakkında bilgi verir misin?" for v in ornek])
    if kisisel or fb.ders_baglami_mi(soru, db):
        return None
    # Konu İş Hayatı'ndaysa ama okulda bu modül kapalıysa: açıkça söyle (alakasız seçenek gösterme)
    if moduller is not None and "is_hayati" not in moduller:
        tum = fb.bilgi_ara(db, soru, (moduller | {"is_hayati"}))
        if tum and tum[0].belge.modul == "is_hayati" and tum[0].puan >= fb.BAGLAM_ESIK:
            return Cevap("Bu konu İş Hayatı bölümünde anlatılıyor; okulunun paketinde bu bölüm yer almıyor. "
                         "Rehber öğretmenine sorabilirsin. 🌱", "icerik_yok", ["Rehber öğretmenime nasıl ulaşırım?"])
    # Zayıf adaylardan seçenek: soruda ad yoksa yalnızca genel türler (bir mesleğin günü / zor günleri rastgele önerilmez)
    # [kör ölçüm] alakasız tek terim önerilmesin ("kebap tarifi" → "Algoritmik düşünme"): en az iki ortak sözcük kökü
    kok = set(fb.sorgu_kokleri(soru)) - _GENEL_KOK
    if not coz and any(k in f" {fb.duzelt(soru)} " for k in fb._TANIM):
        ilgili = [s for s in d.ara(soru, moduller, adet=3) if s.belge.tur == "sozluk" and s.puan >= fb.ESIK]
        return Cevap("Bu kavram sistemdeki sözlükte yok, o yüzden tanım veremiyorum. 🌱 Sözlükte benzer kavramlara bakabilirsin"
                     + (":" if ilgili else "; rehber öğretmenine de sorabilirsin."), "bilinmiyor",
                     [soru_sablonu(s.belge) for s in ilgili])
    hepsi = d.ara(soru, moduller, adet=8)
    # [2026-11-02 simülasyon] Genel (bir bölüme bağlı olmayan) belge soruyla en az iki kökte örtüşüyorsa doğrudan o
    # ("mülakata nasıl hazırlanırım" → Mülakat Pratiği ipuçları; bölüm adı sorulmaz)
    genel = [] if coz else [s for s in d.ara(soru, moduller, adet=60) if not s.belge.varlik and s.belge.tur != "sozluk"
                            and s.puan >= 8.0 and len(kok & set(s.belge.kokler)) >= 2
                            and fb._niyet_katsayisi(soru, s.belge.tur) > 1]
    if genel:
        diger = [soru_sablonu(s.belge) for s in genel[1:3] if s.belge.baslik != genel[0].belge.baslik]
        return Cevap(fb.bilgi_cevabi(genel[:1]), "icerik", list(dict.fromkeys(diger)))
    # Soru bir bölüme/mesleğe bağlı içerik türünü soruyor ama ad yok ("iş görüşmesinde ne sorarlar"): adı sor
    ust = [s for s in hepsi[:3] if s.belge.varlik]
    if len(ust) == 3 and len({s.belge.tur for s in ust}) == 1 and fb._niyet_katsayisi(soru, ust[0].belge.tur) > 1:
        tur = ust[0].belge.tur
        ne = {"mulakat": "Mülakat soruları bölüm bölüm hazırlandı", "gun": "Bir gününü yaşa sayfaları meslek meslek hazırlandı",
              "zorgun": "Zor günler meslek meslek anlatılıyor"}.get(tur, "Bu içerik bölüm bölüm hazırlandı")
        genel_ad = [soru_sablonu(s.belge) for s in d.ara(soru, moduller, adet=60)
                    if not s.belge.varlik and s.belge.tur != "sozluk" and s.puan >= 8.0][:1]
        return Cevap(f"{ne}. Hangi bölüm ya da meslek için soruyorsun? Adını yazarsan onu gösteririm; örnekler: 🌱",
                     "netlestirme", list(dict.fromkeys(genel_ad + [soru_sablonu(s.belge) for s in ust]))[:4])
    adaylar = [s for s in hepsi
               if s.puan >= 8.0 and not s.belge.varlik
               and (len(kok & set(s.belge.kokler)) >= 2 or fb._niyet_katsayisi(soru, s.belge.tur) > 1)]
    secenek = list(dict.fromkeys(soru_sablonu(s.belge) for s in adaylar))[:3]
    if secenek:
        return Cevap("Tam anlayamadım; şunlardan birini mi soruyorsun? 🌱", "netlestirme", secenek)
    return None
