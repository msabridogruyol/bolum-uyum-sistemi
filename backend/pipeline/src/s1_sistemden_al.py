# -*- coding: utf-8 -*-
r"""
S1 — Sistemden güncel kodu, en son veri sürümünü ve canlı listeleri alır                       [2026-11-01]

1) Kod: sistemdeki pipeline kodu (backend/pipeline/) bu bilgisayardakiyle karşılaştırılır; değişen / eksik dosya indirilir.
   Sistemde artık olmayan src/*.py dosyaları silinmez, _silinecek/ klasörüne taşınır.
   pipeline_calistir.ps1 ya da s1'in kendisi değiştiyse çıkış kodu 10 olur; çalıştırma dosyası kendini yeni hâliyle yeniden başlatır.
2) Veri: başka bir bilgisayar daha yeni bir veri sürümü gönderdiyse değişen dosyalar indirilir (parça özetleriyle doğrulanır).
   Bu bilgisayarda gönderilmemiş sonuç varken sistemde daha yeni sürüm varsa DURULUR (biri ötekinin üzerine yazmasın);
   sistemdekini almak için: pipeline_calistir.ps1 -SistemdekiniAl (bu bilgisayardakiler önce yedekler/ klasörüne kopyalanır).
3) Canlı listeler (ad uyuşmazlığı olmasın diye her çalıştırmada):
   * Bölümler: veri/bolumler.csv canlı listeyle eşitlenir. Bölüm kimliği (id) veri/bolum_kimlik.csv'de tutulur; canlıda adı
     değişen bölüm yeni adıyla güncellenir ve eski → yeni ad veri/bolum_ad_degisiklikleri.csv'ye yazılır (b1 diğer veri
     dosyalarına uygular). Canlıdan kaldırılan bölüm listeden çıkar (b1 diğer dosyalardan da çıkarır). Yeni bölüm eklenir.
     Değişen / yeni kısa açıklamanın İngilizcesi (veri/bolumler_en.csv, Model C) çeviri modeliyle yenilenir.
   * K5: veri/k5_eksenleri.csv ve veri/k5_cumleleri.csv canlı K5 bankasından yazılır (değişmeyen cümlenin İngilizcesi korunur).
   * Özellikler: puanlar özellik kutup cümlelerinden (veri/degisken_kutuplari.csv) hesaplanır; özellik adı / tanımı değişince
     yalnızca uyarı verilir. Canlıda pipeline'ın tanımadığı bir özellik varsa DURULUR (yöntem güncellemesi gerekir).
   * Özetler veri/canli_ozet.json'a yazılır; s2 bunları veri sürümüyle birlikte gönderir (sayaç bu özetlere bakar).
Kullanım:  C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\s1_sistemden_al.py [--kurulum] [--sistemdekini-al]
"""
import csv
import io
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sistem_baglanti import (KOK, BaglantiHatasi, api, durum_oku, durum_yaz, dosya_ozeti, indir, sha256,  # noqa: E402
                             yerel_dosyalar)

VERI = KOK / "veri"
DAMGA = f"{datetime.now():%Y%m%d_%H%M%S}"
KOD_YENIDEN_BASLAT = 10
# Bunlardan biri güncellenirse çalışma yeni koduyla baştan başlar (çalışan s1 eski kodu bellekte tutar)
YENIDEN_BASLATAN = {"pipeline_calistir.ps1", "src/s1_sistemden_al.py", "src/sistem_baglanti.py"}
# s1'in her çalıştırmada canlıdan yeniden ürettiği dosyalar: "gönderilmemiş iş" sayılmaz (çakışma denetimine girmez)
TURETILEN = {"veri/canli_ozet.json", "veri/canli_degiskenler.csv", "veri/bolum_kimlik.csv", "veri/bolum_ad_degisiklikleri.csv",
             "veri/bolumler.csv", "veri/bolumler_en.csv", "veri/k5_eksenleri.csv", "veri/k5_cumleleri.csv"}


def csv_oku(yol: Path, ayirici=None) -> tuple[list[str], list[dict]]:
    if not yol.exists():
        return [], []
    metin = yol.read_text(encoding="utf-8-sig")
    ilk = metin.split("\n", 1)[0]
    ayirici = ayirici or (";" if ilk.count(";") > ilk.count(",") else ",")
    r = csv.DictReader(io.StringIO(metin), delimiter=ayirici)
    return list(r.fieldnames or []), list(r)


