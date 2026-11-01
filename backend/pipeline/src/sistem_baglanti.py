# -*- coding: utf-8 -*-
"""
Sistemle bağlantı (s1 ve s2 kullanır). Yalnızca Python'un kendi kütüphaneleri; ek kurulum gerekmez.     [2026-11-01]

  ayar.json            — kurulumda yazılır: {"api": sistem adresi, "anahtar": bilgisayar anahtarı, "cihaz_adi": ...}
  .senkron_durumu.json — bu bilgisayarın en son aldığı / gönderdiği veri sürümü ve dosya özetleri
Veri dosyaları sistemde (Supabase Storage) PARCA_BOYUTU'luk parçalar hâlinde, içerik özetiyle saklanır;
değişmeyen parça bir daha gönderilmez ve indirilmez.
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KOK = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else Path(__file__).resolve().parents[1]
AYAR = KOK / "ayar.json"
DURUM = KOK / ".senkron_durumu.json"
PARCA_BOYUTU = 20 * 1024 * 1024
# Sistemde saklanan klasörler (kod hariç: kod sistemden ayrıca gelir)
KAPSAM = ("veri", "onet", "onbellek", "cikti")
HARIC_AD = {"calistirma_log.txt", "_esco_ad_tr_checkpoint.json", "_esco_aciklama_tr_checkpoint.json"}
HARIC_UZANTI = {".pyc", ".tmp"}


class BaglantiHatasi(Exception):
    pass


def ayar() -> dict:
    if not AYAR.exists():
        raise BaglantiHatasi("Bu bilgisayar sisteme bağlı değil (ayar.json yok). Admin paneli → Pipeline Sonuçları → "
                             "'Bu bilgisayara kur' ile kurulum dosyasını indirip çalıştırın.")
    return json.loads(AYAR.read_text(encoding="utf-8-sig"))


def _yeniden_dene(fn, deneme: int = 4):
    for i in range(deneme):
        try:
            return fn()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if isinstance(e, urllib.error.HTTPError) and (e.code < 500 or i == deneme - 1):
                raise   # çağıran sunucunun açıklamasını (detail) okuyup gösterir
            if i == deneme - 1:
                raise BaglantiHatasi(f"Sisteme ulaşılamadı: {e}")
            time.sleep(2 * (i + 1))


def api(yontem: str, yol: str, govde=None, ham: bool = False, zaman_asimi: int = 120):
    a = ayar()
    veri = None if govde is None else json.dumps(govde, ensure_ascii=False).encode("utf-8")
    istek = urllib.request.Request(a["api"].rstrip("/") + yol, data=veri, method=yontem,
                                   headers={"X-Pipeline-Anahtari": a["anahtar"], "Content-Type": "application/json"})

    def cagir():
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as y:
            icerik = y.read()
            return icerik if ham else (json.loads(icerik) if icerik else None)
    try:
        return _yeniden_dene(cagir)
    except urllib.error.HTTPError as e:
        try:
            ayrinti = json.loads(e.read()).get("detail")
        except Exception:
            ayrinti = None
        if ayrinti is None and e.code >= 500:
            raise BaglantiHatasi(f"Sisteme ulaşılamadı ({e.code}: {e.reason}). Sunucu yeniden başlıyor ya da kapalı olabilir; "
                                 "birkaç dakika sonra tekrar deneyin.")
        raise BaglantiHatasi(f"Sistem isteği reddetti ({e.code}): {ayrinti or e.reason}")


class AdresSuresiDoldu(BaglantiHatasi):
    pass


def tam_adres(adres: str) -> str:
    """Depo adresi göreli gelebilir (sunucunun kendi diskindeki depo: /pipeline-istemci/depo/...): sistem adresine eklenir."""
    return ayar()["api"].rstrip("/") + adres if adres.startswith("/") else adres


def indir(adres: str) -> bytes:
    adres = tam_adres(adres)

    def cagir():
        with urllib.request.urlopen(adres, timeout=300) as y:
            return y.read()
    try:
        return _yeniden_dene(cagir)
    except urllib.error.HTTPError as e:
        if e.code in (400, 401, 403):
            raise AdresSuresiDoldu(f"İndirme adresi geçersiz ya da süresi dolmuş ({e.code}).")
        raise BaglantiHatasi(f"Depodan indirilemedi ({e.code}).")


def yukle(adres: str, veri: bytes) -> None:
    istek = urllib.request.Request(tam_adres(adres), data=veri, method="PUT",
                                   headers={"Content-Type": "application/octet-stream", "x-upsert": "true"})

    def cagir():
        with urllib.request.urlopen(istek, timeout=600) as y:
            y.read()
    try:
        _yeniden_dene(cagir)
    except urllib.error.HTTPError as e:
        govde = e.read()[:300]
        # Önceki deneme aslında yüklenmişse (zaman aşımı sonrası tekrar): parça içerik özetiyle adlandırıldığı için aynıdır
        if e.code in (400, 409) and (b"Duplicate" in govde or b"already exists" in govde):
            return
        raise BaglantiHatasi(f"Depoya yükleme reddedildi ({e.code}): {govde!r}")


def sha256(veri: bytes) -> str:
    return hashlib.sha256(veri).hexdigest()


def dosya_ozeti(yol: Path) -> dict:
    """Dosyanın tam özeti + parça özetleri."""
    h, parcalar, boyut = hashlib.sha256(), [], 0
    with open(yol, "rb") as f:
        while True:
            parca = f.read(PARCA_BOYUTU)
            if not parca:
                break
            h.update(parca); parcalar.append(sha256(parca)); boyut += len(parca)
    return {"sha256": h.hexdigest(), "boyut": boyut, "parcalar": parcalar}


def parca_oku(yol: Path, sira: int) -> bytes:
    with open(yol, "rb") as f:
        f.seek(sira * PARCA_BOYUTU)
        return f.read(PARCA_BOYUTU)


def guvenli_hedef(yol: str, klasorler=KAPSAM) -> Path:
    """Sistemden gelen göreli yolu bu bilgisayardaki pipeline klasörü içinde tutar (dışarı yazılamaz)."""
    parcalar = yol.replace("\\", "/").split("/")
    if not yol or yol.startswith("/") or ":" in yol or any(p in ("", ".", "..") for p in parcalar) or \
            (klasorler is not None and parcalar[0] not in klasorler):
        raise BaglantiHatasi(f"Sistemden beklenmeyen dosya yolu geldi, yazılmadı: {yol[:120]!r}")
    hedef = (KOK / yol).resolve()
    if not hedef.is_relative_to(KOK.resolve()):
        raise BaglantiHatasi(f"Sistemden beklenmeyen dosya yolu geldi, yazılmadı: {yol[:120]!r}")
    return hedef


def yerel_dosyalar() -> dict[str, Path]:
    sonuc = {}
    for klasor in KAPSAM:
        for p in sorted((KOK / klasor).rglob("*")):
            if p.is_file() and p.name not in HARIC_AD and p.suffix not in HARIC_UZANTI and "__pycache__" not in p.parts:
                sonuc[p.relative_to(KOK).as_posix()] = p
    return sonuc


def durum_oku() -> dict | None:
    return json.loads(DURUM.read_text(encoding="utf-8")) if DURUM.exists() else None


def durum_yaz(surum_id, dosyalar: dict) -> None:
    gecici = DURUM.with_suffix(".yaziliyor")
    gecici.write_text(json.dumps({"surum_id": surum_id, "dosyalar": {y: d["sha256"] for y, d in dosyalar.items()}},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(gecici, DURUM)
