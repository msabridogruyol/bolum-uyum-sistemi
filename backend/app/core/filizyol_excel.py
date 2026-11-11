# -*- coding: utf-8 -*-
"""
[2026-11-11] Filizyol markalı Excel çıktısı (hesap giriş listeleri, toplu yükleme şablonu).

Kullanıcı isteği: "Excelin içeriği de Filizyola özgü olsun, amblemi vb. kısa açıklaması vs olsun."

Sayfa düzeni (tek çalışma sayfası; toplu yükleme yalnızca ilk sayfayı okur):
  1–4   amblem + "Filizyol" + "Kendi yolunu filizlendir" + belge başlığı + okul / tarih
  6–    kısa açıklama ve kullanım notları (birleştirilmiş, kaydırmalı satırlar)
  sonra tablo başlığı (turuncu) + zebra satırlar, başlık satırında bölmeler dondurulur
  en altta gizlilik notu
Tablo başlığı ilk 30 satır içinde kalır: okul_yonetimi._satirlari_coz başlığı orada arar (dosya geri yüklenebilir).
Hücre değerleri app/core/excel_guvenligi.guvenli_kaydet ile kaydedilir (formül enjeksiyonu).
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

from app.core.excel_guvenligi import guvenli_kaydet

AMBLEM = Path(__file__).resolve().parent.parent / "data" / "amblem.png"
TURUNCU, KOYU, KREM, CIZGI, SOLUK = "E8804A", "2C2717", "FAF7EF", "ECE5D3", "7A7157"
BASLIK_EN_GEC_SATIR = 30


def markali_xlsx(belge: str, kolonlar: list[str], satirlar: list[list], *, alt_baslik: str | None = None,
                 aciklama: list[str] | None = None, sayfa_adi: str = "Filizyol", gizlilik: str | None = None,
                 genislikler: dict[str, int] | None = None) -> bytes:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sayfa_adi[:31]
    ws.sheet_view.showGridLines = False
    son = get_column_letter(max(len(kolonlar), 4))
    ince = Side(style="thin", color=CIZGI)

    # --- başlık bandı (amblem A1:A4, metin B sütunundan itibaren)
    for r in range(1, 5):
        ws.row_dimensions[r].height = 18
        for c in range(1, max(len(kolonlar), 4) + 1):
            ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=KREM)
    try:
        from openpyxl.drawing.image import Image
        resim = Image(str(AMBLEM))
        resim.width = resim.height = 64
        ws.add_image(resim, "A1")
    except Exception:   # Pillow yoksa amblemsiz devam (yazı kimliği yeterli)
        ws.cell(row=1, column=1, value="🌱").font = Font(size=26)
    ws.cell(row=1, column=2, value="Filizyol").font = Font(name="Calibri", size=20, bold=True, color=KOYU)
    ws.cell(row=2, column=2, value="Kendi yolunu filizlendir").font = Font(name="Calibri", size=10, italic=True, color="A79C7C")
    ws.cell(row=3, column=2, value=belge).font = Font(name="Calibri", size=13, bold=True, color=TURUNCU)
    if alt_baslik:
        ws.cell(row=4, column=2, value=alt_baslik).font = Font(name="Calibri", size=10, color=SOLUK)
    ws.row_dimensions[1].height = 26

    # --- açıklama
    satir = 6
    for metin in (aciklama or []):
        ws.merge_cells(f"A{satir}:{son}{satir}")
        h = ws.cell(row=satir, column=1, value=metin)
        h.font = Font(name="Calibri", size=10.5, color=KOYU, bold=metin.endswith(":"))
        h.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[satir].height = 15 * max(1, -(-len(metin) // 120))
        satir += 1
    ilk = satir + 1
    assert ilk <= BASLIK_EN_GEC_SATIR, "açıklama çok uzun: tablo başlığı geri yüklemede bulunamaz"

    # --- tablo
    for j, k in enumerate(kolonlar, start=1):
        c = ws.cell(row=ilk, column=j, value=k)
        c.font = Font(name="Calibri", bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=TURUNCU)
        c.alignment = Alignment(vertical="center", horizontal="left")
        c.border = Border(bottom=ince)
    ws.row_dimensions[ilk].height = 22
    for i, r in enumerate(satirlar, start=ilk + 1):
        for j, v in enumerate(r, start=1):
            c = ws.cell(row=i, column=j, value=v)
            c.font = Font(name="Calibri", size=11, color=KOYU)
            c.border = Border(bottom=ince)
            if (i - ilk) % 2 == 0:
                c.fill = PatternFill("solid", fgColor=KREM)
    for j, k in enumerate(kolonlar, start=1):
        harf = get_column_letter(j)
        uz = max([len(str(k))] + [len(str(r[j - 1] or "")) for r in satirlar[:500] if j - 1 < len(r)])
        ws.column_dimensions[harf].width = (genislikler or {}).get(k) or min(45, max(12, uz + 3))
    ws.freeze_panes = ws.cell(row=ilk + 1, column=1)
    if satirlar:
        ws.auto_filter.ref = f"A{ilk}:{get_column_letter(len(kolonlar))}{ilk + len(satirlar)}"

    # --- gizlilik notu
    if gizlilik:
        alt = ilk + len(satirlar) + 2
        ws.merge_cells(f"A{alt}:{son}{alt}")
        n = ws.cell(row=alt, column=1, value=gizlilik)
        n.font = Font(name="Calibri", size=9.5, italic=True, color=SOLUK)
        n.alignment = Alignment(wrap_text=True)
        ws.row_dimensions[alt].height = 28

    # --- yazdırma
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{ilk}:{ilk}"
    ws.oddFooter.center.text = "Filizyol · &P / &N"
    wb.properties.creator = "Filizyol"
    wb.properties.title = belge

    b = io.BytesIO()
    guvenli_kaydet(wb, b)
    return b.getvalue()


def markali_xlsx_b64(*a, **k) -> str:
    return base64.b64encode(markali_xlsx(*a, **k)).decode()


GIRIS_ACIKLAMASI = [
    "Filizyol, öğrencilerin ilgi, yetenek ve çalışma biçimlerini beş boyutta değerlendirip onlara uygun bölüm ve meslekleri "
    "gösteren bir rehberlik sistemidir. Bu listede açılan hesapların giriş bilgileri yer alır.",
    "Nasıl kullanılır:",
    "1) Giriş adresi: {adres}  ·  Öğrenciler ve okul yetkilileri aynı giriş ekranını kullanır.",
    "2) Geçici şifre yalnızca ilk giriş içindir; ilk girişte kişi kendi şifresini belirler. \"(kendi şifresi)\" yazan hesaplar şifresini "
    "zaten değiştirmiştir; unutulduysa giriş ekranındaki \"Şifremi unuttum\" kullanılır.",
    "3) Bu dosyayı düzenleyip aynı ekrandan geri yükleyebilirsiniz; kayıtlı e-postalar güncellenir.",
]
GIZLILIK = ("Gizlidir: Bu dosya kişisel veri ve şifre içerir. Yalnızca hesap sahiplerine iletin, ortak klasörlerde ya da "
            "e-posta zincirlerinde tutmayın; iş bitince silin.")
