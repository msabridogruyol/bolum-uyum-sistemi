# -*- coding: utf-8 -*-
r"""
S2 — Bu çalıştırmanın veri, önbellek ve çıktı dosyalarını sisteme (Supabase Storage) gönderir            [2026-11-01]

Neden: pipeline başka bir bilgisayarda çalıştırıldığında en son veriyle başlasın; hazır vektörler olmadan yeni bilgisayar
saatlerce yeniden hesaplamak zorunda kalır ve sonuçlar bilgisayardan bilgisayara çok küçük de olsa farklılaşabilir.
  * Kapsam: veri/, onet/, onbellek/, cikti/ (kod sistemden ayrıca gelir; yedekler/, venv/, _silinecek/ gönderilmez).
  * Dosyalar 20 MB'lık parçalara bölünür; sistemde zaten olan parça gönderilmez (genellikle yalnızca değişenler gider).
  * Sürüm kaydına bu çalıştırmada kullanılan canlı listelerin özeti (veri/canli_ozet.json) eklenir; admin panelindeki sayaç
    "son çalıştırmadan beri bölüm / K5 listesi değişti mi" sorusunu buna bakarak yanıtlar.
  * Bu adım hiçbir şeyi canlıya ALMAZ. Çıktılar yine admin → Pipeline Sonuçları ekranından canlıya alınır.
Kullanım:  C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\s2_sisteme_gonder.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sistem_baglanti import (KOK, PARCA_BOYUTU, BaglantiHatasi, api, ayar, dosya_ozeti, durum_oku, durum_yaz,  # noqa: E402
                             parca_oku, sha256, yerel_dosyalar, yukle)


def main():
    zorla = "--zorla" in sys.argv
    try:
        a = ayar()
        taban = (durum_oku() or {}).get("surum_id")      # bu bilgisayarın en son aldığı / gönderdiği sürüm
        dosyalar = {y: dosya_ozeti(p) for y, p in yerel_dosyalar().items()}
        if not dosyalar:
            raise BaglantiHatasi("Gönderilecek dosya bulunamadı.")
        parca_yeri = {}
        for y, d in dosyalar.items():
            for i, p in enumerate(d["parcalar"]):
                parca_yeri.setdefault(p, (KOK / y, i, d["boyut"]))
        istek = [{"sha256": p, "boyut": min(PARCA_BOYUTU, yer[2] - yer[1] * PARCA_BOYUTU)} for p, yer in parca_yeri.items()]
        eksik, var_olan = {}, 0
        for i in range(0, len(istek), 100):                # sunucu her grupta yalnızca eksikler için adres üretir
            c = api("POST", "/pipeline-istemci/gonderim/baslat", {"parcalar": istek[i:i + 100]})
            eksik.update(c["eksik"]); var_olan += c["var_olan"]
        gonderilen = 0
        for n, (p, adres) in enumerate(sorted(eksik.items()), 1):
            yol, sira, _ = parca_yeri[p]
            veri = parca_oku(yol, sira)
            if sha256(veri) != p:
                raise BaglantiHatasi(f"{yol.relative_to(KOK).as_posix()} gönderim sırasında değişti; pipeline bitmeden "
                                     "dosyaları açmayın ve bu adımı tekrar çalıştırın.")
            yukle(adres, veri)
            gonderilen += len(veri)
            print(f"  {n}/{len(eksik)} parça gönderildi ({yol.relative_to(KOK).as_posix()}, {len(veri) / 1e6:.1f} MB)", flush=True)
        ozet_yolu = KOK / "veri" / "canli_ozet.json"
        girdi = json.loads(ozet_yolu.read_text(encoding="utf-8")).get("ozet") if ozet_yolu.exists() else None
        try:
            sonuc = api("POST", "/pipeline-istemci/gonderim/tamamla",
                        {"dosyalar": dosyalar, "girdi_ozeti": girdi, "aciklama": f"{a.get('cihaz_adi', '')}",
                         "taban_surum_id": taban, "zorla": zorla})
        except BaglantiHatasi as e:
            if "(409)" in str(e):
                raise BaglantiHatasi(
                    f"{e}\nİki seçenek var:\n"
                    "  * Diğer bilgisayarın sonucunu kullanmak (buradaki sonuç gönderilmez):  "
                    "pipeline_calistir.ps1 -SistemdekiniAl\n"
                    "  * Bu bilgisayarın sonucunu en yeni yapmak (diğeri sürüm geçmişinde kalır):  "
                    "C:\\pipeline\\venv\\Scripts\\python.exe C:\\pipeline\\src\\s2_sisteme_gonder.py --zorla")
            raise
        durum_yaz(sonuc["surum_id"], dosyalar)
    except BaglantiHatasi as e:
        print(f"\n!!! {e}\nÇıktılar bu bilgisayarda duruyor; canlıya alma etkilenmez. Sorun giderilince yalnızca bu adımı "
              "çalıştırabilirsiniz:  C:\\pipeline\\venv\\Scripts\\python.exe C:\\pipeline\\src\\s2_sisteme_gonder.py")
        sys.exit(2)
    toplam = sum(d["boyut"] for d in dosyalar.values())
    print(f"Tamam: veri sürümü {sonuc['surum_id']} kaydedildi — {len(dosyalar)} dosya ({toplam / 1e6:.0f} MB); "
          f"{len(eksik)} yeni parça gönderildi ({gonderilen / 1e6:.1f} MB), {var_olan} parça sistemde zaten vardı.")


if __name__ == "__main__":
    main()
