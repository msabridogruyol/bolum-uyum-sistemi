# -*- coding: utf-8 -*-
"""
[2026-10-12] Çoklu dil — sunucu tarafı.

1) İstek dili: istemci her isteğe `X-Dil` başlığı ekler (frontend/src/yardimci/dil.js). DilAraKatmani bunu
   bir bağlam değişkenine yazar; Filiz (openai_ile_konus) cevabı bu dilde verir.
2) İçerik çevirisi: arayüz metinleri tarayıcıdaki dil paketinden çevrilir. Pakette olmayan uzun sistem içerikleri
   (bölüm açıklamaları, sözlük, iş hayatı içerikleri) POST /ceviri/icerik ile buradan istenir:
     * Yalnızca İÇERİK HAVUZUNDA bulunan metinler çevrilir: bolumler.detay, app/data/*.json ve sözlük dosyası.
       Havuzda olmayan hiçbir metin (öğrenci adı, kullanıcı yazısı vb.) yapay zekâya gönderilmez.
     * Her metin bir dile bir kez çevrilir ve ceviri_onbellek tablosunda saklanır; sonraki isteklerde veritabanından okunur.
     * OpenAI anahtarı yoksa ya da çeviri zamanında bitmezse metin Türkçe kalır (hata verilmez).
"""
from __future__ import annotations

import contextvars
import hashlib
import json
import logging
import os
import pathlib
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

from sqlalchemy import text
from sqlalchemy.orm import Session

_log = logging.getLogger("ceviri")

DILLER = {
    "tr": "Türkçe", "en": "English", "de": "Deutsch", "fr": "Français", "ru": "Русский", "es": "Español",
    "it": "Italiano", "ar": "العربية", "zh": "中文", "hi": "हिन्दी", "uz": "Oʻzbekcha", "az": "Azərbaycanca", "ko": "한국어",
}
# Yapay zekâya verilecek dil adı (İngilizce adı daha güvenilir sonuç verir)
DIL_INGILIZCE = {
    "en": "English", "de": "German", "fr": "French", "ru": "Russian", "es": "Spanish", "it": "Italian",
    "ar": "Modern Standard Arabic", "zh": "Simplified Chinese", "hi": "Hindi", "uz": "Uzbek (Latin script)",
    "az": "Azerbaijani (Latin script)", "ko": "Korean",
}

_istek_dili: contextvars.ContextVar[str] = contextvars.ContextVar("istek_dili", default="tr")


def dil_coz(deger: str | None) -> str:
    d = (deger or "").strip().lower()[:5].split("-")[0]
    return d if d in DILLER else "tr"


def istek_dili() -> str:
    return _istek_dili.get()


