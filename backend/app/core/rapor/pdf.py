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

from app.core.kucuk_grup import DIPNOT, GIZLI_METIN   # [2026-10-10] KVKK küçük grup gizleme
from app.core.rapor.veri import yuvarla   # [2026-10-14] gösterilen sayılar: yarım yukarı (ekrandaki Math.round ile aynı)
from app.core.seviye import gelisime_acik_mi, guclu_mu   # [2026-10-10] ortak düzey bantları

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
            r = renk or (YESIL if guclu_mu(deger) else AMBER if gelisime_acik_mi(deger) else colors.HexColor("#E8804A"))
            d.add(Rect(etiket_gen, y + 1, w, 7, fillColor=r, strokeColor=None))
            d.add(String(etiket_gen + cubuk_gen + 4, y + 2, f"{yuvarla(deger)}" if maks == 100 else f"{deger:g}",
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


def _swot_kitle(v: dict, kitle: str) -> dict:
    """[2026-10-12] Öğrenci ve veli raporunda SWOT kendi diliyle (sen / üçüncü kişi) yeniden kurulur."""
    from app.core.rapor.veri import swot
    return swot(v, kitle)


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
             "k5_bekliyor": "İş türü soruları (K5) bekliyor; uyumu 70 ve üzeri bölümlerin kendi aralarındaki sırası bu adım tamamlanınca netleşir."}.get(v["durum"], "")
    return [st.p(_e(metin), st.not_), Spacer(1, 4)]



# ============================================================================= [2026-10-12] yorum ve öneriler bölümü
# İçerik: app/core/rapor/yorum.py (kural tabanlı; rapordaki verilerden). Kitleye göre başlıklar:
_YORUM_BASLIK = {
    "ogrenci": ("Bunu yap", "Bundan kaçın", "Güçlü yönlerini nasıl kullanırsın?", "Gelişmek için küçük adımlar",
                "Rehber öğretmeninle konuşabileceklerin"),
    "veli": ("Yapabilecekleriniz", "Kaçınmanız gerekenler", "Güçlü yönlerini nasıl destekleyebilirsiniz?",
             "Gelişebileceği alanlarda evde destek", "Rehber öğretmenle görüşmede sorabilecekleriniz"),
    "ogretmen": ("Önerilenler", "Kaçınılması gerekenler", "Güçlü yönlerini sınıfta değerlendirme",
                 "Gelişim için sınıf içi destek", ""),
    "rehber": ("Yapılması gerekenler", "Yapılmaması gerekenler", "Güçlü yönlerin değerlendirilmesi",
               "Gelişim için destek", "Görüşme gündemi"),
}


def _ozet_kutusu(st, cumleler: list[str], baslik="Kısaca"):
    if not cumleler:
        return []
    kutu = Table([[[Paragraph(f"<b>{_e(baslik)}</b>", ParagraphStyle("ozb", parent=st.hucre_b, textColor=st.vurgu, fontSize=9.8)),
                    Paragraph(_e(" ".join(cumleler)), ParagraphStyle("ozg", parent=st.govde, fontSize=9.6, leading=13.6))]]],
                 colWidths=[174 * mm])
    kutu.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF6EE")),
                              ("LINEBEFORE", (0, 0), (0, -1), 3, st.vurgu),
                              ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                              ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return [kutu, Spacer(1, 8)]


def _yap_kacin(st, yap: list[str], kacin: list[str], b_yap: str, b_kacin: str, gen=174 * mm):
    if not yap and not kacin:
        return []

    def sutun(baslik, renk, isaret, maddeler):
        icerik = [Paragraph(f"<b>{_e(baslik)}</b>", ParagraphStyle("ykb", parent=st.hucre_b, textColor=renk, fontSize=9.8))]
        for m in maddeler or ["—"]:
            icerik.append(Paragraph(f"<font color='#{renk.hexval()[2:]}'><b>{isaret}</b></font> {_e(m)}",
                                    ParagraphStyle("ykm", parent=st.hucre, fontSize=8.8, leading=12, leftIndent=9, firstLineIndent=-9,
                                                   spaceBefore=2.5)))
        return icerik
    t = Table([[sutun(b_yap, YESIL, "+", yap), sutun(b_kacin, KIRMIZI, "–", kacin)]], colWidths=[gen / 2, gen / 2])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.6, CIZGI),
                           ("INNERGRID", (0, 0), (-1, -1), 0.6, CIZGI),
                           ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F3F8F1")), ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FBF0EE")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return [t, Spacer(1, 8)]


def _ad_metin_listesi(st, baslik: str, satirlar: list[dict]):
    if not satirlar or not baslik:
        return []
    h = [st.p(_e(baslik), st.h3)]
    for x in satirlar:
        h.append(st.p(f"<b>{_e(x['ad'])}:</b> {_e(x['metin'])}", ParagraphStyle("adm", parent=st.govde, leftIndent=8, spaceAfter=2.5)))
    h.append(Spacer(1, 5))
    return h


def _yorum_bolumu(st, y: dict, kitle: str, ozet: bool = True, baslik: str | None = None):
    """Rapora 'ne anlama geliyor / ne yapmalı / neden kaçınmalı' bölümünü ekler."""
    b_yap, b_kacin, b_guclu, b_destek, b_gorusme = _YORUM_BASLIK.get(kitle, _YORUM_BASLIK["rehber"])
    h = [st.p(_e(baslik or y.get("baslik") or "Değerlendirme ve öneriler"), st.h2)]
    if ozet:
        h += _ozet_kutusu(st, y.get("ozet") or [])
    h += _yap_kacin(st, y.get("yap") or [], y.get("kacin") or [], b_yap, b_kacin)
    h += _ad_metin_listesi(st, b_guclu, y.get("guclu") or [])
    h += _ad_metin_listesi(st, b_destek, y.get("destek") or [])
    if y.get("gorusme") and b_gorusme:
        h.append(st.p(_e(b_gorusme), st.h3))
        for m in y["gorusme"]:
            h.append(st.p("• " + _e(m), ParagraphStyle("gm", parent=st.govde, leftIndent=8, spaceAfter=1.5)))
        h.append(Spacer(1, 4))
    for n in y.get("notlar") or []:
        h.append(st.p(_e(n), st.not_))
    return h


# ============================================================================= [2026-10-10] deneme / net bölümü
OTURUM_RENK = {"TYT": colors.HexColor("#2A78D6"), "AYT": colors.HexColor("#EB6834"), "YDT": colors.HexColor("#1BAF7A")}


