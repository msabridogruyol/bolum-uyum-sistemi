# -*- coding: utf-8 -*-
"""
[2026-11-01] Pipeline veri deposu — "disk" türü (kendi sunucu). Ayar: PIPELINE_DEPO=disk, PIPELINE_DEPO_DIZINI=<klasör>.

Supabase türüyle aynı davranış, aynı işlevler:
  * Parçalar <klasör>/parca/<sha256> olarak durur (içerik özetiyle adlandırılır, değişmeyen parça yeniden gönderilmez).
  * Bilgisayar parçayı backend üzerinden yükler / indirir. Adres kısa süreli imzalıdır (HMAC, JWT_SECRET_KEY ile):
      GET / PUT  /pipeline-istemci/depo/<sha256>?islem=indir|yukle&son=<unix zaman>&imza=<hmac>
    Adres göreli verilir; bilgisayar kendi ayar.json'daki sistem adresinin önüne ekler (alan adı değişse de doğru kalır).
  * Yüklemede içerik özeti sunucuda denetlenir: adıyla uyuşmayan parça kabul edilmez (bozuk parça depoya giremez).
Ek kütüphane ya da servis gerekmez; klasörün yedeği alınması yeterlidir.
"""
import hashlib
import hmac
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

ADRES_ONEKI = "/pipeline-istemci/depo"


def _dizin() -> Path:
    return Path(settings.PIPELINE_DEPO_DIZINI).expanduser() / "parca"


def _hata(m):
    from app.core.pipeline_depo import DepoHatasi
    return DepoHatasi(m)


def hazir_mi() -> bool:
    try:
        _dizin().mkdir(parents=True, exist_ok=True)
        return os.access(_dizin(), os.W_OK)
    except OSError:
        return False


def kova_hazirla() -> None:
    if not hazir_mi():
        raise _hata(f"Disk deposu klasörü oluşturulamadı ya da yazılamıyor: {_dizin()}")


def _yol(sha256: str) -> Path:
    if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
        raise _hata("Geçersiz parça özeti.")
    return _dizin() / sha256


def mevcut_parcalar() -> dict[str, str]:
    if not _dizin().exists():
        return {}
    sonuc = {}
    for p in _dizin().iterdir():
        if p.is_file() and len(p.name) == 64:
            sonuc[p.name] = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()
    return sonuc


def _imza(islem: str, sha256: str, son: int) -> str:
    return hmac.new(settings.JWT_SECRET_KEY.encode(), f"{islem}:{sha256}:{son}".encode(), hashlib.sha256).hexdigest()


def _adres(islem: str, sha256: str, sure_sn: int) -> str:
    son = int(time.time()) + sure_sn
    return f"{ADRES_ONEKI}/{sha256}?islem={islem}&son={son}&imza={_imza(islem, sha256, son)}"


def imza_gecerli_mi(islem: str, sha256: str, son: int, imza: str) -> bool:
    return son >= time.time() and hmac.compare_digest(_imza(islem, sha256, son), imza or "")


def indirme_adresleri(ozetler: list[str], sure_sn: int = 3600) -> dict[str, str]:
    sonuc = {}
    for o in ozetler:
        if not _yol(o).exists():
            raise _hata(f"Parça depoda yok: {o[:12]}…")
        sonuc[o] = _adres("indir", o, sure_sn)
    return sonuc


def yukleme_adresi(sha256: str) -> str:
    _yol(sha256)
    return _adres("yukle", sha256, 3600)


def parca_oku(sha256: str) -> bytes:
    p = _yol(sha256)
    if not p.exists():
        raise _hata("Parça depoda yok.")
    return p.read_bytes()


def parca_yaz(sha256: str, veri: bytes) -> None:
    if hashlib.sha256(veri).hexdigest() != sha256:
        raise _hata("Parça içeriği adıyla uyuşmuyor; kabul edilmedi.")
    p = _yol(sha256)
    p.parent.mkdir(parents=True, exist_ok=True)
    gecici = p.with_name(p.name + f".{os.getpid()}.tmp")
    gecici.write_bytes(veri)
    os.replace(gecici, p)


def parcalari_sil(ozetler: list[str]) -> int:
    for o in ozetler:
        try:
            _yol(o).unlink()
        except FileNotFoundError:
            pass
    return len(ozetler)


def parca_bozuk_mu(sha256: str) -> bool:
    p = _yol(sha256)
    if not p.exists():
        return False
    if hashlib.sha256(p.read_bytes()).hexdigest() == sha256:
        return False
    p.unlink()
    return True
