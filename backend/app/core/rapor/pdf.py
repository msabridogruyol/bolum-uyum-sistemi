# -*- coding: utf-8 -*-
"""
[2026-10-10] PDF raporları (reportlab): öğrenci · veli · yönetici (öğrenci bazlı) ve okul genel raporu.
Türkçe karakterler için Liberation Sans gömülür. Renk vurgusu okulun tema rengidir.
"""
import base64
import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

_FONT = Path(__file__).resolve().parent / "fontlar"
_KAYITLI = False


def _fontlar():
    global _KAYITLI
    if _KAYITLI:
        return
    pdfmetrics.registerFont(TTFont("Filiz", str(_FONT / "LiberationSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Filiz-B", str(_FONT / "LiberationSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Filiz-I", str(_FONT / "LiberationSans-Italic.ttf")))
    pdfmetrics.registerFontFamily("Filiz", normal="Filiz", bold="Filiz-B", italic="Filiz-I", boldItalic="Filiz-B")
    _KAYITLI = True


TR = ZoneInfo("Europe/Istanbul")
GRI = colors.HexColor("#6B6257")
ACIK = colors.HexColor("#F6F1E8")
CIZGI = colors.HexColor("#E6DDCF")
YESIL = colors.HexColor("#4E8A4F")
AMBER = colors.HexColor("#C98A1B")
KIRMIZI = colors.HexColor("#C0473A")


def _renk(hex_: str | None):
    try:
        return colors.HexColor(hex_ or "#E8804A")
    except Exception:
        return colors.HexColor("#E8804A")


def _tarih(z, saat=False) -> str:
    if not z:
        return "—"
    if isinstance(z, datetime):
        z = z.astimezone(TR) if z.tzinfo else z
        return z.strftime("%d.%m.%Y %H:%M" if saat else "%d.%m.%Y")
    if hasattr(z, "strftime"):   # date
        return z.strftime("%d.%m.%Y")
    return str(z)


def _e(metin) -> str:
    """Paragraph içinde güvenli metin."""
    return (str(metin or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class _Stil:
    def __init__(self, vurgu):
        self.vurgu = vurgu
        self.baslik = ParagraphStyle("b", fontName="Filiz-B", fontSize=19, leading=23, textColor=colors.HexColor("#2B2620"), spaceAfter=2)
        self.alt = ParagraphStyle("a", fontName="Filiz", fontSize=10, leading=13, textColor=GRI, spaceAfter=8)
        self.h2 = ParagraphStyle("h2", fontName="Filiz-B", fontSize=12.5, leading=16, textColor=vurgu, spaceBefore=10, spaceAfter=5, keepWithNext=1)
        self.h3 = ParagraphStyle("h3", fontName="Filiz-B", fontSize=10, leading=13, textColor=colors.HexColor("#2B2620"), spaceAfter=2, keepWithNext=1)
        self.govde = ParagraphStyle("g", fontName="Filiz", fontSize=9.3, leading=13, textColor=colors.HexColor("#3A342D"), alignment=TA_LEFT)
        self.kucuk = ParagraphStyle("k", fontName="Filiz", fontSize=8, leading=10.5, textColor=GRI)
        self.hucre = ParagraphStyle("h", fontName="Filiz", fontSize=8.4, leading=11, textColor=colors.HexColor("#3A342D"))
        self.hucre_b = ParagraphStyle("hb", parent=self.hucre, fontName="Filiz-B")
        self.not_ = ParagraphStyle("n", parent=self.govde, fontName="Filiz-I", textColor=GRI, fontSize=8.6, leading=12)

    def p(self, metin, stil=None):
        return Paragraph(metin, stil or self.govde)


def _cubuklar(satirlar: list[tuple[str, float | None]], genislik=170 * mm, renk=None, etiket_gen=58 * mm, maks=100.0):
    """Yatay çubuk grafiği: [(etiket, değer 0-100)]."""
    satir_y = 13
    h = max(1, len(satirlar)) * satir_y + 4
    d = Drawing(genislik, h)
    cubuk_gen = genislik - etiket_gen - 22 * mm
    for i, (etiket, deger) in enumerate(satirlar):
        y = h - (i + 1) * satir_y + 2
        d.add(String(0, y + 2, (etiket or "")[:42], fontName="Filiz", fontSize=8, fillColor=colors.HexColor("#3A342D")))
        d.add(Rect(etiket_gen, y + 1, cubuk_gen, 7, fillColor=ACIK, strokeColor=None))
        if deger is not None:
            w = max(1.5, cubuk_gen * max(0.0, min(1.0, float(deger) / maks)))
            r = renk or (YESIL if deger >= 62 else AMBER if deger < 40 else colors.HexColor("#E8804A"))
            d.add(Rect(etiket_gen, y + 1, w, 7, fillColor=r, strokeColor=None))
            d.add(String(etiket_gen + cubuk_gen + 4, y + 2, f"{deger:.0f}" if maks == 100 else f"{deger:g}",
                         fontName="Filiz-B", fontSize=8, fillColor=colors.HexColor("#3A342D")))
    return d


def _tablo(st, basliklar, satirlar, genislikler, zebra=True, kucuk=False):
    hs = st.hucre if not kucuk else ParagraphStyle("hk", parent=st.hucre, fontSize=7.4, leading=9.5)
    veri = [[Paragraph(f"<b>{_e(b)}</b>", hs) for b in basliklar]]
    for s in satirlar:
        veri.append([c if hasattr(c, "wrap") else Paragraph(_e(c), hs) for c in s])
    t = Table(veri, colWidths=genislikler, repeatRows=1)
    stil = [
        ("BACKGROUND", (0, 0), (-1, 0), ACIK), ("LINEBELOW", (0, 0), (-1, 0), 0.6, st.vurgu),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, CIZGI),
    ]
    if zebra:
        for i in range(2, len(veri), 2):
            stil.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FCFAF6")))
    t.setStyle(TableStyle(stil))
    return t


def _swot(st, s: dict, gen=174 * mm):
    def kutu(baslik, renk, maddeler):
        icerik = [Paragraph(f"<b>{baslik}</b>", ParagraphStyle("sb", parent=st.hucre_b, textColor=renk, fontSize=9.5))]
        for m in maddeler or ["—"]:
            icerik.append(Paragraph("• " + _e(m), st.hucre))
        return icerik
    t = Table([[kutu("Güçlü yönler (S)", YESIL, s["S"]), kutu("Gelişim alanları (W)", AMBER, s["W"])],
               [kutu("Fırsatlar (O)", colors.HexColor("#3D7CA8"), s["O"]), kutu("Dikkat edilecekler (T)", KIRMIZI, s["T"])]],
              colWidths=[gen / 2, gen / 2])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, CIZGI), ("INNERGRID", (0, 0), (-1, -1), 0.6, CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F3F8F1")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FBF5E8")), ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#EFF5FA")),
        ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#FBF0EE")),
    ]))
    return t


