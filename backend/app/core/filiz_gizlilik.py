# -*- coding: utf-8 -*-
"""
[2026-10-11] Filiz — hiyerarşi ve kişisel veri koruması (öğrenci Filiz'i + yönetim Filiz'i ortak).

İlke: "birbirlerinin bilgisi olmasın". Bir öğrenci başka bir öğrencinin bilgisini soramaz; okul yetkilisi yalnızca kendi
okulundaki öğrencileri görür (başka okulda böyle bir kişinin olup olmadığı ASLA belli edilmez); süper admin tüm sistemi görür.
Yapay zekâ hizmet sağlayıcısına (OpenAI) giden HİÇBİR metinde öğrenci adı, e-posta, telefon, TC kimlik no, öğrenci no olmaz.

Parçalar:
  temel_maskele(metin)          — e-posta → [e-posta], telefon → [telefon], 11 haneli sayı (TC) → [numara],
                                  "no 1234" / "numarası 1234" → "no [öğrenci no]", 5+ haneli sayı → [numara]
  AdDizini                      — bir kapsamdaki (okul ya da tüm sistem) öğrenci ad-soyadları: Türkçe büyük/küçük harf ve
                                  aksan duyarsız eşleşme; tam ad ve "ad + soyad" çiftleri (ör. "Ayşe Nur Kaya" → "Ayşe Kaya",
                                  "Nur Kaya"); ekli yazım ("Yılmaz'ın", "Yılmazın") da yakalanır. maskele() → "[öğrenci]".
  ad_benzeri_ciftler(metin)     — veritabanından BAĞIMSIZ: büyük harfle başlayan, panel sözlüğünde olmayan iki ardışık
                                  kelime (ör. "Mehmet Demir"). Kapsam dışındaki bir kişinin adı da dış servise gitmesin ve
                                  cevap, kişinin başka bir okulda olup olmamasına göre DEĞİŞMESİN diye.
  ogrenci_hiyerarsi_yaniti(...) — öğrenci başka bir öğrenciyi hedefleyen bir soru sorduysa sabit ret cevabı (AI'ya gitmez).
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.filiz_rehber import _sade

OGRENCI_ETIKETI = "[öğrenci]"

# ============================================================================= temel maskeleme
_MASKELER = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[e-posta]"),
    (re.compile(r"(?<!\d)(?:\+?90[\s-]?)?0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"), "[telefon]"),
    (re.compile(r"(?<!\d)\d{11}(?!\d)"), "[numara]"),
    (re.compile(r"(?i)\b(no|numara(?:sı|si|lı|li)?|numaram|nolu|numaralı)\s*[:#.]?\s*\d{1,10}\b"), r"\1 [öğrenci no]"),
    (re.compile(r"(?<!\d)\d{5,}(?!\d)"), "[numara]"),
]
_EPOSTA = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_OGR_NO = re.compile(r"(?i)\b(?:no|numara(?:sı|si|lı|li)?|numaram|nolu|numaralı)\s*[:#.]?\s*(\d{1,10})\b")


def temel_maskele(metin: str | None) -> str:
    m = metin or ""
    for desen, yerine in _MASKELER:
        m = desen.sub(yerine, m)
    return m


def eposta_bul(metin: str | None) -> list[str]:
    return [e.lower().rstrip(".") for e in _EPOSTA.findall(metin or "")]


def ogrenci_no_bul(metin: str | None) -> list[str]:
    return _OGR_NO.findall(metin or "")


# ============================================================================= Türkçe kelime bölme
_KELIME = re.compile(r"\w+", re.U)


def _n(kelime: str) -> str:
    return re.sub(r"[^0-9a-z]", "", _sade(kelime))


def _parcala(metin: str) -> list[tuple[str, int, int, str]]:
    """[(normalize_kelime, başlangıç, bitiş, özgün)] — kesme işareti ayırır ("Yılmaz'ın" → yilmaz, in)."""
    return [(_n(t.group()), t.start(), t.end(), t.group()) for t in _KELIME.finditer(metin or "") if _n(t.group())]


def ad_normalize(ad: str | None) -> tuple[str, ...]:
    return tuple(x for x in (_n(t) for t in _KELIME.findall(ad or "")) if x)


def _ek_uyar(kelime: str, ad: str, son: bool) -> bool:
    """Ad parçası: tam eşit; son parçada (kesmesiz yazılmış) en çok 4 harflik ek kabul edilir (Yılmazın, Kayanın)."""
    if kelime == ad:
        return True
    return son and len(ad) >= 4 and kelime.startswith(ad) and len(kelime) - len(ad) <= 4


# ============================================================================= ad dizini
@dataclass
class OgrenciKaydi:
    id: str
    ad_soyad: str
    email: str = ""
    ogrenci_no: str | None = None
    okul_id: int | None = None
    okul_ad: str | None = None
    sinif: str | None = None
    sube: str | None = None
    ad_parcalari: tuple[str, ...] = field(default=())


class AdDizini:
    def __init__(self, kayitlar: list[OgrenciKaydi]):
        self.kayitlar = kayitlar
        self._varyant: dict[str, list[tuple[tuple[str, ...], OgrenciKaydi]]] = {}   # ilk kelime → [(varyant, kayıt)]
        self.ilk_adlar: set[str] = set()
        for k in kayitlar:
            p = k.ad_parcalari = ad_normalize(k.ad_soyad)
            if len(p) < 2:   # tek kelimelik ad: yanlış eşleşme riski yüksek (ör. "Deniz"), tek başına aranmaz
                continue
            varyantlar = {p} | {(p[i], p[-1]) for i in range(len(p) - 1)}
            for v in varyantlar:
                self._varyant.setdefault(v[0], []).append((v, k))
            self.ilk_adlar.add(p[0])
        for v in self._varyant.values():
            v.sort(key=lambda x: -len(x[0]))   # uzun varyant önce ("ayse nur kaya" > "ayse kaya")

    def eslesmeler(self, metin: str) -> list[tuple[int, int, OgrenciKaydi, tuple[str, ...]]]:
        """[(başlangıç_karakteri, bitiş_karakteri, kayıt, varyant)] — örtüşmeyen, soldan sağa."""
        par = _parcala(metin)
        sonuc, i = [], 0
        while i < len(par):
            bulundu = None
            for v, k in self._varyant.get(par[i][0], []):
                n = len(v)
                if i + n <= len(par) and all(_ek_uyar(par[i + j][0], v[j], j == n - 1) for j in range(n)):
                    bulundu = (n, v)
                    break
            if bulundu:
                n, v = bulundu
                for v2, k in self._varyant.get(par[i][0], []):   # aynı ada sahip tüm öğrenciler
                    if v2 == v:
                        sonuc.append((par[i][1], par[i + n - 1][2], k, v))
                i += n
            else:
                i += 1
        return sonuc

    def bul(self, metin: str) -> list[OgrenciKaydi]:
        gorulen, l = set(), []
        for _, _, k, _ in self.eslesmeler(metin):
            if k.id not in gorulen:
                gorulen.add(k.id)
                l.append(k)
        return l

    def maskele(self, metin: str | None, haric: tuple[str, ...] | None = None) -> str:
        """Dizindeki öğrenci adlarını "[öğrenci]" yapar. haric: kendi adı (normalize parçalar) — o varyant maskelenmez."""
        m = metin or ""
        araliklar = sorted({(b, s) for b, s, _, v in self.eslesmeler(m) if not (haric and _kendi_adi_mi(v, haric))}, reverse=True)
        for b, s in araliklar:
            m = m[:b] + OGRENCI_ETIKETI + m[s:]
        return m


def _kendi_adi_mi(varyant: tuple[str, ...], kendi: tuple[str, ...]) -> bool:
    if not kendi:
        return False
    if varyant == kendi:
        return True
    return len(varyant) == 2 and varyant[-1] == kendi[-1] and varyant[0] in kendi[:-1]


def dizin_yukle(db: Session, okul_id: int | None = None, tum_sistem: bool = False, haric_id=None) -> AdDizini:
    """okul_id verilirse yalnızca o okulun öğrencileri; tum_sistem=True ise tüm öğrenciler (süper admin)."""
    if not tum_sistem and not okul_id:
        return AdDizini([])
    kosul, p = ("TRUE", {}) if tum_sistem else ("o.okul_id = :ok", {"ok": okul_id})
    if haric_id is not None:
        kosul += " AND o.id <> :h"
        p["h"] = haric_id
    try:
        with db.begin_nested():
            satirlar = db.execute(text(f"""
                SELECT o.id, o.ad_soyad, o.email, o.ogrenci_no, o.okul_id, k.ad AS okul_ad, o.sinif, o.sube
                  FROM ogrenciler o LEFT JOIN okullar k ON k.id = o.okul_id
                 WHERE {kosul}"""), p).all()
    except Exception:
        satirlar = []
    return AdDizini([OgrenciKaydi(id=str(r.id), ad_soyad=r.ad_soyad or "", email=(r.email or "").lower(), ogrenci_no=r.ogrenci_no,
                                  okul_id=r.okul_id, okul_ad=r.okul_ad, sinif=r.sinif, sube=r.sube) for r in satirlar])


# ============================================================================= ad benzeri çiftler (veritabanından bağımsız)
# Büyük harfle başlayan ve aşağıdaki sözlükte olmayan iki ardışık kelime bir kişi adı olabilir. Panel/ürün adları, kurum
# türleri ve sık kelimeler sözlükte — "Rapor Merkezi", "Tek Bakışta", "Hacettepe Üniversitesi" ad sayılmaz.
_AD_OLMAYAN_KOKLER = tuple("""
rapor merke bakis okul panel sinif sube ogren ogret yetki rehbe istat anket takvi kulup tercih mezun paket kayit
gorun filiz siste kayna denem atlas hata audit tuik pipel param soru bolum mesle univ fakul lise kolej anado sosya
muhen hukuk egiti psiko danis veli toplu excel kontr super admin yonet genel konu sayfa liste giris sifre hesap
yeni ekle duzen test aday akran gelis kurum turki ankar istan izmi bursa antal konya adana mudur yardi hanim hoca
merkez veri bilgi ozet tablo grafik karsi hepsi bugun yarin lutfen merhaba selam tesek
""".split())
# kısa ya da ad olarak da kullanılan kelimeler: yalnızca TAM eşleşme (ör. "bu" Burak'ı, "sali" Salih'i dışlamasın)
_AD_OLMAYAN_KELIMELER = set("""
ve ile ama nasil neden nerede nedir hangi kim ben siz biz bu su tek net tyt ayt yks lgs osym meb yok sss log tip fen
koc is bey tum sil pdf pazartesi sali carsamba persembe cuma cumartesi pazar ocak subat mart nisan mayis haziran
temmuz agustos eylul ekim kasim aralik
""".split())


def _ad_olabilir(kelime: str, ozgun: str) -> bool:
    if len(ozgun) < 2 or not ozgun[0].isupper() or ozgun.isupper() or not ozgun.isalpha():
        return False
    return kelime not in _AD_OLMAYAN_KELIMELER and not kelime.startswith(_AD_OLMAYAN_KOKLER)


def ad_benzeri_ciftler(metin: str | None) -> list[tuple[int, int]]:
    """[(başlangıç, bitiş)] — "Mehmet Demir", "Ayşe Nur Kaya". Cümle başındaki ilk kelime de aday olabilir; ikinci kelime de
    büyük harfle başlamalı."""
    par = _parcala(metin or "")
    sonuc, i = [], 0
    while i < len(par) - 1:
        if _ad_olabilir(par[i][0], par[i][3]) and _ad_olabilir(par[i + 1][0], par[i + 1][3]) and \
                (metin or "")[par[i][2]:par[i + 1][1]].strip() == "":
            j = i + 1
            while j + 1 < len(par) and _ad_olabilir(par[j + 1][0], par[j + 1][3]) and (metin or "")[par[j][2]:par[j + 1][1]].strip() == "":
                j += 1
            sonuc.append((par[i][1], par[j][2]))
            i = j + 1
        else:
            i += 1
    return sonuc


def ad_benzerlerini_maskele(metin: str | None, etiket: str = "[kişi]") -> str:
    m = metin or ""
    for b, s in reversed(ad_benzeri_ciftler(m)):
        m = m[:b] + etiket + m[s:]
    return m


# ============================================================================= öğrenci tarafı: hiyerarşi koruması
HIYERARSI_YANITI = ("Başka öğrencilerin bilgilerini paylaşamam; her öğrencinin sonuçları yalnızca kendisine ve okulunun "
                    "yetkililerine açıktır. İstersen kendi sonuçların hakkında konuşalım. 🌱")
TOPLU_YANITI = ("Okulunun yüklediği bir denemeye en az 5 öğrenci katıldıysa o denemenin okul ortalaması Net Takibi sayfasında, "
                "senin netlerinin yanında gösterilir. Bunun dışında sınıf ya da okul ortalaması, okul içi sıralama gibi başka "
                "öğrencilerin sonuçlarına dayanan bilgileri paylaşamam. İstersen kendi netlerin ve hedefin hakkında konuşalım. 🌱")

_AKRAN = ("arkadas", "sinifimdak", "sinifimizdak", "sinifdak", "sinifta kim", "subemdek", "subemizdek", "okulumdak", "okulumuzdak",
          "diger ogrenci", "baska ogrenci", "digerlerin", "herkesin", "sinifin", "subenin", "kanka", "sevgilim",
          "ogrencilerin", "baskasinin", "baskalarinin")
_VERI = ("sonuc", "puan", "hedef", "net", "not", "skor", "uyum", "profil", "sirala", "derece", "test", "bolum", "tercih",
         "guclu", "zayif", "rapor", "basari", "cikti", "yapti", "aldi", "kac", "ne kadar", "secti", "istedi", "deneme")
_EN_KIM = re.compile(r"\ben (yuksek|dusuk|basarili|basarisiz|iyi|kotu|cok|az|fazla)\b.*\b(kim|kimin|kimde|kimler|hangi ogrenci)\b")
_TOPLU = re.compile(r"\b(okul|sinif|sube|okulun|sinifin|subenin|okulumuzun|sinifimizin|subemizin)\w* ortalama|"
                    r"ortalama\w* (okul|sinif|sube)|\bkacinci\w*\b.*\b(okul|sinif|sube)|\b(okul|sinif|sube)\w*\b.*\bkacinci|"
                    r"\b(okul|sinif|sube)\w* (ici )?siralama")


def _icerir(n: str, kokler) -> bool:
    return any(re.search(r"(?:^|\s)" + re.escape(k), n) for k in kokler)


def ogrenci_hiyerarsi_yaniti(metin: str, dizin: AdDizini, kendi_ad: str | None) -> str | None:
    """Öğrencinin sorusu başka bir öğrenciyi hedefliyorsa sabit cevap; değilse None.
    dizin: öğrencinin okulundaki DİĞER öğrenciler (kendisi hariç)."""
    n = " ".join(_n(t) for t in _KELIME.findall(metin or "") if _n(t))
    kendi = ad_normalize(kendi_ad)
    # 1) okuldaki başka bir öğrencinin adı (kendi adı hariç — aynı adı taşıyan bir okul arkadaşı olsa bile)
    if any(not _kendi_adi_mi(v, kendi) for _, _, _, v in dizin.eslesmeler(metin or "")):
        return HIYERARSI_YANITI
    # 2) "en yüksek net kimde", "en başarılı öğrenci kim"
    if _EN_KIM.search(n):
        return HIYERARSI_YANITI
    # 3) toplu sorular: yalnızca sistemin zaten gösterdiği okul ortalaması (Net Takibi, 5+ kuralı)
    if _TOPLU.search(n):
        return TOPLU_YANITI
    # 4) "arkadaşımın / sınıfımdakilerin / diğer öğrencilerin ... sonucu, puanı, hedefi, neti"
    if _icerir(n, _AKRAN) and _icerir(n, _VERI):
        return HIYERARSI_YANITI
    # 5) "Ayşe'nin puanı" — okuldaki bir öğrencinin ilk adı + kesme işaretli ek + veri kelimesi (kendi ilk adı hariç)
    for r in re.finditer(r"(\w+)\s*['’`]\s*\w{1,5}", metin or ""):
        ad = _n(r.group(1))
        if ad in dizin.ilk_adlar and (not kendi or ad != kendi[0]) and _icerir(n, _VERI):
            return HIYERARSI_YANITI
    return None


def ogrenci_dizini(db: Session, ogrenci) -> AdDizini:
    """Öğrencinin okulundaki diğer öğrenciler (okulsuz öğrencide boş)."""
    return dizin_yukle(db, okul_id=getattr(ogrenci, "okul_id", None), haric_id=getattr(ogrenci, "id", None))


KENDI_AD_ETIKETI = "[ad]"


def kendi_adini_maskele(metin: str | None, kendi_ad: str | None) -> str:
    """[2026-10-14] Öğrencinin kendi adı yapay zekâya gitmez — ama adı sıradan bir kelime olan öğrencinin ("Doğa", "Deniz",
    "Barış") cümlesi de bozulmamalı. Kural:
      * ad ve soyad birlikte geçerse (sırayla, aradaki ikinci ad atlanabilir; ekli hâli dahil) → "[ad]";
      * soyad tek başına yalnızca BÜYÜK harfle ve cümle başında değilken → "[ad]" ("Kaya ailesi" evet, "kaya tırmanışı" hayır);
      * ad tek başına maskelenmez: tek başına kimliği belirlemez ve çoğu zaman sıradan bir kelimedir."""
    m = metin or ""
    parcalar = ad_normalize(kendi_ad)
    if len(parcalar) < 2 or not m:
        return m
    tok = _parcala(m)
    soyad = parcalar[-1]
    araliklar: list[tuple[int, int]] = []
    i = 0
    while i < len(tok):
        # ad (+ isteğe bağlı ikinci ad) + soyad dizisi
        bulundu = None
        if tok[i][0] == parcalar[0]:
            for n in range(len(parcalar), 1, -1):
                hedef = (parcalar[0],) + parcalar[len(parcalar) - n + 1:]   # tam ad ya da ilk ad + soyad
                if i + len(hedef) <= len(tok) and all(_ek_uyar(tok[i + k][0], hedef[k], k == len(hedef) - 1)
                                                         for k in range(len(hedef))):
                    bulundu = len(hedef)
                    break
        if bulundu:
            araliklar.append((tok[i][1], tok[i + bulundu - 1][2]))
            i += bulundu
            continue
        n, b, e, oz = tok[i]
        if len(soyad) >= 3 and _ek_uyar(n, soyad, True) and oz[:1].isupper():
            onceki = m[:b].rstrip()
            if onceki and onceki[-1] not in ".!?:\n\"“'(":
                araliklar.append((b, e))
        i += 1
    for b, e in sorted(araliklar, reverse=True):
        m = m[:b] + KENDI_AD_ETIKETI + m[e:]
    return m


def ogrenci_metni_maskele(dizin: AdDizini, metin: str | None, kendi_ad: str | None) -> str:
    """Yapay zekâya giden öğrenci metni: temel maskeleme + okul arkadaşlarının adları + öğrencinin kendi adı."""
    return kendi_adini_maskele(dizin.maskele(temel_maskele(metin), haric=ad_normalize(kendi_ad)), kendi_ad)


def kimlik_uuid(deger) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(deger))
    except (TypeError, ValueError):
        return None