def csv_yaz(yol: Path, alanlar: list[str], satirlar: list[dict], ayirici: str, bom: bool = True) -> bool:
    """İçerik değişmediyse dosyaya dokunmaz (gereksiz yeni veri sürümü oluşmasın). Değiştiyse önce yedekler."""
    tampon = io.StringIO()
    w = csv.DictWriter(tampon, fieldnames=alanlar, delimiter=ayirici, lineterminator="\n", extrasaction="ignore")
    w.writeheader(); w.writerows(satirlar)
    yeni = ("\ufeff" if bom else "") + tampon.getvalue()
    if yol.exists() and yol.read_text(encoding="utf-8-sig") == yeni.lstrip("\ufeff"):
        return False
    if yol.exists():
        yedek = KOK / "yedekler" / f"s1_{DAMGA}"
        yedek.mkdir(parents=True, exist_ok=True)
        shutil.copy(yol, yedek / yol.name)
    yol.write_text(yeni, encoding="utf-8")
    return True


def cevir(metinler: list[str]) -> list[str]:
    if not metinler:
        return []
    print(f"  {len(metinler)} metin İngilizceye çevriliyor (Model C için)…")
    from ceviri import ceviri_yap
    return ceviri_yap(metinler)


# ------------------------------------------------------------------------------------------------ 1) kod
def kodu_guncelle(manifest: dict) -> bool:
    calistirici_degisti, degisen = False, []
    sistemdeki = {d["yol"] for d in manifest["kod"]}
    for d in manifest["kod"]:
        yol = KOK / d["yol"]
        if yol.exists() and sha256(yol.read_bytes()) == d["sha256"]:
            continue
        veri = api("GET", "/pipeline-istemci/kod?yol=" + d["yol"], ham=True)
        if sha256(veri) != d["sha256"]:
            raise BaglantiHatasi(f"İndirilen kod dosyası doğrulanamadı: {d['yol']}")
        yol.parent.mkdir(parents=True, exist_ok=True)
        if yol.exists():
            yedek = KOK / "yedekler" / f"kod_{DAMGA}" / d["yol"]
            yedek.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(yol, yedek)
        yol.write_bytes(veri)
        degisen.append(d["yol"])
        calistirici_degisti |= d["yol"] in YENIDEN_BASLATAN
    for p in sorted((KOK / "src").glob("*.py")):
        yol = p.relative_to(KOK).as_posix()
        if yol not in sistemdeki:
            hedef = KOK / "_silinecek" / f"kod_{DAMGA}" / yol
            hedef.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), hedef)
            print(f"  sistemde olmayan eski kod dosyası _silinecek klasörüne taşındı: {yol}")
    print(f"Kod: sürüm {manifest['kod_surumu']} — " + (f"{len(degisen)} dosya güncellendi: {', '.join(degisen)}" if degisen
                                                      else "bu bilgisayardaki kod güncel"))
    return calistirici_degisti


