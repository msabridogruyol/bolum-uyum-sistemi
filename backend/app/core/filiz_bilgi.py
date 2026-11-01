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


# ------------------------------------------------------------------------- [2026-10-31] öğrenci dilini düzeltme
# Öğrenciler soruları tam ve doğru yazmaz: Türkçe karakter yok, konuşma dili ("olcam", "calisiyo", "napcam"), kısaltma
# ("bil muh", "pdr"), ekli bölüm adları ("hukukta", "psikolojiden"), küçük yazım hataları. Sorgu önce düzeltilir;
# bölüm/meslek adları ekli ve hafif hatalı yazılsa da tanınır (Dizin.varliklari_coz).
_KELIME = {
    "bi": "bir", "bisey": "bir sey", "birsey": "bir sey", "bise": "bir sey", "nasi": "nasil", "nasıl": "nasil", "niye": "neden",
    "napcam": "ne yapacagim", "napicam": "ne yapacagim", "napcaz": "ne yapacagiz", "napiyim": "ne yapayim", "napayim": "ne yapayim",
    "napim": "ne yapayim", "napcak": "ne yapacak", "napcan": "ne yapacaksin", "napıcak": "ne yapacak", "naptin": "ne yaptin", "noluyo": "ne oluyor", "noldu": "ne oldu", "nedir ki": "nedir",
    "tmm": "tamam", "slm": "selam", "mrb": "merhaba", "msl": "mesela", "bn": "ben", "bnm": "benim", "sn": "sen", "snn": "senin",
    "cok": "cok", "cokmu": "cok mu", "zormu": "zor mu", "kolaymi": "kolay mi", "iyimi": "iyi mi", "varmi": "var mi",
    "sene": "yil", "senelik": "yillik", "seneligi": "yilligi", "kac senelik": "kac yillik", "uni": "universite",
    "univ": "universite", "unv": "universite", "fak": "fakulte", "fakultesi": "fakulte", "falan": "", "filan": "", "ya": "",
    "abi": "", "abla": "", "hocam": "", "lan": "", "yaa": "", "ki": "", "yani": "", "acaba": "", "lazim": "lazim",
    "psk": "psikoloji", "pdr": "rehberlik ve psikolojik danismanlik", "ybs": "yonetim bilisim sistemleri",
    "uluslararasi": "uluslararasi", "ui": "uluslararasi iliskiler", "iibf": "iktisadi ve idari bilimler",
    "dt": "dis hekimligi", "makina": "makine", "dishekimligi": "dis hekimligi", "tipfakultesi": "tip",
    # [2026-11-02 simülasyon] bitişik yazılan sık soru kalıpları
    "kacyil": "kac yil", "kacyillik": "kac yillik", "kacsene": "kac yil", "kacsenelik": "kac yillik", "nekadar": "ne kadar",
    "nerde": "nerede", "nedemek": "ne demek", "hangibolum": "hangi bolum", "kac il": "kac yil", "kac yl": "kac yil",
    "pan turu": "puan turu", "pan turuyle": "puan turuyle", "senkimsin": "sen kimsin",
}
_IKILI = {   # kısaltma + "muh"
    "bil": "bilgisayar", "bilg": "bilgisayar", "bilgi": "bilgisayar", "end": "endustri", "endus": "endustri",
    "elk": "elektrik ve elektronik", "elek": "elektrik ve elektronik", "ee": "elektrik ve elektronik", "mak": "makine", "makina": "makine", "makine": "makine", "elektrik": "elektrik ve elektronik", "elektronik": "elektrik ve elektronik",
    "bilgisayar": "bilgisayar", "endustri": "endustri", "insaat": "insaat", "kimya": "kimya", "yazilim": "yazilim",
    "ins": "insaat", "kim": "kimya", "yaz": "yazilim", "yzl": "yazilim", "gida": "gida", "cevre": "cevre", "harita": "harita",
}
_MUH = {"muh", "muhen", "muhendis", "muhendislik", "muhendisligi", "muh.", "mh"}   # _IKILI kısaltmasından sonra
_MUH_KISA = {"muh", "muhen", "muh.", "mh"}                                               # herhangi bir sözcükten sonra


# Sistemdeki belgelerde geçen sözcükler (Dizin kurulurken doldurulur) + sık sözcükler: bunlar konuşma dili sayılmaz
_BILINEN: set[str] = set("""ancak gercek gercekten oyuncak kucak bucak sucuk bicak ocak sacak yumurcak tencere bircok
hicbir pecete""".split())


# [2026-11-02 simülasyon] Tek harf hatası düzeltme: "petrl" → petrol, "gretmenligi" → ogretmenligi, "bolmler" → bolumler,
# "maari" → maarif. Yalnızca "çapa" sözcüklerine (bölüm / meslek adları, takma adlar, sözlük terimleri ve Filiz'in konu
# anahtarları) ve yalnızca sorgu sözcüğü sistemin hiçbir metninde geçmiyorsa uygulanır; tek aday yoksa dokunulmaz.
_CAPA: set[str] = set()
_SILME: dict[str, str | None] = {}     # çapa sözcüğünden bir harf silinmiş biçim → çapa (öğrenci bir harfi atlamış)
_DEGIS: dict[str, str | None] = {}     # bir harfi "?" olan biçim → çapa (öğrenci bir harfi yanlış yazmış)


_KALICI_CAPA: list[tuple[list[str], bool]] = []   # Filiz'in konu sözcükleri: dizin yenilenince yeniden eklenir