def _logo_okuyucu(logo: str | None):
    if not logo or not logo.startswith("data:image/") or "svg" in logo[:30]:
        return None
    try:
        return ImageReader(io.BytesIO(base64.b64decode(logo.split(",", 1)[1])))
    except Exception:
        return None


def _belge(baslik_sag: str, okul: dict, tarih):
    _fontlar()
    tampon = io.BytesIO()
    vurgu = _renk(okul.get("renk"))
    logo = _logo_okuyucu(okul.get("logo"))

    def sayfa(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(vurgu)
        canvas.rect(0, h - 6, w, 6, stroke=0, fill=1)
        x = 18 * mm
        if logo is not None:
            try:
                canvas.drawImage(logo, x, h - 20 * mm, width=11 * mm, height=11 * mm, preserveAspectRatio=True, mask="auto")
                x += 13 * mm
            except Exception:
                pass
        canvas.setFont("Filiz-B", 9.5)
        canvas.setFillColor(colors.HexColor("#2B2620"))
        canvas.drawString(x, h - 14 * mm, okul.get("ad") or "")
        canvas.setFont("Filiz", 8)
        canvas.setFillColor(GRI)
        canvas.drawString(x, h - 18 * mm, "Filizyol · Bölüm Uyum ve Kariyer Koçluğu")
        canvas.drawRightString(w - 18 * mm, h - 14 * mm, baslik_sag)
        canvas.drawRightString(w - 18 * mm, h - 18 * mm, _tarih(tarih, saat=True))
        canvas.setStrokeColor(CIZGI)
        canvas.line(18 * mm, h - 22 * mm, w - 18 * mm, h - 22 * mm)
        canvas.setFont("Filiz", 7.2)
        canvas.drawString(18 * mm, 10 * mm, "Kişisel veri içerir — yalnızca öğrenci, veli ve okulun yetkili personeliyle paylaşınız.")
        canvas.drawRightString(w - 18 * mm, 10 * mm, f"Sayfa {doc.page}")
        canvas.restoreState()

    doc = BaseDocTemplate(tampon, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=27 * mm, bottomMargin=17 * mm,
                          title=baslik_sag, author="Filizyol")
    cerceve = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="n")
    doc.addPageTemplates([PageTemplate(id="s", frames=[cerceve], onPage=sayfa)])
    return doc, tampon, _Stil(vurgu)