def _sayi(x) -> str:
    if x is None:
        return "—"
    return (f"{yuvarla(x, 2):.2f}".rstrip("0").rstrip(".")).replace(".", ",")


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
        d.add(String(sol - 3, y(v) - 2.5, f"{yuvarla(v)}", fontName="Filiz", fontSize=6.5, fillColor=GRI, textAnchor="end"))
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
        acik = yuvarla((k["toplam_hedef"] or 0) - (k["toplam_ben"] or 0), 2)
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
    from app.core.rapor.yorum import ogrenci_yorumu, ozellik_anlami   # [2026-10-12] yorum ve öneriler
    y = ogrenci_yorumu(v, "ogrenci")
    h.append(Spacer(1, 6))
    h += _ozet_kutusu(st, y["ozet"], "Kısaca")
    if v["katmanlar"]:
        h.append(st.p("Profilin bir bakışta", st.h2))
        h.append(_cubuklar([(f"{k['kod']} · {k['ad']}", k["ortalama"]) for k in v["katmanlar"]] +
                           [(f"K5 · {x['ad']}", x["puan"]) for x in v["k5"][:2]], renk=st.vurgu))
    if v["gucluler"]:
        h.append(st.p("Güçlü yönlerin", st.h2))
        for x in v["gucluler"]:
            h.append(KeepTogether([st.p(f"<b>{_e(x['ad'])}</b> · {x['seviye']} ({yuvarla(x.get('ham', x['puan']))})", st.h3),
                                   st.p(_e(x.get("yorum") or ozellik_anlami(x.get("kod"), "yuksek") or x.get("aciklama") or ""), st.govde),
                                   Spacer(1, 4)]))
    if v["gelisim"]:
        h.append(st.p("Daha az öne çıkan yönlerin", st.h2))
        h.append(st.p("Bunlar eksiklik değil; bir kısmı çalışma tarzın ya da ilgilerin, bir kısmı pratikle gelişebilen beceriler. "
                      "Bölüm seçerken bunları da hesaba kat.", st.not_))
        for x in v["gelisim"]:
            from app.core.rapor.yorum import DUSUK_AD
            parca = [st.p(f"<b>{_e(DUSUK_AD.get(x.get('kod'), x['ad']))}</b> ({yuvarla(x.get('ham', x['puan']))})", st.h3)]
            anlam = x.get("yorum") or ozellik_anlami(x.get("kod"), "dusuk")
            if anlam:
                parca.append(st.p(_e(anlam)))
            oneri = x.get("oneri") or ozellik_anlami(x.get("kod"), "dusuk", "yap")
            if oneri:
                parca.append(st.p("<i>Öneri:</i> " + _e(oneri)))
            parca.append(Spacer(1, 4))
            h.append(KeepTogether(parca))
    if v["bolumler"]:
        h.append(st.p("Sana en uygun 10 bölüm", st.h2))
        h.append(_tablo(st, ["#", "Bölüm", "Alan", "Uyum", "Neden?"],
                        [[str(b["sira"]), b["ad"], b.get("alan") or "", f"%{yuvarla(b['uyum'])}", ", ".join(b.get("ortusen") or [])]
                         for b in v["bolumler"]], [8 * mm, 52 * mm, 34 * mm, 14 * mm, 66 * mm]))
        h.append(st.p("Uyum, bölümün tüm bölümler içinde senin profiline yakınlığını gösterir (100 = en yakın, 0 = en uzak); başarı tahmini değildir.", st.kucuk))
    if v["hedef"]:
        hd = v["hedef"]
        il = hd.get("ilerleme") or {}
        h.append(st.p("Hedefin ve yol haritan", st.h2))
        h.append(st.p(f"<b>Hedef bölüm:</b> {_e(hd['ad'])}" + (f" · uyum %{yuvarla(hd['uyum'])}" if hd.get("uyum") is not None else "")
                      + (f" · önerilerinde {hd['sira']}. sırada" if hd.get("sira") else "")))
        if il.get("toplam"):
            h.append(st.p(f"<b>Yol haritası:</b> {il.get('tamamlanan', 0)} / {il['toplam']} adım tamamlandı"
                          + (f" · sıradaki adım: {_e(hd.get('siradaki'))}" if hd.get("siradaki") else "")))
        for x in hd.get("odak", [])[:3]:
            h.append(st.p(f"• <b>{_e(x['ad'])}:</b> {_e(x.get('neden') or '')}", st.govde))
    if v.get("hedef_kiyasi"):
        h += _hedef_kiyasi_bolumu(st, v["hedef_kiyasi"], "ogrenci")
    if netler:
        h += _net_bolumu(st, v, "ogrenci")
    h.append(st.p("SWOT analizin", st.h2))
    h.append(_swot(st, _swot_kitle(v, "ogrenci")))
    h.append(Spacer(1, 4))
    h += _yorum_bolumu(st, y, "ogrenci", ozet=False, baslik="Şimdi ne yapmalısın?")
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
    h.append(st.p(f"Bu rapor, çocuğunuzun (<b>{_e(v['kisi']['ad_soyad'])}</b>) Filizyol değerlendirmesinde verdiği cevaplara göre hazırlanmıştır. "
                  "Değerlendirme; değerler, kişilik ve çalışma tarzı, tercih ettiği iş ortamı ve ilgi alanlarını ölçer. "
                  "Bir başarı ya da zekâ testi <b>değildir</b>; doğru veya yanlış cevabı yoktur. Sonuçlar çocuğunuzun bugünkü "
                  "eğilimlerini gösterir ve zamanla değişebilir."))
    h += _bitmedi_notu(st, v)
    from app.core.rapor.yorum import ogrenci_yorumu   # [2026-10-12] yorum ve öneriler
    y = ogrenci_yorumu(v, "veli")
    h.append(Spacer(1, 4))
    h += _ozet_kutusu(st, y["ozet"], "Kısaca")
    if v["gucluler"]:
        h.append(st.p("Çocuğunuzun öne çıkan güçlü yönleri", st.h2))
        from app.core.rapor.yorum import ozellik_anlami
        destek_guclu = {x["ad"]: x["metin"] for x in y["guclu"]}
        for x in v["gucluler"][:5]:
            m = destek_guclu.get(x["ad"]) or ozellik_anlami(x.get("kod"), "yuksek", "veli")
            h.append(st.p(f"• <b>{_e(x['ad'])}</b> — {_e(x['seviye'])}" + (f". {_e(m)}" if m else "")))
    if y["destek"]:
        h.append(st.p("Gelişebileceği alanlar ve evde nasıl destek olabilirsiniz", st.h2))
        for x in y["destek"]:
            h.append(st.p(f"• <b>{_e(x['ad'])}</b> — {_e(x['metin'])}"))
    if v["bolumler"]:
        h.append(st.p("Çocuğunuza uygun görünen bölümler", st.h2))
        h.append(_tablo(st, ["#", "Bölüm", "Alan", "Uyum"],
                        [[str(b["sira"]), b["ad"], b.get("alan") or "", f"%{yuvarla(b['uyum'])}"] for b in v["bolumler"][:6]],
                        [10 * mm, 90 * mm, 52 * mm, 22 * mm]))
        h.append(st.p("Uyum, bölümün tüm bölümler içinde çocuğunuzun profiline yakınlığını gösterir (100 = en yakın, 0 = en uzak); başarı tahmini değildir.", st.kucuk))
        h.append(st.p("Uyum yüzdesi; çocuğunuzun profilinin bölümün gerektirdiği özelliklerle ne kadar örtüştüğünü gösterir, "
                      "başarı ya da kazanma olasılığı anlamına gelmez.", st.not_))
    if v["hedef"]:
        hd = v["hedef"]
        il = hd.get("ilerleme") or {}
        h.append(st.p("Hedef ve çalışma planı", st.h2))
        h.append(st.p(f"Çocuğunuzun seçtiği hedef bölüm: <b>{_e(hd['ad'])}</b>."
                      + (f" Kişisel yol haritasında {il.get('tamamlanan', 0)} / {il['toplam']} adımı tamamladı." if il.get("toplam") else "")))
    if v.get("hedef_kiyasi"):
        h += _hedef_kiyasi_bolumu(st, v["hedef_kiyasi"], "veli")
    if netler:
        h += _net_bolumu(st, v, "veli")
    h.append(st.p("Özet (SWOT)", st.h2))
    h.append(_swot(st, _swot_kitle(v, "veli")))
    h.append(st.p("Velilere öneriler", st.h2))
    h += _yap_kacin(st, (y["yap"] + VELI_ONERILERI[:2])[:6], y["kacin"], *_YORUM_BASLIK["veli"][:2])
    h.append(st.p("Rehber öğretmenle görüşmede sorabilecekleriniz", st.h2))
    for m in (y["gorusme"] or VELI_SORULARI) + ["Bir sonraki değerlendirme ne zaman yapılacak?"]:
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
        ["Güven puanı", f"{yuvarla(tur['guven'])} / 100" if tur.get("guven") is not None else "—",
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
    from app.core.rapor.yorum import ogrenci_yorumu   # [2026-10-12] rehber için yorum, öneriler ve görüşme gündemi
    y = ogrenci_yorumu(v, "rehber")
    h += _yorum_bolumu(st, y, "rehber")
    if v["katmanlar"]:
        h.append(st.p("Katman sonuçları", st.h2))
        h.append(_cubuklar([(f"{k['kod']} · {k['ad']}", k["ortalama"]) for k in v["katmanlar"]], renk=st.vurgu))
        for k in v["katmanlar"]:
            h.append(KeepTogether([st.p(f"{k['kod']} · {_e(k['ad'])} (ortalama {yuvarla(k['ortalama'])})", st.h3),
                                   _cubuklar([(x["ad"], x.get("ham", x["puan"])) for x in k["ozellikler"]]), Spacer(1, 5)]))
    if v["k5"]:
        h.append(st.p("İş türü tercihleri (K5)", st.h2))
        h.append(_cubuklar([(x["ad"], x["puan"]) for x in v["k5"]]))
    if v["bolumler"]:
        h.append(st.p("Bölüm önerileri (ilk 10)", st.h2))
        h.append(_tablo(st, ["#", "Bölüm", "Alan", "Uyum", "Örtüşen özellikler", "Dikkat"],
                        [[str(b["sira"]), b["ad"], b.get("alan") or "", f"%{yuvarla(b['uyum'])}", ", ".join(b.get("ortusen") or []),
                          b.get("dikkat") or ""] for b in v["bolumler"]],
                        [7 * mm, 40 * mm, 27 * mm, 12 * mm, 45 * mm, 43 * mm], kucuk=True))
        h.append(st.p("Uyum, bölümün tüm bölümler içinde öğrencinin profiline yakınlığını gösterir (100 = en yakın, 0 = en uzak); başarı tahmini değildir.", st.kucuk))
    if v["hedef"]:
        hd = v["hedef"]
        il = hd.get("ilerleme") or {}
        h.append(st.p("Hedef bölüm ve koçluk", st.h2))
        h.append(st.p(f"<b>{_e(hd['ad'])}</b> · seçim: {_tarih(hd.get('secim'))}"
                      + (f" · uyum %{yuvarla(hd['uyum'])}" if hd.get("uyum") is not None else "")
                      + (f" · öneri sırası {hd['sira']}" if hd.get("sira") else " · ilk 10 öneri dışında")
                      + (f" · yol haritası {il.get('tamamlanan', 0)}/{il['toplam']}" if il.get("toplam") else "")))
        if hd.get("odak"):
            h.append(_tablo(st, ["Odak alanı", "Neden önemli"], [[x["ad"], x.get("neden") or ""] for x in hd["odak"]],
                            [40 * mm, 134 * mm], kucuk=True))
    if v.get("hedef_kiyasi"):
        h += _hedef_kiyasi_bolumu(st, v["hedef_kiyasi"], "yonetici")
    elif v.get("hedef_kiyasi_notu"):
        h += [st.p(_KIYAS_BASLIK["yonetici"], st.h2), st.p(_e(v["hedef_kiyasi_notu"]), st.not_)]
    if netler:
        h += _net_bolumu(st, v, "yonetici")
    h.append(st.p("SWOT analizi", st.h2))
    h.append(_swot(st, v["swot"]))
    if v.get("uyum_aciklama"):   # [2026-10-17] yalnızca rehber / okul yetkilisi raporu
        h += _uyum_aciklama_eki(st, v["uyum_aciklama"])
    doc.build(h)
    return tampon.getvalue()



# ============================================================================= [2026-10-17] hedef bölüm kıyası (öğrenci, veli, yönetici)
_KIYAS_SINIF = {"uyumlu": "uyumlu", "fazla": "beklenenden fazla", "eksik": "beklenenden az",
                "belirgin_fazla": "belirgin fazla", "belirgin_eksik": "belirgin az"}
_KIYAS_BASLIK = {"ogrenci": "Hedef bölümünle kıyas", "veli": "Hedef bölüm ile diğer bölümlerin kıyası", "yonetici": "Hedef bölüm kıyası"}
_KIYAS_NOT = {
    "ogrenci": ("Puan farkı, iki bölümün sana yakınlık puanları arasındaki farktır. Özellikler bu farkın en çok nereden geldiğini "
                "gösterir: “geride bırakan” özellikte o bölüm senin profiline hedefinden daha yakın, “öne çıkaran” özellikte "
                "hedefin daha yakın. Parantez içi, senin düzeyinin o bölümün beklediğine göre durumudur. Bu özelliklerdeki gelişim "
                "adımları için koçluk ekranına bakabilirsin."),
    "veli": ("Puan farkı, iki bölümün çocuğunuzun profiline yakınlık puanları arasındaki farktır. Özellikler bu farkın en çok "
             "nereden geldiğini gösterir: “geride bırakan” özellikte o bölüm çocuğunuzun profiline hedefinden daha yakın, "
             "“öne çıkaran” özellikte hedef bölüm daha yakın. Parantez içi, çocuğunuzun düzeyinin o bölümün beklediğine göre "
             "durumudur. Başarı ya da kazanma olasılığı anlamına gelmez."),
    "yonetici": ("Puan farkı = hedefin uyumu − bölümün uyumu. Özellik etkisi = hedefteki katkı − bölümdeki katkı ('bu özellik "
                 "olmasaydı' katkılarının farkı; gösterilen puanla aynı hesap). Geride bırakan: farkı hedef aleyhine açan, "
                 "öne çıkaran: hedef lehine açan özellikler. Parantez içi: öğrencinin düzeyinin bölüm beklentisine göre fark sınıfı."),
}


def _kiyas_sinif(x: dict, anahtar: str, kitle: str) -> str:
    sinif = x.get(anahtar) or "uyumlu"
    if (x.get("kod") or "").startswith("D") and sinif != "uyumlu":   # değerler: önem dili
        kim = {"ogrenci": "senin için", "veli": "çocuğunuz için", "yonetici": "öğrenci için"}[kitle]
        derece = "çok " if sinif.startswith("belirgin") else ""
        return f"{kim} {derece}daha {'önemli' if sinif.endswith('fazla') else 'az önemli'}"
    return _KIYAS_SINIF.get(sinif, sinif)


def _kiyas_ozellikleri(xs: list, kitle: str, hedefli: bool) -> str:
    if not xs:
        return "—"
    parcalar = []
    for x in xs:
        if hedefli:
            parcalar.append(f"<b>{_e(x['ad'])}</b> (hedefte {_kiyas_sinif(x, 'hedef_sinif', kitle)}, "
                            f"burada {_kiyas_sinif(x, 'bolum_sinif', kitle)})")
        else:
            parcalar.append(f"<b>{_e(x['ad'])}</b> ({_kiyas_sinif(x, 'bolum_sinif', kitle)})")
    return "<br/>".join(parcalar)


def _hedef_kiyasi_bolumu(st, k: dict, kitle: str) -> list:
    hs = ParagraphStyle("hk2", parent=st.hucre, fontSize=7.6, leading=9.8)
    toplam = k.get("bolum_sayisi") or 301
    h = [st.p(_KIYAS_BASLIK[kitle], st.h2)]
    hd = k.get("hedef")
    satirlar = k.get("satirlar") or []
    if hd is None:
        h.append(st.p("<b>Not:</b> Hedef bölüm seçilmediği için kıyas yapılamadı. Aşağıda seçilen bölümlerin sonuçları ve puanı en çok "
                      "etkileyen özellikler yer alıyor; hedef bölüm seçildiğinde bölümler hedefe göre kıyaslanır.", st.not_))
        veri = [[Paragraph(f"{_e(s['bolum'])}<br/>%{yuvarla(s['uyum'])} · {s['sira']}. sıra", hs),
                 Paragraph(_kiyas_ozellikleri(s.get("yukselten"), kitle, False), hs),
                 Paragraph(_kiyas_ozellikleri(s.get("dusuren"), kitle, False), hs)] for s in satirlar]
        if veri:
            h.append(_tablo(st, ["Bölüm", "Puanı yükselten özellikler", "Puanı düşüren özellikler"], veri,
                            [50 * mm, 62 * mm, 62 * mm], kucuk=True))
    else:
        h.append(st.p(f"<b>Hedef bölüm:</b> {_e(hd['bolum'])} · uyum %{yuvarla(hd['uyum'])} · {toplam} bölüm içinde {hd['sira']}. sırada"))
        if not satirlar:
            h.append(st.p("Kıyas için hedefin dışında bölüm seçilmedi.", st.not_))
        veri = []
        for s in satirlar:
            f = s.get("fark") or 0
            fark = "eşit" if abs(f) < 0.5 else (f"hedef {yuvarla(abs(f))} puan geride" if f < 0 else f"hedef {yuvarla(f)} puan önde")
            veri.append([Paragraph(f"{_e(s['bolum'])}<br/>%{yuvarla(s['uyum'])} · {s['sira']}. sıra", hs), Paragraph(fark, hs),
                         Paragraph(_kiyas_ozellikleri(s.get("geride_birakan"), kitle, True), hs),
                         Paragraph(_kiyas_ozellikleri(s.get("one_cikaran"), kitle, True), hs)])
        if veri:
            h.append(_tablo(st, ["Bölüm", "Puan farkı", "Hedefi geride bırakan", "Hedefi öne çıkaran"], veri,
                            [40 * mm, 22 * mm, 56 * mm, 56 * mm], kucuk=True))
        h.append(st.p(_KIYAS_NOT[kitle], st.kucuk))
    if k.get("kirpildi"):
        h.append(st.p(f"En çok {k.get('sinir', 6)} bölüm (hedef dahil) kıyaslanabilir; fazlası rapora alınmadı.", st.kucuk))
    return h


# ============================================================================= [2026-10-17] uyum açıklama eki (yalnızca yönetici raporu)
_FARK_ZEMIN = {"yesil": colors.HexColor("#DCEFD6"), "turuncu": colors.HexColor("#FBE3C2"), "kirmizi": colors.HexColor("#F6CFCB")}
_SINIF_AD = {"uyumlu": "uyumlu", "fazla": "fazla", "eksik": "az", "belirgin_fazla": "belirgin fazla", "belirgin_eksik": "belirgin az"}


def _isaretli(x, o=0) -> str:
    if x is None:
        return "—"
    x = round(float(x), o)
    if x == 0:
        return "0"
    return ("+" if x > 0 else "") + f"{x:.{o}f}".replace(".", ",")


def _uyum_aciklama_eki(st, ek: dict) -> list:
    """Rehber için: neden bu bölümler üstte / altta? Özellik × bölüm fark matrisi, katkılar ve soru–cevap dökümü."""
    from reportlab.platypus import PageBreak
    m = ek.get("matris")
    h = [PageBreak(), st.p("Ek: Uyum açıklaması", st.h2),
         st.p("Bu ek yalnızca okul yetkilisi / rehberlik içindir; öğrenci ve veli raporlarında yer almaz. Uyum puanı göreli: "
              "Tüm bölümler içinde öğrencinin profiline yakınlık (100 = en yakın). <b>Fark</b> = öğrenci − bölüm beklentisi "
              "(katman içi ölçek): |fark| &lt; 5 uyumlu (yeşil), 5–15 fazla / az (turuncu), 15+ belirgin (kırmızı). "
              "<b>Katkı</b> = bu özellik hesaba katılmasaydı uyum puanı ne kadar değişirdi (artı yükseltiyor, eksi düşürüyor). "
              "Katkı da göreli bir ölçüdür: bir özellikte fark olsa bile öğrenci o özellikte bu bölüme diğer bölümlerin çoğundan "
              "daha yakınsa katkı artı çıkabilir.",
              st.kucuk), Spacer(1, 4)]
    if m and m.get("bolumler"):
        bolumler = m["bolumler"]
        hs = ParagraphStyle("ue", parent=st.hucre, fontSize=6.8, leading=8.4)
        hb = ParagraphStyle("ueb", parent=hs, fontName="Filiz-B")
        n = len(bolumler)
        b_gen = min(22 * mm, (174 * mm - 58 * mm) / max(1, n))
        bas = [Paragraph("<b>Özellik</b>", hs), Paragraph("<b>Öğr.</b>", hs)] + [
            Paragraph(f"<b>{b['sira']}. {_e((b['bolum'] or '')[:34])}</b><br/>%{yuvarla(b['uyum'])}{' · hedef' if b.get('hedef') else ''}", hs)
            for b in bolumler]
        veri, stil = [bas], [("BACKGROUND", (0, 0), (-1, 0), ACIK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                             ("LINEBELOW", (0, 0), (-1, -1), 0.25, CIZGI), ("ALIGN", (1, 1), (-1, -1), "CENTER")]
        onceki = None
        for j, oz in enumerate(m["ozellikler"]):
            if oz.get("katman") != onceki:
                onceki = oz.get("katman")
                veri.append([Paragraph(f"<b>{_e(onceki or '')}</b>", hb)] + [""] * (n + 1))
                stil += [("SPAN", (0, len(veri) - 1), (-1, len(veri) - 1)), ("BACKGROUND", (0, len(veri) - 1), (-1, len(veri) - 1), colors.HexColor("#FCFAF6"))]
            satir = [Paragraph(f"{_e(oz['kod'])} {_e(oz['ad'])}", hs), Paragraph(str(yuvarla(oz["ogrenci"])), hb)]
            for i, b in enumerate(bolumler):
                c = b["hucreler"][j]
                satir.append(Paragraph(_isaretli(c["fark"]), hs))
                stil.append(("BACKGROUND", (2 + i, len(veri)), (2 + i, len(veri)), _FARK_ZEMIN[c["renk"]]))
            veri.append(satir)
        t = Table(veri, colWidths=[46 * mm, 12 * mm] + [b_gen] * n, repeatRows=1)
        t.setStyle(TableStyle(stil))
        h += [st.p("Özellik × bölüm farkı", st.h3), t, Spacer(1, 6), st.p("Puanı en çok yükselten / düşüren özellikler", st.h3)]
        oz = m["ozellikler"]
        satirlar = []
        for b in bolumler:
            def liste(xs, b=b):
                return "; ".join(f"{oz[x['j']]['ad']} ({_isaretli(x['katki'], 1)}, {_SINIF_AD[b['hucreler'][x['j']]['sinif']]})" for x in xs) or "—"
            k5 = f" · K5 {_isaretli(b['k5_katkisi'], 1)}" if b.get("k5_katkisi") is not None else ""
            satirlar.append([f"{b['sira']}. {b['bolum']} (%{yuvarla(b['uyum'])}{k5})", liste(b["yukselten"]), liste(b["dusuren"])])
        h.append(_tablo(st, ["Bölüm", "Yükselten", "Düşüren"], satirlar, [44 * mm, 65 * mm, 65 * mm], kucuk=True))
    cevaplar = ek.get("cevaplar") or []
    if cevaplar:
        h += [Spacer(1, 6), st.p(f"Soru–cevap dökümü ({ek.get('tur_no')}. değerlendirme, {len(cevaplar)} cevap)", st.h3),
              st.p("Her cevabın hangi özelliğe kaç puan kattığı (0–100) gösterilir; dikkat kontrolü soruları puanlamaya girmez.", st.kucuk)]
        satirlar = []
        for c in cevaplar:
            secilen = next((x["metin"] for x in c["secenekler"] if x["secildi"]), "—")
            en_az = next((x["metin"] for x in c["secenekler"] if x["en_az"]), None)
            cevap = secilen + (f" · en az: {en_az}" if en_az else "")
            if c.get("kontrol"):
                katki = "Dikkat kontrolü: " + ("doğru" if c["kontrol"]["dogru"] else "yanlış")
            else:
                katki = ", ".join(f"{k['kod']} {yuvarla(k['puan'])}" for k in c["katkilar"]) or "—"
            satirlar.append([str(c["sira"]), c["katman"], c["soru"], cevap, katki])
        h.append(_tablo(st, ["#", "Katman", "Soru", "Cevap", "Katkı"], satirlar,
                        [7 * mm, 14 * mm, 68 * mm, 50 * mm, 35 * mm], kucuk=True))
    return h


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
    durum = {"tamamlandi": "Tamamlandı", "devam": "Devam ediyor", "k5_bekliyor": "İş türü soruları bekliyor",
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
    from app.core.rapor.yorum import ogrenci_yorumu   # [2026-10-12] kişilik ayrıntısı içermeyen öneriler
    y = ogrenci_yorumu(v, "ogretmen")
    y["yap"] = (y["yap"] + SINIF_OGRETMENI_ONERILERI)[:5]
    h += _yorum_bolumu(st, y, "ogretmen", baslik="Sınıf öğretmenine öneriler")
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
        if n is None:   # [2026-10-10] KVKK küçük grup
            return GIZLI_METIN
        return f"{n} (%{yuvarla(100 * n / toplam) if toplam else 0})"

    def g(x, k):   # gizlenen kırılım hücresi
        return "—" if x.get(k) is None else str(x[k])

    def tm(x):
        return "—" if x.get("tamamlayan") is None else f"%{yuvarla(100 * x['tamamlayan'] / x['ogrenci']) if x['ogrenci'] else 0}"
    kg = v.get("kucuk_grup") or {}
    sayi_st = ParagraphStyle("kpi", fontName="Filiz-B", fontSize=14, leading=18, textColor=st.vurgu)
    kpi = Table([[[Paragraph(a, st.kucuk), Paragraph(str(b), sayi_st)] for a, b in
                  [("Öğrenci", toplam), ("Giriş yapan", oran(o.get("giris_yapan", 0))), ("Teste başlayan", oran(o.get("teste_baslayan", 0))),
                   ("Tamamlayan", oran(o.get("tamamlayan", 0))), ("Hedef seçen", oran(o.get("hedef_secen", 0)))]]],
                colWidths=[34.8 * mm] * 5)
    kpi.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACIK), ("INNERGRID", (0, 0), (-1, -1), 2, colors.white),
                             ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    h += [kpi, Spacer(1, 6)]
    # [2026-10-12] Yönetici özeti ve öncelikli işler (kim / ne zaman)
    from app.core.rapor.yorum import okul_yorumu
    y = okul_yorumu(v)
    h += _ozet_kutusu(st, y["ozet"], "Yönetici özeti")
    if y.get("isler"):
        h.append(st.p("Öncelikli işler", st.h2))
        h.append(_tablo(st, ["#", "Ne yapılmalı?", "Kim?", "Ne zaman?"],
                        [[str(i), x["metin"], x["kim"], x["ne_zaman"]] for i, x in enumerate(y["isler"], 1)],
                        [8 * mm, 104 * mm, 38 * mm, 24 * mm]))
        h.append(Spacer(1, 6))
    h.append(st.p("Değerlendirme durumu", st.h2))
    if o.get("kapsam_gizli"):
        h.append(st.p(f"Bu kapsamda {GIZLI_METIN} olduğundan durum dağılımı gösterilmez; öğrenci listesine bakın.", st.not_))
    else:
        h.append(_cubuklar([(d["etiket"], d["sayi"]) for d in o.get("durumlar", [])], maks=max(1, toplam), renk=st.vurgu))
    subeler = [x for x in o.get("subeler", []) if x["sube"]]
    if subeler and not sube_mi:
        h.append(st.p("Şubelere göre", st.h2))
        h.append(_tablo(st, ["Şube", "Sınıf öğretmeni", "Öğrenci", "Giriş yapan", "Tamamlayan", "Tamamlama"],
                        [[x["etiket"], (x.get("ogretmen") or {}).get("ad") or "—", str(x["ogrenci"]), g(x, "giris_yapan"),
                          g(x, "tamamlayan"), tm(x)] for x in subeler],
                        [22 * mm, 50 * mm, 22 * mm, 28 * mm, 28 * mm, 24 * mm]))
    if o.get("siniflar") and not ks.get("sinif"):
        h.append(st.p("Sınıflara göre", st.h2))
        h.append(_tablo(st, ["Sınıf", "Öğrenci", "Giriş yapan", "Devam eden", "Tamamlayan", "Tamamlama"],
                        [[s["sinif"], str(s["ogrenci"]), g(s, "giris_yapan"), g(s, "devam"), g(s, "tamamlayan"), tm(s)]
                         for s in o["siniflar"]],
                        [40 * mm, 24 * mm, 28 * mm, 28 * mm, 28 * mm, 26 * mm]))
    if v["alanlar"]:
        h.append(st.p("Öğrencilerin en uyumlu çıktığı alanlar (1. öneriye göre)", st.h2))
        h.append(_cubuklar([(a["alan"] + (f" ({GIZLI_METIN})" if a["sayi"] is None else ""), a["sayi"]) for a in v["alanlar"]],
                           maks=max([a["sayi"] for a in v["alanlar"] if a["sayi"] is not None] or [1]), renk=st.vurgu))
    if o.get("en_cok_onerilen") or o.get("en_cok_hedeflenen"):
        h.append(st.p("En çok önerilen ve hedeflenen bölümler", st.h2))
        sol = o.get("en_cok_onerilen") or []
        sag = o.get("en_cok_hedeflenen") or []
        sy = lambda x: f" ({x['sayi'] if x['sayi'] is not None else GIZLI_METIN})"  # noqa: E731
        satir = [[(sol[i]["bolum"] + sy(sol[i])) if i < len(sol) else "",
                  (sag[i]["bolum"] + sy(sag[i])) if i < len(sag) else ""] for i in range(max(len(sol), len(sag)))]
        h.append(_tablo(st, ["1. öneri olarak", "Hedef olarak"], satir, [87 * mm, 87 * mm]))
    if v["katman_ort"] and v.get("okul_katman_ort"):
        okul_ort = {k["kod"]: yuvarla(k["ortalama"]) for k in v["okul_katman_ort"]}

        def katman_satiri(k):   # [2026-10-14] fark, GÖSTERİLEN yuvarlanmış değerlerden; okul değeri yoksa "—"
            g, o = yuvarla(k["ortalama"]), okul_ort.get(k["kod"])
            return [f"{k['kod']} · {k['ad']}", str(g), "—" if o is None else str(o), "—" if o is None else f"{g - o:+d}"]
        h.append(st.p("Katman ortalamaları — okul ortalamasıyla karşılaştırma", st.h2))
        h.append(_tablo(st, ["Katman", "Şube" if sube_mi else "Sınıf düzeyi", "Okul", "Fark"],
                        [katman_satiri(k) for k in v["katman_ort"]],
                        [86 * mm, 30 * mm, 30 * mm, 28 * mm]))
        h.append(st.p("Fark ±5 puandan büyükse grup okul ortalamasından belirgin biçimde ayrışıyor demektir.", st.not_))
    elif v["katman_ort"]:
        h.append(st.p("Katman ortalamaları (testi tamamlayanlar; güven eşiğinin altındakiler hariç)", st.h2))
        h.append(_cubuklar([(f"{k['kod']} · {k['ad']}", k["ortalama"]) for k in v["katman_ort"]], renk=st.vurgu))
    elif kg.get("profil_gizli"):
        h.append(st.p("Katman ortalamaları ve ortak güçlü yönler", st.h2))
        h.append(st.p(f"Testi tamamlayan {GIZLI_METIN} olduğundan profil ortalamaları gösterilmez.", st.not_))
    if v["ortak_guclu"]:
        satir = [[f"{a['ad']} ({yuvarla(a['ortalama'])})", f"{b['ad']} ({yuvarla(b['ortalama'])})"] for a, b in zip(v["ortak_guclu"], v["ortak_gelisim"])]
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
                      + (f"Son TYT ortalaması <b>{_sayi(tyt[0])}</b> ({tyt[1]} öğrenci)" if tyt[0] is not None
                         else f"Son TYT ortalaması: {GIZLI_METIN}" if tyt[1] else "")
                      + (f" · son AYT ortalaması <b>{_sayi(ayt[0])}</b> ({ayt[1]} öğrenci)" if ayt[0] is not None
                         else f" · son AYT ortalaması: {GIZLI_METIN}" if ayt[1] else "") + ".", st.govde))
        if nt.get("dersler"):
            h.append(_tablo(st, ["Ders", "Soru", "Son deneme ortalaması", "Öğrenci", "Doluluk"],
                            [[d["ad"], str(d["soru"]), _sayi(d["ort"]) if d["ort"] is not None else GIZLI_METIN, str(d["n"]),
                              f"%{yuvarla(100 * d['ort'] / d['soru'])}" if d["ort"] is not None else "—"] for d in nt["dersler"]],
                            [70 * mm, 18 * mm, 40 * mm, 22 * mm, 24 * mm], kucuk=True))
            h.append(st.p("Doluluk oranı düşük dersler, ders öğretmenleriyle birlikte planlanacak destek çalışmaları için ipucu verir.", st.not_))
    elif netler:
        h.append(st.p("Deneme ve net özeti", st.h2))
        h.append(st.p("Bu kapsamda henüz Net Takibi'ne deneme sonucu giren öğrenci yok.", st.not_))
    if y.get("guclu") or y.get("destek") or y.get("kacin"):
        h.append(st.p("Sonuçları nasıl kullanmalı?", st.h2))
        h += _ad_metin_listesi(st, "Ortak güçlü yönlerden yararlanmak için", y.get("guclu") or [])
        h += _ad_metin_listesi(st, "Ortak gelişim alanları için etkinlik önerisi", y.get("destek") or [])
        h.append(st.p("Yapılmaması gerekenler", st.h3))
        for m in y.get("kacin") or []:
            h.append(st.p("• " + _e(m), ParagraphStyle("okm", parent=st.govde, leftIndent=8, spaceAfter=1.5)))
        for n in y.get("notlar") or []:
            h.append(st.p(_e(n), st.not_))
    if kg.get("uygulandi"):
        h.append(st.p(DIPNOT, st.not_))
    if v["gecersiz"]:
        h.append(st.p(f"Güvenilirlik: {v['gecersiz']} öğrencinin son değerlendirmesi güven eşiğinin altında; yeniden değerlendirme önerilir.", st.govde))
    if v["ogrenciler"]:
        h.append(st.p("Öğrenci listesi", st.h2))
        if sube_mi and netler:
            h.append(_tablo(st, ["No", "Ad soyad", "Durum", "1. öneri", "Hedef", "Güven", "Son TYT", "Son AYT"],
                            [[x.get("no") or "", x["ad_soyad"] + (" (test)" if x["test"] else ""), x["durum"], x["ilk_bolum"], x["hedef"],
                              f"{yuvarla(x['guven'])}" if x["guven"] is not None else "", _sayi(x.get("son_tyt")) if x.get("son_tyt") is not None else "",
                              _sayi(x.get("son_ayt")) if x.get("son_ayt") is not None else ""] for x in v["ogrenciler"]],
                            [10 * mm, 31 * mm, 23 * mm, 31 * mm, 31 * mm, 16 * mm, 16 * mm, 16 * mm], kucuk=True))
        elif sube_mi:
            h.append(_tablo(st, ["No", "Ad soyad", "Durum", "1. öneri", "Hedef", "Güven"],
                            [[x.get("no") or "", x["ad_soyad"] + (" (test)" if x["test"] else ""), x["durum"], x["ilk_bolum"], x["hedef"],
                              f"{yuvarla(x['guven'])}" if x["guven"] is not None else ""] for x in v["ogrenciler"]],
                            [12 * mm, 38 * mm, 28 * mm, 40 * mm, 40 * mm, 16 * mm], kucuk=True))
        else:
            h.append(_tablo(st, ["Ad soyad", "Sınıf", "Durum", "1. öneri", "Hedef", "Güven"],
                            [[x["ad_soyad"] + (" (test)" if x["test"] else ""), x["sinif"], x["durum"], x["ilk_bolum"], x["hedef"],
                              f"{yuvarla(x['guven'])}" if x["guven"] is not None else ""] for x in v["ogrenciler"]],
                            [36 * mm, 18 * mm, 29 * mm, 37 * mm, 37 * mm, 17 * mm], kucuk=True))
    doc.build(h)
    return tampon.getvalue()


