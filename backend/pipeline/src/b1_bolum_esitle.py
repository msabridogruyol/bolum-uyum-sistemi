# -*- coding: utf-8 -*-
r"""
B1 — Bölüm adlarını veri dosyalarında canlı listeyle eşitler                                  [2026-10-29; 2026-11-01]

Gerçek bölüm listesi canlı sistemdir: s1, veri/bolumler.csv'yi canlı listeyle eşitler ve canlıda adı değişen bölümleri
veri/bolum_ad_degisiklikleri.csv'ye yazar. Bu adım aynı değişikliği bölüme bağlı TÜM veri dosyalarına uygular:
  * adı değişen bölüm: eski ad yeni adla değiştirilir (ders planı, TÜİK eşleşmesi vb. bölümde kalır),
  * canlıda olmayan bölüm: satırları çıkarılır.
Önceden kaldırılan bölümler burada elle yazılı bir listeydi; artık liste canlıdan geldiği için elle liste yok.
  * veri/ içindeki her .csv dosyasında bölüm sütunu ("ad" — bolumler*.csv — ya da "bolum") taranır.
    bolumler.csv, bolumler_en.csv ve bolum_kimlik.csv'yi s1 yazar; bunlara dokunulmaz.
  * Değişen her dosyanın önceki hali yedekler/b1_<tarih>/ klasörüne kopyalanır. Tekrar çalıştırmak güvenlidir.
Kullanım:  C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\b1_bolum_esitle.py      (s1'den sonra, b2'den ÖNCE)
"""
import csv
import io
import shutil
import sys
from datetime import datetime
from pathlib import Path

KOK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
VERI, YEDEK = KOK / "veri", KOK / "yedekler" / f"b1_{datetime.now():%Y%m%d_%H%M%S}"

S1_YAZAR = {"bolumler.csv", "bolumler_en.csv", "bolum_kimlik.csv", "bolum_ad_degisiklikleri.csv"}


def oku(yol, ayirici):
    if not yol.exists():
        return []
    return list(csv.DictReader(yol.read_text(encoding="utf-8-sig").splitlines(), delimiter=ayirici))


GECERLI = {r["ad"].strip() for r in oku(VERI / "bolumler.csv", ",")}
YENI_AD = {r["eski_ad"].strip(): r["yeni_ad"].strip() for r in oku(VERI / "bolum_ad_degisiklikleri.csv", ";")}


def isle(yol):
    ham = yol.read_bytes()
    bom = ham.startswith(b"\xef\xbb\xbf")
    metin = ham.decode("utf-8-sig")
    satirlar = metin.splitlines(keepends=True)
    if not satirlar:
        return 0, 0
    ayirici = ";" if satirlar[0].count(";") > satirlar[0].count(",") else ","
    baslik = next(csv.reader([satirlar[0]], delimiter=ayirici))
    sutun = "ad" if yol.name.startswith("bolumler") and "ad" in baslik else "bolum" if "bolum" in baslik else None
    if sutun is None:
        return 0, 0
    j = baslik.index(sutun)
    kalan, silinen, degisen = [satirlar[0]], 0, 0
    # satır içinde tırnaklı alt satır olabilir: csv ile okunur, ham satır korunarak yazılır
    okuyucu = csv.reader(satirlar[1:], delimiter=ayirici)
    tampon = satirlar[1:]
    i = 0
    for kayit in okuyucu:
        n = okuyucu.line_num - i            # bu kaydın kapladığı ham satır sayısı
        ham_kayit = tampon[i:i + n]; i += n
        ad = kayit[j].strip() if kayit and len(kayit) > j else None
        if ad is not None and ad in YENI_AD:
            kayit[j] = YENI_AD[ad]
            tamp = io.StringIO()
            csv.writer(tamp, delimiter=ayirici, lineterminator="\r\n" if ham_kayit[-1].endswith("\r\n") else "\n").writerow(kayit)
            kalan.append(tamp.getvalue()); degisen += 1
        elif ad is not None and ad not in GECERLI:
            silinen += 1
        else:
            kalan.extend(ham_kayit)
    if silinen or degisen:
        YEDEK.mkdir(parents=True, exist_ok=True)
        shutil.copy(yol, YEDEK / yol.name)
        yol.write_bytes(("\ufeff" if bom else "").encode("utf-8") + "".join(kalan).encode("utf-8"))
    return silinen, degisen


def main():
    if not GECERLI:
        raise SystemExit("veri/bolumler.csv boş ya da yok — önce s1_sistemden_al.py çalışmalı.")
    toplam_s = toplam_d = 0
    for yol in sorted(VERI.glob("*.csv")):
        if yol.name in S1_YAZAR:
            continue
        s, d = isle(yol)
        if s or d:
            print(f"  {yol.name}: {s} satır çıkarıldı, {d} satırda bölüm adı güncellendi")
            toplam_s += s; toplam_d += d
    print(f"Tamam: {len(GECERLI)} bölüm; {toplam_s} satır çıkarıldı, {toplam_d} satırda ad güncellendi"
          + (f" (eski dosyalar: {YEDEK})" if toplam_s or toplam_d else " (zaten eşit)"))


if __name__ == "__main__":
    main()