# ------------------------------------------------------------------------------------------------ 2) veri
def veriyi_al(manifest: dict, kurulum: bool, sistemdekini_al: bool) -> None:
    sistem = manifest.get("veri")
    if not sistem:
        print("Veri: sistemde henüz veri sürümü yok — bu bilgisayardaki veri kullanılacak, çalıştırma sonunda gönderilecek.")
        return
    durum = durum_oku()
    if durum and durum.get("surum_id") == sistem["surum_id"]:
        print(f"Veri: bu bilgisayar sistemdeki son sürümle aynı (sürüm {sistem['surum_id']}).")
        return
    yerel = yerel_dosyalar()
    yerel_ozet = {y: dosya_ozeti(p)["sha256"] for y, p in yerel.items()}
    if durum and not sistemdekini_al:
        gonderilmemis = [y for y, s in yerel_ozet.items() if y not in TURETILEN and durum["dosyalar"].get(y) != s]
        if gonderilmemis:
            raise BaglantiHatasi(
                f"Sistemde başka bir bilgisayarın gönderdiği daha yeni veri var (sürüm {sistem['surum_id']}, "
                f"{sistem.get('cihaz_adi') or '?'}), ama bu bilgisayarda gönderilmemiş {len(gonderilmemis)} dosya da var "
                f"(ör. {', '.join(gonderilmemis[:3])}). Biri ötekinin üzerine yazmasın diye durdu.\n"
                "Sistemdekini kullanmak için:  powershell -ExecutionPolicy Bypass -File C:\\pipeline\\pipeline_calistir.ps1 "
                "-SistemdekiniAl   (bu bilgisayardakiler önce yedekler klasörüne kopyalanır)")
    elif not durum and yerel and not kurulum and not sistemdekini_al:
        raise BaglantiHatasi(
            "Bu bilgisayardaki veri sistemdeki hiçbir sürümle eşleştirilemedi (ilk eşleştirme). Sistemdeki son sürümü "
            "almak için -SistemdekiniAl ile çalıştırın.")
    hedefler = {y: d for y, d in sistem["dosyalar"].items() if yerel_ozet.get(y) != d["sha256"]}
    if hedefler:
        parcalar = sorted({p for d in hedefler.values() for p in d["parcalar"]})
        adresler = api("POST", "/pipeline-istemci/parca-adresleri", {"parcalar": parcalar})["adresler"]
        yedek = KOK / "yedekler" / f"veri_oncesi_{DAMGA}"
        toplam = 0
        for y, d in sorted(hedefler.items()):
            veri = b""
            for p in d["parcalar"]:
                parca = indir(adresler[p])
                if sha256(parca) != p:
                    raise BaglantiHatasi(f"İndirilen parça doğrulanamadı ({y}).")
                veri += parca
            if sha256(veri) != d["sha256"]:
                raise BaglantiHatasi(f"İndirilen dosya doğrulanamadı: {y}")
            hedef = KOK / y
            if hedef.exists():
                (yedek / y).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(hedef, yedek / y)
            hedef.parent.mkdir(parents=True, exist_ok=True)
            gecici = hedef.with_name(hedef.name + ".tmp")
            gecici.write_bytes(veri); gecici.replace(hedef)
            toplam += len(veri)
        print(f"Veri: sistemdeki sürüm {sistem['surum_id']} alındı — {len(hedefler)} dosya, {toplam / 1e6:.1f} MB"
              + (f" (önceki hâlleri: {yedek})" if yedek.exists() else ""))
    else:
        print(f"Veri: dosyalar sistemdeki sürüm {sistem['surum_id']} ile zaten aynı.")
    durum_yaz(sistem["surum_id"], sistem["dosyalar"])


