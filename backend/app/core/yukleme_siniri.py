"""
[2026-10-11] Yükleme boyut sınırları — tek yerde, tutarlı.

Sınırlar (bayt = çözülmüş dosya; base64/data URL metni ~%33 daha uzundur):
  Genel istek gövdesi (her POST/PUT/PATCH)          25 MB  → 413 (Content-Length'ten ve akışta sayarak)
  POST /istemci-hata gövdesi                         32 KB
  Tablo dosyaları (Excel / CSV; base64)              10 MB ve en çok 20.000 satır
      öğrenci toplu yükleme, okul denemeleri, İş Hayatı veri dosyası (TÜİK bağlantısı dahil)
  Ön yüzde ayrıştırılıp JSON satır listesi gelen toplu yüklemeler: en çok 20.000 satır
      soru bankası, kutup soruları, bölüm açıklamaları, meslekler (ESCO), soru geçerlilik sonuçları, toplu öğrenci oluşturma
  Pipeline taslak yüklemesi (bölüm × değişken)       en çok 100.000 satır (≈300 bölüm × 160 değişken = 48.000)
  Görseller (data URL karakter sınırı, mevcut kontroller):
      profil fotoğrafı ~2 MB · kimlik doğrulama karesi ~1 MB · okul amblemi ~300 KB · portfolyo belgesi (PDF/görsel) ~1 MB
"""
from __future__ import annotations

import base64
import json

from fastapi import HTTPException

MB = 1024 * 1024
GOVDE_EN_FAZLA_BAYT = 25 * MB
TABLO_EN_FAZLA_BAYT = 10 * MB
TABLO_EN_FAZLA_SATIR = 20_000
PIPELINE_EN_FAZLA_SATIR = 100_000
YOL_SINIRLARI = {"/istemci-hata": 32 * 1024}   # yol → gövde sınırı (genelden küçük)


def _sayi(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _mb(b: int) -> str:
    return f"{b / MB:.0f} MB" if b >= MB else f"{b // 1024} KB"


def base64_coz(icerik: str, en_fazla_bayt: int = TABLO_EN_FAZLA_BAYT) -> bytes:
    """data URL ya da düz base64 → bayt. Önce metin uzunluğundan (çözmeden) sonra gerçek bayt sayısından denetler."""
    ham = (icerik or "").split(",", 1)[-1]
    if len(ham) > (en_fazla_bayt * 4) // 3 + 8:
        raise HTTPException(status_code=413, detail=f"Dosya çok büyük (en fazla {_mb(en_fazla_bayt)}).")
    try:
        veri = base64.b64decode(ham)
    except Exception:
        raise HTTPException(status_code=400, detail="Dosya okunamadı.")
    if len(veri) > en_fazla_bayt:
        raise HTTPException(status_code=413, detail=f"Dosya çok büyük (en fazla {_mb(en_fazla_bayt)}).")
    return veri


def satir_siniri(n: int, en_fazla: int = TABLO_EN_FAZLA_SATIR) -> None:
    if n > en_fazla:
        raise HTTPException(status_code=413, detail=f"Bir yüklemede en fazla {_sayi(en_fazla)} satır olabilir "
                                                    f"(gönderilen: {_sayi(n)}). Dosyayı bölerek yükleyin.")


class GovdeCokBuyuk(Exception):
    pass


def _yanit_413(sinir: int) -> tuple[dict, dict]:
    govde = json.dumps({"detail": f"İstek çok büyük (en fazla {_mb(sinir)}). Daha küçük bir dosya yükleyin."},
                       ensure_ascii=False).encode("utf-8")
    return ({"type": "http.response.start", "status": 413, "headers": [
        (b"content-type", b"application/json; charset=utf-8"), (b"content-length", str(len(govde)).encode())]},
        {"type": "http.response.body", "body": govde})


class GovdeBoyutuAraKatmani:
    """Saf ASGI ara katmanı: Content-Length sınırı aşıyorsa uygulamaya hiç girmeden 413.
    Başlık yoksa / yanlışsa gövde akarken sayılır; sınır aşılınca okuma kesilir ve yanıt 413'e çevrilir
    (FastAPI gövde okuma hatasını 400'e sardığı için yanıt başlangıcı burada yakalanıp değiştirilir)."""

    def __init__(self, app, en_fazla: int = GOVDE_EN_FAZLA_BAYT, yol_sinirlari: dict | None = None):
        self.app = app
        self.en_fazla = en_fazla
        self.yol_sinirlari = YOL_SINIRLARI if yol_sinirlari is None else yol_sinirlari

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in ("POST", "PUT", "PATCH"):
            return await self.app(scope, receive, send)
        sinir = self.yol_sinirlari.get(scope.get("path", "").rstrip("/"), self.en_fazla)
        for ad, deger in scope.get("headers") or []:
            if ad == b"content-length":
                try:
                    uzunluk = int(deger)
                except ValueError:
                    uzunluk = 0
                if uzunluk > sinir:
                    bas, govde = _yanit_413(sinir)
                    await send(bas)
                    await send(govde)
                    return
                break

        durum = {"okunan": 0, "asildi": False, "basladi": False, "yutuluyor": False}

        async def say_receive():
            mesaj = await receive()
            if mesaj["type"] == "http.request":
                durum["okunan"] += len(mesaj.get("body", b""))
                if durum["okunan"] > sinir:
                    durum["asildi"] = True
                    raise GovdeCokBuyuk()
            return mesaj

        async def degistir_send(mesaj):
            if mesaj["type"] == "http.response.start":
                durum["basladi"] = True
                if durum["asildi"]:
                    bas, govde = _yanit_413(sinir)
                    await send(bas)
                    await send(govde)
                    durum["yutuluyor"] = True
                    return
            if durum["yutuluyor"]:
                return
            await send(mesaj)

        try:
            await self.app(scope, say_receive, degistir_send)
        except GovdeCokBuyuk:
            if not durum["basladi"]:
                bas, govde = _yanit_413(sinir)
                await send(bas)
                await send(govde)