# ============================================================================= [2026-10-10] yönetici özeti (Rapor Merkezi → Tek Bakışta)
# Durum renkleri (frontend istatistik/palet.js DURUM ile aynı anlam): iyi yeşil, uyarı sarı, kritik kırmızı — açık zeminli.
_TON_ZEMIN = {"iyi": colors.HexColor("#D9F0D9"), "iyi_hafif": colors.HexColor("#EDF7ED"),
              "uyari": colors.HexColor("#FDF0CF"), "kotu": colors.HexColor("#F7D9D9")}
_SEVIYE_ZEMIN = {"yuksek": colors.HexColor("#F7D9D9"), "orta": colors.HexColor("#FBE3D7"), "dusuk": colors.HexColor("#FDF0CF")}
_SEVIYE_YAZI = {"yuksek": colors.HexColor("#A52A2A"), "orta": colors.HexColor("#A3502A"), "dusuk": colors.HexColor("#7A5C00")}
_BULGU = {"dikkat": ("!", colors.HexColor("#B32D2D"), colors.HexColor("#FBEAEA")),
          "olumlu": ("+", colors.HexColor("#0A7A0A"), colors.HexColor("#EAF6EA")),
          "bilgi": ("i", colors.HexColor("#2A5FA8"), colors.HexColor("#EAF1FA"))}


