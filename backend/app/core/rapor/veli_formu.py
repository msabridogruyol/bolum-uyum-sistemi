"""
[2026-11-05] Veli onay formu (PDF). Öğrenci başına: 1 sayfa imzalanacak form + arkasında aydınlatma metni (aynen).
Toplu üretimde (sınıf / seçili öğrenciler) her öğrenci ayrı bir paket olarak başlar; aile formu ve metni birlikte alır.
Metinler app/core/kvkk_metinleri.py'den gelir (VELI_FORM_*, AYDINLATMA_METNI); burada metin yazılmaz.
"""
from datetime import datetime

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Spacer, Table, TableStyle

from app.core.kvkk_metinleri import (
    AYDINLATMA_METNI, KVKK_SURUM, VELI_FORM_GIRIS, VELI_FORM_MADDELERI, VELI_FORM_NOT, VELI_FORM_SURUM,
)
from app.core.rapor.pdf import ACIK, CIZGI, TR, _belge, _e


def _kutu():
    return "☐"


def veli_formu_pdf(ogrenciler: list[dict], okul: dict) -> bytes:
    """ogrenciler: [{ad_soyad, sinif, sube, ogrenci_no}] · okul: {ad, renk, logo}"""
    doc, tampon, st = _belge("Veli onay formu", okul, datetime.now(TR))
    akis = []
    aydinlatma = [p.strip() for p in AYDINLATMA_METNI.split("\n\n") if p.strip()]
    for i, o in enumerate(ogrenciler):
        if i:
            akis.append(PageBreak())
        akis += [st.p("Veli Onay Formu", st.baslik),
                 st.p("Filizyol bölüm ve kariyer uyum sistemi · 18 yaşından küçük öğrenciler için", st.alt)]
        kunye = [["Öğrenci", o.get("ad_soyad") or "", "Okul", okul.get("ad") or "Okul harici"],
                 ["Sınıf / şube", " / ".join(filter(None, [o.get("sinif"), o.get("sube")])) or "—", "Öğrenci no", o.get("ogrenci_no") or "—"]]
        t = Table([[st.p(f"<b>{_e(a)}</b>", st.kucuk), st.p(_e(b), st.hucre), st.p(f"<b>{_e(c)}</b>", st.kucuk), st.p(_e(d), st.hucre)]
                   for a, b, c, d in kunye], colWidths=[28 * mm, 59 * mm, 28 * mm, 59 * mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACIK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        akis += [t, Spacer(1, 10), st.p(_e(VELI_FORM_GIRIS.format(surum=KVKK_SURUM))), Spacer(1, 8)]
        satirlar = [[st.p("<b>Madde</b>", st.hucre), st.p("<b>Onaylıyorum</b>", st.hucre), st.p("<b>Onaylamıyorum</b>", st.hucre)]]
        for _k, metin, zorunlu in VELI_FORM_MADDELERI:
            satirlar.append([st.p(_e(metin) + ("" if zorunlu else " <i>(isteğe bağlı)</i>"), st.hucre),
                             st.p(_kutu(), st.h3), st.p(_kutu(), st.h3)])
        mt = Table(satirlar, colWidths=[114 * mm, 30 * mm, 30 * mm])
        mt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, CIZGI), ("BACKGROUND", (0, 0), (-1, 0), ACIK),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        akis += [mt, Spacer(1, 8), st.p(_e(VELI_FORM_NOT), st.not_), Spacer(1, 16)]
        # [2026-11-05] Öğrenci de "bilgilendirildim" diye imzalar (basılı belge setiyle aynı)
        imza = [["", "Veli", "Öğrenci (bilgilendirildim)"], ["Adı soyadı", "", o.get("ad_soyad") or ""],
                ["Öğrenciye yakınlığı", "", "—"], ["Tarih", "", ""], ["İmza", "", ""]]
        it = Table([[st.p(f"<b>{a}</b>", st.hucre), st.p(_e(b), st.hucre), st.p(_e(c), st.hucre)] for a, b, c in imza],
                   colWidths=[38 * mm, 68 * mm, 68 * mm], rowHeights=[8 * mm, 11 * mm, 11 * mm, 11 * mm, 18 * mm])
        it.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, CIZGI), ("BACKGROUND", (0, 0), (0, -1), ACIK),
                                ("BACKGROUND", (0, 0), (-1, 0), ACIK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        akis += [it, Spacer(1, 10),
                 st.p(f"Form sürümü {VELI_FORM_SURUM} · Aydınlatma metni sürümü {KVKK_SURUM}. İmzalı formu okulunuza teslim ediniz; "
                      "okul formu aldığını sistemde işaretleyince öğrencinin değerlendirmesi açılır. Formun aslı okulda saklanır.", st.kucuk),
                 PageBreak(), st.p("Ek: Aydınlatma Metni", st.h2)]
        for p in aydinlatma:
            akis.append(st.p(_e(p).replace("\n", "<br/>"), st.kucuk))
            akis.append(Spacer(1, 4))
    if not akis:
        akis.append(st.p("Seçili öğrenci yok."))
    doc.build(akis)
    return tampon.getvalue()