class DilAraKatmani:
    """Saf ASGI ara katmanı: X-Dil başlığını bağlam değişkenine yazar (eşzamanlı uç noktalara da geçer)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        deger = None
        for ad, v in scope.get("headers") or []:
            if ad == b"x-dil":
                deger = v.decode("latin-1", "ignore")
                break
        jeton = _istek_dili.set(dil_coz(deger))
        try:
            await self.app(scope, receive, send)
        finally:
            _istek_dili.reset(jeton)


def yapay_zeka_dil_talimati() -> str:
    """Filiz için: seçili dil Türkçe değilse cevabı o dilde vermesini söyleyen ek talimat."""
    d = istek_dili()
    if d == "tr":
        return ""
    return (f"\n\nDİL: Öğrenci arayüzü {DIL_INGILIZCE[d]} dilinde kullanıyor. Cevabını tamamen {DIL_INGILIZCE[d]} "
            f"dilinde yaz (Always answer in {DIL_INGILIZCE[d]}). YKS, TYT, AYT, YÖK Atlas gibi Türk sınav ve kurum adlarını "
            f"çevirmeden bırak; bölüm adlarını çevirebilirsin.")


# ----------------------------------------------------------------------------- içerik havuzu
_VERI = pathlib.Path(__file__).resolve().parent.parent / "data"
_HAVUZ: set[str] = set()
_HAVUZ_ZAMAN = 0.0
_HAVUZ_KILIT = threading.Lock()
HAVUZ_SN = 600
EN_KISA, EN_UZUN = 12, 4000

_ozet = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
_normal = lambda s: re.sub(r"\s+", " ", s).strip()


def _yapraklar(v, cikti: set[str]):
    if isinstance(v, str):
        s = _normal(v)
        if EN_KISA <= len(s) <= EN_UZUN and re.search(r"[^\W\d_]{3,}", s):
            cikti.add(s)
            # Ekranda paragraf / madde olarak bölünen metinler için satır ve cümle grupları da havuza girer
            if "\n" in v:
                for satir in v.split("\n"):
                    t = _normal(satir.lstrip("-•* "))
                    if EN_KISA <= len(t) <= EN_UZUN:
                        cikti.add(t)
    elif isinstance(v, dict):
        for x in v.values():
            _yapraklar(x, cikti)
    elif isinstance(v, (list, tuple)):
        for x in v:
            _yapraklar(x, cikti)


def _havuz_kur(db: Session) -> set[str]:
    h: set[str] = set()
    for f in sorted(_VERI.glob("*.json")):
        try:
            _yapraklar(json.loads(f.read_text("utf-8")), h)
        except Exception as e:  # bozuk dosya diğerlerini engellemesin
            _log.warning("Çeviri havuzu: %s okunamadı: %s", f.name, e)
    try:
        for (detay,) in db.execute(text("SELECT detay FROM bolumler WHERE detay IS NOT NULL")).all():
            _yapraklar(detay, h)
        for (m,) in db.execute(text("SELECT meslekler FROM meslek_grubu_ai_etkisi WHERE meslekler IS NOT NULL")).all():
            _yapraklar(m, h)
    except Exception as e:
        _log.warning("Çeviri havuzu: veritabanı içeriği okunamadı: %s", e)
        db.rollback()
    return h


def havuz(db: Session) -> set[str]:
    global _HAVUZ, _HAVUZ_ZAMAN
    if _HAVUZ and time.time() - _HAVUZ_ZAMAN < HAVUZ_SN:
        return _HAVUZ
    with _HAVUZ_KILIT:
        if not _HAVUZ or time.time() - _HAVUZ_ZAMAN >= HAVUZ_SN:
            _HAVUZ = _havuz_kur(db)
            _HAVUZ_ZAMAN = time.time()
    return _HAVUZ


def havuzu_temizle():
    global _HAVUZ_ZAMAN
    _HAVUZ_ZAMAN = 0.0


# ----------------------------------------------------------------------------- yapay zekâ çevirisi
PARTI = 25          # bir istekte en çok metin
ESZAMANLI = 4       # aynı anda en çok OpenAI isteği
SURE_SN = 25        # bir /ceviri/icerik isteğinde en çok bekleme


def _anahtar_var() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def _parti_cevir(metinler: list[str], dil: str) -> list[str | None]:
    """OpenAI ile toplu çeviri. Test ortamında bu fonksiyon değiştirilebilir (monkeypatch)."""
    # [2026-10-31] Filiz'le aynı yapay zekâ kapısı: eşzamanlılık sınırı, yeniden deneme yok; kapı doluysa çeviri atlanır (Türkçe kalır)
    from app.core.ai_koc_servisi import yz_sohbet
    istem = (
        f"Translate each Turkish text in the JSON array into {DIL_INGILIZCE[dil]}. The texts are content of a career-guidance "
        "app for high-school students (university majors, occupations, glossary). Keep emojis, numbers, URLs, markdown and "
        "line breaks. Do not translate the names YKS, TYT, AYT, YÖK Atlas, ÖSYM, KPSS, Filizyol, Filiz or Turkish proper names "
        "(universities, cities, institutions). Address the student informally, as the Turkish does. "
        'Return ONLY a JSON object {"t": [...]} with the translations in the same order and the same count.'
    )
    icerik = yz_sohbet([{"role": "system", "content": istem}, {"role": "user", "content": json.dumps(metinler, ensure_ascii=False)}],
                       temperature=0.2, max_tokens=None, yedek=False, zaman_asimi=SURE_SN, response_format={"type": "json_object"})
    veri = json.loads(icerik or "{}")
    t = veri.get("t") if isinstance(veri, dict) else None
    if not isinstance(t, list) or len(t) != len(metinler):
        return [None] * len(metinler)
    return [x.strip() if isinstance(x, str) and x.strip() else None for x in t]


_HAVUZ_IS = ThreadPoolExecutor(max_workers=ESZAMANLI, thread_name_prefix="ceviri")


def onbellekten(db: Session, metinler: list[str], dil: str) -> dict[str, str]:
    if not metinler:
        return {}
    ozetler = {_ozet(m): m for m in metinler}
    satirlar = db.execute(
        text("SELECT kaynak_ozet, ceviri FROM ceviri_onbellek WHERE dil = :d AND kaynak_ozet = ANY(:o)"),
        {"d": dil, "o": list(ozetler)},
    ).all()
    return {ozetler[o.strip()]: c for o, c in satirlar if o.strip() in ozetler}


def _kaydet(db: Session, dil: str, ciftler: list[tuple[str, str]]):
    for kaynak, ceviri in ciftler:
        db.execute(
            text("INSERT INTO ceviri_onbellek (dil, kaynak_ozet, kaynak, ceviri) VALUES (:d, :o, :k, :c) "
                 "ON CONFLICT (dil, kaynak_ozet) DO NOTHING"),
            {"d": dil, "o": _ozet(kaynak), "k": kaynak, "c": ceviri},
        )
    db.commit()


_SURUYOR: set[tuple[str, str]] = set()
_SURUYOR_KILIT = threading.Lock()


def _arka_planda_kaydet(dil: str, ciftler: list[tuple[str, str]]):
    """İstek beklemeyi bıraktıktan sonra biten çeviriyi kendi oturumuyla saklar (sonraki istekte hazır olur)."""
    if not ciftler:
        return
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        _kaydet(db, dil, ciftler)
    except Exception as e:
        db.rollback()
        _log.warning("Çeviri önbelleğe yazılamadı: %s", e)
    finally:
        db.close()


def _cevir(parti: list[str], dil: str) -> list[tuple[str, str]]:
    try:
        return [(k, c) for k, c in zip(parti, _parti_cevir(parti, dil)) if c]
    finally:
        with _SURUYOR_KILIT:
            for k in parti:
                _SURUYOR.discard((dil, k))


def icerik_cevir(db: Session, metinler: list[str], dil: str) -> list[str | None]:
    """Sıra korunur; çevrilemeyen / havuzda olmayan metin için None."""
    if dil == "tr" or dil not in DIL_INGILIZCE:
        return [None] * len(metinler)
    normal = [_normal(m or "") for m in metinler]
    h = havuz(db)
    uygun = sorted({m for m in normal if m in h})
    sonuc = onbellekten(db, uygun, dil)
    if _anahtar_var():
        with _SURUYOR_KILIT:   # aynı metin başka bir istekte zaten çevriliyorsa ikinci kez gönderilmez
            eksik = [m for m in uygun if m not in sonuc and (dil, m) not in _SURUYOR]
            _SURUYOR.update((dil, m) for m in eksik)
        isler = [_HAVUZ_IS.submit(_cevir, eksik[i:i + PARTI], dil) for i in range(0, len(eksik), PARTI)]
        bitis = time.time() + SURE_SN
        yeni: list[tuple[str, str]] = []
        for is_ in isler:
            try:
                ciftler = is_.result(timeout=max(0.1, bitis - time.time()))
            except FuturesTimeout:
                # Bekleme süresi doldu: çeviri bitince arka planda saklanır, sonraki istekte hazır olur
                is_.add_done_callback(lambda f: _arka_planda_kaydet(dil, f.result()) if not f.exception() else None)
                _log.info("İçerik çevirisi arka planda sürüyor (%s)", dil)
                continue
            except Exception as e:  # kota / ağ / anahtar hatası: Türkçe kalır
                _log.warning("İçerik çevirisi alınamadı (%s): %s", dil, type(e).__name__)
                continue
            yeni.extend(ciftler)
            sonuc.update(ciftler)
        if yeni:
            try:
                _kaydet(db, dil, yeni)
            except Exception as e:
                db.rollback()
                _log.warning("Çeviri önbelleğe yazılamadı: %s", e)
    return [sonuc.get(m) for m in normal]