def capa_kalici_ekle(sozcukler, degisim: bool = False) -> None:
    _KALICI_CAPA.append((list(sozcukler), degisim))
    capa_ekle(sozcukler, degisim)


def _capa_sifirla() -> None:
    """Dizin her kurulduğunda çapalar yalnızca o dizinin adlarından + kalıcı konu sözcüklerinden yeniden kurulur
    (eski içerikten kalan adlar düzeltmeyi yanlış yöne çekmesin)."""
    _CAPA.clear()
    _SILME.clear()
    _DEGIS.clear()
    for sozcukler, degisim in _KALICI_CAPA:
        capa_ekle(sozcukler, degisim)


def capa_ekle(sozcukler, degisim: bool = True) -> None:
    """degisim=False: yalnızca atlanan harf düzeltilir (Filiz'in konu sözcükleri; "okumam" → "okusam" gibi geçerli bir
    sözcüğü başka bir sözcüğe çevirmemek için yanlış harf düzeltmesi yalnızca bölüm / meslek / terim adlarına yapılır)."""
    for x in sozcukler:
        for w in sade(x).split():
            if len(w) < 4 or w in _DURAK:
                continue
            _CAPA.add(w)
            for i in range(len(w)):
                k = w[:i] + w[i + 1:]
                if len(k) >= 4:
                    _SILME[k] = w if _SILME.get(k, w) == w else None
                if degisim and len(w) >= 6:
                    k = w[:i] + "?" + w[i + 1:]
                    _DEGIS[k] = w if _DEGIS.get(k, w) == w else None


def _bitisik_ayir(w: str) -> str:
    """[2026-11-02 simülasyon] Boşluğu unutulmuş iki sözcük ("halkoyunlari", "teknolojisimuhendisligi"): sözcük sistemde
    yoksa ve iki parçası da sistemin bildiği sözcüklerse ayrılır (en dengeli bölünme)."""
    if len(w) < 8 or w in _BILINEN or w in _CAPA or not w.isalpha():
        return w
    en = None
    for i in range(3, len(w) - 3):
        a, b = w[:i], w[i:]
        if (a in _CAPA or a in _BILINEN) and (b in _CAPA or b in _BILINEN) and len(a) >= 4 and len(b) >= 4:
            if en is None or min(len(a), len(b)) > min(len(en[0]), len(en[1])):
                en = (a, b)
    return f"{en[0]} {en[1]}" if en else w


def _yazim(w: str) -> str:
    if len(w) < 4 or not _CAPA or w in _CAPA or w in _BILINEN or w in _DURAK or w in _KELIME or not w.isalpha():
        return w
    if _SILME.get(w):                   # en sık hata atlanan harf: tek adayı varsa o
        return _SILME[w]
    aday = {_DEGIS.get(w[:i] + "?" + w[i + 1:]) for i in range(len(w))}
    aday.discard(None)
    return aday.pop() if len(aday) == 1 else w


def _konusma_eki(w: str) -> str:
    if len(w) < 4 or w in _BILINEN:
        return w
    m = re.match(r"^(\w+?[^aeiou])c(a|e)m$", w)                  # olcam → olacagim, yapcam → yapacagim, edcem → edecegim
    if m and len(m.group(1)) >= 2:
        return m.group(1) + ("acagim" if m.group(2) == "a" else "ecegim")
    m = re.match(r"^(\w+?)yc(a|e)m$", w)                           # okuycam → okuyacagim
    if m:
        return m.group(1) + ("yacagim" if m.group(2) == "a" else "yecegim")
    m = re.match(r"^(\w+?[^aeiou])c(a|e)k$", w)                  # olcak → olacak
    if m and len(m.group(1)) >= 2:
        return m.group(1) + ("acak" if m.group(2) == "a" else "ecek")
    for son, yeni in (("iyom", "iyorum"), ("uyom", "uyorum"),
                      ("iyo", "iyor"), ("uyo", "uyor"), ("cez", "cegiz"), ("caz", "cagiz")):
        if w.endswith(son) and len(w) > len(son) + 1:
            return w[: -len(son)] + yeni
    return w


def _tekrarsiz(out: list[str], acilim: list[str]) -> None:
    """Açılımın başı zaten yazılmışsa sil: ["elektrik"] + "elektrik ve elektronik" → tek "elektrik"."""
    for k in range(min(len(out), len(acilim)), 0, -1):
        if out[-k:] == acilim[:k]:
            del out[-k:]
            return


def anahtar_var(a: str, t: str) -> bool:
    """Anahtar sözcük başında eşleşir, alt dize olarak değil: "koc" ≠ "kocaeli", "zor" ≠ "zorunlu", "hey" ≠ "heyecanliyim".
    3 harf ve altı anahtarlara en çok 3, 4 harflilere en çok 7 harflik ek."""
    a = a.strip()
    if not a:
        return False
    kuyruk = (r"[a-z]{0,3}(?![a-z0-9])" if len(a) <= 3 else r"[a-z]{0,7}(?![a-z0-9])") if len(a) <= 4 and a[-1].isalnum() else ""
    return re.search(rf"(?<![a-z0-9]){re.escape(a)}{kuyruk}", t) is not None


