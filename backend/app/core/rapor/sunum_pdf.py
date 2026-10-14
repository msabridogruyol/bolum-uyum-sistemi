"""
[2026-10-14] Veli toplantısı sunumunun PDF çizimi (reportlab).

Slaytlar app/core/rapor/veli_sunumu.py'deki AYNI slayt fonksiyonlarıyla kurulur: çizim yardımcıları (_metin, _kart, _daire,
cubuk, halka …) slayt bir PdfSlayt ise çizim komutlarını buraya kaydeder; PowerPoint ile PDF'in içeriği hiçbir zaman ayrışmaz.
Yazı tipi: Liberation Sans (Arial ile aynı ölçüler), PDF'in içine gömülür — dosya her cihazda aynı görünür.

İki sayfa düzeni:
  * slayt  — 13,333 × 7,5 inç (16:9), her sayfa bir slayt; perdeye yansıtmak ve paylaşmak için;
  * notlu  — A4 dikey "notlar sayfası": üstte slayt, altında o slaytın konuşma notu; sunumu yapan öğretmen için.
"""
from __future__ import annotations

import io
import math
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph

INC = 72.0


def _fontlar():
    from app.core.rapor.pdf import _fontlar as kaydet
    kaydet()


def _renk(h: str):
    return HexColor("#" + h)


