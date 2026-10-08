"""
[2026-10-08] YÖK Atlas'tan bölümün üniversite/program bilgilerini (kontenjan, taban puan, başarı sırası)
çeker ve veritabanında önbellekler.

Kaynak: yokatlas.yok.gov.tr tercih kılavuzu JSON uç noktaları (yokatlas-py kütüphanesi üzerinden).
ÖNEMLİ: Bu, YÖK Atlas'ın resmî olarak belgelenmiş/açık bir API'si değildir; site yapısı değişirse
çalışmayabilir. Bu yüzden:
  - Sonuçlar YOKATLAS_ONBELLEK_GUN gün veritabanında tutulur (YÖK Atlas'a bölüm başına haftada en fazla 1 istek).
  - Hata olursa son başarılı veri döner; hiç veri yoksa ekranda kibar bir mesaj gösterilir.
  - Özellik, sistem parametresi 'yokatlas_aktif' = 'false' yapılarak kapatılabilir.
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Bolum, YokatlasOnbellek
from app.core.katman_servisi import parametre_oku

YOKATLAS_ONBELLEK_GUN = 7
MAKS_PROGRAM = 600          # bir bölüm için en fazla bu kadar program satırı saklanır
_istemci = None
_kilit = threading.Lock()


def _normalize(metin: str) -> str:
    tablo = str.maketrans("ÇĞİIÖŞÜçğıöşüÂâÎîÛû", "cgiiosucgiosuaaiiuu")
    return " ".join((metin or "").translate(tablo).lower().split())


def _istemci_al():
    global _istemci
    with _kilit:
        if _istemci is None:
            from yokatlas_py import YokAtlasClient  # gecikmeli import: kütüphane yoksa uygulama yine açılır
            from yokatlas_py.config import Settings
            _istemci = YokAtlasClient(settings=Settings(timeout=15, max_retries=1, lookup_cache_ttl=86400))
        return _istemci


def _program_grubu_idleri(bolum_adi: str) -> list[int]:
    """Bölüm adıyla BİREBİR (Türkçe-normalize) aynı adlı YÖK Atlas program gruplarını döner.
    Benzer adlı başka bir bölümü yanlışlıkla göstermemek için bulanık eşleşme KULLANILMAZ."""
    hedef = _normalize(bolum_adi)
    return [g.birim_grup_id for g in _istemci_al().list_program_groups() if _normalize(g.birim_grup_adi) == hedef]


def _satir(p) -> dict:
    c = p.current
    return {
        "kilavuz_kodu": p.kilavuz_kodu,
        "universite": p.universite_adi,
        "universite_turu": p.universite_turu,
        "il": p.uni_il_adi or p.il_adi,
        "fakulte": p.fymk_adi,
        "program": p.birim_adi,
        "puan_turu": p.puan_turu,
        "ogrenim_dili": p.ogrenim_dili_adi,
        "burs": p.burs_orani_adi,
        "ogrenim_turu": p.ogrenim_turu_adi,
        "ogrenim_suresi": p.ogrenim_suresi,
        "yil": c.year,
        "kontenjan": c.kontenjan,
        "yerlesen": c.yerlesen,
        "taban_puan": c.min_puan,
        "basari_sirasi": c.basari_sirasi,
        "gecmis": [
            {"yil": h.year, "kontenjan": h.kontenjan, "taban_puan": h.min_puan, "basari_sirasi": h.basari_sirasi}
            for h in p.history if h.kontenjan or h.min_puan or h.basari_sirasi
        ],
    }


def _yokatlastan_cek(bolum_adi: str) -> dict:
    gruplar = _program_grubu_idleri(bolum_adi)
    if not gruplar:
        return {"eslesme": False, "programlar": [], "yil": None}
    istemci = _istemci_al(); satirlar = []; yil = None; sayfa = 0
    while len(satirlar) < MAKS_PROGRAM:
        s = istemci.search({"birim_grup_id": gruplar}, page=sayfa, size=100, sort_by="basariSirasi",
                           direction="ASC", smart_search=False)
        yil = yil or s.yil
        satirlar += [_satir(p) for p in s.content]
        if s.last or not s.content:
            break
        sayfa += 1
    return {"eslesme": True, "programlar": satirlar, "yil": yil}


def bolum_universiteleri(db: Session, bolum: Bolum) -> dict:
    """Önbellek tazeyse onu, değilse YÖK Atlas'tan yenisini döner. Hata durumunda eski veri korunur."""
    kayit = db.get(YokatlasOnbellek, bolum.id)
    simdi = datetime.now(timezone.utc)
    taze = kayit is not None and kayit.veri is not None and kayit.guncellenme is not None and \
        (simdi - kayit.guncellenme.replace(tzinfo=kayit.guncellenme.tzinfo or timezone.utc)) < timedelta(days=YOKATLAS_ONBELLEK_GUN)
    aktif = (parametre_oku(db, "yokatlas_aktif", "true") or "true").lower() != "false"

    if not taze and aktif:
        try:
            veri = _yokatlastan_cek(bolum.ad)
            if kayit is None:
                kayit = YokatlasOnbellek(bolum_id=bolum.id)
                db.add(kayit)
            kayit.veri = veri; kayit.guncellenme = simdi; kayit.hata = None
            db.commit()
        except Exception as e:  # ağ hatası, YÖK Atlas yapı değişikliği vb.
            db.rollback()
            kayit = db.get(YokatlasOnbellek, bolum.id)
            if kayit is None:
                return {"durum": "hata", "mesaj": "Üniversite bilgileri şu anda YÖK Atlas'tan alınamıyor. Daha sonra tekrar dene.",
                        "programlar": [], "yil": None, "kaynak": "YÖK Atlas"}
            kayit.hata = str(e)[:500]; db.commit()

    if kayit is None or kayit.veri is None:
        return {"durum": "kapali", "mesaj": "Üniversite bilgileri şu anda gösterilemiyor.", "programlar": [], "yil": None, "kaynak": "YÖK Atlas"}
    v = kayit.veri
    if not v.get("eslesme"):
        return {"durum": "eslesme_yok", "mesaj": "Bu bölüm YÖK Atlas'ta tek bir program adıyla yer almıyor (farklı adlarla açılıyor olabilir).",
                "programlar": [], "yil": None, "kaynak": "YÖK Atlas"}
    return {"durum": "tamam", "mesaj": None, "programlar": v.get("programlar", []), "yil": v.get("yil"),
            "guncellenme": kayit.guncellenme.isoformat() if kayit.guncellenme else None, "kaynak": "YÖK Atlas"}