# ------------------------------------------------------------------------------------------------ 3) canlı listeler
def bolumleri_esitle(canli: list[dict]) -> None:
    alan_b, eski = csv_oku(VERI / "bolumler.csv")
    alanlar = alan_b or ["ad", "kisa_aciklama"]
    _, kimlik = csv_oku(VERI / "bolum_kimlik.csv", ";")
    ad_of_id = {int(r["id"]): r["ad"] for r in kimlik if r.get("id")}
    canli_id = {b["id"]: b for b in canli}
    canli_ad = {b["ad"]: b for b in canli}
    if not ad_of_id:   # ilk eşleştirme: pipeline adları canlı adlarla eşlenir
        ad_of_id = {canli_ad[r["ad"]]["id"]: r["ad"] for r in eski if r["ad"] in canli_ad}
    degisen_ad = {ad_of_id[i]: canli_id[i]["ad"] for i in ad_of_id if i in canli_id and canli_id[i]["ad"] != ad_of_id[i]}
    eski_by_ad = {r["ad"]: r for r in eski}
    yeni_satirlar, gorulen = [], set()
    for r in eski:                                       # mevcut sıra korunur (sonuçlar gereksiz yere oynamasın)
        ad = degisen_ad.get(r["ad"], r["ad"])
        b = canli_ad.get(ad)
        if b is None or ad in gorulen:
            continue
        yeni_satirlar.append({**r, "ad": ad, "kisa_aciklama": b["kisa_aciklama"]}); gorulen.add(ad)
    eklenen = [b for b in canli if b["ad"] not in gorulen]
    for b in eklenen:
        yeni_satirlar.append({a: "" for a in alanlar} | {"ad": b["ad"], "kisa_aciklama": b["kisa_aciklama"]})
    kaldirilan = [r["ad"] for r in eski if degisen_ad.get(r["ad"], r["ad"]) not in canli_ad]
    csv_yaz(VERI / "bolumler.csv", alanlar, yeni_satirlar, ",", bom=False)
    csv_yaz(VERI / "bolum_kimlik.csv", ["id", "ad"],
            [{"id": canli_ad[r["ad"]]["id"], "ad": r["ad"]} for r in yeni_satirlar], ";")
    csv_yaz(VERI / "bolum_ad_degisiklikleri.csv", ["eski_ad", "yeni_ad"],
            [{"eski_ad": e, "yeni_ad": y} for e, y in degisen_ad.items()], ";")

    # İngilizce (Model C): ad değişmediyse ve kısa açıklama aynıysa eski çeviri korunur
    alan_en, en = csv_oku(VERI / "bolumler_en.csv")
    alan_en = alan_en or ["ad", "ad_en", "kisa_aciklama_en"]
    en_by_ad = {r["ad"]: r for r in en}
    cevrilecek_ad, cevrilecek_ac, en_satir = [], [], []
    for r in yeni_satirlar:
        onceki_ad = next((e for e, y in degisen_ad.items() if y == r["ad"]), r["ad"])
        e = en_by_ad.get(onceki_ad)
        eski_aciklama = (eski_by_ad.get(onceki_ad) or {}).get("kisa_aciklama")
        satir = {"ad": r["ad"], "ad_en": (e or {}).get("ad_en", ""), "kisa_aciklama_en": (e or {}).get("kisa_aciklama_en", "")}
        if e is None or onceki_ad != r["ad"]:
            cevrilecek_ad.append(len(en_satir))
        if e is None or eski_aciklama != r["kisa_aciklama"]:
            cevrilecek_ac.append(len(en_satir))
        en_satir.append(satir)
    cevrilmis = cevir([yeni_satirlar[i]["ad"].title() for i in cevrilecek_ad] +
                      [yeni_satirlar[i]["kisa_aciklama"] for i in cevrilecek_ac if yeni_satirlar[i]["kisa_aciklama"]])
    k = 0
    for i in cevrilecek_ad:
        en_satir[i]["ad_en"] = cevrilmis[k].upper(); k += 1
    for i in cevrilecek_ac:
        if yeni_satirlar[i]["kisa_aciklama"]:
            en_satir[i]["kisa_aciklama_en"] = cevrilmis[k]; k += 1
        else:
            en_satir[i]["kisa_aciklama_en"] = ""
    csv_yaz(VERI / "bolumler_en.csv", alan_en, en_satir, ",", bom=False)

    print(f"Bölümler: canlıda {len(canli)} — pipeline'da {len(yeni_satirlar)}"
          + (f" | adı değişen {len(degisen_ad)}: " + "; ".join(f"{e} → {y}" for e, y in degisen_ad.items()) if degisen_ad else "")
          + (f" | yeni {len(eklenen)}: " + ", ".join(b["ad"] for b in eklenen) if eklenen else "")
          + (f" | kaldırılan {len(kaldirilan)}: " + ", ".join(kaldirilan) if kaldirilan else ""))
    if eklenen:
        _, dersler = csv_oku(VERI / "bolum_dersleri.csv")
        ders_var = {r.get("bolum", "").strip() for r in dersler}
        yok = [b["ad"] for b in eklenen if b["ad"] not in ders_var]
        if yok:
            print(f"  Not: {len(yok)} yeni bölümün resmî ders planı veri/bolum_dersleri.csv'de yok; bölüm metni kısa açıklamadan "
                  f"kurulur: {', '.join(yok)}")


def sirayi_koru(yeni: list[dict], eski: list[dict], anahtar) -> list[dict]:
    """Canlı liste, dosyadaki mevcut sırayla yazılır; yeni kayıtlar sona eklenir (sonuçlar sıra yüzünden oynamasın)."""
    yer = {anahtar(r): i for i, r in enumerate(eski)}
    return sorted(yeni, key=lambda r: yer.get(anahtar(r), len(yer)))   # sorted kararlı: yeniler canlı sırasıyla