def duzelt(m: str | None) -> str:
    """Sorgu metnini sadeleştirir ve konuşma dilini / kısaltmaları açar (yalnızca öğrenci sorusu için; belgeler değil)."""
    t = sade(m)
    for k, v in sorted(_KELIME.items(), key=lambda x: -len(x[0])):
        if " " in k:
            t = re.sub(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", v, t)
    kel = t.split()
    out = []
    i = 0
    while i < len(kel):
        w = kel[i]
        if i + 1 < len(kel) and w in _IKILI and kel[i + 1].rstrip(".") in _MUH:
            _tekrarsiz(out, _IKILI[w].split())                       # "elektrik elektronik muh": "elektrik" iki kez yazılmasın
            out.append(f"{_IKILI[w]} muhendisligi")
            i += 2
            continue
        if i + 1 < len(kel) and w in _IKILI and kel[i + 1] in ("muhendisi", "muhendisiyim", "muhendisleri"):
            _tekrarsiz(out, _IKILI[w].split())
            out.append(f"{_IKILI[w]} muhendisi")                    # "elektrik muhendisi" → Elektrik ve Elektronik Müh.
            i += 2
            continue
        if w in _MUH_KISA and out and out[-1] not in _DURAK:   # "harita muh", "gida muh." (tam "muhendis" sözcüğü değişmez)
            out.append("muhendisligi")
            i += 1
            continue
        w = _KELIME.get(w, w)
        if w and " " not in w:
            k = _konusma_eki(w)
            w = k if k != w else _yazim(w)     # konuşma dili ("olcam") yazım hatası sayılmaz
            if " " not in w:
                w = _bitisik_ayir(w)
        out.append(w)
        i += 1
    return " ".join(x for x in out if x)


def sorgu_kokleri(m: str | None) -> list[str]:
    return [w[:5] for w in duzelt(m).split() if len(w) > 1 and w not in _DURAK]


_BULUNMA_EKI = {"da", "de", "ta", "te", "nda", "nde", "inde", "inda", "unda", "unde"}
_DERS_ADI = set("""matematik fizik kimya biyoloji tarih cografya felsefe istatistik edebiyat kimya sosyoloji psikoloji ekonomi
muhasebe hukuk""".split())
_KISA_EKLER = {"ta", "da", "te", "de", "tan", "dan", "ten", "den", "ti", "ci", "in", "nin", "a", "e", "i", "yi", "ya", "ye",
               "ci", "cu", "la", "le", "ki"}


def _ek_toleransli(q: str, e: str) -> bool:
    """q (sorudaki sözcük) e'nin (bölüm/meslek adı sözcüğü) ekli ya da hafif hatalı biçimi mi?
    hukukta~hukuk, psikolojiden~psikoloji, muhendisliginde~muhendisligi, psikolji~psikoloji."""
    if q == e:
        return True
    if len(e) < 4:
        return q.startswith(e) and q[len(e):] in _KISA_EKLER          # tip → tipta, tipin
    if q.startswith(e) and len(q) - len(e) <= 6:
        return True
    if len(e) >= 6 and (e[:-1] == q and e[-1] in "iu" or e.endswith("si") and e[:-2] == q):
        return True                                                    # "kalite kontrol uzman" ~ "uzmani" (iyelik eki yazılmamış)
    yumusama = {"k": "g", "p": "b", "t": "d", "c": "c"}
    if (len(e) >= 5 and e[-1] in yumusama and len(q) > len(e) - 1 and q.startswith(e[:-1])
            and q[len(e) - 1] == yumusama[e[-1]] and len(q) - len(e) <= 6):    # hemsirelik → hemsireligi (k→ğ)
        return True
    if len(e) >= 7 and len(q) >= 6 and q[:2] == e[:2] and abs(len(q) - len(e)) <= 2 and (
            q not in _BILINEN or (e.startswith(q) and len(e) - len(q) <= 2)):   # "tasarim"~"tasarimi"; "programi"≠"programci"
        from difflib import SequenceMatcher
        return SequenceMatcher(None, q, e).ratio() >= 0.86              # tek harf hatası / eksik harf
    return False


@dataclass
class Belge:
    tur: str                 # bolum | bolum_ders | bolum_is | bolum_bilmen | meslek | gun | sozluk | ders | yol | zorgun | dusunme | cv | mulakat | mulakat_pratik
    baslik: str
    metin: str
    nerede: str              # öğrenciye gösterilen yer: "Bölümler › Hukuk › Meslekler"
    modul: str | None = None # None = her pakette
    varlik: str = ""         # sadeleştirilmiş bölüm ya da meslek adı
    adlar: tuple = ()        # sözlük: terim ve eş anlamlıları (sadeleştirilmiş); yalnızca soruda aynen geçerse eşleşir
    kokler: Counter = field(default_factory=Counter)
    sahip: str = ""          # meslek / gün sayfasının ait olduğu bölüm (Dizin kurulurken)


@dataclass
class Sonuc:
    belge: Belge
    puan: float


class Dizin:
    def __init__(self, belgeler: list[Belge], esanlam: dict[str, list[str]] | None = None):
        self.belgeler = belgeler
        self.ters: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for i, b in enumerate(belgeler):
            b.kokler = Counter(kokler(f"{b.baslik} {b.baslik} {b.metin}"))
            for k, n in b.kokler.items():
                self.ters[k].append((i, n))
        self.ort = (sum(sum(b.kokler.values()) for b in belgeler) / len(belgeler)) if belgeler else 1.0
        for b in belgeler:
            _BILINEN.update(w for w in sade(f"{b.baslik} {b.metin}").split() if len(w) >= 4)
        self.varliklar = sorted({b.varlik for b in belgeler if b.varlik}, key=len, reverse=True)
        # Bölümler (sade ad → görünen ad) ve meslek → bölüm köprüsü (bölüm sayfalarındaki meslek listelerinden, veriden)
        self.bolumler: dict[str, str] = {}
        self.meslek_bolum: dict[str, set[str]] = defaultdict(set)
        for b in belgeler:
            if b.tur == "bolum" and b.varlik:
                self.bolumler[b.varlik] = b.baslik.removesuffix(" bölümü")
        for b in belgeler:
            if b.tur == "meslek" and b.varlik and "(" in b.baslik:
                bolum_gorunen = b.baslik.rsplit("(", 1)[1].rstrip(")")
                bv = next((k for k, v in self.bolumler.items() if v == bolum_gorunen), None)
                if bv:
                    self.meslek_bolum[b.varlik].add(bv)
                    b.sahip = bv                     # bu meslek sayfası hangi bölümün ("Akademisyen (Politika ve Ekonomi)")
        for b in belgeler:
            if b.tur in ("gun", "zorgun") and len(self.meslek_bolum.get(b.varlik, ())) == 1:
                b.sahip = next(iter(self.meslek_bolum[b.varlik]))
        # Takma adlar → bölüm(ler): veriden türetilenler + onaylı gündelik eş anlamlılar (esanlam)
        self.takma: dict[str, set[str]] = defaultdict(set)
        for v in self.bolumler:
            kel = v.split()
            if len(kel) == 1:
                for ek in ("ligi", "ligi", "lik", "luk", "lugu", "ligi"):
                    if v.endswith(ek) and len(v) - len(ek) >= 3:
                        self.takma[v[: -len(ek)]].add(v)                 # eczacilik → eczaci, mimarlik → mimar
            if "ve" in kel:
                self.takma[" ".join(k for k in kel if k != "ve")].add(v)   # elektrik elektronik muhendisligi
                bas = " ".join(kel[: kel.index("ve")])
                if len(bas) >= 6:
                    self.takma[bas].add(v)                                  # "gastronomi" → Gastronomi ve Mutfak Sanatları
            if kel[-1] == "muhendisligi":
                self.takma[" ".join(kel[:-1] + ["muhendisi"])].add(v)      # bilgisayar muhendisi
                kok = " ".join(k for k in kel[:-1] if k != "ve")
                if len(kok) >= 5:
                    self.takma[kok].add(v)                                  # "makine" → Makine Mühendisliği (bölüm adı değilse belirsiz kalır)
                self.takma["muhendis"].add(v)
                self.takma["muhendislik"].add(v)
            if kel[-1] == "ogretmenligi":
                self.takma[" ".join(kel[:-1] + ["ogretmeni"])].add(v)      # biyoloji ogretmeni
                self.takma["ogretmen"].add(v)
                self.takma["ogretmenlik"].add(v)
        for meslek, bolumler in self.meslek_bolum.items():
            self.takma[meslek] |= bolumler
        _capa_sifirla()
        capa_ekle(list(self.bolumler) + list(self.varliklar) + [a for b in belgeler if b.tur == "sozluk" for a in b.adlar])
        for k, hedefler in (esanlam or {}).items():
            for h in hedefler:
                if sade(h).strip() in self.bolumler:
                    k2 = sade(k).strip()
                    self.takma[k2].add(sade(h).strip())
                    if k2.endswith(" ogretmeni"):
                        self.takma[k2.removesuffix("ogretmeni") + "ogretmenligi"].add(sade(h).strip())   # ingilizce ogretmenligi
        capa_ekle(list(self.takma))
        # Aday dizini: ilk iki harfe göre (hız)
        self._aday: dict[str, list[tuple[str, tuple[str, ...]]]] = defaultdict(list)
        for anahtar in set(self.varliklar) | set(self.takma):
            tok = tuple(anahtar.split())
            if tok and len(anahtar) >= 3:
                self._aday[tok[0][:2]].append((anahtar, tok))

    def _idf(self, k: str) -> float:
        n = len(self.ters.get(k, ()))
        return math.log(1 + (len(self.belgeler) - n + 0.5) / (n + 0.5)) if n else 0.0

    def varliksiz_metin(self, soru: str) -> str:
        """Düzeltilmiş soru, tanınan bölüm/meslek adları çıkarılmış hâliyle ("İnsan Kaynakları Yönetimi" içindeki
        "kaynak" ders bağlamı, "Dil ve Konuşma Terapisi" içindeki "konu" sanılmasın)."""
        q = duzelt(soru).split()
        silinecek: set[int] = set()
        self.varliklari_coz(soru, _konum=silinecek)
        return " ".join(w for i, w in enumerate(q) if i not in silinecek)

    def _birlesikleri_ayir(self, q: list[str]) -> list[str]:
        """[2026-11-02 simülasyon] Boşluksuz yazılan çok sözcüklü ad ("turizmrehberligi", "bilgisayarmuhendisligi") ayrılır.
        Yalnızca sözcük hiçbir ada uymuyorsa ve birleşik biçim en az 10 harfse denenir."""
        if not hasattr(self, "_birlesik"):
            b: dict[str, dict[str, tuple]] = {}
            for liste in self._aday.values():
                for _anahtar, tok in liste:
                    if len(tok) >= 2 and len("".join(tok)) >= 10:
                        b.setdefault("".join(tok)[:5], {})["".join(tok)] = tok
            self._birlesik = b
        out = []
        for w in q:
            ad = None
            if len(w) >= 10:
                for birlesik, tok in self._birlesik.get(w[:5], {}).items():
                    if w == birlesik or (w.startswith(birlesik) and w[len(birlesik):] in _KISA_EKLER) \
                            or _ek_toleransli(w, birlesik):
                        ad = tok
                        break
            out.extend(ad if ad else [w])
        return out

    def varliklari_coz(self, soru: str, _konum: set[int] | None = None) -> list[tuple[str, set[str]]]:
        """Soruda geçen bölüm / meslek / takma adlar: [(sorudaki anahtar, hedef varlıklar)]. Ekli ve hafif hatalı yazım tanınır.
        Uzun eşleşme öncelikli; aynı sözcük iki kez kullanılmaz. Hedef birden çoksa ad belirsizdir (ör. "ogretmen")."""
        q = self._birlesikleri_ayir(duzelt(soru).split())
        adaylar = []
        for i, w in enumerate(q):
            for anahtar, tok in self._aday.get(w[:2], ()):
                n = len(tok)
                if i + n > len(q):
                    continue
                if len(tok) == 1 and len(anahtar) < 4 and not (q[i] == anahtar or (
                        q[i].startswith(anahtar) and q[i][len(anahtar):] in _KISA_EKLER)):
                    continue                                              # "tip", "ebe": tam yazım ya da yaygın ek ("tipta")
                if all(_ek_toleransli(q[i + j], tok[j]) for j in range(n)):
                    tam = sum(q[i + j] == tok[j] for j in range(n))
                    fark = sum(abs(len(q[i + j]) - len(tok[j])) for j in range(n))
                    adaylar.append((n, tam, fark, len(anahtar), i, anahtar))
        # çok sözcüklü > tam yazım > yazılana en yakın ("grafik tasarim" = Grafik Tasarımı, "grafik tasarımcı" değil) > uzun ad
        adaylar.sort(key=lambda a: (-a[0], -a[1], a[2], -a[3]))
        kullanilan: set[int] = set()
        sonuc = []
        for n, _, _, _, i, anahtar in adaylar:
            yer = set(range(i, i + n))
            if yer & kullanilan:
                continue
            kullanilan |= yer
            if _konum is not None:
                _konum |= yer
            hedef = set()
            if anahtar in self.bolumler:
                hedef = {anahtar}                                         # tam bölüm adı: türetilmiş takma adlar devreye girmez
            else:
                if anahtar in self.varliklar:
                    hedef.add(anahtar)
                hedef |= self.takma.get(anahtar, set())
            if hedef:
                sonuc.append((anahtar, hedef, i, n))
        bulunma = [x for x in sonuc if any(h in self.bolumler for h in x[1])]
        if len(bulunma) >= 2:
            ekli = [x for x in bulunma if q[x[2] + x[3] - 1] != x[0].split()[-1]
                    and q[x[2] + x[3] - 1][len(x[0].split()[-1]):] in _BULUNMA_EKI]
            if ekli:
                sonuc = [x for x in sonuc if not (x[0] in _DERS_ADI and x not in ekli)]
        return [(a, h) for a, h, _, _ in sonuc]

    def soru_varliklari(self, soru: str) -> list[str]:
        """Belirsiz olmayan varlıklar (puanlamada öne alınır). Bir takma ad tek bölüme çıkıyorsa o bölüm de eklenir."""
        out: list[str] = []
        for anahtar, hedef in self.varliklari_coz(soru):
            bolum_hedef = {h for h in hedef if h in self.bolumler}
            if anahtar in self.varliklar:
                out.append(anahtar)
            if len(bolum_hedef) == 1:
                out.extend(bolum_hedef)
        return list(dict.fromkeys(out))

    def ara(self, soru: str, moduller: set[str] | None = None, adet: int = 3) -> list[Sonuc]:
        sorgu = sorgu_kokleri(soru)
        if not sorgu:
            return []
        varliklar = set(self.soru_varliklari(soru))
        # Takma adla sorulan bölümün kendi adı da aranır ("iktisat" → Ekonomi, "pdr" → Rehberlik ve Psikolojik Danışmanlık)
        sorgu = sorgu + [w[:5] for v in varliklar if v in self.bolumler for w in v.split() if len(w) > 1 and w not in _DURAK]
        t_soru = f" {duzelt(soru)} "
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
            if b.adlar and not any(f" {a} " in t_soru and _sozluk_kapsar(a, t_soru) for a in b.adlar):
                continue          # sözlük: terim soruda aynen geçmiyorsa ("taban puan" ≠ "taban suyu") ya da sorulanı kapsamıyorsa
            if varliklar:
                if b.varlik in varliklar:
                    p *= VARLIK_KATSAYI      # adı soruda geçen bölüm/meslek
                elif b.tur in ("meslek", "gun", "zorgun") and getattr(b, "sahip", "") in varliklar:
                    p *= VARLIK_KATSAYI * 0.6   # bölümün diğer meslekleri: o bölüme ait ama sorulan meslekten geride
                elif b.varlik:
                    p *= 0.3      # başka bir bölüm/meslekten gelen belge geri plana
            p *= _niyet_katsayisi(soru, b.tur)
            sonuc.append(Sonuc(b, p))
        sonuc.sort(key=lambda s: -s.puan)
        return sonuc[:adet]


# ---------------------------------------------------------------------------------------------------------- niyet
_NIYET = [
    (("ders", "okut", "ogren", "mufredat", "egitim", "matematik var", "fizik var", "kimya var", "biyoloji var", "matematik agir",
      "matematik cok", "kodlama var", "cizim var"), {"bolum_ders": 1.8}),
    (("ne is yapar", "is yapar", "ne is yapiyor", "ne isi yapar", "ne yapiyor", "okuyan ne", "bitiren ne", "mezunu ne"),
     {"meslek": 1.8, "bolum_is": 1.8}),
    (("gunu", "gunum", "gunun", "bir gun", "ne yapar", "is gunu", "gunluk", "ne is yapar", "is yapar", "ne yapiyor",
      "ne is yapiyor", "ne isi yapar", "gorevi ne", "isi ne"), {"gun": 1.8, "meslek": 1.8}),
    (("yetenek sinav", "ozel yetenek", "giris sinav", "nasil girilir", "kimler girebilir", "erkek", "kiz ogrenci", "alim sart",
      "sarti", "sartlari", "boy kilo", "saglik raporu"), {"bolum_bilmen": 2.2}),
    (("nasil olun", "nasil giri", "nasil bas", "girmek ici", "olmak ici", "yolu", "giden yol", "adim"), {"meslek": 1.4, "yol": 2.2}),
    (("calis", "nerede", "is bul", "is imkan", "kariyer", "mezun"), {"bolum_is": 1.6, "meslek": 1.3}),
    (("kimler", "uygun", "kime uyar", "ozellik"), {"bolum": 1.4}),
    (("hakkinda", "bilgi", "anlat", "nedir", "nasil bir", "tanit", "puan"), {"bolum": 1.6}),
    (("kac yil", "suresi", "kac yilda", "kac donem", "kac yillik"), {"bolum": 2.5}),
    (("zor", "stres", "kotu yan", "zorluk"), {"zorgun": 1.8, "bolum_bilmen": 1.5}),
    (("mulakat", "gorusme sor", "is gorusmesi"), {"mulakat": 2.0, "mulakat_pratik": 1.6}),
    (("cv", "ozgecmis"), {"cv": 2.0}),
    (("ne demek", "anlami", "nedir", "tanim"), {"sozluk": 1.6}),
    (("brut", "net maas", "bordro", "sgk", "kidem", "ihbar", "izin", "mesai", "sozlesme", "staj", "para yonet", "sigorta"), {"ders": 2.0}),
    (("kok neden", "korelasyon", "algoritma", "ikiye bol", "ogrenmeyi ogren", "veriyi oku"), {"dusunme": 2.0}),
]


def _niyet_katsayisi(soru: str, tur: str) -> float:
    t = duzelt(soru)
    k = 1.0
    for anahtarlar, turler in _NIYET:
        if tur in turler and any(anahtar_var(a, t) for a in anahtarlar):
            k = max(k, turler[tur])
    if k == 1.0 and tur in _YALNIZ_NIYETLE:
        k = _YALNIZ_NIYETLE[tur]     # mülakat / zor gün sayfaları yalnızca o sorulunca öne çıkar ("ebe ne iş yapar" ≠ mülakat)
    return k


_YALNIZ_NIYETLE = {"mulakat": 0.3, "zorgun": 0.7, "mulakat_pratik": 0.4}


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
                                     (f"Puan türü: {d.get('puan_turu')}." if not str(d.get("puan_turu")).lower().startswith("değişken")
                                      else "Puan türü: üniversiteye göre değişir.") if d.get("puan_turu") else "",
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


def _meslek_goster(anahtar: str) -> str:
    """[2026-11-02] Veri dosyalarındaki meslek anahtarları küçük harfli ve "İ" harfi Python'un lower() çıktısıyla
    ("i̇", birleşik nokta) yazılı: ekranda "Ağaç işleri endüstri mühendisi" biçiminde gösterilir."""
    a = (anahtar or "").replace("i̇", "i").strip()
    return (a[:1].replace("i", "İ").upper() + a[1:]) if a else a


def _dosya_belgeleri() -> list[Belge]:
    out: list[Belge] = []
    sen = _oku("meslek_senaryolari.json") or {}
    for meslek, liste in sen.items():
        if not isinstance(liste, list):
            continue
        anlar = [f"{s.get('saat', '')} {s.get('baslik', '')}: {s.get('durum', '')}" for s in liste if isinstance(s, dict)]
        if anlar:
            out.append(Belge("gun", f"Bir gününü yaşa: {_meslek_goster(meslek)}", " ".join(anlar),
                             "Bölüm sayfası › Meslekler › 🎬 Bir gününü yaşa", None, sade(meslek).strip()))
    # Ana sözlük: Sözlük sayfasındaki sistem terimleri (frontend/src/yardimci/sozluk.js → scripts/sozluk_temel_kopyala.mjs).
    # Sayfadaki gibi önceliklidir: aynı adlı genişletilmiş terim eklenmez.
    ana: set[str] = set()
    for t in (_oku("sozluk_temel.json") or {}).get("terimler") or []:
        if isinstance(t, dict) and t.get("ad") and t.get("t"):
            ham = [str(t["ad"]), str(t["ad"]).split("(")[0], *(t.get("es") or [])]
            adlar = tuple(a for a in {" ".join(sade(x).split()) for x in ham} if len(a) >= 2)
            ana |= set(adlar)
            ornek = f" Örnek: {t['o']}" if t.get("o") else ""
            b = Belge("sozluk", str(t["ad"]), f"{t['t']}{ornek}", "Sözlük", None, "", adlar)
            b.sahip = "ana"
            out.append(b)
    soz = _oku("sozluk_genis.json") or {}
    for t in soz.get("terimler") or []:
        if isinstance(t, list) and len(t) >= 3 and t[0] and t[2] and " ".join(sade(str(t[0])).split()) not in ana:
            ornek = f" Örnek: {t[3]}" if len(t) > 3 and t[3] else ""
            ham = [str(t[0]), str(t[0]).split("(")[0], *(t[4] if len(t) > 4 and isinstance(t[4], list) else [])]
            adlar = tuple(a for a in {" ".join(sade(x).split()) for x in ham} if len(a) >= 2)
            out.append(Belge("sozluk", str(t[0]), f"{t[2]}{ornek}", "Sözlük", None, "", adlar))
    # [2026-11-02 simülasyon] Meslek dili (bölüm penceresindeki "Meslek dili" sekmesi: meslekte kullanılan terimler) Filiz'in
    # dizininde yoktu. Sözlükte aynı adlı terim yoksa sözlük maddesi gibi eklenir ("triyaj ne demek").
    var_olan = {a for b in out if b.tur == "sozluk" for a in b.adlar}
    try:
        jargon = json.loads((Path(__file__).resolve().parent / "meslek_jargonu.json").read_text(encoding="utf-8"))
    except Exception:
        jargon = {}
    for bolum, liste in (jargon or {}).items():
        for t in liste or []:
            if not isinstance(t, dict) or not t.get("terim") or not t.get("anlam"):
                continue
            ad = " ".join(sade(str(t["terim"]).split("(")[0]).split())
            if len(ad) < 3 or ad in var_olan:
                continue
            var_olan.add(ad)
            ornek = f" Örnek: {t['ornek']}" if t.get("ornek") else ""
            out.append(Belge("sozluk", str(t["terim"]), f"{t['anlam']}{ornek}", f"Bölümler › {_ad(bolum)} › Meslek dili", None, "", (ad,)))
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
            out.append(Belge("zorgun", f"{_meslek_goster(meslek)}: zor günler", " ".join(sen_), "İş Hayatı › Zor Günler", "is_hayati",
                             sade(meslek).strip()))
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
    # [2026-11-02 simülasyon] Mülakat Pratiği (genel mülakat soruları, ipuçları, STAR) Filiz'in dizininde yoktu:
    # "mülakatta kendimden nasıl bahsederim" gibi sorular cevapsız kalıyordu.
    mp = _oku("is_hayati_mulakat.json") or {}
    st = mp.get("star") or {}
    if st.get("baslik"):
        oge = " ".join(f"{o.get('ad', '')}: {o.get('aciklama', '')}" for o in st.get("ogeler") or [] if isinstance(o, dict))
        out.append(Belge("mulakat_pratik", f"Mülakatta {st['baslik']}", f"{st.get('aciklama', '')} {oge}".strip(),
                         "İş Hayatı › Mülakat Pratiği", "is_hayati", ""))
    if mp.get("ipuclari_genel"):
        out.append(Belge("mulakat_pratik", "Mülakata hazırlanma ipuçları", _liste(mp["ipuclari_genel"]), "İş Hayatı › Mülakat Pratiği",
                         "is_hayati", ""))
    for kat in mp.get("kategoriler") or []:
        for q in kat.get("sorular") or [] if isinstance(kat, dict) else []:
            if isinstance(q, dict) and q.get("soru"):
                out.append(Belge("mulakat_pratik", f"Mülakat sorusu: {q['soru']}",
                                 f"Neden sorulur: {q.get('neden', '')} Nasıl cevaplarsın: {_liste(q.get('ipuclari'))}".strip(),
                                 f"İş Hayatı › Mülakat Pratiği › {kat.get('ad', '')}", "is_hayati", ""))
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
    """Önbellekli dizin. Süresi dolunca yalnızca bir istek yeniden kurar; o sırada gelen diğer istekler eski dizinle
    cevaplanır (yenileme anında tüm Filiz isteklerinin ~0,7 sn beklemesi önlenir)."""
    global _DIZIN, _DIZIN_ZAMANI
    if _DIZIN is not None and time.time() - _DIZIN_ZAMANI > DIZIN_OMRU_SN:
        if not _KILIT.acquire(blocking=False):
            return _DIZIN
        _KILIT.release()
    with _KILIT:
        if _DIZIN is None or time.time() - _DIZIN_ZAMANI > DIZIN_OMRU_SN:
            try:
                bolum = _bolum_belgeleri(db)
            except Exception:
                db.rollback()
                bolum = []
            _DIZIN = Dizin(bolum + _dosya_belgeleri(), (_oku("filiz_esanlamlar.json") or {}).get("esanlam") or {})
            # Bölümler okunamadıysa (geçici veritabanı hatası) dizin 1 dakika sonra yeniden kurulur, 30 dakika beklenmez
            _DIZIN_ZAMANI = time.time() if bolum else time.time() - DIZIN_OMRU_SN + 60
        return _DIZIN


def dizini_sifirla() -> None:
    global _DIZIN
    with _KILIT:
        _DIZIN = None


# ---------------------------------------------------------------------------------------------------------- cevap
_KISISEL = ("bana", "benim", "benim icin", "hedefim", "hedefime", "sonucum", "sonuclarim", "puanim", "guclu yon",
            "uygun mu", "uyar mi", "secmeli miyim", "yapmaliyim", "ne yapayim", "gorevim", "yol haritam", "profilim",
            "hedef bolum", "bolumum", "bolumumu", "bolumume", "netlerim", "netim")


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


_TANIM = ("ne demek", "nedir", "anlami", "ne anlama", "ne demektir", "nedemek")


_KISALTMA_SORU = {"nasil", "hesaplanir", "hesaplaniyor", "hesaplanir mi", "ise", "yarar", "onemli", "neye", "gore", "acilimi"}


def _sozluk_kapsar(a: str, t: str) -> bool:
    """Tanım sorusunda sorulan şeyin tamamı terim olmalı: "ek yerleştirme nedir" ≠ "Yerleştirme (enstalasyon)",
    "brüt ve net maaş farkı nedir" ≠ "Net maaş"."""
    anahtar = next((k for k in _TANIM if k in t), None)
    if not anahtar:
        return True
    konu = [w for w in t.split(anahtar)[0].split() if w not in _DURAK]
    return not [w for w in konu if w not in a.split()]


def sozluk_bul(db: Session, soru: str) -> Belge | None:
    """Tanım sorusunda ("X ne demek / nedir") sözlükte X aynen geçen en uzun terim."""
    t = f" {duzelt(soru)} "
    tanim = any(k in t for k in _TANIM)
    soru_mu = tanim or "?" in (soru or "") or any(k in t for k in (" mi ", " mu ", " mi", " mu", " nasil ", " ne ", " neden "))
    if not soru_mu:
        return None
    en, uz = None, 0
    for b in dizin(db).belgeler:
        if b.tur == "sozluk":
            for a in b.adlar:
                # Tanım kalıbı yoksa yalnızca çok sözcüklü terim ("hazirlik sinifi", "taban puan") ya da ana sözlükteki
                # kısaltma ("OBP", "KKTC"): sıradan tek sözcük her soruda geçebilir
                kisaltma = (b.sahip == "ana" and str(b.baslik).split()[0].isupper() and len(a) >= 3
                            and not [w for w in t.split() if w not in _DURAK and w not in a.split() and w not in _KISALTMA_SORU])
                if not (len(a) > uz and f" {a} " in f"{t} " and (tanim or " " in a or kisaltma)) or not _sozluk_kapsar(a, t):
                    continue
                en, uz = b, len(a)
    return en


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
_DERS_BAGLAMI = ("netim", "netler", "net artir", "kac net", "calisay", "calismali", "nasil calis", "ders calis", "deneme", "konu", "tyt", "ayt", "yks", "kaynak",
                 "kitap", "soru coz", "test coz", "sinav", "odev", "not ort", "karne", "ogretmen bana")


def ders_baglami_mi(soru: str, db: Session | None = None) -> bool:
    try:
        t = f" {dizin(db).varliksiz_metin(soru)} "
    except Exception:
        t = f" {duzelt(soru)} "
    # Bölüme giriş / meslek sınavları ders çalışma bağlamı değildir ("grafik tasarım için yetenek sınavı var mı")
    t = re.sub(r"\b(?:ozel yetenek|yetenek|giris|alan|yeterlilik|yeterlik|kpss|ales|yds|uzmanlik) sinav\w*", " ", t)
    return any(f" {k}" in t for k in _DERS_BAGLAMI)


def bilgi_sorusu_mu(db: Session, soru: str) -> bool:
    """Soruda bir bölüm / meslek adı geçiyor, bilgi niyeti var, soru öğrencinin kendisine ya da ders çalışmaya dair değil:
    önce içerikten cevaplanır."""
    if kisisel_mi(soru) or ders_baglami_mi(soru, db):
        return False
    t = f" {duzelt(soru)} "
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


# ------------------------------------------------------------------------- [2026-10-31] "anlaşılamayan" listesi için
# Serbest öğrenci metninde sistemde kaydı olmayan adlar (öğretmen, arkadaş), okul/semt adları ve özel nitelikli kişisel veri
# (sağlık, din vb.) olabilir. Liste, yalnızca sistemin kendi içeriğinde geçen sözcükleri ve soru kalıplarını açık bırakır;
# geri kalan her sözcük "▢" olur. Özel nitelikli veri sözcükleri sistem içeriğinde geçse bile maskelenir.
_OZEL_NITELIK = tuple("""depres ilac hastal tedavi psikiyat terapi kanser epilep dehb adhd otizm otist intihar taciz istismar
hamile gebe kurtaj din mezhep alevi sunni hristiyan yahudi ateist etnik kurt cingene engell sakat bipolar sizofren anksiyete
panik atak yeme bozuk anoreks bulim bagimli alkol sigara uyusturucu esrar hapis sabika cinsel""".split())


def sistem_disi_maskele(metin: str | None) -> str:
    out = []
    for parca in (metin or "").split():
        if parca.startswith("[") and parca.endswith("]"):
            out.append(parca)
            continue
        for w in sade(parca).split():
            if any(c.isdigit() for c in w) or (len(w) == 1 and out and out[-1] == "▢"):
                out.append("▢")                    # sınıf / şube / numara ("11-B")
            elif any(w.startswith(o) for o in _OZEL_NITELIK):
                out.append("▢")
            elif (len(w) <= 2 or w in _DURAK or w in _BILINEN or w in _KELIME or w in _IKILI or w in _MUH
                  or all(x in _BILINEN or x in _DURAK for x in duzelt(w).split())
                  or any(len(w) - k >= 4 and w[: len(w) - k] in _BILINEN for k in range(1, 7))):
                out.append(w)
            else:
                out.append("▢")
    return " ".join(out)
