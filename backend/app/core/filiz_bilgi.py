# -*- coding: utf-8 -*-
"""
[2026-10-31] Filiz bilgi katmanı: sistemdeki içerikten kaynak göstererek cevap.

Katmanlı Filiz'in 1. katmanı. Yapay zekâya gitmeden, sistemde zaten var olan içerikte arar:
  * Bölümler (bolumler.kisa_aciklama + detay: özet, neler öğrenilir, örnek dersler, kimler için uygun, çalışma alanları,
    bilmen gerekenler, öğrenim süresi, puan türü) ve bölüm sayfasındaki meslekler (ne yapar, bir iş günü, çalışma ortamı,
    beceriler, nasıl olunur)                                                                     — her pakette
  * "Bir gününü yaşa" senaryoları (meslek_senaryolari.json)                                      — her pakette
  * Sözlük (sozluk_genis.json)                                                                    — her pakette
  * İş Hayatı: okulda öğretilmeyenler, mesleğe giden yol, zor günler, düşünme atölyesi, CV rehberi, mülakat simülasyonu
                                                                                                  — yalnızca is_hayati modülü açıksa
Paket kuralı korunur: öğrencinin okulunda kapalı olan modülün içeriği aramaya hiç girmez.

Arama: Türkçe sadeleştirme + kısa kök (ilk 5 harf) + BM25. Soruda bir bölüm ya da meslek adı geçiyorsa o varlığın
belgeleri öne alınır; "ders", "bir günü", "nasıl olunur", "zor", "mülakat" gibi niyet sözcükleri belge bölümünü seçer.
Hiçbir şey uydurulmaz: cevap yalnızca bulunan belgenin metninden kurulur ve nereden geldiği yazılır.
Dizin süreç başına bir kez kurulur ve DIZIN_OMRU_SN sonra yenilenir (bölüm içerikleri nadiren değişir).
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

_VERI = Path(__file__).resolve().parents[1] / "data"
DIZIN_OMRU_SN = 1800
ESIK = 12.0           # bu puanın altındaki eşleşme "bulunamadı" sayılır (simülasyonla seçildi: alakasız eşleşmeler < 10)
BAGLAM_ESIK = 15.0    # yapay zekâya bağlam olarak verilecek en düşük puan
VARLIK_KATSAYI = 2.5  # soruda adı geçen bölüm/meslek belgelerinin puan çarpanı

_DURAK = set("""ve veya ile de da mi mı mu mü ne bir bu su şu o icin için gibi kadar daha cok çok en ben sen biz
bana beni benim sana senin bunu sunu onu nasil nasıl neden nicin niçin hangi hangisi var yok olur olan olarak ama fakat
ki ise acaba lutfen lütfen merhaba selam filiz bilgi ver anlat soyle söyle hakkinda hakkında nedir neler""".split())


def sade(m: str | None) -> str:
    t = (m or "").replace("İ", "i").replace("I", "ı").lower()
    t = t.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))
    return re.sub(r"[^a-z0-9+ ]+", " ", t.replace("i̇", "i"))


def kokler(m: str | None) -> list[str]:
    return [w[:5] for w in sade(m).split() if len(w) > 1 and w not in _DURAK]


@dataclass
class Belge:
    tur: str                 # bolum | bolum_ders | bolum_is | bolum_bilmen | meslek | gun | sozluk | ders | yol | zorgun | dusunme | cv | mulakat
    baslik: str
    metin: str
    nerede: str              # öğrenciye gösterilen yer: "Bölümler › Hukuk › Meslekler"
    modul: str | None = None # None = her pakette
    varlik: str = ""         # sadeleştirilmiş bölüm ya da meslek adı
    adlar: tuple = ()        # sözlük: terim ve eş anlamlıları (sadeleştirilmiş); yalnızca soruda aynen geçerse eşleşir
    kokler: Counter = field(default_factory=Counter)


@dataclass
class Sonuc:
    belge: Belge
    puan: float


class Dizin:
    def __init__(self, belgeler: list[Belge]):
        self.belgeler = belgeler
        self.ters: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for i, b in enumerate(belgeler):
            b.kokler = Counter(kokler(f"{b.baslik} {b.baslik} {b.metin}"))
            for k, n in b.kokler.items():
                self.ters[k].append((i, n))
        self.ort = (sum(sum(b.kokler.values()) for b in belgeler) / len(belgeler)) if belgeler else 1.0
        self.varliklar = sorted({b.varlik for b in belgeler if b.varlik}, key=len, reverse=True)

    def _idf(self, k: str) -> float:
        n = len(self.ters.get(k, ()))
        return math.log(1 + (len(self.belgeler) - n + 0.5) / (n + 0.5)) if n else 0.0

    def soru_varliklari(self, soru: str) -> list[str]:
        t = f" {sade(soru)} "
        bulunan = []
        for v in self.varliklar:   # uzundan kısaya: "endustri muhendisligi" "muhendislik"ten önce
            if len(v) >= 4 and f" {v} " in t and not any(v in b for b in bulunan):
                bulunan.append(v)
        return bulunan

    def ara(self, soru: str, moduller: set[str] | None = None, adet: int = 3) -> list[Sonuc]:
        sorgu = kokler(soru)
        if not sorgu:
            return []
        varliklar = set(self.soru_varliklari(soru))
        t_soru = f" {sade(soru)} "
        puan: dict[int, float] = defaultdict(float)
        for k in set(sorgu):
            idf = self._idf(k)
            for i, n in self.ters.get(k, ()):
                b = self.belgeler[i]
                uz = sum(b.kokler.values())
                puan[i] += idf * n * 2.2 / (n + 1.2 * (0.25 + 0.75 * uz / self.ort))
        sonuc = []
        for i, p in puan.items():
            b = self.belgeler[i]
            if b.modul and (moduller is None or b.modul not in moduller):
                continue          # paket kuralı: kapalı modülün içeriği yok
            if b.adlar and not any(f" {a} " in t_soru for a in b.adlar):
                continue          # sözlük: terim soruda aynen geçmiyorsa ("taban puan" ≠ "taban suyu")
            if varliklar:
                if b.varlik in varliklar:
                    p *= VARLIK_KATSAYI
                elif b.varlik:
                    p *= 0.3      # başka bir bölüm/meslekten gelen belge geri plana
            p *= _niyet_katsayisi(soru, b.tur)
            sonuc.append(Sonuc(b, p))
        sonuc.sort(key=lambda s: -s.puan)
        return sonuc[:adet]


# ---------------------------------------------------------------------------------------------------------- niyet
_NIYET = [
    (("ders", "okut", "ogren", "mufredat", "egitim"), {"bolum_ders": 1.8}),
    (("gunu", "gunum", "gunun", "bir gun", "ne yapar", "is gunu", "gunluk"), {"gun": 1.8, "meslek": 1.5}),
    (("nasil olun", "nasil giri", "nasil bas", "girmek ici", "olmak ici", "yolu", "giden yol", "adim"), {"meslek": 1.4, "yol": 2.2}),
    (("calis", "nerede", "is bul", "is imkan", "kariyer", "mezun"), {"bolum_is": 1.6, "meslek": 1.3}),
    (("kimler", "uygun", "kime uyar", "ozellik"), {"bolum": 1.4}),
    (("hakkinda", "bilgi", "anlat", "nedir", "nasil bir", "tanit", "kac yil", "suresi", "puan tur"), {"bolum": 1.6}),
    (("zor", "stres", "kotu yan", "zorluk"), {"zorgun": 1.8}),
    (("mulakat", "gorusme sor", "is gorusmesi"), {"mulakat": 2.0}),
    (("cv", "ozgecmis"), {"cv": 2.0}),
    (("ne demek", "anlami", "nedir", "tanim"), {"sozluk": 1.6}),
    (("brut", "net maas", "bordro", "sgk", "kidem", "ihbar", "izin", "mesai", "sozlesme", "staj", "para yonet"), {"ders": 2.0}),
    (("kok neden", "korelasyon", "algoritma", "ikiye bol", "ogrenmeyi ogren", "veriyi oku"), {"dusunme": 2.0}),
]


def _niyet_katsayisi(soru: str, tur: str) -> float:
    t = sade(soru)
    k = 1.0
    for anahtarlar, turler in _NIYET:
        if tur in turler and any(a in t for a in anahtarlar):
            k = max(k, turler[tur])
    return k


# ---------------------------------------------------------------------------------------------------------- belgeler
def _oku(ad: str):
    try:
        return json.loads((_VERI / ad).read_text(encoding="utf-8"))
    except Exception:
        return None


def _ad(bolum_ad: str) -> str:
    from app.core.filiz_rehber import _baslik
    return _baslik(bolum_ad) if bolum_ad else bolum_ad


def _liste(x) -> str:
    if isinstance(x, list):
        parca = [str(i).strip() for i in x if i and str(i).strip()]
        return " ".join(p if p[-1] in ".!?…" else p + "." for p in parca)
    return str(x or "")


def _bolum_belgeleri(db: Session) -> list[Belge]:
    from sqlalchemy import text
    out: list[Belge] = []
    for b in db.execute(text("SELECT ad, kisa_aciklama, detay FROM bolumler ORDER BY ad")).all():
        d = b.detay if isinstance(b.detay, dict) else (json.loads(b.detay) if isinstance(b.detay, str) and b.detay.strip().startswith('{') else {})
        ad = _ad(b.ad)
        v = sade(b.ad).strip()
        yer = f"Bölümler › {ad}"
        # Kısa olgular başta: cevap kırpıldığında da süre ve puan türü görünsün
        genel = " ".join(x for x in [f"Öğrenim süresi: {d.get('ogrenim_suresi')}." if d.get("ogrenim_suresi") else "",
                                     f"Puan türü: {d.get('puan_turu')}." if d.get("puan_turu") else "",
                                     d.get("ozet") or b.kisa_aciklama or "",
                                     f"Kimler için uygun: {_liste(d.get('kimler_icin_uygun'))}" if d.get("kimler_icin_uygun") else ""] if x)
        if genel:
            out.append(Belge("bolum", f"{ad} bölümü", genel, f"{yer} › Genel bakış", None, v))
        ders = " ".join(x for x in [_liste(d.get("neler_ogrenilir")),
                                    f"Örnek dersler: {_liste(d.get('ornek_dersler'))}." if d.get("ornek_dersler") else ""] if x)
        if ders:
            out.append(Belge("bolum_ders", f"{ad}: neler öğrenilir, hangi dersler var", ders, f"{yer} › Genel bakış", None, v))
        meslek_adlari = [m.get("ad") for m in (d.get("meslekler") or []) if isinstance(m, dict) and m.get("ad")]
        is_metni = " ".join(x for x in [_liste(d.get("calisma_alanlari")),
                                        f"Mezunların sık yaptığı meslekler: {', '.join(meslek_adlari)}." if meslek_adlari else ""] if x)
        if is_metni:
            out.append(Belge("bolum_is", f"{ad} mezunları nerelerde çalışır", is_metni, f"{yer} › Meslekler", None, v))
        if d.get("bilmen_gerekenler"):
            out.append(Belge("bolum_bilmen", f"{ad} hakkında bilmen gerekenler", _liste(d.get("bilmen_gerekenler")), f"{yer} › Genel bakış", None, v))
        for m in d.get("meslekler") or []:
            if not isinstance(m, dict) or not m.get("ad"):
                continue
            parca = [m.get("aciklama") or ""]
            if m.get("gunluk_isler"):
                parca.append("Bir iş gününde: " + _liste(m.get("gunluk_isler")))
            if m.get("calisma_ortami"):
                parca.append("Çalışma ortamı: " + str(m["calisma_ortami"]))
            if m.get("gerekli_beceriler"):
                parca.append("Gereken beceriler: " + ", ".join(str(x) for x in m["gerekli_beceriler"]) + "."
                             if isinstance(m["gerekli_beceriler"], list) else "Gereken beceriler: " + str(m["gerekli_beceriler"]))
            if m.get("nasil_olunur"):
                parca.append("Nasıl olunur: " + str(m["nasil_olunur"]))
            out.append(Belge("meslek", f"{m['ad']} ({ad})", " ".join(p for p in parca if p),
                             f"{yer} › Meslekler › {m['ad']}", None, sade(m["ad"]).strip()))
    return out


def _dosya_belgeleri() -> list[Belge]:
    out: list[Belge] = []
    sen = _oku("meslek_senaryolari.json") or {}
    for meslek, liste in sen.items():
        if not isinstance(liste, list):
            continue
        anlar = [f"{s.get('saat', '')} {s.get('baslik', '')}: {s.get('durum', '')}" for s in liste if isinstance(s, dict)]
        if anlar:
            out.append(Belge("gun", f"Bir gününü yaşa: {meslek}", " ".join(anlar),
                             "Bölüm sayfası › Meslekler › 🎬 Bir gününü yaşa", None, sade(meslek).strip()))
    soz = _oku("sozluk_genis.json") or {}
    for t in soz.get("terimler") or []:
        if isinstance(t, list) and len(t) >= 3 and t[0] and t[2]:
            ornek = f" Örnek: {t[3]}" if len(t) > 3 and t[3] else ""
            adlar = tuple(a for a in {sade(t[0]).strip(), *(sade(x).strip() for x in (t[4] if len(t) > 4 and isinstance(t[4], list) else []))} if len(a) >= 2)
            out.append(Belge("sozluk", str(t[0]), f"{t[2]}{ornek}", "Sözlük", None, "", adlar))
    # ---- İş Hayatı (yalnızca is_hayati modülü açık okullarda)
    ders = _oku("is_hayati_dersler.json") or {}
    for d in ders.get("dersler") or []:
        kart = " ".join(f"{k.get('baslik', '')}: {k.get('metin', '')}" for k in d.get("kartlar") or [] if isinstance(k, dict))
        out.append(Belge("ders", d.get("baslik", ""), f"{d.get('ozet', '')} {kart}".strip(),
                         f"İş Hayatı › Okulda Öğretilmeyenler › {d.get('baslik', '')}", "is_hayati", ""))
    yol = _oku("meslege_yol.json") or {}
    for kod, a in (yol.get("alanlar") or {}).items():
        if not isinstance(a, dict) or not a.get("adimlar"):
            continue
        adim = " → ".join(f"{x.get('baslik', '')} ({x.get('aciklama', '')})" for x in a["adimlar"] if isinstance(x, dict))
        out.append(Belge("yol", f"{a.get('ad', kod)} alanında mesleğe giden yol", adim.replace("{SURE}", "lisans süresi"),
                         "İş Hayatı › Mesleğe Giden Yol", "is_hayati", ""))
    zg = _oku("zor_gunler.json") or {}
    for kod, a in (zg.get("alanlar") or {}).items():
        sen_ = [f"{s.get('baslik', '')}: {s.get('durum', '')}" for s in a.get("senaryolar") or [] if isinstance(s, dict)]
        if sen_:
            out.append(Belge("zorgun", f"{a.get('ad', kod)} alanında zor günler", " ".join(sen_), "İş Hayatı › Zor Günler", "is_hayati", ""))
    for meslek, liste in (zg.get("meslekler") or {}).items():
        sen_ = [f"{s.get('baslik', '')}: {s.get('durum', '')} {s.get('basa_cikma', '')}" for s in liste or [] if isinstance(s, dict)]
        if sen_:
            out.append(Belge("zorgun", f"{meslek}: zor günler", " ".join(sen_), "İş Hayatı › Zor Günler", "is_hayati", sade(meslek).strip()))
    du = _oku("dusunme_atolyesi.json") or {}
    for a in du.get("araclar") or []:
        arac = a.get("arac") or {}
        out.append(Belge("dusunme", a.get("ad", ""), f"{a.get('ozet', '')} {arac.get('metin', '') if isinstance(arac, dict) else ''}".strip(),
                         f"İş Hayatı › Düşünme Atölyesi › {a.get('ad', '')}", "is_hayati", ""))
    cv = _oku("cv_rehberi.json") or {}
    for k in cv.get("konular") or []:
        if isinstance(k, dict) and k.get("baslik"):
            bloklar = " ".join(str(x.get("metin", "")) for x in k.get("bloklar") or [] if isinstance(x, dict) and x.get("metin"))
            out.append(Belge("cv", k["baslik"], f"{k.get('ozet', '')} {bloklar}".strip(), "İş Hayatı › CV Atölyesi › CV Rehberi", "is_hayati", ""))
    ms = _oku("mulakat_simulasyonu.json") or {}
    for bolum, m in (ms.get("bolumler") or {}).items():
        if not isinstance(m, dict):
            continue
        sorular = [s.get("soru", s) if isinstance(s, dict) else str(s) for s in m.get("sorular") or []]
        out.append(Belge("mulakat", f"{_ad(bolum)} mülakat simülasyonu", f"Pozisyon: {m.get('pozisyon', '')}. Örnek sorular: {_liste(sorular)}",
                         "İş Hayatı › Mülakat Simülasyonu", "is_hayati", sade(bolum).strip()))
    return [b for b in out if b.baslik and b.metin]


_DIZIN: Dizin | None = None
_DIZIN_ZAMANI = 0.0
_KILIT = threading.Lock()


def dizin(db: Session) -> Dizin:
    global _DIZIN, _DIZIN_ZAMANI
    with _KILIT:
        if _DIZIN is None or time.time() - _DIZIN_ZAMANI > DIZIN_OMRU_SN:
            try:
                bolum = _bolum_belgeleri(db)
            except Exception:
                db.rollback()
                bolum = []
            _DIZIN = Dizin(bolum + _dosya_belgeleri())
            _DIZIN_ZAMANI = time.time()
        return _DIZIN


def dizini_sifirla() -> None:
    global _DIZIN
    with _KILIT:
        _DIZIN = None


# ---------------------------------------------------------------------------------------------------------- cevap
_KISISEL = ("bana", "benim", "benim icin", "hedefim", "hedefime", "sonucum", "sonuclarim", "puanim", "guclu yon",
            "uygun mu", "uyar mi", "secmeli miyim", "yapmaliyim", "ne yapayim", "gorevim", "yol haritam", "profilim")


def kisisel_mi(soru: str) -> bool:
    t = f" {sade(soru)} "
    return any(f" {k}" in t for k in _KISISEL)


def _kirp(m: str, n: int = 520) -> str:
    m = " ".join(m.split())
    if len(m) <= n:
        return m
    kes = m[:n]
    nokta = max(kes.rfind(". "), kes.rfind("; "))
    return (kes[:nokta + 1] if nokta > n * 0.5 else kes.rstrip() + "…")


def bilgi_ara(db: Session, soru: str, moduller: set[str] | None) -> list[Sonuc]:
    d = dizin(db)
    sonuc = [s for s in d.ara(soru, moduller) if s.puan >= ESIK]
    # Soruda bölüm/meslek adı yokken belirli bir bölüme ait belge ancak güçlü eşleşmeyle gelir (yanlış bölümü anlatmamak için)
    if sonuc and not d.soru_varliklari(soru):
        sonuc = [s for s in sonuc if not s.belge.varlik or s.puan >= BAGLAM_ESIK]
    return sonuc


def sozluk_sorusu_mu(db: Session, soru: str) -> bool:
    """Soruda sözlükteki bir terim aynen geçiyor ve tanım soruluyor ("... ne demek / nedir / anlamı")."""
    t = sade(soru)
    if not any(k in t for k in ("ne demek", "nedir", "anlami", "ne anlama")):
        return False
    r = dizin(db).ara(soru, set(), adet=1)
    return bool(r) and r[0].belge.tur == "sozluk" and r[0].puan >= ESIK


# Bilgi niyeti: bölüm / meslek hakkında soru. Ders / sınav çalışması bağlamı değil ("Matematik netimi nasıl artırırım",
# "tarih dersine nasıl çalışayım", "biyoloji için kaynak öner" bölüm tanıtımına gitmemeli). [bağımsız inceleme 2026-10-31]
_BILGI_NIYET = ("bolum", "fakulte", "mezun", "meslek", "hangi ders", "dersler", "neler ogren", "ne ogren", "okutul", "is gunu",
                "bir gunu", "bir gunde", "gununde", "ne yapar", "ne is yapar", "nasil olun", "nerede calis", "nerelerde",
                "hakkinda", "nedir", "nasil bir", "kac yil", "suresi", "puan tur", "kimler", "mulakat", "zor gun", "zor mu",
                "is imkan", "is bul", "kariyer", "olmak icin", "giden yol", "anlat")
_DERS_BAGLAMI = ("net", "calisay", "calismali", "nasil calis", "ders calis", "deneme", "konu", "tyt", "ayt", "yks", "kaynak",
                 "kitap", "soru coz", "test coz", "sinav", "odev", "not ort", "karne", "ogretmen bana")


def ders_baglami_mi(soru: str) -> bool:
    t = f" {sade(soru)} "
    return any(f" {k}" in t for k in _DERS_BAGLAMI)


def bilgi_sorusu_mu(db: Session, soru: str) -> bool:
    """Soruda bir bölüm / meslek adı geçiyor, bilgi niyeti var, soru öğrencinin kendisine ya da ders çalışmaya dair değil:
    önce içerikten cevaplanır."""
    t = f" {sade(soru)} "
    if kisisel_mi(soru) or any(f" {k}" in t for k in _DERS_BAGLAMI):
        return False
    return any(k in t for k in _BILGI_NIYET) and bool(dizin(db).soru_varliklari(soru))


def bilgi_cevabi(sonuclar: list[Sonuc]) -> str | None:
    if not sonuclar:
        return None
    ilk = sonuclar[0].belge
    cevap = f"📖 {ilk.baslik}\n{_kirp(ilk.metin)}\n\nKaynak: {ilk.nerede}"
    digerleri = [s.belge for s in sonuclar[1:3] if s.belge.baslik != ilk.baslik]
    if digerleri:
        cevap += "\nİlgili: " + " · ".join(f"{b.baslik} ({b.nerede})" for b in digerleri)
    return cevap


def baglam_metni(sonuclar: list[Sonuc], sinir: int = 1800) -> str:
    """Yapay zekâya verilecek, sistemdeki ilgili içerik (kaynaklı). Boşsa ''."""
    parcalar, toplam = [], 0
    for s in sonuclar:
        if s.puan < BAGLAM_ESIK:
            continue
        p = f"[{s.belge.nerede}] {s.belge.baslik}: {_kirp(s.belge.metin, 700)}"
        if toplam + len(p) > sinir:
            break
        parcalar.append(p)
        toplam += len(p)
    return "\n".join(parcalar)