def k5_esitle(eksenler: list[dict], cumleler: list[dict]) -> None:
    _, eski_eksen = csv_oku(VERI / "k5_eksenleri.csv", ";")
    csv_yaz(VERI / "k5_eksenleri.csv", ["kod", "alan", "ad"], sirayi_koru(eksenler, eski_eksen, lambda r: r["kod"]), ";")
    _, eski = csv_oku(VERI / "k5_cumleleri.csv", ";")
    en_of = {r["metin"]: r.get("metin_en", "") for r in eski if r.get("metin_en")}
    eksik = sorted({c["metin"] for c in cumleler if c["metin"] not in en_of})
    en_of.update(zip(eksik, cevir(eksik)))
    satirlar = [{"kod": c["kod"], "sira": str(c["sira"]), "metin": c["metin"], "metin_en": en_of.get(c["metin"], "")} for c in cumleler]
    csv_yaz(VERI / "k5_cumleleri.csv", ["kod", "sira", "metin", "metin_en"],
            sirayi_koru(satirlar, eski, lambda r: (r["kod"], str(r["sira"]))), ";")
    print(f"K5: {len(eksenler)} iş türü, {len(cumleler)} etkinlik cümlesi" + (f" ({len(eksik)} yeni / değişen cümle çevrildi)" if eksik else ""))


def degiskenleri_denetle(canli: list[dict]) -> None:
    """Puanlar kutup cümlelerinden gelir; burada yalnızca (1) pipeline'ın tanımadığı özellik var mı, (2) canlıda ad / tanım
    son çalıştırmadan beri değişti mi bakılır. Karşılaştırma bir önceki canlı kopyayla yapılır (veri/canli_degiskenler.csv)."""
    _, yerel = csv_oku(VERI / "degiskenler.csv")
    bilinen = {r["kod"] for r in yerel}
    bilinmeyen = [d["kod"] for d in canli if d["kod"] not in bilinen]
    if bilinmeyen:
        raise BaglantiHatasi(f"Canlıda pipeline'ın tanımadığı özellik var: {', '.join(bilinmeyen)}. Bu özelliğin kutup cümleleri ve "
                             "profil yöntemi eklenmeden pipeline çalıştırılamaz (yöntem güncellemesi gerekir).")
    _, onceki = csv_oku(VERI / "canli_degiskenler.csv", ";")
    onceki_of = {r["kod"]: (r["ad"], r["aciklama"]) for r in onceki}
    farkli = [d["kod"] for d in canli if onceki_of and onceki_of.get(d["kod"]) != (d["ad"], d["aciklama"])]
    csv_yaz(VERI / "canli_degiskenler.csv", ["kod", "ad", "aciklama", "katman"], canli, ";")
    print(f"Özellikler: canlıda {len(canli)}" + (
        f" | son çalıştırmadan beri adı / tanımı değişen {len(farkli)}: {', '.join(farkli)} — puanlar kutup cümlelerinden "
        "(veri/degisken_kutuplari.csv) hesaplandığı için sonuç değişmez; kutup cümlelerinin yeni tanıma uygunluğunu kontrol edin."
        if farkli else (" — son çalıştırmadan beri değişiklik yok" if onceki_of else " — ilk kayıt alındı")))


def main():
    kurulum, sistemdekini_al = "--kurulum" in sys.argv, "--sistemdekini-al" in sys.argv
    try:
        manifest = api("GET", "/pipeline-istemci/manifest")
        calistirici = kodu_guncelle(manifest)
        if calistirici and not kurulum:
            print("Çalıştırma dosyası ya da s1 güncellendi; çalıştırma yeni hâliyle yeniden başlıyor.")
            sys.exit(KOD_YENIDEN_BASLAT)
        veriyi_al(manifest, kurulum, sistemdekini_al)
        canli = api("GET", "/pipeline-istemci/canli")
        VERI.mkdir(parents=True, exist_ok=True)
        bolumleri_esitle(canli["bolumler"])
        k5_esitle(canli["k5_eksenleri"], canli["k5_cumleleri"])
        degiskenleri_denetle(canli["degiskenler"])
        ozet = json.dumps({"ozet": canli["ozet"], "kod_surumu": manifest["kod_surumu"]}, ensure_ascii=False, indent=1)
        yol = VERI / "canli_ozet.json"
        if not yol.exists() or yol.read_text(encoding="utf-8") != ozet:   # değişmediyse dokunulmaz
            yol.write_text(ozet, encoding="utf-8")
    except BaglantiHatasi as e:
        print(f"\n!!! {e}")
        sys.exit(2)
    print("Tamam. Sıradaki: b1_bolum_esitle.py")


if __name__ == "__main__":
    main()