def _yuzde_m(x) -> str:
    return "—" if x is None else f"%{yuvarla(x)}"


def _isaret(x) -> str:
    if x is None:
        return "—"
    x = yuvarla(x, 2)
    return ("+" if x > 0 else "") + _sayi(x)


def yonetici_ozeti_pdf(v: dict, okul: dict) -> bytes:
    """Tek Bakışta ekranının PDF'i: bulgular, KPI, kritik öğrenciler, şube karşılaştırması, akademik sıralama, hedef–uyum.
    Okul içinde kalacak isimli rapordur (altbilgide "Kişisel veri içerir" uyarısı)."""
    tarih = datetime.now(TR)
    doc, tampon, st = _belge("Yönetici Özeti", okul, tarih)
    f, k, oo = v["filtre"], v["kpi"], v["okul_ort"]
    h = [st.p("Yönetici Özeti", st.baslik),
         st.p(f"{_e(okul.get('ad'))} · {_e(f['etiket'])} · {_tarih(tarih)} · test hesapları hariç", st.alt)]

    # ---- öne çıkan bulgular
    if v.get("bulgular"):
        h.append(st.p("Öne çıkan bulgular", st.h2))
        satir, stil = [], [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LINEBELOW", (0, 0), (-1, -1), 2, colors.white)]
        for i, b in enumerate(v["bulgular"]):
            ik, renk, zemin = _BULGU[b["tur"]]
            satir.append([Paragraph(f"<b>{ik}</b>", ParagraphStyle("bi", parent=st.hucre_b, textColor=colors.white, alignment=1, fontSize=10)),
                          Paragraph(_e(b["metin"]), st.hucre)])
            stil += [("BACKGROUND", (0, i), (0, i), renk), ("BACKGROUND", (1, i), (1, i), zemin)]
        t = Table(satir, colWidths=[8 * mm, 166 * mm])
        t.setStyle(TableStyle(stil))
        h += [t, st.p("! dikkat gerektiren · + olumlu · i bilgi", st.kucuk)]

    # ---- KPI şeridi
    sayi_st = ParagraphStyle("kpi", fontName="Filiz-B", fontSize=14, leading=18, textColor=st.vurgu)
    kpiler = [("Öğrenci", str(k["ogrenci"])), ("Tamamlama", _yuzde_m(k["tamamlama"]))]
    if k.get("tyt_kaynak"):
        kpiler.append(("Ort. son TYT neti", _sayi(k["tyt"])))
    kpiler.append(("Kritik öğrenci", str(k["kritik"])) if v.get("rehberlik") else ("Takip gereken", str(k["takip"])))
    if k.get("kocluk_aktif") is not None:
        kpiler.append(("Koçlukta aktif", str(k["kocluk_aktif"])))
    kpiler.append(("Hedef seçen", _yuzde_m(k["hedef"])))
    gen = 174 * mm / len(kpiler)
    kpi = Table([[[Paragraph(a, st.kucuk), Paragraph(b, sayi_st)] for a, b in kpiler]], colWidths=[gen] * len(kpiler))
    kpi.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACIK), ("INNERGRID", (0, 0), (-1, -1), 2, colors.white),
                             ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    notlar = (["Kritik: erken uyarıda yüksek seviyedeki öğrenci."] if v.get("rehberlik") else [])
    notlar += (["Koçlukta aktif: son 30 günde gelişim adımı ya da haftalık görev tamamlayan."] if k.get("kocluk_aktif") is not None else [])
    notlar += (["Ort. son TYT neti: akademik sıralamadaki kaynağa göre."] if k.get("tyt_kaynak") else [])
    h += [Spacer(1, 6), kpi] + ([st.p(" · ".join(notlar), st.kucuk)] if notlar else [])

    # ---- kritik öğrenciler
    kr = v["kritik"]
    h.append(st.p(kr["baslik"], st.h2))
    if not kr["ogrenciler"]:
        h.append(st.p("Şu anda takip gerektiren öğrenci yok.", st.not_))
    else:
        satirlar, stil = [], []
        for i, s in enumerate(kr["ogrenciler"], 1):
            gor = (f"Planlandı: {_tarih(datetime.fromisoformat(s['yaklasan_gorusme']))}" if s.get("yaklasan_gorusme")
                   else _tarih(datetime.fromisoformat(s["son_gorusme"]).date()) if s.get("son_gorusme") else "Görüşme yok")
            satirlar.append([s["ad_soyad"], s["sube"],
                             Paragraph(f"<b>{s['seviye_ad']}</b>", ParagraphStyle("sv", parent=st.hucre, textColor=_SEVIYE_YAZI[s["seviye"]])),
                             "; ".join(n["ad"] for n in s["nedenler"]),
                             _tarih(datetime.fromisoformat(s["son_giris"])) if s.get("son_giris") else "—"]
                            + ([gor] if v.get("rehberlik") else []))
            stil.append(("BACKGROUND", (2, i), (2, i), _SEVIYE_ZEMIN[s["seviye"]]))
        bas = ["Ad soyad", "Şube", "Seviye", "Nedenler", "Son giriş"] + (["Son görüşme"] if v.get("rehberlik") else [])
        gen = [36 * mm, 15 * mm, 16 * mm, 57 * mm, 22 * mm, 28 * mm] if v.get("rehberlik") else [40 * mm, 16 * mm, 18 * mm, 74 * mm, 26 * mm]
        t = _tablo(st, bas, satirlar, gen, zebra=False, kucuk=True)
        t.setStyle(TableStyle(stil))
        h.append(t)
        if kr["toplam"] > len(kr["ogrenciler"]):
            h.append(st.p(f"İlk {len(kr['ogrenciler'])} öğrenci gösteriliyor (toplam {kr['toplam']}); tamamı Rehberlik sekmesinde.", st.not_))

    # ---- şube karşılaştırması
    sb = v.get("subeler") or []
    if sb:
        tyt_var = any(s.get("tyt") is not None for s in sb)
        sut = [("tamamlama", "Tamamlama", _yuzde_m), ("aktif7", "7 gün aktif", _yuzde_m)] \
            + ([("tyt", "Ort. TYT", _sayi)] if tyt_var else []) + [("hedef", "Hedef seçen", _yuzde_m), ("kritik", "Kritik", str)]
        satirlar = [[s["etiket"], str(s["ogrenci"])] + [bc(s[kk]) if s.get(kk) is not None else "—" for kk, _, bc in sut] for s in sb]
        satirlar.append(["Okul ortalaması", str(oo["ogrenci"])] + [bc(oo[kk]) if oo.get(kk) is not None else "—" for kk, _, bc in sut])
        gen = [30 * mm, 18 * mm] + [126 * mm / len(sut)] * len(sut)
        t = _tablo(st, ["Şube", "Öğrenci"] + [a for _, a, _ in sut], satirlar, gen, zebra=False, kucuk=True)
        stil = [("BACKGROUND", (0, len(satirlar)), (-1, len(satirlar)), ACIK), ("LINEABOVE", (0, len(satirlar)), (-1, len(satirlar)), 0.6, GRI)]
        for i, s in enumerate(sb, 1):
            for j, (kk, _, _) in enumerate(sut, 2):
                z = _TON_ZEMIN.get(s["tonlar"].get(kk))
                if z is not None:
                    stil.append(("BACKGROUND", (j, i), (j, i), z))
                if s["vurgu"].get(kk):
                    stil.append(("BOX", (j, i), (j, i), 1, YESIL if s["vurgu"][kk] == "en_iyi" else KIRMIZI))
        t.setStyle(TableStyle(stil))
        h += [st.p("Şube karşılaştırması", st.h2), t,
              st.p("Hücre renkleri okul ortalamasına göredir: yeşil daha iyi, sarı biraz geride, kırmızı belirgin geride (≥15 puan; "
                   "TYT'de ortalamanın %15'i). Çerçeveli hücreler sütunun en iyi (yeşil) ve en geride (kırmızı) şubesidir. "
                   "Kritik sütununda az olan iyidir.", st.not_)]

    # ---- akademik sıralama
    ak = (v.get("akademik") or {}).get("oturumlar") or {}
    for ot, a in ak.items():
        bolum = [st.p(f"Akademik sıralama · {ot}", st.h2), st.p(_e(a["kaynak_metni"]) + f" · okul ortalaması <b>{_sayi(a['okul_ort'])}</b> net", st.kucuk), Spacer(1, 3)]
        sat = lambda l: [[str(i), x["ad_soyad"], x["sube"], _sayi(x["net"]), _isaret(x["fark"])] for i, x in enumerate(l, 1)]  # noqa: E731
        bas = ["#", "Ad soyad", "Şube", "Net", "Okula fark"]
        gen = [7 * mm, 32 * mm, 14 * mm, 14 * mm, 18 * mm]
        sol = _tablo(st, bas, sat(a["en_yuksek"]), gen, kucuk=True) if a["en_yuksek"] else st.p("—", st.kucuk)
        sag = _tablo(st, bas, sat(a["en_dusuk"]), gen, kucuk=True) if a["en_dusuk"] else st.p(
            "Katılımcıların tamamı soldaki listede." if a["en_yuksek"] else "—", st.not_)
        ikili = Table([[st.p("En yüksek 10", st.h3), st.p("En düşük 10", st.h3)], [sol, sag]], colWidths=[87 * mm, 87 * mm])
        ikili.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        bolum.append(ikili)
        if a["yukselen"] or a["dusen"]:
            dsat = lambda l: [[x["ad_soyad"], x["sube"], f"{_sayi(x['onceki'])} → {_sayi(x['son'])}", _isaret(x["fark"])] for x in l]  # noqa: E731
            dbas, dgen = ["Ad soyad", "Şube", "Net", "Fark"], [32 * mm, 14 * mm, 25 * mm, 14 * mm]
            ikili = Table([[st.p("En çok yükselen 5", st.h3), st.p("En çok düşen 5", st.h3)],
                           [_tablo(st, dbas, dsat(a["yukselen"]), dgen, kucuk=True) if a["yukselen"] else st.p("Yükselen yok.", st.not_),
                            _tablo(st, dbas, dsat(a["dusen"]), dgen, kucuk=True) if a["dusen"] else st.p("Düşen yok.", st.not_)]],
                          colWidths=[87 * mm, 87 * mm])
            ikili.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
            bolum += [Spacer(1, 4), ikili, st.p("Değişim: " + _e(a.get("degisim_metni") or ""), st.kucuk)]
        h += bolum

    # ---- hedef–uyum
    hu = v.get("hedef_uyum") or {}
    if hu.get("ogrenciler"):
        h.append(st.p("Hedef bölümüyle uyumu düşük öğrenciler — koçlukta destek fırsatı", st.h2))
        h.append(_tablo(st, ["Ad soyad", "Şube", "Hedef bölüm", "Uyum"],
                        [[x["ad_soyad"], x["sube"], x["bolum"], f"%{x['uyum']}"] for x in hu["ogrenciler"]],
                        [50 * mm, 20 * mm, 84 * mm, 20 * mm], kucuk=True))
        h.append(st.p(f"Hedef seçip değerlendirmeyi tamamlayan {hu['hedefli']} öğrenciden {hu['sayi']} öğrencinin hedef bölümle uyumu "
                      f"%{hu['esik']}'ın altında. Bu bir engel değil; öğrenciyle hedefin nedenlerini ve yakın alternatifleri birlikte "
                      "konuşmak için bir fırsattır.", st.not_))
    h.append(Spacer(1, 6))
    h.append(st.p("Sıralamalar yalnızca deneme netleri, net değişimi, katılım ve hedef uyumuna göredir; kişilik, değer ve ilgi "
                  "sonuçları bir başarı ölçüsü olmadığından sıralamada kullanılmaz.", st.not_))
    doc.build(h)
    return tampon.getvalue()