class PdfSlayt:
    """Bir slaytın çizim komutları (inç cinsinden, sol üst köşe başlangıç — python-pptx ile aynı koordinatlar)."""

    def __init__(self, w: float, h: float):
        self.w, self.h = w, h
        self.arka_renk = "FFFFFF"
        self.komutlar: list[tuple] = []
        self.not_metni = ""

    # ---- kayıt
    def arka(self, renk):
        self.arka_renk = renk

    def metin(self, *a, **k):
        self.komutlar.append(("metin", a, k))

    def kart(self, *a, **k):
        self.komutlar.append(("kart", a, k))

    def daire(self, *a, **k):
        self.komutlar.append(("daire", a, k))

    def oval(self, *a, **k):
        self.komutlar.append(("oval", a, k))

    def cizgi(self, *a, **k):
        self.komutlar.append(("cizgi", a, k))

    def resim(self, *a, **k):
        self.komutlar.append(("resim", a, k))

    def cubuk(self, *a, **k):
        self.komutlar.append(("cubuk", a, k))

    def halka(self, *a, **k):
        self.komutlar.append(("halka", a, k))

    # ---- çizim
    def ciz(self, c: rl_canvas.Canvas):
        c.saveState()
        yol = c.beginPath()
        yol.rect(0, 0, self.w * INC, self.h * INC)
        c.clipPath(yol, stroke=0, fill=0)   # slayt dışına taşan şekiller (kapak daireleri) kırpılır — notlar sayfasında da
        c.setFillColor(_renk(self.arka_renk))
        c.rect(0, 0, self.w * INC, self.h * INC, stroke=0, fill=1)
        for tur, a, k in self.komutlar:
            getattr(self, "_" + tur)(c, *a, **k)
        c.restoreState()

    def _y(self, y, h=0.0):
        """pptx üst kenarı (inç) → reportlab alt kenarı (nokta)."""
        return (self.h - y - h) * INC

    # metin --------------------------------------------------------------------------------------------------------------
    def _metin(self, c, x, y, w, h, parcalar, boyut=16, renk="2B2620", kalin=False, hiza="sol", dikey="ust", satir_arasi=None):
        paragraflar = parcalar if isinstance(parcalar, list) else [parcalar]
        hz = {"sol": TA_LEFT, "orta": TA_CENTER, "sag": TA_RIGHT}[hiza]
        bloklar = []
        for par in paragraflar:
            runs = par if isinstance(par, list) else [(par, {})]
            if not any(t for t, _ in runs):
                runs = [(" ", {})]
            en_buyuk = max(o.get("boyut", boyut) for _, o in runs)
            parcali = "".join(
                f'<font name="{"Filiz-B" if o.get("kalin", kalin) else ("Filiz-I" if o.get("italik") else "Filiz")}" '
                f'size="{o.get("boyut", boyut)}" color="#{o.get("renk", renk)}">{escape(t)}</font>' for t, o in runs)
            st = ParagraphStyle("s", fontName="Filiz", fontSize=en_buyuk, leading=en_buyuk * 1.2, alignment=hz,
                                spaceAfter=satir_arasi or 0)
            p = Paragraph(parcali, st)
            _, ph = p.wrap(w * INC, 10_000)
            bloklar.append((p, ph, satir_arasi or 0))
        toplam = sum(ph for _, ph, _ in bloklar) + sum(s for _, _, s in bloklar[:-1])
        ust = (self.h - y) * INC
        if dikey == "orta":
            ust -= max(0.0, (h * INC - toplam) / 2)
        elif dikey == "alt":
            ust -= max(0.0, h * INC - toplam)
        for p, ph, s in bloklar:
            p.drawOn(c, x * INC, ust - ph)
            ust -= ph + s

    # şekiller -----------------------------------------------------------------------------------------------------------
    def _kart(self, c, x, y, w, h, dolgu, yuvarlak=0.06):
        c.setFillColor(_renk(dolgu))
        r = min(w, h) * yuvarlak * INC
        c.roundRect(x * INC, self._y(y, h), w * INC, h * INC, r, stroke=0, fill=1)

    def _oval(self, c, x, y, cap, dolgu):
        c.setFillColor(_renk(dolgu))
        c.circle((x + cap / 2) * INC, self._y(y + cap / 2), cap / 2 * INC, stroke=0, fill=1)

    def _daire(self, c, x, y, cap, dolgu, yazi, yazi_renk="FFFFFF", boyut=16):
        self._oval(c, x, y, cap, dolgu)
        c.setFillColor(_renk(yazi_renk))
        c.setFont("Filiz-B", boyut)
        c.drawCentredString((x + cap / 2) * INC, self._y(y + cap / 2) - boyut * 0.35, yazi)

    def _cizgi(self, c, x1, y1, x2, y2, renk, kalinlik=2):
        c.setStrokeColor(_renk(renk))
        c.setLineWidth(kalinlik)
        c.line(x1 * INC, self._y(y1), x2 * INC, self._y(y2))

    def _resim(self, c, akis, x, y, h):
        try:
            img = ImageReader(akis)
            iw, ih = img.getSize()
            w = h * iw / ih
            c.drawImage(img, x * INC, self._y(y, h), w * INC, h * INC, mask="auto")
        except (OSError, ValueError, ZeroDivisionError):   # okunamayan logo: kapak logosuz çizilir (PowerPoint'teki gibi)
            return

    # grafikler ----------------------------------------------------------------------------------------------------------
    @staticmethod
    def _adim(ust: float) -> float:
        for a in (1, 2, 5, 10, 20, 25, 50, 100, 200, 500):
            if ust / a <= 10:
                return a
        return ust / 10

    def _etiket_yaz(self, c, metin, x, y, genislik, boyut, hiza="sag", renk="2B2620", en_cok=2):
        """Kategori etiketi: genişliğe sığmazsa iki satıra böl (gerekirse kısalt)."""
        c.setFillColor(_renk(renk))
        c.setFont("Filiz", boyut)
        kelimeler, satirlar, s = metin.split(), [], ""
        for k in kelimeler:
            aday = (s + " " + k).strip()
            if c.stringWidth(aday, "Filiz", boyut) <= genislik or not s:
                s = aday
            else:
                satirlar.append(s)
                s = k
        if s:
            satirlar.append(s)
        if len(satirlar) > en_cok:
            satirlar = satirlar[:en_cok]
            while c.stringWidth(satirlar[-1] + "…", "Filiz", boyut) > genislik and len(satirlar[-1]) > 1:
                satirlar[-1] = satirlar[-1][:-1]
            satirlar[-1] += "…"
        lh = boyut * 1.15
        y0 = y + (len(satirlar) - 1) * lh / 2
        for i, t in enumerate(satirlar):
            yy = y0 - i * lh - boyut * 0.35
            if hiza == "sag":
                c.drawRightString(x, yy, t)
            elif hiza == "orta":
                c.drawCentredString(x, yy, t)
            else:
                c.drawString(x, yy, t)

    def _cubuk(self, c, x, y, w, h, kategoriler, seriler, yatay=True, eksen_max=None, sonek="", renkler=("E8804A", "B8AFA2")):
        degerler = [v for _, l in seriler for v in l if v is not None]
        ust = eksen_max or (max(degerler) * 1.15 if degerler else 1)
        adim = self._adim(ust)
        ust = math.ceil(ust / adim) * adim
        n, m = len(kategoriler), len(seriler)
        gosterge = 0.4 if m > 1 else 0.0
        X, Y, Wp, Hp = x * INC, self._y(y, h), w * INC, h * INC
        Y += gosterge * INC
        Hp -= gosterge * INC
        c.setFont("Filiz", 11)
        if yatay:
            etiket_w = min(Wp * 0.42, max(c.stringWidth(k, "Filiz", 12) for k in kategoriler) + 8) if kategoriler else 0
            ax_x, ax_w = X + etiket_w + 6, Wp - etiket_w - 6 - 34
            ax_y, ax_h = Y + 18, Hp - 24
            # dikey kılavuz çizgileri ve değer etiketleri (altta)
            c.setLineWidth(0.6)
            k = 0.0
            while k <= ust + 1e-9:
                gx = ax_x + ax_w * k / ust
                c.setStrokeColor(_renk("E6DDCF"))
                c.line(gx, ax_y, gx, ax_y + ax_h)
                c.setFillColor(_renk("6B6257"))
                c.setFont("Filiz", 11)
                c.drawCentredString(gx, ax_y - 14, f"{k:g}")
                k += adim
            bant = ax_h / max(n, 1)
            kal = bant * 0.62 / m
            for i, kat in enumerate(kategoriler):
                merkez = ax_y + ax_h - bant * (i + 0.5)
                self._etiket_yaz(c, kat, ax_x - 6, merkez, etiket_w - 4, 12)
                for j, (_, l) in enumerate(seriler):
                    v = l[i]
                    if v is None:
                        continue
                    by = merkez + kal * m / 2 - kal * (j + 1)
                    c.setFillColor(_renk(renkler[j % len(renkler)]))
                    c.rect(ax_x, by + 1, ax_w * min(v, ust) / ust, kal - 2, stroke=0, fill=1)
                    c.setFillColor(_renk("2B2620"))
                    c.setFont("Filiz-B", 12 if m == 1 else 10)
                    c.drawString(ax_x + ax_w * min(v, ust) / ust + 4, by + kal / 2 - 4, f"{v:.0f}{sonek}")
            c.setStrokeColor(_renk("C9C1B5"))
            c.line(ax_x, ax_y, ax_x, ax_y + ax_h)
        else:
            ax_x, ax_w = X + 30, Wp - 34
            ax_y, ax_h = Y + 34, Hp - 50
            c.setLineWidth(0.6)
            k = 0.0
            while k <= ust + 1e-9:
                gy = ax_y + ax_h * k / ust
                c.setStrokeColor(_renk("E6DDCF"))
                c.line(ax_x, gy, ax_x + ax_w, gy)
                c.setFillColor(_renk("6B6257"))
                c.setFont("Filiz", 11)
                c.drawRightString(ax_x - 4, gy - 4, f"{k:g}")
                k += adim
            bant = ax_w / max(n, 1)
            kal = bant * 0.62 / m
            for i, kat in enumerate(kategoriler):
                merkez = ax_x + bant * (i + 0.5)
                self._etiket_yaz(c, kat, merkez, ax_y - 16, bant - 4, 12, hiza="orta")
                for j, (_, l) in enumerate(seriler):
                    v = l[i]
                    if v is None:
                        continue
                    bx = merkez - kal * m / 2 + kal * j
                    bh = ax_h * min(v, ust) / ust
                    c.setFillColor(_renk(renkler[j % len(renkler)]))
                    c.rect(bx + 1, ax_y, kal - 2, bh, stroke=0, fill=1)
                    c.setFillColor(_renk("2B2620"))
                    c.setFont("Filiz-B", 12)
                    c.drawCentredString(bx + kal / 2, ax_y + bh + 4, f"{v:.0f}{sonek}")
            c.setStrokeColor(_renk("C9C1B5"))
            c.line(ax_x, ax_y, ax_x + ax_w, ax_y)
        if m > 1:   # gösterge (altta)
            gx = X + Wp / 2 - 90
            for j, (ad, _) in enumerate(seriler):
                c.setFillColor(_renk(renkler[j % len(renkler)]))
                c.rect(gx, Y - gosterge * INC + 6, 9, 9, stroke=0, fill=1)
                c.setFillColor(_renk("2B2620"))
                c.setFont("Filiz", 12)
                c.drawString(gx + 13, Y - gosterge * INC + 7, ad)
                gx += c.stringWidth(ad, "Filiz", 12) + 34

    def _halka(self, c, x, y, w, h, kategoriler, degerler, baslik=None, renkler=("E8804A",), arka="FFFFFF"):
        X, Y, Wp, Hp = x * INC, self._y(y, h), w * INC, h * INC
        ust = Y + Hp
        if baslik:
            c.setFillColor(_renk("2B2620"))
            c.setFont("Filiz-B", 14)
            c.drawCentredString(X + Wp / 2, ust - 18, baslik)
            ust -= 32
        gosterge_w = min(Wp * 0.42, max(c.stringWidth(k, "Filiz", 12) for k in kategoriler) + 22) if kategoriler else 0
        alan_w, alan_h = Wp - gosterge_w, ust - Y - 6
        r = min(alan_w, alan_h) / 2 - 4
        cx, cy = X + alan_w / 2, Y + alan_h / 2 + 3
        toplam = sum(v for v in degerler if v) or 1
        aci = 90.0
        c.setStrokeColor(_renk("FFFFFF"))
        c.setLineWidth(1.5)
        orta_noktalar = []
        for i, v in enumerate(degerler):
            if not v:
                continue
            kapsam = -360.0 * v / toplam
            c.setFillColor(_renk(renkler[i % len(renkler)]))
            if abs(kapsam) >= 359.99:
                c.circle(cx, cy, r, stroke=1, fill=1)
            else:
                c.wedge(cx - r, cy - r, cx + r, cy + r, aci, kapsam, stroke=1, fill=1)
            orta = math.radians(aci + kapsam / 2)
            orta_noktalar.append((orta, v))
            aci += kapsam
        c.setFillColor(_renk(arka))
        c.circle(cx, cy, r * 0.55, stroke=0, fill=1)
        c.setFillColor(_renk("FFFFFF"))
        c.setFont("Filiz-B", 12)
        for a, v in orta_noktalar:
            rr = r * 0.775
            c.drawCentredString(cx + rr * math.cos(a), cy + rr * math.sin(a) - 4, f"{v:.0f}")
        # gösterge (sağda)
        gy = cy + len(kategoriler) * 9
        for i, k in enumerate(kategoriler):
            c.setFillColor(_renk(renkler[i % len(renkler)]))
            c.rect(X + alan_w + 4, gy - 1, 8, 8, stroke=0, fill=1)
            self._etiket_yaz(c, k, X + alan_w + 16, gy + 3, gosterge_w - 18, 12, hiza="sol")
            gy -= 20


