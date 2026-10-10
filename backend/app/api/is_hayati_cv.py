# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı → CV Atölyesi (sekme 'cv'). Göç: 0057 (tablo is_hayati_cv).

Öğrenci (/ogrenci/is-hayati/..., modül kapısı is_hayati otomatik — bkz. is_hayati.py):
  GET    /cv              — kayıtlı CV (yoksa null) + portfolyodan üretilmiş taslak + kontrol listesi + beceri önerileri
  PUT    /cv              — {icerik, paylas} kaydet → kontrol listesiyle döner
  DELETE /cv              — CV'yi sil (baştan başla)
  GET    /cv/pdf          — tek sayfa, ATS dostu PDF (tablo / görsel yok)
  GET    /cv/ilanlar?bolum_id= — "İlan okuma" egzersizi: kurgusal örnek ilanlar (seçili bölümle ilgili olanlar önce)
Okul (yalnızca öğrenci paylaşırsa; modül kapısı okul_modulu("is_hayati")):
  GET    /yonetim/ogrenci/{ogrenci_id}/is-hayati-cv       — paylaşılan CV (ön yazı hariç)
  GET    /yonetim/ogrenci/{ogrenci_id}/is-hayati-cv/pdf   — denetim kaydı yazılır

Kişisel bilgi: yalnızca ad, e-posta, şehir saklanır. TC kimlik no, doğum tarihi, fotoğraf, medeni durum, din vb. alan yoktur;
metinde geçerse kontrol listesi uyarır. "OKUL ONAYLI" işareti istemciden alınmaz: her yanıtta portfolyo kaydının okul
doğrulamasından (başlık + kurum değişmediyse) yeniden hesaplanır.
"""
import io
import json
import re
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz, olay_yaz
from app.core.paketler import okul_modulu
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter()
yonetim_router = APIRouter(prefix="/yonetim", tags=["İş Hayatı · CV"])
_YONETIM_KAPI = [Depends(okul_modulu("is_hayati"))]

_ILANLAR = Path(__file__).resolve().parents[1] / "data" / "ornek_ilanlar.json"

# kod → (varsayılan başlık, tip)   tip: liste | etiket | dil
BOLUMLER = {
    "egitim": ("Eğitim", "liste"),
    "deneyim": ("Deneyim ve görevler", "liste"),
    "projeler": ("Projeler", "liste"),
    "gonulluluk": ("Gönüllülük", "liste"),
    "oduller": ("Ödüller ve yarışmalar", "liste"),
    "sertifikalar": ("Sertifikalar ve kurslar", "liste"),
    "beceriler": ("Beceriler", "etiket"),
    "diller": ("Diller", "dil"),
    "ilgi": ("İlgi alanları", "etiket"),
}
TUR_BOLUM = {"proje": "projeler", "gonullu": "gonulluluk", "yarisma": "oduller", "sertifika": "sertifikalar",
             "staj": "deneyim", "gorev": "deneyim", "spor_sanat": "deneyim", "diger": "deneyim"}
DIL_SEVIYE = ["A1", "A2", "B1", "B2", "C1", "C2", "Ana dil"]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
EN_BUYUK_JSON = 60_000


# ============================================================================= yardımcılar
def _s(v, n: int) -> str:
    return re.sub(r"[ \t]+\n", "\n", str(v or "")).strip()[:n]


def _tr_buyuk(v: str) -> str:
    return str(v or "").replace("i", "İ").replace("ı", "I").upper()


def _norm(v) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip().casefold()


def _uid() -> str:
    return uuid.uuid4().hex[:10]


def _temizle(icerik: dict) -> dict:
    """İstemciden gelen CV içeriğini şemaya indirger (bilinmeyen alanlar, istemcinin 'onayli' bayrağı atılır)."""
    if not isinstance(icerik, dict):
        raise HTTPException(400, "Geçersiz CV içeriği.")
    k = icerik.get("kisisel") if isinstance(icerik.get("kisisel"), dict) else {}
    sonuc = {"surum": 1,
             "kisisel": {"ad": _s(k.get("ad"), 80), "eposta": _s(k.get("eposta"), 120), "sehir": _s(k.get("sehir"), 60)},
             "profil": _s(icerik.get("profil"), 700), "bolumler": []}
    gorulen = set()
    for b in icerik.get("bolumler") or []:
        if not isinstance(b, dict) or b.get("kod") not in BOLUMLER or b["kod"] in gorulen:
            continue
        kod = b["kod"]
        gorulen.add(kod)
        tip = BOLUMLER[kod][1]
        ogeler = []
        for o in (b.get("ogeler") or [])[:25]:
            if tip == "liste" and isinstance(o, dict):
                pid = o.get("portfolyo_id")
                ogeler.append({"id": _s(o.get("id"), 20) or _uid(), "baslik": _s(o.get("baslik"), 140), "kurum": _s(o.get("kurum"), 120),
                               "donem": _s(o.get("donem"), 60), "aciklama": _s(o.get("aciklama"), 900), "gizli": bool(o.get("gizli")),
                               "portfolyo_id": pid if isinstance(pid, int) else None,
                               "kulup": bool(o.get("kulup"))})
            elif tip == "etiket" and isinstance(o, str) and o.strip():
                ogeler.append(_s(o, 40))
            elif tip == "dil" and isinstance(o, dict) and _s(o.get("dil"), 30):
                ogeler.append({"dil": _s(o.get("dil"), 30), "seviye": o.get("seviye") if o.get("seviye") in DIL_SEVIYE else "B1"})
        sonuc["bolumler"].append({"kod": kod, "baslik": _s(b.get("baslik"), 50) or BOLUMLER[kod][0], "gizli": bool(b.get("gizli")),
                                  "ogeler": ogeler})
    for kod, (ad, _t) in BOLUMLER.items():   # eksik bölüm varsa sona (gizli değil, boş) eklenir
        if kod not in gorulen:
            sonuc["bolumler"].append({"kod": kod, "baslik": ad, "gizli": False, "ogeler": []})
    oy = icerik.get("on_yazi")
    if isinstance(oy, dict):
        sonuc["on_yazi"] = {"tur": _s(oy.get("tur"), 20),
                            "alanlar": {_s(a, 30): _s(v, 1500) for a, v in list((oy.get("alanlar") or {}).items())[:12] if isinstance(v, str)}}
    if len(json.dumps(sonuc, ensure_ascii=False)) > EN_BUYUK_JSON:
        raise HTTPException(400, "CV çok uzun. Bir sayfalık CV için açıklamaları kısalt.")
    return sonuc


def _ay_yil(d) -> str:
    if not d:
        return ""
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return f"{AYLAR[d.month - 1]} {d.year}"


def _donem(bas, bit, devam: bool) -> str:
    a, b = _ay_yil(bas), _ay_yil(bit)
    if a and b:
        return a if a == b else f"{a} – {b}"
    if a:
        return f"{a} – devam ediyor" if devam else a
    return b


def _egitim_donemi(o: Ogrenci) -> str:
    m = re.match(r"(\d+)", o.sinif or "")
    if not m:
        return ""
    bugun = date.today()
    ogretim_yili = bugun.year if bugun.month >= 9 else bugun.year - 1
    return f"Eylül {ogretim_yili - (int(m.group(1)) - 9)} – devam ediyor"


def _okul_adi(db: Session, o: Ogrenci) -> str:
    if not o.okul_id:
        return o.okul or ""
    return db.execute(text("SELECT ad FROM okullar WHERE id = :i"), {"i": o.okul_id}).scalar() or ""


# Güçlü yön (değerlendirme özelliği) → CV'de yazılabilecek beceri ifadesi. K1 (değerler) beceri olmadığı için önerilmez.
BECERI_IFADESI = {
    "Belirsizlik ve risk toleransı": "Belirsizlikle başa çıkma", "Dinamik ortam tercihi": "Hızlı tempoya uyum", "Duygusal hassasiyet": "Empati",
    "Liderlik isteği": "Liderlik", "Sorumluluk ve disiplin": "Planlı ve disiplinli çalışma", "Uyum ve işbirliği": "Ekip çalışması",
    "Yeniliğe açıklık": "Yeni şeyler öğrenme", "İnsanlarla çalışma (dışadönüklük)": "İnsanlarla iletişim",
    "Baskı altında karar verme": "Baskı altında karar verme", "Ekip ve çatışma yönetimi": "Çatışma çözme",
    "Eleştiriye açıklık": "Geri bildirime açıklık", "Strateji ve iş dünyası yetkinliği": "Stratejik düşünme",
    "Zaman yönetimi ve önceliklendirme": "Zaman yönetimi", "İnisiyatif alma": "İnisiyatif alma",
    "Büyük resmi görme (sezgisel stil)": "Bütünü görme", "Doğa ve laboratuvar eğilimi": "Deney ve gözlem",
    "Fiziksel ve hareket eğilimi": "El becerisi", "Girişimcilik ve ikna eğilimi": "İkna ve sunum", "Sayısal ve veri eğilimi": "Sayısal analiz",
    "Sözel ve dil eğilimi": "Yazılı ve sözlü anlatım", "Tasarım ve uzamsal eğilim": "Görsel tasarım",
    "Yapılandırılmış çalışma stili": "Düzenli ve sistemli çalışma", "İnsan odaklı eğilim": "İnsanlara yardım etme",
}


def _guclu_yonler(db: Session, o: Ogrenci) -> list[dict]:
    """Profilim / Koçluk ekranlarındaki "Güçlü yönlerin" ile aynı kaynak (rapor verisi); değerler katmanı (K1) hariç."""
    try:
        from app.core.rapor.veri import ogrenci_raporu_verisi
        v = ogrenci_raporu_verisi(db, o)
    except Exception:
        db.rollback()
        return []
    k1 = {x["ad"] for k in v.get("katmanlar", []) if k.get("kod") == "K1" for x in k.get("ozellikler", [])}
    gucluler = [x for x in v.get("gucluler", []) if x["ad"] not in k1]
    if len(gucluler) < 3:
        tum = sorted((x for k in v.get("katmanlar", []) if k.get("kod") != "K1" for x in k.get("ozellikler", [])), key=lambda x: -x["puan"])
        gucluler += [x for x in tum if x not in gucluler][:3 - len(gucluler)]
    return [{"ad": BECERI_IFADESI.get(x["ad"], x["ad"]), "kaynak": x["ad"]} for x in gucluler[:6]]


def _taslak(db: Session, o: Ogrenci, pv: dict) -> dict:
    """Portfolyodan otomatik doldurulmuş CV taslağı."""
    okul = _okul_adi(db, o)
    bol = {k: [] for k in BOLUMLER}
    if okul:
        sinif = re.match(r"(\d+)", o.sinif or "")
        bol["egitim"].append({"id": _uid(), "baslik": okul, "kurum": f"Lise, {sinif.group(1)}. sınıf" if sinif else ("Lise mezunu" if (o.sinif or "") == "Mezun" else "Lise"),
                              "donem": _egitim_donemi(o), "aciklama": "", "gizli": False, "portfolyo_id": None, "kulup": False})
    for k in sorted(pv["kayitlar"], key=lambda x: x.get("baslangic") or "", reverse=True):
        aciklama = k.get("aciklama") or ""
        if k["tur"] == "yarisma" and k.get("derece"):
            aciklama = f"{k['derece']}. {aciklama}".strip()
        if k["tur"] == "gonullu" and k.get("saat"):
            aciklama = (aciklama + f" Toplam {k['saat']} saat gönüllü çalıştım.").strip()
        bol[TUR_BOLUM.get(k["tur"], "deneyim")].append({
            "id": _uid(), "baslik": k["baslik"], "kurum": k.get("kurum") or "",
            "donem": _donem(k.get("baslangic"), k.get("bitis"), k["tur"] in ("gonullu", "staj", "gorev", "proje", "spor_sanat")),
            "aciklama": aciklama, "gizli": False, "portfolyo_id": k["id"], "kulup": False})
    for kl in pv["kulupler"]:
        bol["deneyim"].append({"id": _uid(), "baslik": f"{kl['ad']} üyesi", "kurum": okul, "donem": _donem(kl.get("baslangic"), None, True),
                               "aciklama": "", "gizli": False, "portfolyo_id": None, "kulup": True})
    p = pv["profil"]
    bol["beceriler"] = list(p.get("yetenekler") or [])[:10]
    bol["diller"] = [{"dil": d["dil"], "seviye": d["seviye"]} for d in p.get("diller") or []]
    bol["ilgi"] = [x.strip()[:40] for x in re.split(r"[,;\n]", o.ilgi_alanlari or "") if x.strip()][:8]
    return {"surum": 1, "kisisel": {"ad": o.ad_soyad, "eposta": o.email, "sehir": ""},
            "profil": (p.get("hakkimda") or "")[:450],
            "bolumler": [{"kod": kod, "baslik": ad, "gizli": False, "ogeler": bol[kod]} for kod, (ad, _t) in BOLUMLER.items()]}


def _portfolyo(db: Session, o: Ogrenci) -> dict:
    try:
        from app.api.portfolyo import portfolyo_verisi
        return portfolyo_verisi(db, o)
    except Exception:
        db.rollback()
        return {"kayitlar": [], "kulupler": [], "profil": {"hakkimda": "", "yetenekler": [], "diller": []}}


def _onaylari_isle(icerik: dict, pv: dict) -> dict:
    """Her liste öğesine 'onayli' ve 'onaylayan' ekler — yalnızca okul doğrulamasından, başlık + kurum değişmediyse."""
    kayit = {k["id"]: k for k in pv["kayitlar"]}
    kulup = {_norm(f"{k['ad']} üyesi") for k in pv["kulupler"]}
    for b in icerik["bolumler"]:
        if BOLUMLER[b["kod"]][1] != "liste":
            continue
        for o in b["ogeler"]:
            o["onayli"], o["onaylayan"] = False, None
            k = kayit.get(o.get("portfolyo_id"))
            if k and k.get("dogrulandi") and _norm(k["baslik"]) == _norm(o["baslik"]) and _norm(k.get("kurum")) == _norm(o["kurum"]):
                o["onayli"], o["onaylayan"] = True, k.get("dogrulayan")
            elif o.get("kulup") and _norm(o["baslik"]) in kulup:
                o["onayli"], o["onaylayan"] = True, "okul kulüp kaydı"
    return icerik


def _gorunen(icerik: dict, kod: str) -> list:
    b = next((x for x in icerik["bolumler"] if x["kod"] == kod), None)
    if b is None or b["gizli"]:
        return []
    return [o for o in b["ogeler"] if not (isinstance(o, dict) and o.get("gizli"))]


# ============================================================================= PDF (tek sayfa, ATS dostu)
def cv_pdf(icerik: dict, renk: str | None = None) -> tuple[bytes, int]:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

    from app.core.rapor.pdf import _e, _fontlar, _renk
    _fontlar()
    vurgu = _renk(renk)
    koyu = colors.HexColor("#22201C")
    gri = colors.HexColor("#5E574F")
    ad_st = ParagraphStyle("ad", fontName="Filiz-B", fontSize=18, leading=22, textColor=koyu)
    ilt_st = ParagraphStyle("il", fontName="Filiz", fontSize=9.2, leading=12, textColor=gri, spaceAfter=4)
    h_st = ParagraphStyle("h", fontName="Filiz-B", fontSize=10.5, leading=13, textColor=vurgu, spaceBefore=7, spaceAfter=1, keepWithNext=1)
    g_st = ParagraphStyle("g", fontName="Filiz", fontSize=9.2, leading=12, textColor=koyu)
    o_st = ParagraphStyle("o", parent=g_st, spaceBefore=3)
    m_st = ParagraphStyle("m", parent=g_st, leftIndent=9, bulletIndent=1, textColor=colors.HexColor("#3A342D"))
    k_st = ParagraphStyle("k", fontName="Filiz", fontSize=7.4, leading=9.5, textColor=gri)
    ONAY = ' <font color="#4E8A4F"><b>OKUL ONAYLI</b></font>'

    k = icerik["kisisel"]
    h = [Paragraph(_e(k.get("ad") or ""), ad_st),
         Paragraph(" | ".join(_e(x) for x in (k.get("eposta"), k.get("sehir")) if x), ilt_st)]

    def baslik(metin):
        h.append(Paragraph(_e(_tr_buyuk(metin)), h_st))
        h.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D9D2C7"), spaceBefore=1, spaceAfter=3))

    if icerik.get("profil"):
        baslik("Profil")
        h.append(Paragraph(_e(icerik["profil"]).replace("\n", " "), g_st))
    onay_var = False
    for b in icerik["bolumler"]:
        ogeler = _gorunen(icerik, b["kod"])
        if not ogeler:
            continue
        tip = BOLUMLER[b["kod"]][1]
        if tip == "liste":
            baslik(b["baslik"])
            for o in ogeler:
                if not o.get("baslik"):
                    continue
                ust = f"<b>{_e(o['baslik'])}</b>" + (f", {_e(o['kurum'])}" if o.get("kurum") else "")
                if o.get("donem"):
                    ust += f" | {_e(o['donem'])}"
                if o.get("onayli"):
                    ust += ONAY
                    onay_var = True
                parca = [Paragraph(ust, o_st)]
                for satir in [x.strip(" -•\t") for x in (o.get("aciklama") or "").split("\n") if x.strip(" -•\t")]:
                    parca.append(Paragraph(_e(satir), m_st, bulletText="•"))
                h.append(KeepTogether(parca))
        elif tip == "etiket":
            baslik(b["baslik"])
            h.append(Paragraph(", ".join(_e(x) for x in ogeler), g_st))
        else:
            baslik(b["baslik"])
            h.append(Paragraph(", ".join(f"{_e(d['dil'])} ({_e(d['seviye'])})" for d in ogeler), g_st))
    if onay_var:
        h += [Spacer(1, 8), Paragraph("OKUL ONAYLI: kayıt, öğrencinin okulu tarafından belgesiyle doğrulanmıştır (Filizyol e-Portfolyo). "
                                      "Diğer bilgiler öğrencinin kendi beyanıdır.", k_st)]
    tampon = io.BytesIO()
    doc = SimpleDocTemplate(tampon, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=15 * mm, bottomMargin=14 * mm,
                            title=f"Özgeçmiş - {k.get('ad') or ''}", author=k.get("ad") or "", subject="Özgeçmiş", creator="Filizyol")
    doc.build(h)
    return tampon.getvalue(), doc.page


# ============================================================================= kontrol listesi
_FIIL = re.compile(r"(?:[dt][ıiuü](?:m|k|n|nız|niz|nuz|nüz)?|yor(?:um|uz|lar)?|m[ıiuü]ş(?:ım|im|um|üm|ız|iz|uz|üz)?|[ae]c[ae]ğ[ıi]m|(?:ır|ir|ur|ür|ar|er)(?:ım|im|um|üm|ız|iz|uz|üz))$")
_KISISEL = [
    (re.compile(r"(?<!\d)\d{11}(?!\d)"), "11 haneli numara (TC kimlik no olabilir)"),
    (re.compile(r"\bt\.?\s?c\.?\s*(?:kimlik|no)|\bkimlik\s*(?:no|numara)", re.I), "kimlik numarası"),
    (re.compile(r"doğum\s*(?:tarihi|yeri)|\bd\.\s?t\.", re.I), "doğum tarihi / yeri"),
    (re.compile(r"medeni\s*hal|medeni\s*durum|\bbekâ?r\b|\bevli\b", re.I), "medeni durum"),
    (re.compile(r"\bdin(?:i)?\s*[:：]|\bmezhep", re.I), "din / inanç"),
    (re.compile(r"kan\s*grubu|\bboy\s*[:：]|\bkilo\s*[:：]", re.I), "sağlık / fiziksel bilgi"),
    (re.compile(r"\bcinsiyet|\buyruk|\bnüfus", re.I), "cinsiyet / uyruk / nüfus bilgisi"),
    (re.compile(r"anne\s*ad|baba\s*ad", re.I), "anne / baba adı"),
]
_KLISE = ["çalışkan", "dürüst", "sorumluluk sahibi", "takım çalışmasına", "iletişimi güçlü", "azimli", "disiplinli", "hırslı",
          "pozitif", "yeniliklere açık", "öğrenmeye açık", "problem çözme yeteneği", "liderlik özelliği", "detaycı", "titiz"]
_KISALTMA = {"TÜBİTAK", "UNICEF", "UNESCO", "GITHUB", "ERASMUS", "TEKNOFEST", "MEB", "YÖK", "ÖSYM", "TOEFL", "IELTS", "OSTİM", "SEFERBERLİK"}
_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
_AY_ADI = "(?:" + "|".join(AYLAR) + "|Oca|Şub|Mar|Nis|May|Haz|Tem|Ağu|Eyl|Eki|Kas|Ara)"
_TARIH_BICIM = [("ay_yil", re.compile(rf"^{_AY_ADI}\.? \d{{4}}$", re.I)), ("sayisal", re.compile(r"^\d{1,2}[./]\d{4}$")),
                ("yil", re.compile(r"^\d{4}$")), ("tam", re.compile(r"^\d{1,2}[./]\d{1,2}[./]\d{4}$"))]
_EPOSTA = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
DENEYIM = ("deneyim", "projeler", "gonulluluk")


def _cumleler(metin: str) -> list[str]:
    parcalar = []
    for satir in (metin or "").split("\n"):
        satir = satir.strip(" -•\t")
        parcalar += [c.strip() for c in re.split(r"(?<=\D[.!?])\s+", satir) if c.strip()]
    return parcalar


def _son_kelime(c: str) -> str:
    kel = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşüâîû]+", c)
    return kel[-1].lower().replace("i̇", "i") if kel else ""


def _tarih_bicimi(donem: str) -> set:
    bicim = set()
    for parca in re.split(r"\s*[–—-]\s*", donem):
        parca = parca.strip()
        if not parca or parca.lower().startswith("devam") or parca.lower() in ("halen", "günümüz"):
            continue
        b = next((ad for ad, r in _TARIH_BICIM if r.match(parca)), "diger")
        bicim.add(b)
    return bicim


def kontrol(icerik: dict, sayfa: int | None) -> dict:
    M = []

    def madde(kod, ad, agirlik, durum, aciklama, oneri, ayrinti=None):
        M.append({"kod": kod, "ad": ad, "agirlik": agirlik, "durum": durum, "aciklama": aciklama, "oneri": oneri,
                  "ayrinti": ayrinti or [], "puan": agirlik if durum == "tamam" else (agirlik / 2 if durum == "kismen" else 0)})

    k = icerik["kisisel"]
    var = [bool(len(k.get("ad") or "") >= 3), bool(_EPOSTA.match(k.get("eposta") or "")), bool(k.get("sehir"))]
    madde("iletisim", "İletişim bilgisi tam", 8, "tamam" if all(var) else ("kismen" if sum(var) >= 2 else "eksik"),
          "İşveren sana ulaşabilmeli: ad soyad, çalışan bir e-posta ve yaşadığın şehir yeter.",
          "Eksik olanı ekle: " + ", ".join(a for a, v in zip(["ad soyad", "geçerli e-posta", "şehir"], var) if not v) if not all(var)
          else "E-postan ad.soyad gibi sade bir adres olsun; takma ad içeren adresler ciddiyetsiz görünür.")

    tum_metin = [icerik.get("profil") or ""] + [k.get(x) or "" for x in ("ad", "eposta", "sehir")]
    for b in icerik["bolumler"]:
        for o in b["ogeler"]:
            tum_metin += [o] if isinstance(o, str) else [str(v) for a, v in o.items() if a in ("baslik", "kurum", "aciklama", "dil")]
    birlesik = "\n".join(tum_metin)
    bulunan = sorted({ad for r, ad in _KISISEL if r.search(birlesik)})
    madde("kisisel", "Gereksiz kişisel bilgi yok", 8, "eksik" if bulunan else "tamam",
          "TC kimlik no, doğum tarihi, fotoğraf, medeni durum, din, sağlık bilgisi CV'de gerekmez; ayrımcılığa ve kimlik hırsızlığına açık kapı bırakır.",
          "Şunları çıkar: " + ", ".join(bulunan) if bulunan else "Böyle kalsın. Gerekirse işveren işe alım sürecinde ayrıca ister.", bulunan)

    pr = (icerik.get("profil") or "").strip()
    madde("profil", "Kısa profil cümlesi", 8, "tamam" if 80 <= len(pr) <= 450 else ("kismen" if pr else "eksik"),
          "CV'nin en üstündeki 2–3 cümle seni özetler: kimsin, neye ilgi duyuyorsun, ne arıyorsun.",
          "Bir profil yaz: \"11. sınıf öğrencisiyim; okul robotik takımında 2 yıldır yazılım sorumlusuyum. Yaz döneminde yazılım ekibinde gözlem stajı arıyorum.\""
          if not pr else ("Biraz daha aç: en az 80 karakter, 2–3 cümle." if len(pr) < 80 else "Kısalt: en fazla 3 cümle; ayrıntılar aşağıdaki bölümlerde zaten var.")
          if not 80 <= len(pr) <= 450 else "İyi. İlana göre son cümleyi (ne aradığını) her başvuruda güncelle.")

    klise = [w for w in _KLISE if w in pr.casefold()]
    madde("klise", "Sıfat yerine kanıt", 5, "eksik" if not pr or len(klise) >= 3 else ("kismen" if len(klise) == 2 else "tamam"),
          "\"Çalışkan, dürüst, sorumluluk sahibi\" her CV'de yazar ve hiçbir şey kanıtlamaz. Yaptığın bir şey bu özelliği kendiliğinden gösterir.",
          ("Şu sıfatları bir örnekle değiştir: " + ", ".join(klise)) if len(klise) >= 2 else ("Önce profil cümleni yaz." if not pr else "İyi: profilin somut."),
          klise)

    egitim = [o for o in _gorunen(icerik, "egitim") if o.get("baslik")]
    madde("egitim", "Eğitim bilgisi", 6, "tamam" if egitim else "eksik",
          "Lisede eğitim bölümü kısadır: okulun, sınıfın ve (varsa) öne çıkan dersler ya da başarılar.",
          "Eğitim bölümüne okulunu ekle." if not egitim else "İstersen öne çıkan bir ders ya da proje ödevini tek satırla ekle.")

    deneyimler = [(kod, o) for kod in (*DENEYIM, "oduller", "sertifikalar") for o in _gorunen(icerik, kod) if o.get("baslik")]
    n = len(deneyimler)
    madde("deneyim_sayisi", "Deneyim, proje ya da etkinlik", 8, "tamam" if n >= 3 else ("kismen" if n else "eksik"),
          "Lisede iş deneyimi beklenmez; kulüp görevi, okul projesi, gönüllülük, yarışma ve kurslar da deneyimdir.",
          "Portfolyona kayıt ekle ya da buraya elle yaz; en az 3 öğe hedefle." if n < 3 else "İyi. İlana en uygun olanları üste taşı.")

    aciklamali = [(kod, o) for kod, o in deneyimler if kod in DENEYIM]
    eksik_ac = [o["baslik"] for _k, o in aciklamali if len((o.get("aciklama") or "").strip()) < 30]
    madde("aciklama", "Her deneyimde ne yaptığın yazıyor", 7,
          "eksik" if not aciklamali else ("tamam" if not eksik_ac else ("kismen" if len(eksik_ac) < len(aciklamali) else "eksik")),
          "Başlık tek başına yetmez: o deneyimde senin ne yaptığını 1–3 maddeyle anlat.",
          ("Açıklama ekle: " + ", ".join(eksik_ac[:4])) if eksik_ac else ("Deneyim, proje ya da gönüllülük ekle." if not aciklamali else "İyi."), eksik_ac)

    fiilsiz, toplam_c = [], 0
    for _k, o in aciklamali:
        cumle = _cumleler(o.get("aciklama") or "")
        toplam_c += len(cumle)
        if cumle and not all(_FIIL.search(_son_kelime(c)) for c in cumle):
            fiilsiz.append(o["baslik"])
    madde("eylem", "Eylem fiili: \"yaptım, hazırladım, yönettim\"", 9,
          "eksik" if not toplam_c else ("tamam" if not fiilsiz else ("kismen" if len(fiilsiz) <= len(aciklamali) / 2 else "eksik")),
          "Her maddeyi senin yaptığın bir eylemle bitir: \"Okul gazetesinin 4 sayısını hazırladım.\" Eylem fiili seni pasif bir katılımcıdan sorumluluk alan biri hâline getirir.",
          ("Şu öğelerde maddeyi bir fiille bitir (\"…katıldım\" yerine \"…tasarladım / düzenledim / öğrettim\"): " + ", ".join(fiilsiz[:4])) if fiilsiz
          else ("Önce deneyimlerine açıklama yaz." if not toplam_c else "İyi. \"Katıldım\" yerine mümkünse daha güçlü fiiller seç: düzenledim, tasarladım, yönettim."),
          fiilsiz)

    olculebilir = [o for kod, o in deneyimler if kod in (*DENEYIM, "oduller")]
    sayili = [o for o in olculebilir if re.search(r"\d", o.get("aciklama") or "")]
    oran = len(sayili) / len(olculebilir) if olculebilir else 0
    madde("sayi", "Somut sonuç ve sayı", 9, "tamam" if olculebilir and oran >= 0.5 else ("kismen" if sayili else "eksik"),
          "Sayı inandırır: kaç kişi, kaç saat, kaç sayı, yüzde kaç artış? \"Kermes düzenledim\" yerine \"Kermesle 40 öğrenciyle 6.500 TL bağış topladık.\"",
          "En az yarısına bir sayı ekle: " + ", ".join(o["baslik"] for o in olculebilir if o not in sayili)[:220] if olculebilir and oran < 0.5
          else ("Önce deneyim ekle." if not olculebilir else "İyi."))

    donemler = [o.get("donem") or "" for _k, o in deneyimler] + [o.get("donem") or "" for o in egitim]
    bicimler = set().union(*[_tarih_bicimi(d) for d in donemler if d]) if any(donemler) else set()
    bos = sum(1 for d in donemler if not d)
    madde("tarih", "Tarih biçimi tutarlı", 6,
          "eksik" if len(bicimler) > 1 or "diger" in bicimler or (donemler and bos == len(donemler)) else ("kismen" if bos else "tamam"),
          "Bütün tarihler aynı biçimde olmalı: hep \"Eylül 2024 – Haziran 2025\" ya da hep \"09/2024 – 06/2025\". Karışık biçim dikkatsizlik izlenimi verir.",
          "Biçimleri tek tipe çevir (önerilen: \"Ay Yıl – Ay Yıl\", devam edenlerde \"– devam ediyor\")." if len(bicimler) > 1 or "diger" in bicimler
          else (f"{bos} öğede tarih yok; ekle." if bos else "İyi."))

    sorun = []
    metinler = [pr] + [o.get("aciklama") or "" for _k, o in deneyimler] + [o.get("baslik") or "" for _k, o in deneyimler]
    if any("  " in m for m in metinler):
        sorun.append("çift boşluk")
    if any(_EMOJI.search(m) for m in metinler):
        sorun.append("emoji")
    if any(re.search(r"[!?]{2,}|\.{4,}", m) for m in metinler):
        sorun.append("tekrarlanan noktalama (!! / ??)")
    if any(w not in _KISALTMA for m in metinler for w in re.findall(r"\b[A-ZÇĞİÖŞÜ]{6,}\b", m)):
        sorun.append("tamamı büyük harfli sözcük")
    if any(c[:1].islower() for m in metinler[:1 + len(deneyimler)] for c in _cumleler(m)):
        sorun.append("küçük harfle başlayan cümle")
    sonlar = [c[-1] in ".!?" for _k, o in aciklamali for c in _cumleler(o.get("aciklama") or "")]
    if sonlar and 0 < sum(sonlar) < len(sonlar):
        sorun.append("maddelerin bir kısmı noktayla bitiyor, bir kısmı bitmiyor")
    madde("yazim", "Yazım tutarlılığı", 7, "tamam" if not sorun else ("kismen" if len(sorun) <= 2 else "eksik"),
          "Yazım hatası ve tutarsızlık, okuyanın ilk elediği şeydir. Büyük harf, noktalama ve madde sonlarını tek tipe getir.",
          ("Düzelt: " + "; ".join(sorun)) if sorun else "İyi. Son bir kez yüksek sesle oku; bir arkadaşına da okut.", sorun)

    bec = _gorunen(icerik, "beceriler")
    madde("beceri", "Beceriler (4–10 tane)", 6, "tamam" if 4 <= len(bec) <= 10 else ("kismen" if bec else "eksik"),
          "Somut beceriler yaz (\"Excel'de tablo ve grafik\", \"Canva\", \"Python temel\", \"sunum yapma\"). Kişilik özelliklerini ise deneyimlerinle göster.",
          "Beceri ekle; önerilerden seçebilirsin." if len(bec) < 4 else ("Çok fazla: en güçlü 10 tanesini bırak." if len(bec) > 10 else "İyi."))

    dil = _gorunen(icerik, "diller")
    madde("dil", "Dil ve seviyesi", 4, "tamam" if dil else "eksik",
          "Bildiğin dilleri seviyesiyle yaz (A1–C2). \"İyi derecede\" gibi belirsiz ifadeler yerine seviye kullan.",
          "Diller bölümüne en az bir dil ve seviyesini ekle." if not dil else "İyi. Bir sınav ya da sertifikan varsa sertifikalar bölümüne ekle.")

    madde("tek_sayfa", "Tek sayfa", 6, "tamam" if sayfa == 1 else ("eksik" if sayfa else "kismen"),
          "Lise öğrencisinin CV'si tek sayfayı geçmemeli. İşe alım yapanlar bir CV'ye çoğu zaman yalnızca birkaç saniye bakar.",
          f"Şu an {sayfa} sayfa: ilanla ilgisiz öğeleri gizle, açıklamaları kısalt." if sayfa and sayfa > 1 else "İyi.")

    onayli = [o for _k, o in deneyimler if o.get("onayli")]
    madde("onay", "En az bir okul onaylı kayıt", 3, "tamam" if onayli else "eksik",
          "Okulunun belgesiyle doğruladığı kayıtlar CV'de \"OKUL ONAYLI\" olarak görünür ve güven verir.",
          "Portfolyondaki bir kaydına belge ekleyip rehber öğretmeninden onay iste. Başlığı ya da kurumu değiştirirsen onay işareti kalkar."
          if not onayli else "İyi.")

    puan = round(sum(m["puan"] for m in M))
    return {"puan": puan, "tamam": sum(1 for m in M if m["durum"] == "tamam"), "toplam": len(M), "sayfa": sayfa, "maddeler": M}


# ============================================================================= öğrenci uçları
def _okul_rengi(db: Session, okul_id) -> str | None:
    if not okul_id:
        return None
    return db.execute(text("SELECT tema_renk FROM okullar WHERE id = :i"), {"i": okul_id}).scalar()


def _kayitli(db: Session, oid):
    return db.execute(text("SELECT icerik, paylas, paylasim_zamani, guncelleme FROM is_hayati_cv WHERE ogrenci_id = :o"), {"o": oid}).first()


def _cevap(db: Session, o: Ogrenci) -> dict:
    pv = _portfolyo(db, o)
    r = _kayitli(db, o.id)
    taslak = _onaylari_isle(_taslak(db, o, pv), pv)
    cv = None
    if r is not None:
        icerik = r.icerik if isinstance(r.icerik, dict) else json.loads(r.icerik or "{}")
        cv = {"icerik": _onaylari_isle(_temizle(icerik), pv), "paylas": bool(r.paylas),
              "paylasim_zamani": r.paylasim_zamani.isoformat() if r.paylasim_zamani else None,
              "guncelleme": r.guncelleme.isoformat() if r.guncelleme else None}
    etkin = cv["icerik"] if cv else taslak
    try:
        _pdf, sayfa = cv_pdf(etkin, _okul_rengi(db, o.okul_id))
    except Exception:
        sayfa = None
    gucluler = _guclu_yonler(db, o)
    return {
        "cv": cv, "taslak": taslak, "kontrol": kontrol(etkin, sayfa),
        "oneriler": {"gucluler": gucluler, "yetenekler": list(pv["profil"].get("yetenekler") or []),
                     "portfolyo_kayit": len(pv["kayitlar"]), "portfolyo_onayli": sum(1 for k in pv["kayitlar"] if k.get("dogrulandi"))},
        "sabitler": {"bolumler": [{"kod": k, "baslik": a, "tip": t} for k, (a, t) in BOLUMLER.items()], "dil_seviyeleri": DIL_SEVIYE},
    }


@ogrenci_router.get("/cv")
def cv_getir(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return _cevap(db, o)


class CvIstek(BaseModel):
    icerik: dict
    paylas: bool = False


@ogrenci_router.put("/cv")
def cv_kaydet(istek: CvIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    icerik = _temizle(istek.icerik)
    onceki = _kayitli(db, o.id)
    db.execute(text("""
        INSERT INTO is_hayati_cv (ogrenci_id, icerik, paylas, paylasim_zamani, guncelleme)
        VALUES (:o, CAST(:i AS JSONB), :p, CASE WHEN :p THEN now() END, now())
        ON CONFLICT (ogrenci_id) DO UPDATE SET icerik = EXCLUDED.icerik, paylas = EXCLUDED.paylas, guncelleme = now(),
            paylasim_zamani = CASE WHEN EXCLUDED.paylas AND NOT is_hayati_cv.paylas THEN now()
                                   WHEN EXCLUDED.paylas THEN is_hayati_cv.paylasim_zamani END
    """), {"o": o.id, "i": json.dumps(icerik, ensure_ascii=False), "p": istek.paylas})
    if (onceki is None and istek.paylas) or (onceki is not None and bool(onceki.paylas) != istek.paylas):
        olay_yaz(db, o.id, "cv_paylasim", "CV okulla paylaşıldı" if istek.paylas else "CV paylaşımı kapatıldı", yapan="ogrenci")
    db.commit()
    return _cevap(db, o)


@ogrenci_router.delete("/cv")
def cv_sil(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    db.execute(text("DELETE FROM is_hayati_cv WHERE ogrenci_id = :o"), {"o": o.id})
    db.commit()
    return _cevap(db, o)


def _pdf_cevap(icerik_b: bytes, ad: str) -> Response:
    from app.api.raporlar import _dosya_adi
    return Response(icerik_b, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{_dosya_adi("CV", ad)}.pdf"', "Cache-Control": "no-store"})


@ogrenci_router.get("/cv/pdf")
def cv_pdf_indir(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    pv = _portfolyo(db, o)
    r = _kayitli(db, o.id)
    icerik = _temizle(r.icerik if isinstance(r.icerik, dict) else json.loads(r.icerik)) if r else _taslak(db, o, pv)
    pdf, _s_ = cv_pdf(_onaylari_isle(icerik, pv), _okul_rengi(db, o.okul_id))
    olay_yaz(db, o.id, "ozgecmis_indir", "İş Hayatı CV PDF", yapan="ogrenci")
    db.commit()
    return _pdf_cevap(pdf, o.ad_soyad)


def _ilanlar() -> dict:
    try:
        return json.loads(_ILANLAR.read_text(encoding="utf-8"))
    except Exception:
        return {"kategoriler": {}, "ilanlar": []}


@ogrenci_router.get("/cv/ilanlar")
def ilanlar(bolum_id: int | None = Query(None), db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core.is_hayati_servisi import tr_kucuk
    veri = _ilanlar()
    ad = ""
    if bolum_id:
        ad = tr_kucuk(db.execute(text("SELECT ad FROM bolumler WHERE id = :i"), {"i": bolum_id}).scalar() or "")
    liste = []
    for i, ilan in enumerate(veri.get("ilanlar", [])):
        ilgili = bool(ad) and any(a in ad for a in ilan.get("anahtarlar", []))
        liste.append({**ilan, "ilgili": ilgili, "_s": (0 if ilgili else (1 if not ilan.get("anahtarlar") else 2), i)})
    liste.sort(key=lambda x: x.pop("_s"))
    return {"kategoriler": veri.get("kategoriler", {}), "ilanlar": liste,
            "not": "Bu ilanların hepsi eğitim amaçlı ÖRNEK ilandır; gerçek bir şirkete ya da kuruma ait değildir."}


# ============================================================================= okul (yalnızca paylaşılan CV)
def _paylasilan(db: Session, yon: AdminKullanici, ogrenci_id: str):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    r = _kayitli(db, o.id)
    return o, (r if r is not None and r.paylas else None)


@yonetim_router.get("/ogrenci/{ogrenci_id}/is-hayati-cv", dependencies=_YONETIM_KAPI)
def okul_cv(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o, r = _paylasilan(db, yon, ogrenci_id)
    if r is None:
        return {"paylasildi": False}
    icerik = _temizle(r.icerik if isinstance(r.icerik, dict) else json.loads(r.icerik))
    icerik.pop("on_yazi", None)   # ön yazı öğrencide kalır
    return {"paylasildi": True, "icerik": _onaylari_isle(icerik, _portfolyo(db, o)),
            "paylasim_zamani": r.paylasim_zamani.isoformat() if r.paylasim_zamani else None,
            "guncelleme": r.guncelleme.isoformat() if r.guncelleme else None}


@yonetim_router.get("/ogrenci/{ogrenci_id}/is-hayati-cv/pdf", dependencies=_YONETIM_KAPI)
def okul_cv_pdf(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o, r = _paylasilan(db, yon, ogrenci_id)
    if r is None:
        raise HTTPException(404, "Öğrenci CV'sini okulla paylaşmamış.")
    icerik = _onaylari_isle(_temizle(r.icerik if isinstance(r.icerik, dict) else json.loads(r.icerik)), _portfolyo(db, o))
    pdf, _s_ = cv_pdf(icerik, _okul_rengi(db, o.okul_id))
    denetim_yaz(db, yon, "cv_indir", "is_hayati_cv", o.id, o.ad_soyad, o.okul_id)
    db.commit()
    return _pdf_cevap(pdf, o.ad_soyad)