def _kunye(st, v, rapor_adi):
    k = v["kisi"]
    tur = v.get("tur") or {}
    satirlar = [
        ["Öğrenci", k["ad_soyad"], "Okul", v["okul"]["ad"]],
        ["Sınıf / şube", " / ".join(filter(None, [k.get("sinif"), k.get("sube")])) or "—", "Öğrenci no", k.get("ogrenci_no") or "—"],
        ["Değerlendirme", f"{tur.get('no', '—')}. tur" if tur else "Başlamadı",
         "Tamamlanma", _tarih(tur.get("tamamlanma")) if tur else "—"],
    ]
    t = Table([[Paragraph(f"<b>{_e(a)}</b>", st.kucuk), Paragraph(_e(b), st.hucre), Paragraph(f"<b>{_e(c)}</b>", st.kucuk),
                Paragraph(_e(d), st.hucre)] for a, b, c, d in satirlar], colWidths=[28 * mm, 59 * mm, 28 * mm, 59 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACIK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return [st.p(rapor_adi, st.baslik), st.p(_e(k["ad_soyad"]) + " · " + _e(v["okul"]["ad"]), st.alt), t, Spacer(1, 8)]


def _bitmedi_notu(st, v):
    if v["durum"] == "tamamlandi":
        return []
    metin = {"baslamadi": "Öğrenci değerlendirmeye henüz başlamadı.",
             "devam": "Değerlendirme henüz tamamlanmadı; aşağıdaki bilgiler tamamlanan katmanlara dayanır, bölüm önerileri oluşmadı.",
             "k5_bekliyor": "Alan soruları (K5) bekliyor; bölüm önerileri bu adım tamamlanınca oluşur."}.get(v["durum"], "")
    return [st.p(_e(metin), st.not_), Spacer(1, 4)]



# ============================================================================= [2026-10-10] deneme / net bölümü
OTURUM_RENK = {"TYT": colors.HexColor("#2A78D6"), "AYT": colors.HexColor("#EB6834"), "YDT": colors.HexColor("#1BAF7A")}


def _sayi(x) -> str:
    if x is None:
        return "—"
    return (f"{x:.2f}".rstrip("0").rstrip(".")).replace(".", ",")


def _net_grafigi(oturumlar: list[dict], gen=174 * mm, yuk=46 * mm):
    """Deneme toplam netlerinin zamana göre çizgi grafiği (oturum başına bir çizgi)."""
    tum = [(t, v) for o in oturumlar for t, v in o["seri"]]
    if len(tum) < 2:
        return None
    d = Drawing(gen, yuk)
    sol, alt, sag, ust = 22, 14, 40, 6
    t0 = min(t for t, _ in tum).toordinal(); t1 = max(t for t, _ in tum).toordinal()
    ymax = max(10, max(v for _, v in tum)); ymax = (int(ymax / 20) + 1) * 20
    x = lambda t: sol + ((t.toordinal() - t0) / ((t1 - t0) or 1)) * (gen - sol - sag)
    y = lambda v: alt + max(0.0, v) / ymax * (yuk - alt - ust)
    for k in range(0, 5):
        v = ymax * k / 4
        d.add(Line(sol, y(v), gen - sag, y(v), strokeColor=CIZGI, strokeWidth=0.4))
        d.add(String(sol - 3, y(v) - 2.5, f"{v:.0f}", fontName="Filiz", fontSize=6.5, fillColor=GRI, textAnchor="end"))
    for o in oturumlar:
        r = OTURUM_RENK.get(o["oturum"], GRI)
        nokta = [c for t, v in o["seri"] for c in (x(t), y(v))]
        if len(o["seri"]) > 1:
            d.add(PolyLine(nokta, strokeColor=r, strokeWidth=1.4))
        for t, v in o["seri"]:
            d.add(Rect(x(t) - 1.6, y(v) - 1.6, 3.2, 3.2, fillColor=r, strokeColor=None))
        t, v = o["seri"][-1]
        d.add(String(x(t) + 4, y(v) - 2.5, f"{o['oturum']} {_sayi(v)}", fontName="Filiz-B", fontSize=7, fillColor=r))
    d.add(String(sol, 2, tum[0][0].strftime("%d.%m.%Y") if hasattr(tum[0][0], "strftime") else "", fontName="Filiz", fontSize=6.5, fillColor=GRI))
    son = max(t for t, _ in tum)
    d.add(String(gen - sag, 2, son.strftime("%d.%m.%Y"), fontName="Filiz", fontSize=6.5, fillColor=GRI, textAnchor="end"))
    return d


def _net_bolumu(st, v: dict, kitle: str) -> list:
    """kitle: ogrenci | veli | yonetici | sinif_ogretmeni — içerik ve dil kitleye göre değişir."""
    n = v.get("netler")
    baslik = {"ogrenci": "Deneme netlerin", "veli": "Deneme sınavı sonuçları", "yonetici": "Deneme ve net takibi",
              "sinif_ogretmeni": "Deneme ve net takibi"}[kitle]
    h = [st.p(baslik, st.h2)]
    if not n or not n.get("oturumlar"):
        h.append(st.p("Öğrenci henüz Net Takibi'ne deneme sonucu girmedi." if kitle != "ogrenci"
                      else "Henüz deneme sonucu girmedin. Net Takibi sayfasına denemelerini eklersen gelişimin burada görünür.", st.not_))
        if n and n.get("konu"):
            h.append(st.p(f"Konu takibi: {n['konu_biten']} konu tamamlandı, {n['konu_calisiyor']} konu çalışılıyor.", st.govde))
        return h
    if kitle == "veli":
        h.append(st.p("Net; doğru sayısından yanlışların dörtte birinin çıkarılmasıyla bulunur. Tek bir deneme değil, "
                      "denemeler boyunca gidişat önemlidir.", st.not_))
    h.append(_tablo(st, ["Oturum", "Deneme", "İlk", "Son", "En iyi", "Son 3 ort.", "Değişim"],
                    [[o["oturum"], str(o["sayi"]), _sayi(o["ilk"]), _sayi(o["son"]), _sayi(o["en_iyi"]), _sayi(o["ort3"]),
                      ("+" if o["degisim"] >= 0 else "") + _sayi(o["degisim"])] for o in n["oturumlar"]],
                    [22 * mm, 20 * mm, 22 * mm, 22 * mm, 24 * mm, 30 * mm, 34 * mm]))
    g = _net_grafigi(n["oturumlar"])
    if g is not None:
        h += [Spacer(1, 4), g]
    if kitle in ("yonetici", "sinif_ogretmeni", "ogrenci") and n["dersler"]:
        h.append(st.p("Ders ders (son deneme ve son 3 deneme ortalaması)", st.h3))
        h.append(_tablo(st, ["Ders", "Soru", "Son", "Önceki", "Son 3 ort."],
                        [[f"{d['oturum']} {d['ad']}", str(d["soru"]), _sayi(d["son"]), _sayi(d["onceki"]), _sayi(d["ort3"])]
                         for d in n["dersler"]], [70 * mm, 18 * mm, 26 * mm, 26 * mm, 34 * mm], kucuk=True))
    k = n.get("kiyas")
    if k:
        hd = k["hedef"]
        acik = round((k["toplam_hedef"] or 0) - (k["toplam_ben"] or 0), 2)
        h.append(st.p("Hedef programla karşılaştırma", st.h3))
        h.append(st.p(f"<b>{_e(hd['universite'])}</b> · {_e(hd['program'])} — {k.get('yil')} yılında bu programa yerleşen son öğrencinin "
                      f"netleri ile son denemelerin ortalaması: <b>{_sayi(k['toplam_ben'])}</b> / {_sayi(k['toplam_hedef'])} net "
                      + (f"(kapatılacak fark <b>{_sayi(acik)}</b> net)." if acik > 0 else "(hedefin üzerinde)."), st.govde))
        if kitle in ("yonetici", "sinif_ogretmeni", "ogrenci"):
            h.append(_tablo(st, ["Ders", "Öğrenci", f"{k.get('yil')} son yerleşen", "Yıllar ort.", "Fark"],
                            [[s["ad"], _sayi(s["ben"]), _sayi(s["hedef"]), _sayi(s["hedef_ortalama"]),
                              ("" if s["fark"] is None else ("+" if s["fark"] >= 0 else "") + _sayi(s["fark"]))]
                             for s in k["satirlar"]], [60 * mm, 26 * mm, 36 * mm, 26 * mm, 26 * mm], kucuk=True))
        h.append(st.p("Hedef netler tek bir kişiye (son yerleşen) aittir ve diploma notu (OBP) da yerleşmeyi etkiler; yön gösterici "
                      "olarak yorumlayınız. Kaynak: YÖK Atlas.", st.not_))
    if n.get("konu"):
        h.append(st.p(f"Konu takibi: <b>{n['konu_biten']}</b> konu tamamlandı, {n['konu_calisiyor']} konu çalışılıyor.", st.govde))
    ilk = (k or {}).get("en_buyuk_acik") or []
    oneriler = {
        "ogrenci": ([f"En büyük açığın {ilk[0]['ad']} dersinde; Net Takibi → Konu Takibi'nde bu dersin bitmeyen konularından başla."]
                    if ilk else []) + ["Her deneme sonrası yanlışlarını konu konu not et; aynı hatayı ikinci kez yapmamak en ucuz nettir."],
        "veli": ["Deneme sonuçlarını not gibi değil, gidişat olarak değerlendirin; düşüş olduğunda yorgunluk, uyku ve stres durumunu birlikte konuşun.",
                 "Düzenli deneme çözmeyi ve sonrasında yanlışları incelemeyi destekleyin."],
        "yonetici": ([f"En büyük net açığı: {', '.join(x['ad'] + ' (' + _sayi(x['fark']) + ')' for x in ilk)}."] if ilk else []),
        "sinif_ogretmeni": ([f"Destek gerektiren dersler: {', '.join(x['ad'] for x in ilk)}. Ders öğretmenleriyle paylaşılabilir."] if ilk else [])
                           + ["Deneme takvimini sınıfla birlikte planlamak ve sonuçların konu bazlı incelenmesini teşvik etmek faydalıdır."],
    }[kitle]
    for m in oneriler:
        h.append(st.p("• " + _e(m), st.govde))
    if kitle == "yonetici":
        h.append(st.p("Deneme listesi", st.h3))
        h.append(_tablo(st, ["Tarih", "Oturum", "Deneme", "Toplam net"],
                        [[_tarih(d["tarih"]), d["oturum"], d.get("ad") or "—", _sayi(d["toplam"])] for d in reversed(n["denemeler"][-15:])],
                        [28 * mm, 20 * mm, 96 * mm, 30 * mm], kucuk=True))
    return h


# ============================================================================= öğrenci raporu
def ogrenci_pdf(v: dict, netler: bool = True) -> bytes:
    doc, tampon, st = _belge("Öğrenci Raporu", v["okul"], v["tarih"])
    h = _kunye(st, v, "Öğrenci Raporu")
    h += _bitmedi_notu(st, v)
    h.append(st.p("Bu rapor, değerlendirmede verdiğin cevaplara göre değerlerini, kişiliğini, sevdiğin iş ortamını ve ilgi alanlarını; "
                  "sana uygun bölümleri ve gelişim planını özetler. Puanlar bir not değil, <b>eğilim</b> gösterir.", st.govde))
    if v["katmanlar"]:
        h.append(st.p("Profilin bir bakışta", st.h2))
        h.append(_cubuklar([(f"{k['kod']} · {k['ad']}", k["ortalama"]) for k in v["katmanlar"]] +
                           [(f"K5 · {x['ad']}", x["puan"]) for x in v["k5"][:2]], renk=st.vurgu))
    if v["gucluler"]:
        h.append(st.p("Güçlü yönlerin", st.h2))
        for x in v["gucluler"]:
            h.append(KeepTogether([st.p(f"<b>{_e(x['ad'])}</b> · {x['seviye']} ({x['puan']:.0f})", st.h3),
                                   st.p(_e(x.get("yorum") or x.get("aciklama") or ""), st.govde), Spacer(1, 4)]))
    if v["gelisim"]:
        h.append(st.p("Gelişebileceğin alanlar", st.h2))
        for x in v["gelisim"]:
            parca = [st.p(f"<b>{_e(x['ad'])}</b> ({x['puan']:.0f})", st.h3)]
            if x.get("yorum"):
                parca.append(st.p(_e(x["yorum"])))
            if x.get("oneri"):
                parca.append(st.p("<i>Öneri:</i> " + _e(x["oneri"])))
            parca.append(Spacer(1, 4))
            h.append(KeepTogether(parca))
    if v["bolumler"]:
        h.append(st.p("Sana en uygun 10 bölüm", st.h2))
        h.append(_tablo(st, ["#", "Bölüm", "Alan", "Uyum", "Neden?"],
                        [[str(b["sira"]), b["ad"], b.get("alan") or "", f"%{b['uyum']:.0f}", ", ".join(b.get("ortusen") or [])]
                         for b in v["bolumler"]], [8 * mm, 52 * mm, 34 * mm, 14 * mm, 66 * mm]))
    if v["hedef"]:
        hd = v["hedef"]
        il = hd.get("ilerleme") or {}
        h.append(st.p("Hedefin ve yol haritan", st.h2))
        h.append(st.p(f"<b>Hedef bölüm:</b> {_e(hd['ad'])}" + (f" · uyum %{hd['uyum']:.0f}" if hd.get("uyum") is not None else "")
                      + (f" · önerilerinde {hd['sira']}. sırada" if hd.get("sira") else "")))
        if il.get("toplam"):
            h.append(st.p(f"<b>Yol haritası:</b> {il.get('tamamlanan', 0)} / {il['toplam']} adım tamamlandı"
                          + (f" · sıradaki adım: {_e(hd.get('siradaki'))}" if hd.get("siradaki") else "")))
        for x in hd.get("odak", [])[:3]:
            h.append(st.p(f"• <b>{_e(x['ad'])}:</b> {_e(x.get('neden') or '')}", st.govde))
    if netler:
        h += _net_bolumu(st, v, "ogrenci")
    h.append(st.p("SWOT analizin", st.h2))
    h.append(_swot(st, v["swot"]))
    h.append(Spacer(1, 8))
    h.append(st.p("Unutma: Sonuçların karar vermene yardımcı olur; son karar senin ve rehber öğretmeninle birlikte verilir. İlgi ve eğilimlerin "
                  "lise yıllarında gelişir; raporu ailenle de konuş, merak ettiğin bölümleri yakından tanı.", st.not_))
    doc.build(h)
    return tampon.getvalue()


# ============================================================================= veli raporu
VELI_ONERILERI = [
    "Çocuğunuzla sonuçları birlikte okuyun; “Sence bu seni anlatıyor mu?” diye sorarak onun yorumunu dinleyin.",
    "Önerilen bölümleri birer “kesin karar” değil, keşfedilecek seçenekler olarak görün.",
    "İlgi duyduğu alanlarda bir meslek sahibiyle tanışma, kampüs gezisi ya da kısa bir atölye fırsatı yaratın.",
    "Gelişime açık alanlarda küçük ve düzenli adımları destekleyin; karşılaştırma yerine ilerlemeyi takdir edin.",
    "Haftalık görevlerini ve yol haritasındaki adımları sorun; bitirdiği adımları kutlayın.",
    "Sorularınız için okulun rehber öğretmeniyle görüşme planlayın.",
]
VELI_SORULARI = [
    "Sonuçlar, çocuğumun okuldaki gözlemlerinizle örtüşüyor mu?",
    "Hedef bölüm için hangi derslere ve puan türüne odaklanmalı?",
    "Gelişime açık alanlarda okul içinde hangi etkinliklere katılabilir?",
    "Bir sonraki değerlendirme ne zaman yapılacak?",
]


def veli_pdf(v: dict, netler: bool = True) -> bytes:
    doc, tampon, st = _belge("Veli Raporu", v["okul"], v["tarih"])
    h = _kunye(st, v, "Veli Bilgilendirme Raporu")
    h.append(st.p("Sayın Veli,", st.h3))
    h.append(st.p(f"Bu rapor, çocuğunuz <b>{_e(v['kisi']['ad_soyad'])}</b>’in Filizyol değerlendirmesinde verdiği cevaplara göre hazırlanmıştır. "
                  "Değerlendirme; değerler, kişilik ve çalışma tarzı, tercih ettiği iş ortamı ve ilgi alanlarını ölçer. "
                  "Bir başarı ya da zekâ testi <b>değildir</b>; doğru veya yanlış cevabı yoktur. Sonuçlar çocuğunuzun bugünkü "
                  "eğilimlerini gösterir ve zamanla değişebilir."))
    h += _bitmedi_notu(st, v)
    if v["gucluler"]:
        h.append(st.p("Çocuğunuzun öne çıkan güçlü yönleri", st.h2))
        for x in v["gucluler"][:5]:
            h.append(st.p(f"• <b>{_e(x['ad'])}</b> — {_e(x.get('yorum') or x.get('aciklama') or x['seviye'])}"))
    if v["gelisim"]:
        h.append(st.p("Gelişebileceği alanlar ve evde nasıl destek olabilirsiniz", st.h2))
        for x in v["gelisim"][:4]:
            h.append(st.p(f"• <b>{_e(x['ad'])}</b>" + (f" — {_e(x['oneri'])}" if x.get("oneri") else "")))
    if v["bolumler"]:
        h.append(st.p("Çocuğunuza uygun görünen bölümler", st.h2))
        h.append(_tablo(st, ["#", "Bölüm", "Alan", "Uyum"],
                        [[str(b["sira"]), b["ad"], b.get("alan") or "", f"%{b['uyum']:.0f}"] for b in v["bolumler"][:6]],
                        [10 * mm, 90 * mm, 52 * mm, 22 * mm]))
        h.append(st.p("Uyum yüzdesi; çocuğunuzun profilinin bölümün gerektirdiği özelliklerle ne kadar örtüştüğünü gösterir, "
                      "başarı ya da kazanma olasılığı anlamına gelmez.", st.not_))
    if v["hedef"]:
        hd = v["hedef"]
        il = hd.get("ilerleme") or {}
        h.append(st.p("Hedef ve çalışma planı", st.h2))
        h.append(st.p(f"Çocuğunuzun seçtiği hedef bölüm: <b>{_e(hd['ad'])}</b>."
                      + (f" Kişisel yol haritasında {il.get('tamamlanan', 0)} / {il['toplam']} adımı tamamladı." if il.get("toplam") else "")))
    if netler:
        h += _net_bolumu(st, v, "veli")
    h.append(st.p("Özet (SWOT)", st.h2))
    h.append(_swot(st, v["swot"]))
    h.append(st.p("Velilere öneriler", st.h2))
    for m in VELI_ONERILERI:
        h.append(st.p("• " + _e(m)))
    h.append(st.p("Rehber öğretmenle görüşmede sorabilecekleriniz", st.h2))
    for m in VELI_SORULARI:
        h.append(st.p("• " + _e(m)))
    tur = v.get("tur") or {}
    if tur and not tur.get("gecerli", True):
        h.append(Spacer(1, 6))
        h.append(st.p("Not: Bu değerlendirmenin güvenilirlik kontrolü düşük çıkmıştır; sonuçlar temkinli yorumlanmalı ve "
                      "rehber öğretmenle birlikte değerlendirilmelidir.", st.not_))
    doc.build(h)
    return tampon.getvalue()


# ============================================================================= yönetici (rehber) raporu
def yonetici_pdf(v: dict, netler: bool = True) -> bytes:
    doc, tampon, st = _belge("Yönetici Raporu", v["okul"], v["tarih"])
    h = _kunye(st, v, "Öğrenci Değerlendirme Raporu (Yönetici)")
    tur = v.get("tur") or {}
    g = v.get("guvenlik") or {}
    a = v.get("aktivite") or {}
    ozet = [
        ["Durum", {"tamamlandi": "Tamamlandı", "devam": "Devam ediyor", "k5_bekliyor": "K5 bekliyor", "baslamadi": "Başlamadı"}.get(v["durum"], v["durum"]),
         "Tur sayısı", str(tur.get("tur_sayisi", 0))],
        ["Güven puanı", f"{tur['guven']:.0f} / 100" if tur.get("guven") is not None else "—",
         "Geçerlilik", ("Geçerli" if tur.get("gecerli", True) else "GEÇERSİZ") if tur else "—"],
        ["Kamera doğrulaması", "Var" if g.get("kamera") else "Yok", "İhlaller",
         ", ".join(f"{x['ad']} ({x['sayi']})" for x in g.get("ihlaller", [])) or "Yok"],
        ["Son giriş", _tarih(a.get("son_giris"), True), "Haftalık görev", f"{a.get('gorev_tamam', 0)} / {a.get('gorev_toplam', 0)} (son 4 hafta: {a.get('son4_hafta', 0)})"],
        ["Yol haritası adımı", str(a.get("adim", 0)), "Listem", ", ".join(v["listem"][:5]) or "—"],
    ]
    h.append(st.p("Özet", st.h2))
    h.append(_tablo(st, ["", "", "", ""], ozet, [32 * mm, 55 * mm, 30 * mm, 57 * mm], zebra=False))
    if tur.get("gecersizlik"):
        h.append(st.p(_e(tur["gecersizlik"]), st.not_))
    if v["katmanlar"]:
        h.append(st.p("Katman sonuçları", st.h2))
        h.append(_cubuklar([(f"{k['kod']} · {k['ad']}", k["ortalama"]) for k in v["katmanlar"]], renk=st.vurgu))
        for k in v["katmanlar"]:
            h.append(KeepTogether([st.p(f"{k['kod']} · {_e(k['ad'])} (ortalama {k['ortalama']:.0f})", st.h3),
                                   _cubuklar([(x["ad"], x["puan"]) for x in k["ozellikler"]]), Spacer(1, 5)]))
    if v["k5"]:
        h.append(st.p("Alan soruları (K5)", st.h2))
        h.append(_cubuklar([(x["ad"], x["puan"]) for x in v["k5"]]))
    if v["bolumler"]:
        h.append(st.p("Bölüm önerileri (ilk 10)", st.h2))
        h.append(_tablo(st, ["#", "Bölüm", "Alan", "Uyum", "Örtüşen özellikler", "Dikkat"],
                        [[str(b["sira"]), b["ad"], b.get("alan") or "", f"%{b['uyum']:.0f}", ", ".join(b.get("ortusen") or []),
                          b.get("dikkat") or ""] for b in v["bolumler"]],
                        [7 * mm, 40 * mm, 27 * mm, 12 * mm, 45 * mm, 43 * mm], kucuk=True))
    if v["hedef"]:
        hd = v["hedef"]
        il = hd.get("ilerleme") or {}
        h.append(st.p("Hedef bölüm ve koçluk", st.h2))
        h.append(st.p(f"<b>{_e(hd['ad'])}</b> · seçim: {_tarih(hd.get('secim'))}"
                      + (f" · uyum %{hd['uyum']:.0f}" if hd.get("uyum") is not None else "")
                      + (f" · öneri sırası {hd['sira']}" if hd.get("sira") else " · ilk 10 öneri dışında")
                      + (f" · yol haritası {il.get('tamamlanan', 0)}/{il['toplam']}" if il.get("toplam") else "")))
        if hd.get("odak"):
            h.append(_tablo(st, ["Odak alanı", "Neden önemli"], [[x["ad"], x.get("neden") or ""] for x in hd["odak"]],
                            [40 * mm, 134 * mm], kucuk=True))
    if netler:
        h += _net_bolumu(st, v, "yonetici")
    h.append(st.p("SWOT analizi", st.h2))
    h.append(_swot(st, v["swot"]))
    if v["swot"]["T"]:
        h.append(st.p("Görüşme için önerilen konular", st.h2))
        for m in v["swot"]["T"][:5]:
            h.append(st.p("• " + _e(m)))
    doc.build(h)
    return tampon.getvalue()



# ============================================================================= [2026-10-10] sınıf öğretmeni raporu
SINIF_OGRETMENI_ONERILERI = [
    "Öğrencinin güçlü yönlerini sınıf içi görevlerde (sunum, grup çalışması, proje) görünür kılacak fırsatlar verin.",
    "Hedef bölümüyle ilgili derslerde başarılarını takdir edin; gelişim alanlarında küçük ve somut hedefler koyun.",
    "Yönlendirme ve ayrıntılı değerlendirme için okulun rehber öğretmeniyle iş birliği yapın.",
]


def sinif_ogretmeni_pdf(v: dict, netler: bool = True) -> bytes:
    """Sınıf öğretmeni için sade rapor: katılım, öne çıkanlar, hedef ve koçluk ilerlemesi, deneme / net takibi.
    Psikolojik ayrıntılar, güven puanı ve ihlaller bu raporda yer almaz."""
    doc, tampon, st = _belge("Sınıf Öğretmeni Raporu", v["okul"], v["tarih"])
    h = _kunye(st, v, "Sınıf Öğretmeni Bilgi Raporu")
    h += _bitmedi_notu(st, v)
    a = v.get("aktivite") or {}
    hd = v.get("hedef") or {}
    il = hd.get("ilerleme") or {}
    durum = {"tamamlandi": "Tamamlandı", "devam": "Devam ediyor", "k5_bekliyor": "Alan soruları bekliyor",
             "baslamadi": "Başlamadı"}.get(v["durum"], v["durum"])
    h.append(st.p("Katılım ve ilerleme", st.h2))
    h.append(_tablo(st, ["", "", "", ""], [
        ["Değerlendirme", durum, "Son giriş", _tarih(a.get("son_giris"), True)],
        ["Hedef bölüm", hd.get("ad") or "Seçilmedi", "Yol haritası",
         f"{il.get('tamamlanan', 0)} / {il['toplam']} adım" if il.get("toplam") else "—"],
        ["Haftalık görev", f"{a.get('gorev_tamam', 0)} / {a.get('gorev_toplam', 0)}", "Son 4 hafta", f"{a.get('son4_hafta', 0)} görev"],
    ], [32 * mm, 55 * mm, 30 * mm, 57 * mm], zebra=False))
    if v["gucluler"]:
        h.append(st.p("Öne çıkan güçlü yönleri", st.h2))
        h.append(st.p(", ".join(f"<b>{_e(x['ad'])}</b>" for x in v["gucluler"][:5]) + ".", st.govde))
    if v["bolumler"]:
        h.append(st.p("Uygun görünen alanlar", st.h2))
        alanlar = []
        for b in v["bolumler"][:6]:
            if b.get("alan") and b["alan"] not in alanlar:
                alanlar.append(b["alan"])
        h.append(st.p(_e(", ".join(alanlar) or ", ".join(b["ad"] for b in v["bolumler"][:3])) + ".", st.govde))
    if netler:
        h += _net_bolumu(st, v, "sinif_ogretmeni")
    h.append(st.p("Sınıf öğretmenine öneriler", st.h2))
    for m in SINIF_OGRETMENI_ONERILERI:
        h.append(st.p("• " + _e(m), st.govde))
    h.append(Spacer(1, 6))
    h.append(st.p("Bu rapor sınıf öğretmeni için sadeleştirilmiştir; kişilik ayrıntıları, güven puanı ve psikolojik değerlendirme "
                  "içermez. Ayrıntılı bilgi için rehber öğretmenle görüşünüz.", st.not_))
    doc.build(h)
    return tampon.getvalue()


# ============================================================================= okul genel raporu
def okul_pdf(v: dict, netler: bool = True) -> bytes:
    o = v["ozet"]
    ks = v.get("kapsam") or {}
    sube_mi = bool(ks.get("sube"))
    if sube_mi:
        baslik = f"{ks['etiket']} Sınıf Raporu"
    elif ks.get("sinif"):
        baslik = f"{ks['sinif']} Raporu"
    else:
        baslik = "Okul Genel Raporu"
    doc, tampon, st = _belge(baslik, v["okul"], v["tarih"])
    alt = _e(v["okul"]["ad"]) + " · " + _tarih(v["tarih"])
    if (ks.get("ogretmen") or {}).get("ad"):
        alt += " · Sınıf öğretmeni: " + _e(ks["ogretmen"]["ad"])
    h = [st.p(baslik, st.baslik), st.p(alt, st.alt)]
    toplam = o.get("toplam") or 0
    birim = "Sınıfın" if sube_mi else ("Sınıf düzeyinin" if ks.get("sinif") else "Okulun")

    def oran(n):
        return f"{n} (%{round(100 * n / toplam) if toplam else 0})"
    sayi_st = ParagraphStyle("kpi", fontName="Filiz-B", fontSize=14, leading=18, textColor=st.vurgu)
    kpi = Table([[[Paragraph(a, st.kucuk), Paragraph(str(b), sayi_st)] for a, b in
                  [("Öğrenci", toplam), ("Giriş yapan", oran(o.get("giris_yapan", 0))), ("Teste başlayan", oran(o.get("teste_baslayan", 0))),
                   ("Tamamlayan", oran(o.get("tamamlayan", 0))), ("Hedef seçen", oran(o.get("hedef_secen", 0)))]]],
                colWidths=[34.8 * mm] * 5)
    kpi.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACIK), ("INNERGRID", (0, 0), (-1, -1), 2, colors.white),
                             ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    h += [kpi, Spacer(1, 6)]
    h.append(st.p("Değerlendirme durumu", st.h2))
    h.append(_cubuklar([(d["etiket"], d["sayi"]) for d in o.get("durumlar", [])], maks=max(1, toplam), renk=st.vurgu))
    subeler = [x for x in o.get("subeler", []) if x["sube"]]
    if subeler and not sube_mi:
        h.append(st.p("Şubelere göre", st.h2))
        h.append(_tablo(st, ["Şube", "Sınıf öğretmeni", "Öğrenci", "Giriş yapan", "Tamamlayan", "Tamamlama"],
                        [[x["etiket"], (x.get("ogretmen") or {}).get("ad") or "—", str(x["ogrenci"]), str(x["giris_yapan"]),
                          str(x["tamamlayan"]), f"%{round(100 * x['tamamlayan'] / x['ogrenci']) if x['ogrenci'] else 0}"] for x in subeler],
                        [22 * mm, 50 * mm, 22 * mm, 28 * mm, 28 * mm, 24 * mm]))
    if o.get("siniflar") and not ks.get("sinif"):
        h.append(st.p("Sınıflara göre", st.h2))
        h.append(_tablo(st, ["Sınıf", "Öğrenci", "Giriş yapan", "Devam eden", "Tamamlayan", "Tamamlama"],
                        [[s["sinif"], str(s["ogrenci"]), str(s["giris_yapan"]), str(s["devam"]), str(s["tamamlayan"]),
                          f"%{round(100 * s['tamamlayan'] / s['ogrenci']) if s['ogrenci'] else 0}"] for s in o["siniflar"]],
                        [40 * mm, 24 * mm, 28 * mm, 28 * mm, 28 * mm, 26 * mm]))
    if v["alanlar"]:
        h.append(st.p("Öğrencilerin en uyumlu çıktığı alanlar (1. öneriye göre)", st.h2))
        h.append(_cubuklar([(a["alan"], a["sayi"]) for a in v["alanlar"]], maks=max(a["sayi"] for a in v["alanlar"]), renk=st.vurgu))
    if o.get("en_cok_onerilen") or o.get("en_cok_hedeflenen"):
        h.append(st.p("En çok önerilen ve hedeflenen bölümler", st.h2))
        sol = o.get("en_cok_onerilen") or []
        sag = o.get("en_cok_hedeflenen") or []
        satir = [[(sol[i]["bolum"] + f" ({sol[i]['sayi']})") if i < len(sol) else "",
                  (sag[i]["bolum"] + f" ({sag[i]['sayi']})") if i < len(sag) else ""] for i in range(max(len(sol), len(sag)))]
        h.append(_tablo(st, ["1. öneri olarak", "Hedef olarak"], satir, [87 * mm, 87 * mm]))
    if v["katman_ort"] and v.get("okul_katman_ort"):
        okul_ort = {k["kod"]: k["ortalama"] for k in v["okul_katman_ort"]}
        h.append(st.p("Katman ortalamaları — okul ortalamasıyla karşılaştırma", st.h2))
        h.append(_tablo(st, ["Katman", "Şube" if sube_mi else "Sınıf düzeyi", "Okul", "Fark"],
                        [[f"{k['kod']} · {k['ad']}", f"{k['ortalama']:.0f}", f"{okul_ort.get(k['kod'], 0):.0f}",
                          f"{k['ortalama'] - okul_ort.get(k['kod'], k['ortalama']):+.0f}"] for k in v["katman_ort"]],
                        [86 * mm, 30 * mm, 30 * mm, 28 * mm]))
        h.append(st.p("Fark ±5 puandan büyükse grup okul ortalamasından belirgin biçimde ayrışıyor demektir.", st.not_))
    elif v["katman_ort"]:
        h.append(st.p("Katman ortalamaları (testi tamamlayanlar)", st.h2))
        h.append(_cubuklar([(f"{k['kod']} · {k['ad']}", k["ortalama"]) for k in v["katman_ort"]], renk=st.vurgu))
    if v["ortak_guclu"]:
        satir = [[f"{a['ad']} ({a['ortalama']:.0f})", f"{b['ad']} ({b['ortalama']:.0f})"] for a, b in zip(v["ortak_guclu"], v["ortak_gelisim"])]
        h.append(KeepTogether([
            st.p(f"{birim} ortak güçlü yönleri ve gelişim alanları", st.h2),
            _tablo(st, ["En yüksek ortalama", "En düşük ortalama"], satir, [87 * mm, 87 * mm]),
            st.p("Düşük ortalamalı özellikler " + ("sınıf rehberlik saatinde" if sube_mi else "okul genelinde")
                 + " planlanacak etkinlikler (kulüp, seminer, proje) için ipucu verir.", st.not_)]))
    nt = v.get("net") or {}
    if netler and nt.get("giren"):
        h.append(st.p("Deneme ve net özeti", st.h2))
        tyt, ayt = nt.get("tyt") or (None, 0), nt.get("ayt") or (None, 0)
        h.append(st.p(f"Net Takibi'ne deneme giren öğrenci: <b>{nt['giren']}</b> / {toplam} · toplam {nt.get('toplam_deneme', 0)} deneme. "
                      + (f"Son TYT ortalaması <b>{_sayi(tyt[0])}</b> ({tyt[1]} öğrenci)" if tyt[0] is not None else "")
                      + (f" · son AYT ortalaması <b>{_sayi(ayt[0])}</b> ({ayt[1]} öğrenci)" if ayt[0] is not None else "") + ".", st.govde))
        if nt.get("dersler"):
            h.append(_tablo(st, ["Ders", "Soru", "Son deneme ortalaması", "Öğrenci", "Doluluk"],
                            [[d["ad"], str(d["soru"]), _sayi(d["ort"]), str(d["n"]), f"%{round(100 * d['ort'] / d['soru'])}"] for d in nt["dersler"]],
                            [70 * mm, 18 * mm, 40 * mm, 22 * mm, 24 * mm], kucuk=True))
            h.append(st.p("Doluluk oranı düşük dersler, ders öğretmenleriyle birlikte planlanacak destek çalışmaları için ipucu verir.", st.not_))
    elif netler:
        h.append(st.p("Deneme ve net özeti", st.h2))
        h.append(st.p("Bu kapsamda henüz Net Takibi'ne deneme sonucu giren öğrenci yok.", st.not_))
    if v["gecersiz"]:
        h.append(st.p(f"Güvenilirlik: {v['gecersiz']} öğrencinin son değerlendirmesi güven eşiğinin altında; yeniden değerlendirme önerilir.", st.govde))
    if v["ogrenciler"]:
        h.append(st.p("Öğrenci listesi", st.h2))
        if sube_mi and netler:
            h.append(_tablo(st, ["No", "Ad soyad", "Durum", "1. öneri", "Hedef", "Güven", "Son TYT", "Son AYT"],
                            [[x.get("no") or "", x["ad_soyad"] + (" (test)" if x["test"] else ""), x["durum"], x["ilk_bolum"], x["hedef"],
                              f"{x['guven']:.0f}" if x["guven"] is not None else "", _sayi(x.get("son_tyt")) if x.get("son_tyt") is not None else "",
                              _sayi(x.get("son_ayt")) if x.get("son_ayt") is not None else ""] for x in v["ogrenciler"]],
                            [10 * mm, 33 * mm, 24 * mm, 32 * mm, 32 * mm, 12 * mm, 15 * mm, 16 * mm], kucuk=True))
        elif sube_mi:
            h.append(_tablo(st, ["No", "Ad soyad", "Durum", "1. öneri", "Hedef", "Güven"],
                            [[x.get("no") or "", x["ad_soyad"] + (" (test)" if x["test"] else ""), x["durum"], x["ilk_bolum"], x["hedef"],
                              f"{x['guven']:.0f}" if x["guven"] is not None else ""] for x in v["ogrenciler"]],
                            [12 * mm, 38 * mm, 28 * mm, 40 * mm, 40 * mm, 16 * mm], kucuk=True))
        else:
            h.append(_tablo(st, ["Ad soyad", "Sınıf", "Durum", "1. öneri", "Hedef", "Güven"],
                            [[x["ad_soyad"] + (" (test)" if x["test"] else ""), x["sinif"], x["durum"], x["ilk_bolum"], x["hedef"],
                              f"{x['guven']:.0f}" if x["guven"] is not None else ""] for x in v["ogrenciler"]],
                            [38 * mm, 18 * mm, 30 * mm, 38 * mm, 38 * mm, 12 * mm], kucuk=True))
    doc.build(h)
    return tampon.getvalue()