def pdf_olustur(slaytlar: list[PdfSlayt], baslik: str, notlu: bool = False, yazar: str = "Filizyol") -> bytes:
    _fontlar()
    out = io.BytesIO()
    if not notlu:
        w, h = slaytlar[0].w * INC, slaytlar[0].h * INC
        c = rl_canvas.Canvas(out, pagesize=(w, h), initialFontName="Filiz", initialFontSize=12)
        c.setTitle(baslik)
        c.setAuthor(yazar)
        for s in slaytlar:
            s.ciz(c)
            c.showPage()
        c.save()
        return out.getvalue()
    # notlar sayfası: A4 dikey, üstte slayt (çerçeveli), altta konuşma notu
    pw, ph = A4
    kenar = 42
    c = rl_canvas.Canvas(out, pagesize=A4, initialFontName="Filiz", initialFontSize=12)
    c.setTitle(baslik)
    c.setAuthor(yazar)
    st = ParagraphStyle("not", fontName="Filiz", fontSize=12, leading=17, textColor=_renk("2B2620"))
    st_b = ParagraphStyle("nb", fontName="Filiz-B", fontSize=11, leading=14, textColor=_renk("6B6257"))
    for i, s in enumerate(slaytlar, 1):
        olcek = (pw - 2 * kenar) / (s.w * INC)
        sh = s.h * INC * olcek
        ust = ph - kenar
        c.saveState()
        c.translate(kenar, ust - sh)
        c.scale(olcek, olcek)
        s.ciz(c)
        c.restoreState()
        c.setStrokeColor(_renk("C9C1B5"))
        c.setLineWidth(0.8)
        c.rect(kenar, ust - sh, pw - 2 * kenar, sh, stroke=1, fill=0)
        y = ust - sh - 26
        p = Paragraph(f"Slayt {i} · Konuşma notu", st_b)
        _, hh = p.wrap(pw - 2 * kenar, 100)
        p.drawOn(c, kenar, y - hh)
        y -= hh + 8
        p = Paragraph(escape(s.not_metni or "—"), st)
        _, hh = p.wrap(pw - 2 * kenar, y - kenar)
        p.drawOn(c, kenar, y - hh)
        c.setFont("Filiz", 9)
        c.setFillColor(_renk("8C8378"))
        c.drawRightString(pw - kenar, kenar - 18, f"{i} / {len(slaytlar)}")
        c.showPage()
    c.save()
    return out.getvalue()
